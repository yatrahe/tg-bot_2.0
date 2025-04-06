from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

after_reg = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📋Задания на отзывы", callback_data="tasks")],
    [InlineKeyboardButton(text="👤 Профиль", callback_data="profile"), InlineKeyboardButton(text="📢Помощь", callback_data="help")]
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
    [InlineKeyboardButton(text="◀️Назад", callback_data="back")]
])

profile_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="💸Вывод средств", callback_data="withdraw")],
    [InlineKeyboardButton(text="◀️Назад", callback_data="back"), InlineKeyboardButton(text="📢Помощь", callback_data="help")]
])

accept_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🟢Получить задание", callback_data="get_task")],
    [InlineKeyboardButton(text="◀️Назад", callback_data="back_to_tasks")]
])