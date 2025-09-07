from aiogram.fsm.state import StatesGroup, State


class SendTimeState(StatesGroup):
    editing = State()