from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from datetime import datetime
import asyncio
import logging

from keyboards.inline_kb import get_main_menu_keyboard
from db import db

# Создаем роутер для команд
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
        "Управление задач
