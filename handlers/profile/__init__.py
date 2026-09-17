from aiogram import Router

from .info import info_router
from .statistics import stats_router

profile_router = Router()

profile_router.include_routers(
    info_router,
    stats_router
)