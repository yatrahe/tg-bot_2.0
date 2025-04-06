from aiogram import F, Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile, InputMediaPhoto

from datetime import datetime
import re

import keyboards as kb
from db import Database, init_db

from GEOapi import get_city_by_coordinates, get_city_data

from gsheet import get_tasks_from_sheets


router = Router()
db = Database("database.db")

local_time = datetime.now().strftime("%d.%m.%Y %H:%M")


class Reg(StatesGroup):
    city = State()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    try:
        user = await db.get_user_by_id(message.from_user.id)
        await init_db()
        if not await db.user_exists(message.from_user.id):
            # Если пользователь отсутствует в БД, добавляем его и запрашиваем город
            await db.add_user(message.from_user.id, message.from_user.full_name)
            await state.set_state(Reg.city)
            await message.answer(
                "Введите Ваш город, или воспользуйтесь кнопкой ниже (только для телефона)",
                reply_markup=kb.location_kb)
            return  # Прерываем выполнение, чтобы не показывать основное сообщение
        
        elif user["is_admin"]:
                await message.answer(
                    f"Добро пожаловать в Админ панель, {message.from_user.full_name}!\n\nНа сегодня: {local_time}\n"
                    "Цены за задания:\n\n📍Яндекс карты: 65₽\n📍Google карты: 35₽\n📍Flamp: 25₽\n📍2GIS: 25₽\n\n"
                    f"Если у вас есть пожелания и предложения, а также вы нашли недочёты, пожалуйста, пишите @M_i_c_h_i_g_a_nnn.",
                    reply_markup=kb.admin_menu)
        
        elif await db.user_exists(message.from_user.id):
            # Если пользователь уже есть в БД, показываем основное меню
            await message.answer(
            f"Добро пожаловать, {message.from_user.full_name}!\n\nНа сегодня: {local_time}\n"
            "Цены за задания:\n\n📍Яндекс карты: 65₽\n📍Google карты: 35₽\n📍Flamp: 25₽\n📍2GIS: 25₽\n\n"
            f"Если у вас есть пожелания и предложения, а также вы нашли недочёты, пожалуйста, пишите @M_i_c_h_i_g_a_nnn.",
            reply_markup=kb.after_reg)
                
    except Exception as e:
        await message.answer("Произошла ошибка. Попробуйте позже.")
        print(f"Ошибка в cmd_start, {e}")


@router.message(Reg.city)
async def process_city(message: Message, state: FSMContext):
    try:
        city = None
        
        if message.location:
            # Обработка геолокации
            location_data = await get_city_by_coordinates(
                message.location.latitude,
                message.location.longitude
            )
            
            if not location_data:
                await message.answer("Не удалось определить город по геолокации. Введите название вручную.")
                return
                
            # Пробуем получить русское название
            ru_name = location_data.get('local_names', {}).get('ru', location_data.get('name'))
            city = ru_name
        else:
            # Обработка ручного ввода
            input_city = message.text.strip()
            
            # Базовая проверка на русские символы
            if not re.fullmatch(r'^[а-яА-ЯёЁ\s-]+$', input_city):
                await message.answer("Пожалуйста, введите название города русскими буквами.")
                return
                
            # Проверяем город через API
            city_data = await get_city_data(input_city)
            
            if not city_data:
                await message.answer(
                    "Город не найден. Пожалуйста, проверьте:\n\n"
                    "1. Правильность написания\n"
                    "2. Что вводите полное название (например, 'Москва' вместо 'Мск')\n"
                    "3. Что город существует в России"
                )
                return
                
            city = city_data.get('local_names', {}).get('ru', city_data.get('name'))

        # Сохраняем город
        await db.set_city(message.from_user.id, city)
        await state.clear()
        
        # Удаляем клавиатуру и показываем меню
        await message.answer(
            f"Город сохранен: {city}",
            reply_markup=ReplyKeyboardRemove()
        )
        await message.answer(
            f"Добро пожаловать, {message.from_user.full_name}!\nВаш город: {city}\n\nНа сегодня: {local_time}\n"
            "Цены за задания:\n\n📍Яндекс карты: 65₽\n📍Google карты: 35₽\n📍Flamp: 25₽\n📍2GIS: 25₽\n\n"
            f"Если у вас есть пожелания и предложения, а также вы нашли недочёты, пожалуйста, пишите @M_i_c_h_i_g_a_nnn.",
            reply_markup=kb.after_reg
        )
        
    except Exception as e:
        await message.answer("Произошла ошибка. Попробуйте еще раз.")
        print(f"Ошибка в process_city: {e}")

