from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from datetime import datetime

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

router = Router()


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


@router.callback_query(lambda c: c.data == "list_projects")
async def list_projects(callback: types.CallbackQuery):
    """Показать список проектов"""
    projects = await db.get_user_projects(callback.from_user.id)
    
    if not projects:
        await callback.message.edit_text(
            "У вас пока нет проектов. Создайте первый проект!",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    projects_text = "📂 Ваши проекты:\n\n"
    for i, project in enumerate(projects, 1):
        desc = project['description'][:50] + "..." if project['description'] else "Нет описания"
        projects_text += f"{i}. {project['name']}\n   📝 {desc}\n\n"
    
    await callback.message.edit_text(
        projects_text,
        reply_markup=get_projects_keyboard(projects)
    )
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("project_"))
async def show_project(callback: types.CallbackQuery):
    """Показать информацию о проекте"""
    project_id = int(callback.data.split("_")[-1])
    
    project = await db.get_project(project_id, callback.from_user.id)
    if not project:
        await callback.answer("Проект не найден", show_alert=True)
        return
    
    # Получаем задачи проекта
    tasks = await db.get_project_tasks(project_id, callback.from_user.id)
    active_tasks = [t for t in tasks if t['status'] == 'активно']
    completed_tasks = [t for t in tasks if t['status'] == 'завершено']
    
    project_text = (
        f"📁 Проект: {project['name']}\n"
        f"📝 Описание: {project['description'] or 'Нет описания'}\n\n"
        f"📊 Статистика:\n"
        f"• Активных задач: {len(active_tasks)}\n"
        f"• Завершенных задач: {len(completed_tasks)}\n"
        f"• Всего задач: {len(tasks)}"
    )
    
    await callback.message.edit_text(
        project_text,
        reply_markup=get_project_actions_keyboard(project_id)
    )
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("project_tasks_"))
async def show_project_tasks(callback: types.CallbackQuery):
    """Показать задачи проекта"""
    project_id = int(callback.data.split("_")[-1])
    
    # Проверяем доступ к проекту
    project = await db.get_project(project_id, callback.from_user.id)
    if not project:
        await callback.answer("Проект не найден", show_alert=True)
        return
    
    tasks = await db.get_project_tasks(project_id, callback.from_user.id)
    
    if not tasks:
        await callback.message.edit_text(
            f"📁 Проект: {project['name']}\n\n"
            "В этом проекте пока нет задач.",
            reply_markup=get_tasks_keyboard(tasks, project_id)
        )
        return
    
    tasks_text = f"📁 Проект: {project['name']}\n📋 Задачи:\n\n"
    
    for i, task in enumerate(tasks, 1):
        status_icon = "✅" if task['status'] == 'завершено' else "⏳"
        deadline_str = task['deadline'].strftime('%d.%m.%y %H:%M')
        tasks_text += f"{i}. {status_icon} {task['title']}\n"
        tasks_text += f"   📅 {deadline_str}\n"
        if task['description']:
            desc = task['description'][:50] + "..." if len(task['description']) > 50 else task['description']
            tasks_text += f"   📝 {desc}\n"
        tasks_text += "\n"
    
    await callback.message.edit_text(
        tasks_text,
        reply_markup=get_tasks_keyboard(tasks, project_id)
    )
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("task_"))
async def show_task(callback: types.CallbackQuery):
    """Показать информацию о задаче"""
    task_id = int(callback.data.split("_")[-1])
    
    task = await db.get_task(task_id, callback.from_user.id)
    if not task:
        await callback.answer("Задача не найдена", show_alert=True)
        return
    
    status_icon = "✅" if task['status'] == 'завершено' else "⏳"
    deadline_str = task['deadline'].strftime('%d.%m.%y %H:%M')
    
    task_text = (
        f"{status_icon} Задача: {task['title']}\n"
        f"📅 Дедлайн: {deadline_str}\n"
        f"📝 Описание: {task['description'] or 'Нет описания'}\n"
        f"💬 Комментарий: {task['comment'] or 'Нет комментария'}\n"
        f"📊 Статус: {task['status']}"
    )
    
    await callback.message.edit_text(
        task_text,
        reply_markup=get_task_actions_keyboard(task_id, task['status'])
    )
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("complete_task_"))
async def complete_task(callback: types.CallbackQuery):
    """Завершить задачу"""
    task_id = int(callback.data.split("_")[-1])
    
    success = await db.update_task_status(
        task_id=task_id,
        user_id=callback.from_user.id,
        status='завершено'
    )
    
    if success:
        await callback.answer("✅ Задача завершена!", show_alert=True)
        # Обновляем сообщение
        await show_task(callback)
    else:
        await callback.answer("❌ Не удалось завершить задачу", show_alert=True)


@router.callback_query(lambda c: c.data.startswith("reopen_task_"))
async def reopen_task(callback: types.CallbackQuery):
    """Вернуть задачу в работу"""
    task_id = int(callback.data.split("_")[-1])
    
    success = await db.update_task_status(
        task_id=task_id,
        user_id=callback.from_user.id,
        status='активно'
    )
    
    if success:
        await callback.answer("↩️ Задача возвращена в работу!", show_alert=True)
        # Обновляем сообщение
        await show_task(callback)
    else:
        await callback.answer("❌ Не удалось вернуть задачу в работу", show_alert=True)


