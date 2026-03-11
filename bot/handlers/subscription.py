from datetime import datetime

from aiogram import Bot, Router, F
from aiogram.enums import ParseMode
from aiogram.types import CallbackQuery, LabeledPrice, Message, PreCheckoutQuery

import db
import keyboards
from config import settings

router = Router()

_MONTH_PRICE = 290000  # копейки
_YEAR_PRICE = 2900000


# --- Статус подписок ---

@router.callback_query(F.data == "subscription")
async def show_subscriptions(callback: CallbackQuery) -> None:
    subs = await db.get_subscriptions_for_user(callback.from_user.id)
    if not subs:
        await callback.message.answer(
            "📭 У вас нет объектов. Сначала добавьте объект.",
            reply_markup=keyboards.main_menu(),
        )
        await callback.answer()
        return

    now = datetime.utcnow().isoformat()
    parts = ["💳 Подписки:\n"]
    buttons = []

    for s in subs:
        exp = s["expires_at"]
        if exp and exp > now:
            exp_date = exp[:10]
            days_left = (datetime.fromisoformat(exp) - datetime.utcnow()).days
            if days_left <= 3:
                parts.append(f"🏭 «{s['name']}» — ⚠️ истекает через {days_left} дн. ({exp_date})")
                buttons.append([keyboards.InlineKeyboardButton(
                    text=f"🔄 Продлить «{s['name']}» — месяц 2 900 ₽",
                    callback_data=f"pay_month:{s['id']}",
                )])
                buttons.append([keyboards.InlineKeyboardButton(
                    text=f"🔄 Продлить «{s['name']}» — год 29 000 ₽",
                    callback_data=f"pay_year:{s['id']}",
                )])
            else:
                parts.append(f"🏭 «{s['name']}» — ✅ до {exp_date}")
        else:
            parts.append(f"🏭 «{s['name']}» — ❌ не оформлена")
            buttons.append([keyboards.InlineKeyboardButton(
                text=f"📅 «{s['name']}» — месяц 2 900 ₽",
                callback_data=f"pay_month:{s['id']}",
            )])
            buttons.append([keyboards.InlineKeyboardButton(
                text=f"🗓 «{s['name']}» — год 29 000 ₽ 🔥",
                callback_data=f"pay_year:{s['id']}",
            )])

    parts.append(
        "\n━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "\n📅 Тариф «Месяц» — 2 900 ₽\n"
        "Доступ к сервису SCROOGE на 30 дней для 1 объекта. "
        "Включает: неограниченное количество передач данных "
        "весового контроля в ФГИС УТКО, валидацию файлов, "
        "уведомления об успешной передаче.\n"
        "\n🗓 Тариф «Год» — 29 000 ₽\n"
        "Доступ к сервису SCROOGE на 365 дней для 1 объекта. "
        "Включает: неограниченное количество передач данных "
        "весового контроля в ФГИС УТКО, валидацию файлов, "
        "уведомления об успешной передаче. "
        "Экономия 5 800 ₽ по сравнению с месячной оплатой."
    )

    buttons.append([keyboards.InlineKeyboardButton(text="↩️ Меню", callback_data="main_menu")])

    await callback.message.answer(
        "\n".join(parts),
        reply_markup=keyboards.InlineKeyboardMarkup(inline_keyboard=buttons),
    )
    await callback.answer()


# --- Выбор тарифа ---

@router.callback_query(F.data.startswith("subscribe_obj:"))
async def show_tariffs(callback: CallbackQuery) -> None:
    pk = int(callback.data.split(":")[1])
    obj = await db.get_object(pk)
    if not obj:
        await callback.answer("Объект не найден", show_alert=True)
        return

    text = (
        f"⚖️ *Подписка на объект «{_escape(obj['name'])}»*\n\n"
        "Выберите тариф:\n\n"
        "📅 *Месяц* — 2 900 ₽\n"
        "🗓 *Год* — 29 000 ₽\n"
        "   ~34 800 ₽~ · 🔥 2 месяца бесплатно"
    )

    await callback.message.answer(
        text,
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=keyboards.subscription_tariffs(pk),
    )
    await callback.answer()


