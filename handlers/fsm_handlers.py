from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from datetime import datetime
import re

from states.user_states import (
    ProjectStates, TaskStates, 
    EditProjectStates, EditTaskStates
)
from keyboards.inline_kb import (
    get_cancel_keyboard,
    get_projects_keyboard
)
from db import db

router = Router()

# Обработчики для создания проекта
@router.callback_query(lambda c: c.data == "new_project")
async def new_project_start(callback: types.CallbackQuery, state: FSMContext):
    """Начало создания нового проекта"""
    await callback.message.edit_text(
        "Введите название проекта:",
        reply_markup=get_cancel_keyboard("cancel_project")
    )
    await state.set_state(ProjectStates.waiting_for_name)
    await callback.answer()


@router.message(StateFilter(ProjectStates.waiting_for_name))
async def process_project_name(message: types.Message, state: FSMContext):
    """Обработка названия проекта"""
    project_name = message.text.strip()
    
    if not project_name:
        await message.answer(
            "Название проекта не может быть пустым. Попробуйте снова:",
            reply_markup=get_cancel_keyboard("cancel_project")
        )
        return
    
    await state.update_data(project_name=project_name)
    await message.answer(
        "Введите описание проекта (или отправьте «-», чтобы пропустить):",
        reply_markup=get_cancel_keyboard("cancel_project")
    )
    await state.set_state(ProjectStates.waiting_for_description)


@router.message(StateFilter(ProjectStates.waiting_for_description))
async def process_project_description(message: types.Message, state: FSMContext):
    """Обработка описания проекта"""
    description = message.text.strip()
    if description == "-":
        description = None
    
    data = await state.get_data()
    project_name = data['project_name']
    
    # Создаем проект в БД
    project_id = await db.create_project(
        user_id=message.from_user.id,
        name=project_name,
        description=description
    )
    
    await message.answer(
        f"✅ Проект «{project_name}» успешно создан!",
        reply_markup=types.ReplyKeyboardRemove()
    )
    
    await state.clear()


# Обработчики для создания задачи
@router.callback_query(lambda c: c.data == "new_task")
async def new_task_start(callback: types.CallbackQuery, state: FSMContext):
    """Начало создания новой задачи - выбор проекта"""
    projects = await db.get_user_projects(callback.from_user.id)
    
    if not projects:
        await callback.message.edit_text(
            "У вас нет проектов. Сначала создайте проект.",
            reply_markup=get_cancel_keyboard("back_to_main")
        )
        return
    
    await callback.message.edit_text(
        "Выберите проект для новой задачи:",
        reply_markup=get_projects_keyboard(projects)
    )
    await state.set_state(TaskStates.waiting_for_project)
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("new_task_project_"))
async def new_task_for_project(callback: types.CallbackQuery, state: FSMContext):
    """Создание задачи для выбранного проекта"""
    project_id = int(callback.data.split("_")[-1])
    
    await state.update_data(project_id=project_id)
    await callback.message.edit_text(
        "Введите название задачи:",
        reply_markup=get_cancel_keyboard("cancel_task")
    )
    await state.set_state(TaskStates.waiting_for_title)
    await callback.answer()


@router.message(StateFilter(TaskStates.waiting_for_title))
async def process_task_title(message: types.Message, state: FSMContext):
    """Обработка названия задачи"""
    title = message.text.strip()
    
    if not title:
        await message.answer(
            "Название задачи не может быть пустым. Попробуйте снова:",
            reply_markup=get_cancel_keyboard("cancel_task")
        )
        return
    
    await state.update_data(title=title)
    await message.answer(
        "Введите описание задачи (или отправьте «-», чтобы пропустить):",
        reply_markup=get_cancel_keyboard("cancel_task")
    )
    await state.set_state(TaskStates.waiting_for_description)


@router.message(StateFilter(TaskStates.waiting_for_description))
async def process_task_description(message: types.Message, state: FSMContext):
    """Обработка описания задачи"""
    description = message.text.strip()
    if description == "-":
        description = None
    
    await state.update_data(description=description)
    await message.answer(
        "Введите дедлайн в формате ДД.ММ.ГГ ЧЧ:ММ (например: 05.02.26 18:30):",
        reply_markup=get_cancel_keyboard("cancel_task")
    )
    await state.set_state(TaskStates.waiting_for_deadline)


