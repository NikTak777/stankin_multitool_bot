from aiogram import Router

from .request import request_router
from .delete import delete_router

friends_router = Router()

friends_router.include_routers(
    request_router,
    delete_router
)