from aiogram import Router

from .request import request_router

friend_router = Router()

friend_router.include_routers(
    request_router
)