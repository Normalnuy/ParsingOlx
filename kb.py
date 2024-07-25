from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

kb = [
        [
            KeyboardButton(text="Добавить пользователя"),
            KeyboardButton(text="Статистика"),
            KeyboardButton(text="Пользователи")
        ],
    ]
keyboard = ReplyKeyboardMarkup(
    keyboard=kb,
    resize_keyboard=True,
    input_field_placeholder="Выберите пункт..."
)

bad_url = [
    [InlineKeyboardButton(text="Удалить пользователя", callback_data="user_delete"),
    InlineKeyboardButton(text="Изменить ссылку", callback_data="edit_url")],
    [InlineKeyboardButton(text="Проверить ещё раз", callback_data="repeat_check"),
    InlineKeyboardButton(text="Пропустить", callback_data="pass")],
]
bad_url = InlineKeyboardMarkup(inline_keyboard=bad_url)

users = [InlineKeyboardButton(text="Удалить пользователя", callback_data="user_delete"),
        InlineKeyboardButton(text="Изменить ссылку", callback_data="edit_url"),
        InlineKeyboardButton(text="Закрыть", callback_data="close")
        ],
users = InlineKeyboardMarkup(inline_keyboard=users)

cancel_buttons = [
    InlineKeyboardButton(text="Отмена", callback_data="cancel")
]
cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[cancel_buttons])


