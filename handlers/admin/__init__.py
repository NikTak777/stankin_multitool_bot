from aiogram import Router

from .summary import summary_router
from .activity import activity_router
from .usability import usability_router
from .tasks import task_router

admin_router = Router()

admin_router.include_routers(
    summary_router,
    activity_router,
    usability_router,
    task_router
)