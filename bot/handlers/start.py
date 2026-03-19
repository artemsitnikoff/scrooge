from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message

import db
import keyboards
from version import __version__

router = Router()

WELCOME = (
    "🦆 SCROOGE — сервис передачи данных\n"
    "весового контроля в ФГИС УТКО.\n\n"
    "Бот помогает операторам полигонов ТКО\n"
    "и объектов обращения с отходами автоматически\n"
    "передавать данные взвешиваний в федеральную\n"
    "систему ФГИС УТКО (api.utko.mnr.gov.ru).\n\n"
    "Работает без постоянного интернета на объекте —\n"
    "загружайте файлы с данными когда есть связь,\n"
    "бот сам отправит в ФГИС УТКО.\n\n"
    "Для начала работы установите ключ доступа\n"
    "в ⚙️ Общие настройки.\n\n"
    "💬 Если возникли проблемы и нужна помощь,\n"
    "вступайте в группу: https://t.me/scrooge_support_utko"
)

HELP_TEXT = (
    f"🦆 SCROOGE v{__version__}\n\n"
    "📖 Доступные команды:\n\n"
    "⚙️ Общие настройки — ввести/обновить ключ доступа\n"
    "   от ППК РЭО к ФГИС УТКО\n\n"
    "🏭 Управление объектами — список объектов\n"
    "   ТКО, добавление и удаление\n\n"
    "📤 Загрузить данные — прикрепить файл\n"
    "   (.xlsx или .json) с данными весового\n"
    "   контроля для отправки в ФГИС УТКО\n\n"
    "💳 Подписка — тарифы и оплата\n"
    "   по каждому объекту\n\n"
    "Команды в чате:\n"
    "/start — главное меню\n"
    "/help — эта справка\n\n"
    "💬 Если возникли проблемы и нужна помощь,\n"
    "вступайте в группу: https://t.me/scrooge_support_utko"
)


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await db.ensure_user(message.from_user.id)
    await message.answer(WELCOME, reply_markup=keyboards.main_menu())


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(HELP_TEXT, reply_markup=keyboards.back_to_menu())


@router.callback_query(F.data == "main_menu")
async def cb_main_menu(callback: CallbackQuery) -> None:
    await callback.message.answer(WELCOME, reply_markup=keyboards.main_menu())
    await callback.answer()


@router.callback_query(F.data == "help")
async def cb_help(callback: CallbackQuery) -> None:
    await callback.message.answer(HELP_TEXT, reply_markup=keyboards.back_to_menu())
    await callback.answer()


@router.callback_query(F.data == "noop")
async def cb_noop(callback: CallbackQuery) -> None:
    await callback.answer()
