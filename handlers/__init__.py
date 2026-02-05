from aiogram import Router

# Создаем роутеры
commands_router = Router()
callbacks_router = Router()
fsm_handlers_router = Router()

# Импортируем обработчики
from . import commands
from . import callbacks
from . import fsm_handlers

# Экспортируем роутеры для удобства
__all__ = ['commands_router', 'callbacks_router', 'fsm_handlers_router']
