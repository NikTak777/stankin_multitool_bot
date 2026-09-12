from aiogram.fsm.state import StatesGroup, State

class SearchProfileState(StatesGroup):
    choosing_username = State()