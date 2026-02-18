from aiogram.fsm.state import State, StatesGroup


class OtherGroupState(StatesGroup):
    waiting_for_group = State()