@router.callback_query(lambda c: c.data.startswith("view_comment_"))
async def view_task_comment(callback: types.CallbackQuery):
    """Показать комментарий задачи"""
    task_id = int(callback.data.split("_")[-1])
    
    task = await db.get_task(task_id, callback.from_user.id)
    if not task:
        await callback.answer("Задача не найдена", show_alert=True)
        return
    
    comment_text = task.get('comment') or 'Нет комментария'
    
    await callback.answer(
        f"💬 Комментарий:\n{comment_text}",
        show_alert=True
    )


@router.callback_query(lambda c: c.data.startswith("edit_task_"))
async def edit_task_menu(callback: types.CallbackQuery):
    """Меню редактирования задачи"""
    task_id = int(callback.data.split("_")[-1])
    
    task = await db.get_task(task_id, callback.from_user.id)
    if not task:
        await callback.answer("Задача не найдена", show_alert=True)
        return
    
    await callback.message.edit_text(
        "Выберите что хотите отредактировать:",
        reply_markup=get_edit_task_fields_keyboard(task_id)
    )
    await callback.answer()


# Обработчики удаления
@router.callback_query(lambda c: c.data.startswith("delete_project_"))
async def delete_project_confirm(callback: types.CallbackQuery):
    """Подтверждение удаления проекта"""
    project_id = int(callback.data.split("_")[-1])
    
    project = await db.get_project(project_id, callback.from_user.id)
    if not project:
        await callback.answer("Проект не найден", show_alert=True)
        return
    
    await callback.message.edit_text(
        f"❗ Вы уверены, что хотите удалить проект «{project['name']}»?\n"
        f"Все задачи в этом проекте также будут удалены!",
        reply_markup=get_confirm_delete_keyboard("project", project_id)
    )
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("delete_task_"))
async def delete_task_confirm(callback: types.CallbackQuery):
    """Подтверждение удаления задачи"""
    task_id = int(callback.data.split("_")[-1])
    
    task = await db.get_task(task_id, callback.from_user.id)
    if not task:
        await callback.answer("Задача не найден", show_alert=True)
        return
    
    await callback.message.edit_text(
        f"❗ Вы уверены, что хотите удалить задачу «{task['title']}»?",
        reply_markup=get_confirm_delete_keyboard("task", task_id)
    )
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("confirm_delete_"))
async def confirm_delete(callback: types.CallbackQuery):
    """Подтверждение и выполнение удаления"""
    parts = callback.data.split("_")
    item_type = parts[2]
    item_id = int(parts[3])
    
    if item_type == "project":
        success = await db.delete_project(item_id, callback.from_user.id)
        message_text = "Проект удален"
    else:  # task
        success = await db.delete_task(item_id, callback.from_user.id)
        message_text = "Задача удалена"
    
    if success:
        await callback.message.edit_text(f"✅ {message_text}!")
        # Возвращаемся к списку проектов
        await list_projects(callback)
    else:
        await callback.answer("❌ Не удалось удалить", show_alert=True)
    
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("cancel_delete_"))
async def cancel_delete(callback: types.CallbackQuery):
    """Отмена удаления"""
    parts = callback.data.split("_")
    item_type = parts[2]
    item_id = int(parts[3])
    
    if item_type == "project":
        await show_project(callback)
    else:  # task
        await show_task(callback)
    
    await callback.answer()


@router.callback_query(lambda c: c.data == "show_reminders")
async def show_reminders(callback: types.CallbackQuery):
    """Показать предстоящие задачи"""
    # Получаем все проекты пользователя
    projects = await db.get_user_projects(callback.from_user.id)
    
    if not projects:
        await callback.message.edit_text(
            "У вас пока нет проектов и задач.",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    reminders_text = "🔔 Предстоящие задачи:\n\n"
    has_upcoming = False
    
    for project in projects:
        tasks = await db.get_project_tasks(project['id'], callback.from_user.id)
        upcoming_tasks = [
            t for t in tasks 
            if t['status'] == 'активно' and t['deadline'] > datetime.now()
        ]
        
        if upcoming_tasks:
            has_upcoming = True
            reminders_text += f"📁 {project['name']}:\n"
            
            for task in sorted(upcoming_tasks, key=lambda x: x['deadline']):
                deadline_str = task['deadline'].strftime('%d.%m.%y %H:%M')
                time_left = task['deadline'] - datetime.now()
                hours_left = int(time_left.total_seconds() // 3600)
                
                reminders_text += f"  ⏳ {task['title']}\n"
                reminders_text += f"    📅 {deadline_str} (осталось ~{hours_left} ч.)\n\n"
    
    if not has_upcoming:
        reminders_text = "✅ У вас нет предстоящих задач с дедлайнами."
    
    await callback.message.edit_text(
        reminders_text,
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()
