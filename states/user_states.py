from aiogram.fsm.state import State, StatesGroup


class ProjectStates(StatesGroup):
    """Состояния FSM для создания проекта"""
    waiting_for_name = State()
    waiting_for_description = State()


class TaskStates(StatesGroup):
    """Состояния FSM для создания задачи"""
    waiting_for_project = State()
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_deadline = State()
    waiting_for_comment = State()


class EditProjectStates(StatesGroup):
    """Состояния FSM для редактирования проекта"""
    waiting_for_name = State()
    waiting_for_description = State()


class EditTaskStates(StatesGroup):
    """Состояния FSM для редактирования задачи"""
    waiting_for_field = State()
    waiting_for_deadline = State()
    waiting_for_comment = State()
