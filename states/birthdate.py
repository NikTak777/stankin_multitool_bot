from aiogram.fsm.state import StatesGroup, State

class BirthdayStates(StatesGroup):
    day = State()
    month = State()
    year = State()