# --- Оплата ---

@router.callback_query(F.data.startswith("pay_month:"))
async def pay_month(callback: CallbackQuery, bot: Bot) -> None:
    pk = int(callback.data.split(":")[1])
    await _send_invoice(callback, bot, pk, "month")


@router.callback_query(F.data.startswith("pay_year:"))
async def pay_year(callback: CallbackQuery, bot: Bot) -> None:
    pk = int(callback.data.split(":")[1])
    await _send_invoice(callback, bot, pk, "year")


async def _send_invoice(callback: CallbackQuery, bot: Bot, object_pk: int, plan: str) -> None:
    if not settings.provider_token:
        await callback.message.answer(
            "⚠️ Платежная система не настроена. Обратитесь к администратору.",
            reply_markup=keyboards.main_menu(),
        )
        await callback.answer()
        return

    obj = await db.get_object(object_pk)
    if not obj:
        await callback.answer("Объект не найден", show_alert=True)
        return

    if plan == "year":
        title = "SCROOGE — тариф «Год»"
        description = (
            f"Объект: {obj['name']}\n"
            "Доступ к сервису SCROOGE на 365 дней для 1 объекта. "
            "Включает: неограниченное количество передач данных "
            "весового контроля в ФГИС УТКО, валидацию файлов, "
            "уведомления об успешной передаче. "
            "Экономия 5 800 ₽ по сравнению с месячной оплатой."
        )
        amount = _YEAR_PRICE
        label = "Доступ к сервису SCROOGE на 365 дней"
    else:
        title = "SCROOGE — тариф «Месяц»"
        description = (
            f"Объект: {obj['name']}\n"
            "Доступ к сервису SCROOGE на 30 дней для 1 объекта. "
            "Включает: неограниченное количество передач данных "
            "весового контроля в ФГИС УТКО, валидацию файлов, "
            "уведомления об успешной передаче."
        )
        amount = _MONTH_PRICE
        label = "Доступ к сервису SCROOGE на 30 дней"

    payload = f"sub_{plan}_{object_pk}_{callback.from_user.id}"

    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title=title,
        description=description,
        payload=payload,
        provider_token=settings.provider_token,
        currency="RUB",
        prices=[LabeledPrice(label=label, amount=amount)],
    )
    await callback.answer()


# --- Pre-checkout ---

@router.pre_checkout_query()
async def on_pre_checkout(pre_checkout: PreCheckoutQuery) -> None:
    await pre_checkout.answer(ok=True)


# --- Successful payment ---

@router.message(F.successful_payment)
async def on_successful_payment(message: Message) -> None:
    payment = message.successful_payment
    payload = payment.invoice_payload  # sub_month_123_456789

    parts = payload.split("_")
    if len(parts) < 4 or parts[0] != "sub":
        return

    plan = parts[1]  # month / year
    object_pk = int(parts[2])
    user_id = int(parts[3])

    obj = await db.get_object(object_pk)
    if not obj:
        await message.answer("❌ Объект не найден.", reply_markup=keyboards.main_menu())
        return

    result = await db.activate_subscription(
        object_db_id=object_pk,
        user_id=user_id,
        plan=plan,
        payment_id=payment.telegram_payment_charge_id,
    )

    exp_date = result["expires_at"][:10]
    period = "12 месяцев" if plan == "year" else "1 месяц"

    await message.answer(
        f"✅ Подписка активирована!\n\n"
        f"🏭 «{obj['name']}»\n"
        f"📅 Тариф: {period}\n"
        f"📅 Активна до: {exp_date}\n"
        f"📤 Передачи в ФГИС УТКО открыты",
        reply_markup=keyboards.main_menu(),
    )


def _escape(text: str) -> str:
    """Экранирование для MarkdownV2."""
    special = r"_*[]()~`>#+-=|{}.!"
    return "".join(f"\\{c}" if c in special else c for c in text)
