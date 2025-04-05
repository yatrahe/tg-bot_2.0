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
