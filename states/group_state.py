from aiogram.fsm.state import State, StatesGroup

class GroupSelectState(StatesGroup):
    choosing_code = State()
    choosing_year = State()
    choosing_group = State()