@router.message(StateFilter(TaskStates.waiting_for_deadline))
async def process_task_deadline(message: types.Message, state: FSMContext):
    """Обработка дедлайна задачи"""
    deadline_str = message.text.strip()
    
    # Парсим дату
    try:
        deadline = datetime.strptime(deadline_str, "%d.%m.%y %H:%M")
        
        # Проверяем, что дата в будущем
        if deadline <= datetime.now():
            raise ValueError("Дата в прошлом")
            
    except (ValueError, TypeError) as e:
        await message.answer(
            "❌ Некорректная дата или дата в прошлом. Попробуйте снова:\n"
            "Формат: ДД.ММ.ГГ ЧЧ:ММ (например: 05.02.26 18:30)",
            reply_markup=get_cancel_keyboard("cancel_task")
        )
        return
    
    await state.update_data(deadline=deadline)
    await message.answer(
        "Введите комментарий к задаче (или отправьте «-», чтобы пропустить):",
        reply_markup=get_cancel_keyboard("cancel_task")
    )
    await state.set_state(TaskStates.waiting_for_comment)


@router.message(StateFilter(TaskStates.waiting_for_comment))
async def process_task_comment(message: types.Message, state: FSMContext):
    """Обработка комментария задачи"""
    comment = message.text.strip()
    if comment == "-":
        comment = None
    
    data = await state.get_data()
    
    # Создаем задачу в БД
    task_id = await db.create_task(
        project_id=data['project_id'],
        title=data['title'],
        description=data.get('description'),
        deadline=data['deadline'],
        comment=comment
    )
    
    deadline_str = data['deadline'].strftime('%d.%m.%y %H:%M')
    await message.answer(
        f"✅ Задача «{data['title']}» успешно создана!\n"
        f"📅 Дедлайн: {deadline_str}",
        reply_markup=types.ReplyKeyboardRemove()
    )
    
    await state.clear()


# Обработчики для редактирования проекта
@router.callback_query(lambda c: c.data.startswith("edit_project_"))
async def edit_project_start(callback: types.CallbackQuery, state: FSMContext):
    """Начало редактирования проекта"""
    project_id = int(callback.data.split("_")[-1])
    
    # Получаем проект
    project = await db.get_project(project_id, callback.from_user.id)
    if not project:
        await callback.answer("Проект не найден", show_alert=True)
        return
    
    await state.update_data(project_id=project_id)
    await callback.message.edit_text(
        f"Текущее название: {project['name']}\n"
        f"Введите новое название:",
        reply_markup=get_cancel_keyboard("cancel_edit_project")
    )
    await state.set_state(EditProjectStates.waiting_for_name)
    await callback.answer()


@router.message(StateFilter(EditProjectStates.waiting_for_name))
async def process_edit_project_name(message: types.Message, state: FSMContext):
    """Обработка нового названия проекта"""
    name = message.text.strip()
    
    if not name:
        await message.answer(
            "Название проекта не может быть пустым. Попробуйте снова:",
            reply_markup=get_cancel_keyboard("cancel_edit_project")
        )
        return
    
    await state.update_data(name=name)
    
    data = await state.get_data()
    project = await db.get_project(data['project_id'], message.from_user.id)
    
    await message.answer(
        f"Текущее описание: {project['description'] or 'Нет описания'}\n"
        f"Введите новое описание (или «-», чтобы пропустить):",
        reply_markup=get_cancel_keyboard("cancel_edit_project")
    )
    await state.set_state(EditProjectStates.waiting_for_description)


@router.message(StateFilter(EditProjectStates.waiting_for_description))
async def process_edit_project_description(message: types.Message, state: FSMContext):
    """Обработка нового описания проекта"""
    description = message.text.strip()
    if description == "-":
        description = None
    
    data = await state.get_data()
    
    # Обновляем проект в БД
    success = await db.update_project(
        project_id=data['project_id'],
        user_id=message.from_user.id,
        name=data['name'],
        description=description
    )
    
    if success:
        await message.answer(
            f"✅ Проект «{data['name']}» успешно обновлен!",
            reply_markup=types.ReplyKeyboardRemove()
        )
    else:
        await message.answer(
            "❌ Не удалось обновить проект",
            reply_markup=types.ReplyKeyboardRemove()
        )
    
    await state.clear()


