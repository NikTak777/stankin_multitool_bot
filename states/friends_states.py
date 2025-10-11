from aiogram.fsm.state import StatesGroup, State


class EditMenuState(StatesGroup):
    editing = State()