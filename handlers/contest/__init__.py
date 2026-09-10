from aiogram import Router

from .info import info_router
from .admin import raffle_router
from .rules import rules_router

contest_router = Router()

contest_router.include_routers(
    info_router,
    raffle_router,
    rules_router
)