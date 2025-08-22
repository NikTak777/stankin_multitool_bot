from aiogram.fsm.state import StatesGroup, State

class GroupRegistration(StatesGroup):
    waiting_for_group_name = State()