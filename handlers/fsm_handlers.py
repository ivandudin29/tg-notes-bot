from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from datetime import datetime
import re
import logging

from states.user_states import (
    ProjectStates, TaskStates, 
    EditProjectStates, EditTaskStates
)
from keyboards.inline_kb import (
    get_cancel_keyboard,
    get_projects_keyboard
)
from db import db

# Создаем роутер
router = Router()

logger = logging.getLogger(__name__)


# ... весь остальной код fsm_handlers.py без изменений ...
# (весь остальной код из предыдущей версии остается таким же)
