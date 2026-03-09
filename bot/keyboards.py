from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚙️ Общие настройки", callback_data="settings")],
        [InlineKeyboardButton(text="🏭 Управление объектами", callback_data="objects")],
        [InlineKeyboardButton(text="📤 Загрузить данные", callback_data="upload_data")],
        [InlineKeyboardButton(text="📖 Все команды", callback_data="help")],
    ])


def objects_menu(objects: list[dict]) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=f"🏭 {obj['name']}", callback_data=f"obj_info:{obj['id']}")]
        for obj in objects
    ]
    buttons.append([
        InlineKeyboardButton(text="➕ Добавить", callback_data="add_object"),
        InlineKeyboardButton(text="🗑 Удалить", callback_data="delete_objects"),
    ])
    buttons.append([InlineKeyboardButton(text="↩️ Меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def object_list(objects: list[dict], action: str) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=f"🏭 {obj['name']}", callback_data=f"{action}:{obj['id']}")]
        for obj in objects
    ]
    buttons.append([InlineKeyboardButton(text="↩️ Меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def confirm_send(valid_count: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"✅ Отправить {valid_count} записей",
                callback_data="confirm_upload",
            ),
        ],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_upload")],
    ])


def confirm_delete(object_pk: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"confirm_del:{object_pk}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="objects")],
    ])


def object_card(object_pk: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Изменить название", callback_data=f"rename_obj:{object_pk}")],
        [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"del_obj:{object_pk}")],
        [InlineKeyboardButton(text="↩️ Объекты", callback_data="objects")],
    ])


def back_to_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="↩️ Меню", callback_data="main_menu")],
    ])


def cancel() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_fsm")],
    ])


def settings_menu(has_key: bool) -> InlineKeyboardMarkup:
    if has_key:
        buttons = [
            [InlineKeyboardButton(text="🗑 Удалить ключ", callback_data="delete_access_key")],
        ]
    else:
        buttons = [
            [InlineKeyboardButton(text="🔑 Ввести ключ доступа", callback_data="set_access_key")],
        ]
    buttons.append([InlineKeyboardButton(text="↩️ Меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
