from aiogram.filters import BaseFilter
from aiogram.types import TelegramObject
from aiogram.fsm.context import FSMContext


class RequireFSM(BaseFilter):
    def __init__(self, *keys: str):
        self.keys = keys

    async def __call__(self, event: TelegramObject, state: FSMContext) -> bool:
        if not state:
            return False

        data = await state.get_data()
        return all(data.get(key) is not None for key in self.keys)