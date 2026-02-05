from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Dict, Any


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура главного меню"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="➕ Новый проект", callback_data="new_project"),
        InlineKeyboardButton(text="📂 Мои проекты", callback_data="list_projects")
    )
    builder.row(
        InlineKeyboardButton(text="🔔 Напоминания", callback_data="show_reminders"),
        InlineKeyboardButton(text="📝 Новая задача", callback_data="new_task")
    )
    return builder.as_markup()


def get_projects_keyboard(projects: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Клавиатура со списком проектов"""
    builder = InlineKeyboardBuilder()
    
    for project in projects:
        builder.row(
            InlineKeyboardButton(
                text=f"📁 {project['name'][:30]}",
                callback_data=f"project_{project['id']}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")
    )
    
    return builder.as_markup()


def get_project_actions_keyboard(project_id: int) -> InlineKeyboardMarkup:
    """Клавиатура действий с проектом"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="📋 Задачи", callback_data=f"project_tasks_{project_id}"),
        InlineKeyboardButton(text="✏️ Ред.", callback_data=f"edit_project_{project_id}")
    )
    builder.row(
        InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete_project_{project_id}"),
        InlineKeyboardButton(text="🔙 Назад", callback_data="list_projects")
    )
    
    return builder.as_markup()


def get_tasks_keyboard(tasks: List[Dict[str, Any]], project_id: int) -> InlineKeyboardMarkup:
    """Клавиатура со списком задач"""
    builder = InlineKeyboardBuilder()
    
    for task in tasks:
        status_icon = "✅" if task['status'] == 'завершено' else "⏳"
        builder.row(
            InlineKeyboardButton(
                text=f"{status_icon} {task['title'][:30]}",
                callback_data=f"task_{task['id']}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data=f"project_{project_id}"),
        InlineKeyboardButton(text="➕ Новая задача", callback_data=f"new_task_project_{project_id}")
    )
    
    return builder.as_markup()


def get_task_actions_keyboard(task_id: int, status: str) -> InlineKeyboardMarkup:
    """Клавиатура действий с задачей"""
    builder = InlineKeyboardBuilder()
    
    if status == 'активно':
        builder.row(
            InlineKeyboardButton(text="✅ Завершить", callback_data=f"complete_task_{task_id}"),
            InlineKeyboardButton(text="✏️ Ред.", callback_data=f"edit_task_{task_id}")
        )
    else:
        builder.row(
            InlineKeyboardButton(text="↩️ Вернуть в работу", callback_data=f"reopen_task_{task_id}"),
            InlineKeyboardButton(text="✏️ Ред.", callback_data=f"edit_task_{task_id}")
        )
    
    builder.row(
        InlineKeyboardButton(text="💬 Комментарий", callback_data=f"view_comment_{task_id}"),
        InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete_task_{task_id}")
    )
    
    return builder.as_markup()


def get_confirm_delete_keyboard(item_type: str, item_id: int) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения удаления"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="❗ Подтвердить удаление",
            callback_data=f"confirm_delete_{item_type}_{item_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data=f"cancel_delete_{item_type}_{item_id}")
    )
    
    return builder.as_markup()


def get_edit_task_fields_keyboard(task_id: int) -> InlineKeyboardMarkup:
    """Клавиатура выбора поля для редактирования задачи"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="📅 Дедлайн", callback_data=f"edit_deadline_{task_id}"),
        InlineKeyboardButton(text="💬 Комментарий", callback_data=f"edit_comment_{task_id}")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data=f"task_{task_id}")
    )
    
    return builder.as_markup()


def get_cancel_keyboard(callback_data: str = "cancel") -> InlineKeyboardMarkup:
    """Клавиатура отмены действия"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data=callback_data)
    )
    return builder.as_markup()
