from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_main_menu_keyboard():
    """Главное меню"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.add(
        InlineKeyboardButton(text="📂 Мои проекты", callback_data="my_projects"),
        InlineKeyboardButton(text="➕ Создать проект", callback_data="create_project"),
        InlineKeyboardButton(text="❓ Помощь", callback_data="help_menu")
    )
    
    return keyboard.as_markup()


def get_projects_keyboard(projects):
    """Клавиатура со списком проектов"""
    keyboard = InlineKeyboardBuilder()
    
    for project in projects:
        keyboard.add(
            InlineKeyboardButton(
                text=f"📁 {project['name']}",
                callback_data=f"project_{project['id']}"
            )
        )
    
    keyboard.add(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")
    )
    
    keyboard.adjust(1)
    return keyboard.as_markup()


def get_project_actions_keyboard(project_id):
    """Действия с проектом"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.add(
        InlineKeyboardButton(
            text="📋 Задачи проекта",
            callback_data=f"view_tasks_{project_id}"
        ),
        InlineKeyboardButton(
            text="➕ Добавить задачу",
            callback_data=f"add_task_to_{project_id}"
        ),
        InlineKeyboardButton(
            text="✏️ Редактировать",
            callback_data=f"edit_project_{project_id}"
        ),
        InlineKeyboardButton(
            text="🗑️ Удалить",
            callback_data=f"delete_project_{project_id}"
        ),
        InlineKeyboardButton(
            text="⬅️ Назад к проектам",
            callback_data="my_projects"
        )
    )
    
    keyboard.adjust(1)
    return keyboard.as_markup()


def get_tasks_keyboard(tasks, project_id):
    """Клавиатура со списком задач"""
    keyboard = InlineKeyboardBuilder()
    
    for task in tasks:
        status_icon = "✅" if task['completed'] else "⏳"
        keyboard.add(
            InlineKeyboardButton(
                text=f"{status_icon} {task['title'][:30]}",
                callback_data=f"task_{task['id']}"
            )
        )
    
    keyboard.add(
        InlineKeyboardButton(
            text="➕ Добавить задачу",
            callback_data=f"add_task_to_{project_id}"
        ),
        InlineKeyboardButton(
            text="⬅️ Назад к проекту",
            callback_data=f"project_{project_id}"
        )
    )
    
    keyboard.adjust(1)
    return keyboard.as_markup()


def get_task_actions_keyboard(task_id):
    """Действия с задачей"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.add(
        InlineKeyboardButton(
            text="✅ Отметить выполненной",
            callback_data=f"complete_task_{task_id}"
        ),
        InlineKeyboardButton(
            text="✏️ Редактировать",
            callback_data=f"edit_task_{task_id}"
        ),
        InlineKeyboardButton(
            text="🗑️ Удалить",
            callback_data=f"delete_task_{task_id}"
        ),
        InlineKeyboardButton(
            text="⬅️ Назад к задачам",
            callback_data="my_projects"
        )
    )
    
    keyboard.adjust(1)
    return keyboard.as_markup()


def get_confirm_delete_keyboard(entity_type, entity_id):
    """Подтверждение удаления"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.add(
        InlineKeyboardButton(
            text="✅ Да, удалить",
            callback_data=f"confirm_delete_{entity_type}_{entity_id}"
        ),
        InlineKeyboardButton(
            text="❌ Нет, отмена",
            callback_data=f"cancel_delete_{entity_type}_{entity_id}"
        )
    )
    
    keyboard.adjust(2)
    return keyboard.as_markup()


def get_edit_task_fields_keyboard(task_id):
    """Выбор поля для редактирования задачи"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.add(
        InlineKeyboardButton(
            text="📝 Название",
            callback_data=f"edit_task_field_{task_id}_title"
        ),
        InlineKeyboardButton(
            text="📄 Описание",
            callback_data=f"edit_task_field_{task_id}_description"
        ),
        InlineKeyboardButton(
            text="📅 Дедлайн",
            callback_data=f"edit_task_field_{task_id}_deadline"
        ),
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=f"task_{task_id}"
        )
    )
    
    keyboard.adjust(1)
    return keyboard.as_markup()


def get_cancel_keyboard():
    """Клавиатура для отмены действия"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.add(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="back_to_main"
        )
    )
    
    return keyboard.as_markup()


def get_help_keyboard():
    """Клавиатура помощи"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.add(
        InlineKeyboardButton(
            text="📋 Команды",
            callback_data="help_commands"
        ),
        InlineKeyboardButton(
            text="📅 Формат даты",
            callback_data="help_date_format"
        ),
        InlineKeyboardButton(
            text="⬅️ Главное меню",
            callback_data="back_to_main"
        )
    )
    
    keyboard.adjust(1)
    return keyboard.as_markup()
