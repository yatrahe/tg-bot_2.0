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

class TaskStates(StatesGroup):
    waiting_for_screenshot = State()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    try:
        user = await db.get_user_by_id(message.from_user.id)
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

#Кнопка назад
@router.callback_query(F.data == "back_to_tasks")
async def back_to_tasks_btn(callback: CallbackQuery):
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

""" Обработка нажатий на категории заданий ----------------------------------------------------- """
@router.callback_query(F.data == "yamaps")
async def yandex_btn(callback: CallbackQuery):
    await callback.answer("")
    await callback.message.edit_text(
        "Задание Яндекс.карты📍\nСтоимость 1 отзыва: 65₽", 
        reply_markup=kb.yamaps_accept
    )

@router.callback_query(F.data == "gmaps")
async def google_btn(callback: CallbackQuery):
    await callback.answer("")
    await callback.message.edit_text(
        "Задание Google Maps📍\nСтоимость 1 отзыва: 35₽", 
        reply_markup=kb.gmaps_accept
    )

@router.callback_query(F.data == "2gis")
async def gis_btn(callback: CallbackQuery):
    await callback.answer("")
    await callback.message.edit_text(
        "Задание 2GIS📍\nСтоимость 1 отзыва: 25₽", 
        reply_markup=kb.gis_accept
    )

@router.callback_query(F.data == "flamp")
async def flamp_btn(callback: CallbackQuery):
    await callback.answer("")
    await callback.message.edit_text(
        "Задание Flamp📍\nСтоимость 1 отзыва: 25₽", 
        reply_markup=kb.flamp_accept
    )


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
        
        tasks = await get_tasks_from_sheets()
        if not tasks:
            await callback.message.answer("Не удалось получить задания из Google Sheets")
            return
            
        await db.clear_tasks()
        
        added_count = 0
        for task in tasks:
            try:
                await db.add_task(
                    task["task_num"],
                    task["external_id"],
                    task["category"],
                    task["description"],
                    task["price"],
                    task["geo"]
                )
                added_count += 1
            except Exception as e:
                print(f"Ошибка при добавлении задания {task}: {e}")
                
        await callback.message.answer(f"Успешно обновлено {added_count}/{len(tasks)} заданий!")
        
    except Exception as e:
        await callback.message.answer("Произошла ошибка при обновлении заданий")
        print(f"Ошибка в update_tasks: {e}")


