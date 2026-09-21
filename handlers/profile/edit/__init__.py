from aiogram import Router

from .group import group_router

edit_router = Router()

edit_router.include_routers(
    group_router
)