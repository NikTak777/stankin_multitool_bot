import asyncio
import aiohttp

from config import settings

base_url: str = f"{settings.SCHEDULE_API_BASE_URL}/group/codes"

async def get_available_group_codes():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(base_url) as resp:
                response = await resp.json()
                return response
    except aiohttp.ClientError:
        return "connection", []
    except asyncio.TimeoutError:
        return "timeout", []
