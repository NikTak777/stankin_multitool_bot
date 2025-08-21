from aiogram.fsm.state import StatesGroup, State

class ScheduleState(StatesGroup):
    choosing_day = State()
    choosing_month = State()