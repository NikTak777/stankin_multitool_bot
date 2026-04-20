from aiogram.fsm.state import StatesGroup, State

class ScheduleState(StatesGroup):
    choosing_day = State()
    choosing_month = State()
    entering_professor_name = State()
    viewing_professor_schedule = State()
    professor_choosing_day = State()
    professor_choosing_month = State()