#Обработка нажатия на кнопку Задания
@router.callback_query(F.data == "tasks")
async def tasks(callback: CallbackQuery):
    await callback.answer("Выберите задание")
    await callback.message.edit_text("В данном разделе вы можете выбрать любую площадку и оставить отзыв. "
                                    "Отзывы оставляете на компании, которые выдает бот. Список заданий ограничен.", reply_markup=kb.tasks_menu)

#Обработка нажатия на кнопку Профиль
@router.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery):
    try:
        user = await db.get_user_by_id(callback.from_user.id)
        await callback.answer("")
        await callback.message.edit_text(f"Добро пожаловать, {callback.from_user.full_name}!\n\n"
                                    "Это ваш личный кабинет. Здесь Вы можете видеть Ваш город, баланс и количество выполненных заданий.\n\n"
                                    f"🏙️Ваш город: {user["city"]}\n"
                                    f"💰Ваш баланс: {user["balance"]}₽\n"
                                    f"📌Количество выполненных заднаий: {user["amount_tasks"]}\n\n"
                                    "‼️Вывод средств доступен от 100₽", reply_markup=kb.profile_menu)
    except Exception as e:
        await callback.message.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")
        print(f"Ошибка в show_profile: {e}")

#Обработка нажатия на кнопку Назад
@router.callback_query(F.data == "back")
async def back_btn(callback: CallbackQuery):
    await callback.answer("Главное меню")
    await callback.message.edit_text(f"Добро пожаловать, {callback.from_user.full_name}!\n\nНа сегодня: {local_time}\n"
                                    "Цены за задания:\n\n📍Яндекс карты: 65₽\n📍Google карты: 35₽\n📍Flamp: 25₽\n📍2GIS: 25₽\n\n"
                                    f"Если у вас есть пожелания и предложения, а также вы нашли недочёты, пожалуйста, пишите @M_i_c_h_i_g_a_nnn.",
                                    reply_markup=kb.after_reg)
#Обработка нажатия на кнопку Яндекс карты
@router.callback_query(F.data == "yamaps")
async def yandex_btn(callback: CallbackQuery):
    await callback.answer("")
    await callback.message.edit_text("Задание Яндекс.карты📍\nСтоимость 1 отзыва: 65₽", reply_markup=kb.accept_menu)

@router.callback_query(F.data == "back_to_tasks")
async def back_to_tasks_btn(callback: CallbackQuery):
    await callback.answer("Выберите задание")
    await callback.message.edit_text("В данном разделе вы можете выбрать любую площадку и оставить отзыв. "
                                    "Отзывы оставляете на компании, которые выдает бот. Список заданий ограничен.", reply_markup=kb.tasks_menu)
    


#АДМИНКА
@router.callback_query(F.data == "admin_panel")
async def admin_panel(callback: CallbackQuery):
    """Отображает админ-панель"""
    try:
        admins = await db.get_admin_ids()
        if callback.from_user.id not in admins:
            await callback.answer("У вас нет прав доступа!")
            return
            
        await callback.message.edit_text(
            "Админ-панель",
            reply_markup=kb.admin_menu
        )
    except Exception as e:
        await callback.answer("Произошла ошибка!")
        print(f"Ошибка в admin_panel: {e}")

@router.callback_query(F.data == "update_tasks")
async def update_tasks(callback: CallbackQuery):
    """Обновляет задания из Google Sheets"""
    try:
        admins = await db.get_admin_ids()
        if callback.from_user.id not in admins:
            await callback.answer("У вас нет прав доступа!")
            return
            
        await callback.answer("Обновление заданий...")
        
        # Получаем задания из Google Sheets
        tasks = await get_tasks_from_sheets()
        if not tasks:
            await callback.message.answer("Не удалось получить задания из Google Sheets")
            return
            
        # Очищаем старые задания
        await db.clear_tasks()
        
        # Добавляем новые задания
        for task in tasks:
            await db.add_task(
                task["external_id"],
                task["category"],
                task["description"],
                task["price"],
                task["geo"]
            )
            
        await callback.message.answer(f"Успешно обновлено {len(tasks)} заданий!")
        
    except Exception as e:
        await callback.message.answer("Произошла ошибка при обновлении заданий")
        print(f"Ошибка в update_tasks: {e}")