from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message

import db
import keyboards
from version import __version__

router = Router()

WELCOME = (
    "🦆 SCROOGE — бот для передачи данных\n"
    "весового контроля в ФГИС УТКО.\n\n"
    "Для начала работы установите ключ доступа\n"
    "в ⚙️ Общие настройки."
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
    "📊 Статус — состояние очереди\n"
    "   и история отправок\n\n"
    "Команды в чате:\n"
    "/start — главное меню\n"
    "/status — статус объектов\n"
    "/help — эта справка"
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
