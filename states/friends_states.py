from aiogram.fsm.state import StatesGroup, State


class EditMenuState(StatesGroup):
    editing = State()


class WishlistSuggestionState(StatesGroup):
    awaiting_wishlist = State()