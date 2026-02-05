from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from datetime import datetime
import logging

from keyboards.inline_kb import (
    get_main_menu_keyboard,
    get_projects_keyboard,
    get_project_actions_keyboard,
    get_tasks_keyboard,
    get_task_actions_keyboard,
    get_confirm_delete_keyboard,
    get_edit_task_fields_keyboard
)
from db import db

# Создаем роутер
router = Router()

logger = logging.getLogger(__name__)


@router.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery):
    """Возврат в главное меню"""
    welcome_text = (
        "👋 Главное меню\n\n"
        "Используй кнопки ниже для навигации:"
    )
    
    await callback.message.edit_text(
        welcome_text,
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "create_project")
async def create_project_callback(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик создания проекта"""
    from states.user_states import ProjectStates
    
    await callback.message.edit_text(
        "📝 Введите название нового проекта:",
        reply_markup=get_main_menu_keyboard()
    )
    await state.set_state(ProjectStates.waiting_for_project_name)
    await callback.answer()


@router.callback_query(lambda c: c.data == "my_projects")
async def show_projects(callback: types.CallbackQuery):
    """Показать список проектов пользователя"""
    try:
        user_id = callback.from_user.id
        projects = await db.get_user_projects(user_id)
        
        if not projects:
            text = "📂 У вас пока нет проектов.\n\nСоздайте первый проект!"
        else:
            text = "📂 Ваши проекты:\n\n"
            for project in projects:
                task_count = await db.get_project_tasks_count(project['id'])
                text += f"• {project['name']} (задач: {task_count})\n"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_projects_keyboard(projects)
        )
        
    except Exception as e:
        logger.error(f"Ошибка при получении проектов: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при загрузке проектов",
            reply_markup=get_main_menu_keyboard()
        )
    
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("project_"))
async def project_selected(callback: types.CallbackQuery):
    """Обработчик выбора проекта"""
    try:
        project_id = int(callback.data.split("_")[1])
        project = await db.get_project_by_id(project_id)
        
        if not project:
            await callback.message.edit_text(
                "❌ Проект не найден",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        tasks = await db.get_project_tasks(project_id)
        
        text = f"📋 Проект: {project['name']}\n\n"
        
        if not tasks:
            text += "📝 Задач пока нет.\n\nДобавьте первую задачу!"
        else:
            text += "📋 Задачи проекта:\n\n"
            for task in tasks:
                status_icon = "✅" if task['completed'] else "⏳"
                deadline_str = task['deadline'].strftime('%d.%m.%y %H:%M')
                text += f"{status_icon} {task['title']}\n"
                text += f"   📅 {deadline_str}\n"
                if task['description']:
                    text += f"   📝 {task['description']}\n"
                text += "\n"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_project_actions_keyboard(project_id)
        )
        
    except Exception as e:
        logger.error(f"Ошибка при выборе проекта: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при загрузке проекта",
            reply_markup=get_main_menu_keyboard()
        )
    
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("add_task_"))
async def add_task_to_project(callback: types.CallbackQuery, state: FSMContext):
    """Добавить задачу в проект"""
    from states.user_states import TaskStates
    
    try:
        project_id = int(callback.data.split("_")[2])
        
        # Сохраняем project_id в состоянии
        await state.update_data(project_id=project_id)
        
        await callback.message.edit_text(
            "📝 Введите название задачи:",
            reply_markup=get_main_menu_keyboard()
        )
        
        await state.set_state(TaskStates.waiting_for_task_title)
        
    except Exception as e:
        logger.error(f"Ошибка при добавлении задачи: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при добавлении задачи",
            reply_markup=get_main_menu_keyboard()
        )
    
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("edit_project_"))
async def edit_project(callback: types.CallbackQuery, state: FSMContext):
    """Редактировать проект"""
    from states.user_states import EditProjectStates
    
    try:
        project_id = int(callback.data.split("_")[2])
        
        # Сохраняем project_id в состоянии
        await state.update_data(project_id=project_id)
        
        await callback.message.edit_text(
            "✏️ Введите новое название проекта:",
            reply_markup=get_main_menu_keyboard()
        )
        
        await state.set_state(EditProjectStates.waiting_for_new_project_name)
        
    except Exception as e:
        logger.error(f"Ошибка при редактировании проекта: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при редактировании проекта",
            reply_markup=get_main_menu_keyboard()
        )
    
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("delete_project_"))
async def delete_project_confirmation(callback: types.CallbackQuery):
    """Подтверждение удаления проекта"""
    try:
        project_id = int(callback.data.split("_")[2])
        
        await callback.message.edit_text(
            "⚠️ Вы уверены, что хотите удалить этот проект?\n\n"
            "❗ Все задачи в проекте также будут удалены!",
            reply_markup=get_confirm_delete_keyboard("project", project_id)
        )
        
    except Exception as e:
        logger.error(f"Ошибка при подтверждении удаления проекта: {e}")
        await callback.message.edit_text(
            "❌ Ошибка",
            reply_markup=get_main_menu_keyboard()
        )
    
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("confirm_delete_project_"))
async def delete_project(callback: types.CallbackQuery):
    """Удаление проекта"""
    try:
        project_id = int(callback.data.split("_")[3])
        
        await db.delete_project(project_id)
        
        await callback.message.edit_text(
            "✅ Проект успешно удален",
            reply_markup=get_main_menu_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Ошибка при удалении проекта: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при удалении проекта",
            reply_markup=get_main_menu_keyboard()
        )
    
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("cancel_delete_"))
async def cancel_delete(callback: types.CallbackQuery):
    """Отмена удаления"""
    try:
        entity_type = callback.data.split("_")[2]
        entity_id = int(callback.data.split("_")[3])
        
        if entity_type == "project":
            project = await db.get_project_by_id(entity_id)
            if project:
                await callback.message.edit_text(
                    f"📋 Проект: {project['name']}",
                    reply_markup=get_project_actions_keyboard(entity_id)
                )
            else:
                await callback.message.edit_text(
                    "✅ Удаление отменено",
                    reply_markup=get_main_menu_keyboard()
                )
        
    except Exception as e:
        logger.error(f"Ошибка при отмене удаления: {e}")
        await callback.message.edit_text(
            "❌ Ошибка",
            reply_markup=get_main_menu_keyboard()
        )
    
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("view_tasks_"))
async def view_project_tasks(callback: types.CallbackQuery):
    """Просмотр задач проекта"""
    try:
        project_id = int(callback.data.split("_")[2])
        tasks = await db.get_project_tasks(project_id)
        
        if not tasks:
            text = "📝 В этом проекте пока нет задач.\n\nДобавьте первую задачу!"
        else:
            text = "📋 Задачи проекта:\n\n"
            for task in tasks:
                status_icon = "✅" if task['completed'] else "⏳"
                deadline_str = task['deadline'].strftime('%d.%m.%y %H:%M')
                text += f"{status_icon} {task['title']}\n"
                text += f"   📅 {deadline_str}\n\n"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_tasks_keyboard(tasks, project_id)
        )
        
    except Exception as e:
        logger.error(f"Ошибка при просмотре задач: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при загрузке задач",
            reply_markup=get_main_menu_keyboard()
        )
    
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("task_"))
async def task_selected(callback: types.CallbackQuery):
    """Обработчик выбора задачи"""
    try:
        task_id = int(callback.data.split("_")[1])
        task = await db.get_task_by_id(task_id)
        
        if not task:
            await callback.message.edit_text(
                "❌ Задача не найдена",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        status = "✅ Завершена" if task['completed'] else "⏳ В процессе"
        deadline_str = task['deadline'].strftime('%d.%m.%y %H:%M')
        
        text = (
            f"📋 Задача: {task['title']}\n\n"
            f"📝 Описание: {task['description'] or 'Нет описания'}\n"
            f"📅 Дедлайн: {deadline_str}\n"
            f"📊 Статус: {status}\n"
            f"🆔 ID задачи: {task_id}"
        )
        
        await callback.message.edit_text(
            text,
            reply_markup=get_task_actions_keyboard(task_id)
        )
        
    except Exception as e:
        logger.error(f"Ошибка при выборе задачи: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при загрузке задачи",
            reply_markup=get_main_menu_keyboard()
        )
    
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("complete_task_"))
async def complete_task(callback: types.CallbackQuery):
    """Отметить задачу как выполненную"""
    try:
        task_id = int(callback.data.split("_")[2])
        
        await db.update_task_status(task_id, completed=True)
        
        task = await db.get_task_by_id(task_id)
        
        if task:
            status = "✅ Завершена"
            deadline_str = task['deadline'].strftime('%d.%m.%y %H:%M')
            
            text = (
                f"📋 Задача: {task['title']}\n\n"
                f"📝 Описание: {task['description'] or 'Нет описания'}\n"
                f"📅 Дедлайн: {deadline_str}\n"
                f"📊 Статус: {status}\n"
                f"🆔 ID задачи: {task_id}"
            )
            
            await callback.message.edit_text(
                text,
                reply_markup=get_task_actions_keyboard(task_id)
            )
        
        await callback.answer("✅ Задача отмечена как выполненная!")
        
    except Exception as e:
        logger.error(f"Ошибка при завершении задачи: {e}")
        await callback.answer("❌ Ошибка при завершении задачи")


@router.callback_query(lambda c: c.data.startswith("edit_task_"))
async def edit_task(callback: types.CallbackQuery, state: FSMContext):
    """Редактировать задачу - выбор поля"""
    try:
        task_id = int(callback.data.split("_")[2])
        
        await callback.message.edit_text(
            "✏️ Выберите, что хотите отредактировать:",
            reply_markup=get_edit_task_fields_keyboard(task_id)
        )
        
        # Сохраняем task_id в состоянии
        await state.update_data(task_id=task_id)
        
    except Exception as e:
        logger.error(f"Ошибка при редактировании задачи: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при редактировании задачи",
            reply_markup=get_main_menu_keyboard()
        )
    
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("edit_task_field_"))
async def edit_task_field(callback: types.CallbackQuery, state: FSMContext):
    """Редактирование конкретного поля задачи"""
    from states.user_states import EditTaskStates
    
    try:
        data = callback.data.split("_")
        task_id = int(data[3])
        field = data[4]
        
        # Сохраняем данные в состоянии
        await state.update_data(task_id=task_id, field=field)
        
        field_names = {
            "title": "название",
            "description": "описание",
            "deadline": "дедлайн"
        }
        
        if field == "deadline":
            instruction = "\n\nФормат: ДД.ММ.ГГ ЧЧ:ММ\nПример: 05.02.26 18:30"
        else:
            instruction = ""
        
        await callback.message.edit_text(
            f"✏️ Введите новое {field_names.get(field, field)}{instruction}:",
            reply_markup=get_main_menu_keyboard()
        )
        
        # Устанавливаем соответствующее состояние
        if field == "title":
            await state.set_state(EditTaskStates.waiting_for_new_title)
        elif field == "description":
            await state.set_state(EditTaskStates.waiting_for_new_description)
        elif field == "deadline":
            await state.set_state(EditTaskStates.waiting_for_new_deadline)
        
    except Exception as e:
        logger.error(f"Ошибка при выборе поля для редактирования: {e}")
        await callback.message.edit_text(
            "❌ Ошибка",
            reply_markup=get_main_menu_keyboard()
        )
    
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("delete_task_"))
async def delete_task_confirmation(callback: types.CallbackQuery):
    """Подтверждение удаления задачи"""
    try:
        task_id = int(callback.data.split("_")[2])
        
        await callback.message.edit_text(
            "⚠️ Вы уверены, что хотите удалить эту задачу?",
            reply_markup=get_confirm_delete_keyboard("task", task_id)
        )
        
    except Exception as e:
        logger.error(f"Ошибка при подтверждении удаления задачи: {e}")
        await callback.message.edit_text(
            "❌ Ошибка",
            reply_markup=get_main_menu_keyboard()
        )
    
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("confirm_delete_task_"))
async def delete_task(callback: types.CallbackQuery):
    """Удаление задачи"""
    try:
        task_id = int(callback.data.split("_")[3])
        
        await db.delete_task(task_id)
        
        await callback.message.edit_text(
            "✅ Задача успешно удалена",
            reply_markup=get_main_menu_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Ошибка при удалении задачи: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при удалении задачи",
            reply_markup=get_main_menu_keyboard()
        )
    
    await callback.answer()
