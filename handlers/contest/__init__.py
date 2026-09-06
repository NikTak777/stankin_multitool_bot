from aiogram import Router

from .info import info_router

contest_router = Router()

contest_router.include_router(info_router)