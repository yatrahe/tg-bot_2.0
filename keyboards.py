from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


admin_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🔄 Обновить задания", callback_data="update_tasks")]
])

after_reg = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📋Задания на отзывы", callback_data="tasks")],
    [InlineKeyboardButton(text="👤 Профиль", callback_data="profile"), InlineKeyboardButton(text="📢Помощь", callback_data="help")]
])

profile_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="💸Вывод средств", callback_data="withdraw")],
    [InlineKeyboardButton(text="◀️Назад", callback_data="back"), InlineKeyboardButton(text="📢Помощь", callback_data="help")]
])

location_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="📍Отправить геолокацию", request_location=True)]],
    resize_keyboard=True
)

tasks_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Яндекс Карты", callback_data="yamaps")],
    [InlineKeyboardButton(text="Google Maps", callback_data="gmaps")],
    [InlineKeyboardButton(text="2GIS", callback_data="2gis")],
    [InlineKeyboardButton(text="Flamp", callback_data="flamp")],
    [InlineKeyboardButton(text="Другие задания", callback_data="other")],
    [InlineKeyboardButton(text="◀️Назад", callback_data="back")]
])

# Для каждой категории своя кнопка принятия задания
yamaps_accept = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🟢Получить задание", callback_data="yamaps_get")],
    [InlineKeyboardButton(text="◀️Назад", callback_data="back_to_tasks")]
])

gmaps_accept = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🟢Получить задание", callback_data="gmaps_get")],
    [InlineKeyboardButton(text="◀️Назад", callback_data="back_to_tasks")]
])

gis_accept = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🟢Получить задание", callback_data="gis_get")],
    [InlineKeyboardButton(text="◀️Назад", callback_data="back_to_tasks")]
])

flamp_accept = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🟢Получить задание", callback_data="flamp_get")],
    [InlineKeyboardButton(text="◀️Назад", callback_data="back_to_tasks")]
])

""" Кнопки для заданий по действиям -------------------------------------------------- """
def get_task_confirmation_keyboard(task_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить выполнение", callback_data=f"confirm_{task_id}")],
        [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{task_id}")]
    ])

def get_next_step_keyboard(task_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➡️ Следующий шаг", callback_data=f"next_step_{task_id}")],
        [InlineKeyboardButton(text="❌ Отменить задание", callback_data=f"cancel_task_{task_id}")]
    ])