""" РАБОТА С ЗАДНАИЯМИ ПО ДЕЙСТВИЯМ И БЕЗ ------------------------------------------"""
@router.callback_query(F.data.endswith("_get"))
async def get_task(callback: CallbackQuery, state: FSMContext):
    try:
        category_map = {
            "yamaps_get": ("Яндекс Карты", 65),
            "gmaps_get": ("Google maps", 35),
            "gis_get": ("2GIS", 25),
            "flamp_get": ("Flamp", 25)
        }
        
        category, price = category_map[callback.data]
        
        user = await db.get_user_by_id(callback.from_user.id)
        if not user or not user['city']:
            await callback.answer("Сначала укажите ваш город в профиле", show_alert=True)
            return

        task = await db.get_active_task_for_user(category, user['city'])
        if not task:
            await callback.answer("Нет доступных заданий в вашем городе", show_alert=True)
            return

        await db.deactivate_task(task['id'])
        await db.add_user_task(callback.from_user.id, task['id'], 'active')

        steps = extract_steps_from_description(task['description'])
        
        if steps:
            await db.update_task_progress(
                callback.from_user.id,
                task['id'],
                0,
                '[]'
            )
            await callback.message.answer(
                f"🔹 Шаг 1 из {len(steps)}\n\n{steps[0]}\n\n"
                "После выполнения отправьте скриншот сюда",
                reply_markup=kb.get_next_step_keyboard(task['id'])
            )
            await state.update_data(
                current_task=task['id'],
                current_step=0,
                total_steps=len(steps),
                category=category,
                price=price
            )
        else:
            await callback.message.answer(
                f"📌 Задание:\n\n{task['description']}\n\n"
                "После выполнения отправьте скриншот сюда"
            )
            await state.update_data(
                current_task=task['id'],
                is_simple_task=True,
                category=category,
                price=price
            )
        
        await state.set_state(TaskStates.waiting_for_screenshot)
        await callback.answer()
        
    except Exception as e:
        print(f"Error in get_task: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)

@router.message(TaskStates.waiting_for_screenshot, F.photo)
async def handle_screenshot(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        task_id = data.get('current_task')
        
        if data.get('is_simple_task'):
            # Обычное задание - отправляем админу на проверку
            admins = await db.get_admin_ids()
            for admin_id in admins:
                await message.bot.send_photo(
                    admin_id,
                    message.photo[-1].file_id,
                    caption=f"Скриншот от пользователя {message.from_user.full_name} (@{message.from_user.username})\n"
                            f"Задание ID: {task_id}",
                    reply_markup=kb.get_task_confirmation_keyboard(task_id)
            )
            await message.answer("Скриншот отправлен на проверку. Ожидайте подтверждения.")
            await state.clear()
        else:
            # Задание с шагами
            current_step = data.get('current_step', 0)
            total_steps = data.get('total_steps', 1)
            
            # Отправляем админу на проверку
            admins = await db.get_admin_ids()
            for admin_id in admins:
                await message.bot.send_photo(
                    admin_id,
                    message.photo[-1].file_id,
                    caption=f"Скриншот шага {current_step+1}/{total_steps} от пользователя {message.from_user.full_name}\n"
                            f"Задание ID: {task_id}",
                    reply_markup=kb.get_task_confirmation_keyboard(f"{task_id}_{current_step}")
                )
            
            await message.answer(f"Скриншот шага {current_step+1} отправлен на проверку. Ожидайте подтверждения.")
            
    except Exception as e:
        print(f"Error in handle_screenshot: {e}")
        await message.answer("Произошла ошибка")

@router.callback_query(F.data.startswith("confirm_"))
async def handle_confirmation(callback: CallbackQuery):
    try:
        parts = callback.data.split("_")
        task_id = int(parts[1])
        
        if len(parts) > 2:  # Подтверждение шага
            step = int(parts[2])
            user_task = await db.get_user_task_by_task_id(task_id)
            
            await db.complete_task_step(user_task['user_id'], task_id, step)
            
            # Проверяем, все ли шаги выполнены
            progress = await db.get_user_task_progress(user_task['user_id'], task_id)
            completed_steps = eval(progress['completed_steps'])
            
            if len(completed_steps) == progress['total_steps']:
                # Все шаги выполнены
                await db.delete_task(task_id)
                await callback.message.answer("Все шаги задания выполнены и подтверждены!")
            else:
                await callback.message.answer(f"Шаг {step+1} подтверждён!")
        else:
            # Подтверждение простого задания
            await db.delete_task(task_id)
            await callback.message.answer("Задание подтверждено и удалено из системы!")
        
        await callback.answer()
        
    except Exception as e:
        print(f"Error in handle_confirmation: {e}")
        await callback.answer("Произошла ошибка")

def extract_steps_from_description(description):
    """Извлекает шаги из описания задания"""
    steps = []
    step_pattern = re.compile(r'Действие \d+: (.*?)(?=\n\nДействие \d+:|$)', re.DOTALL)
    
    matches = step_pattern.finditer(description)
    for match in matches:
        steps.append(match.group(1).strip())
    
    return steps if steps else None


""" ЛЕТС ГОУ------------------------------------------------------------------ """
# Обработчик принятия задания
@router.callback_query(F.data == "get_task")
async def accept_task(callback: CallbackQuery, state: FSMContext):
    try:
        # Определяем категорию задания из предыдущего сообщения
        message_text = callback.message.text
        if "Яндекс.карты" in message_text:
            category = "Яндекс Карты"
            price = 65
        elif "Google Maps" in message_text:
            category = "Google maps"
            price = 35
        elif "2GIS" in message_text:
            category = "2GIS"
            price = 25
        elif "Flamp" in message_text:
            category = "Flamp"
            price = 25
        else:
            await callback.answer("Неизвестная категория заданий")
            return

        # Получаем данные пользователя
        user = await db.get_user_by_id(callback.from_user.id)
        if not user or not user['city']:
            await callback.answer("Сначала укажите ваш город в профиле")
            return

        # Получаем активное задание для пользователя
        task = await db.get_active_task_for_user(category, user['city'])
        
        if not task:
            # Проверяем наличие заданий без привязки к городу
            task = await db.get_active_task_for_user(category, "Все города")
            if not task:
                await callback.answer("Нет доступных заданий в вашем городе")
                return

        # Деактивируем задание
        await db.deactivate_task(task['id'])
        
        # Создаем запись о взятом задании
        await db.add_user_task(
            user_id=callback.from_user.id,
            task_id=task['id'],
            status='active'
        )

        # Обработка задания (шаги или простое задание)
        steps = extract_steps_from_description(task['description'])
        
        if steps:
            # Задание с шагами
            await db.update_task_progress(
                user_id=callback.from_user.id,
                task_id=task['id'],
                current_step=0,
                completed_steps='[]'
            )
            
            await callback.message.answer(
                f"🔹 Шаг 1 из {len(steps)}\n\n{steps[0]}\n\n"
                f"После выполнения отправьте скриншот сюда",
                reply_markup=kb.get_next_step_keyboard(task['id'])
            )
            await state.update_data(
                current_task=task['id'],
                current_step=0,
                total_steps=len(steps),
                category=category,
                price=price
            )
        else:
            # Обычное задание
            await callback.message.answer(
                f"📌 Задание:\n\n{task['description']}\n\n"
                f"После выполнения отправьте скриншот сюда"
            )
            await state.update_data(
                current_task=task['id'],
                is_simple_task=True,
                category=category,
                price=price
            )
        
        await state.set_state(TaskStates.waiting_for_screenshot)
        await callback.answer()
        
    except Exception as e:
        print(f"Error in accept_task: {e}")
        await callback.answer("Произошла ошибка при получении задания")