from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from datetime import datetime
import asyncio
import logging

from keyboards.inline_kb import get_main_menu_keyboard
from db import db

# Создаем роутер
router = Router()

logger = logging.getLogger(__name__)


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    welcome_text = (
        "👋 Привет! Я бот-планировщик задач.\n\n"
        "С моей помощью ты можешь:\n"
        "• Создавать проекты\n"
        "• Добавлять задачи с дедлайнами\n"
        "• Получать напоминания\n"
        "• Отслеживать выполнение\n\n"
        "Используй кнопки ниже для навигации:"
    )
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_menu_keyboard()
    )


@router.message(Command("help"))
async def cmd_help(message: types.Message):
    """Обработчик команды /help"""
    help_text = (
        "📚 Справка по командам:\n\n"
        "Основные команды:\n"
        "/start - Запустить бота\n"
        "/help - Показать эту справку\n\n"
        "Управление проектами:\n"
        "• Создавайте проекты для организации задач\n"
        "• В каждом проекте могут быть задачи\n"
        "• Проекты можно редактировать и удалять\n\n"
        "Управление задачами:\n"
        "• У каждой задачи есть дедлайн\n"
        "• Можно добавлять комментарии\n"
        "• Статус: 'активно' или 'завершено'\n\n"
        "Напоминания:\n"
        "• Бот присылает уведомления за 24 часа до дедлайна\n\n"
        "Формат даты: ДД.ММ.ГГ ЧЧ:ММ\n"
        "Пример: 05.02.26 18:30"
    )
    
    await message.answer(help_text)


async def send_reminders(bot):
    """Фоновая задача для отправки напоминаний"""
    logger.info("Запуск задачи напоминаний...")
    
    while True:
        try:
            tasks = await db.get_upcoming_tasks()
            
            sent_reminders = 0
            for task in tasks:
                try:
                    deadline_str = task['deadline'].strftime('%d.%m.%y %H:%M')
                    reminder_text = (
                        f"❗ Напоминание:\n"
                        f"Задача: «{task['title']}»\n"
                        f"Дедлайн: {deadline_str}"
                    )
                    
                    await bot.send_message(
                        chat_id=task['user_id'],
                        text=reminder_text
                    )
                    sent_reminders += 1
                    
                    # Пауза между отправками, чтобы не превысить лимиты
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Ошибка отправки напоминания пользователю {task.get('user_id')}: {e}")
                    continue
            
            if sent_reminders > 0:
                logger.info(f"Отправлено {sent_reminders} напоминаний")
            else:
                logger.info("Нет задач для напоминаний")
            
        except Exception as e:
            logger.error(f"Ошибка в задаче напоминаний: {e}")
        
        # Проверяем каждые 5 минут
        await asyncio.sleep(300)
