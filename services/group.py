import asyncio
import aiohttp

from config import settings

base_url: str = f"{settings.SCHEDULE_API_BASE_URL}/group"

async def get_available_group_codes():
    url = f"{base_url}/codes"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                response = await resp.json()
                return response
    except aiohttp.ClientError:
        return "connection", []
    except asyncio.TimeoutError:
        return "timeout", []


async def get_available_group_years(user_group_code: str):
    url = f"{base_url}/years"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                params={"user_group_code": user_group_code}
            ) as resp:
                response = await resp.json()
                return response
    except aiohttp.ClientError:
        return "connection", []
    except asyncio.TimeoutError:
        return "timeout", []