# Обработчики для редактирования задачи
@router.callback_query(lambda c: c.data.startswith("edit_deadline_"))
async def edit_task_deadline_start(callback: types.CallbackQuery, state: FSMContext):
    """Начало редактирования дедлайна задачи"""
    task_id = int(callback.data.split("_")[-1])
    
    await state.update_data(task_id=task_id)
    await callback.message.edit_text(
        "Введите новый дедлайн в формате ДД.ММ.ГГ ЧЧ:ММ (например: 05.02.26 18:30):",
        reply_markup=get_cancel_keyboard("cancel_edit_task")
    )
    await state.set_state(EditTaskStates.waiting_for_deadline)
    await callback.answer()


@router.message(StateFilter(EditTaskStates.waiting_for_deadline))
async def process_edit_task_deadline(message: types.Message, state: FSMContext):
    """Обработка нового дедлайна задачи"""
    deadline_str = message.text.strip()
    
    try:
        deadline = datetime.strptime(deadline_str, "%d.%m.%y %H:%M")
        
        # Проверяем, что дата в будущем
        if deadline <= datetime.now():
            raise ValueError("Дата в прошлом")
            
    except (ValueError, TypeError) as e:
        await message.answer(
            "❌ Некорректная дата или дата в прошлом. Попробуйте снова:\n"
            "Формат: ДД.ММ.ГГ ЧЧ:ММ (например: 05.02.26 18:30)",
            reply_markup=get_cancel_keyboard("cancel_edit_task")
        )
        return
    
    data = await state.get_data()
    task_id = data['task_id']
    
    # Обновляем дедлайн в БД
    success = await db.update_task_deadline(
        task_id=task_id,
        user_id=message.from_user.id,
        deadline=deadline
    )
    
    if success:
        deadline_formatted = deadline.strftime('%d.%m.%y %H:%M')
        await message.answer(
            f"✅ Дедлайн задачи обновлен на {deadline_formatted}!",
            reply_markup=types.ReplyKeyboardRemove()
        )
    else:
        await message.answer(
            "❌ Не удалось обновить дедлайн",
            reply_markup=types.ReplyKeyboardRemove()
        )
    
    await state.clear()


@router.callback_query(lambda c: c.data.startswith("edit_comment_"))
async def edit_task_comment_start(callback: types.CallbackQuery, state: FSMContext):
    """Начало редактирования комментария задачи"""
    task_id = int(callback.data.split("_")[-1])
    
    # Получаем текущий комментарий
    task = await db.get_task(task_id, callback.from_user.id)
    if not task:
        await callback.answer("Задача не найдена", show_alert=True)
        return
    
    await state.update_data(task_id=task_id)
    
    current_comment = task.get('comment') or 'Нет комментария'
    await callback.message.edit_text(
        f"Текущий комментарий: {current_comment}\n"
        f"Введите новый комментарий (или «-», чтобы удалить):",
        reply_markup=get_cancel_keyboard("cancel_edit_task")
    )
    await state.set_state(EditTaskStates.waiting_for_comment)
    await callback.answer()


@router.message(StateFilter(EditTaskStates.waiting_for_comment))
async def process_edit_task_comment(message: types.Message, state: FSMContext):
    """Обработка нового комментария задачи"""
    comment = message.text.strip()
    if comment == "-":
        comment = None
    
    data = await state.get_data()
    task_id = data['task_id']
    
    # Обновляем комментарий в БД
    success = await db.update_task_comment(
        task_id=task_id,
        user_id=message.from_user.id,
        comment=comment
    )
    
    if success:
        if comment:
            await message.answer(
                "✅ Комментарий к задаче обновлен!",
                reply_markup=types.ReplyKeyboardRemove()
            )
        else:
            await message.answer(
                "✅ Комментарий к задаче удален!",
                reply_markup=types.ReplyKeyboardRemove()
            )
    else:
        await message.answer(
            "❌ Не удалось обновить комментарий",
            reply_markup=types.ReplyKeyboardRemove()
        )
    
    await state.clear()


# Обработчики отмены
@router.callback_query(lambda c: c.data in ["cancel", "cancel_project", "cancel_task", 
                                           "cancel_edit_project", "cancel_edit_task",
                                           "back_to_main"])
async def cancel_handler(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик отмены действий"""
    await state.clear()
    
    if callback.data == "back_to_main":
        from handlers.commands import cmd_start
        await cmd_start(callback.message)
    else:
        await callback.message.edit_text(
            "Действие отменено.",
            reply_markup=types.ReplyKeyboardRemove()
        )
    
    await callback.answer()
