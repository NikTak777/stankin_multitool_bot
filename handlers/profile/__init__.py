from aiogram import Router

from .info import info_router

profile_router = Router()

profile_router.include_routers(
    info_router
)