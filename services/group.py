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
                if resp.status != 200:
                    return {
                        "status": resp.status,
                        "data": []
                    }
                return response
    except aiohttp.ClientError:
        return {
            "status": 500,
            "data": []
        }
    except asyncio.TimeoutError:
        return {
            "status": 408,
            "data": []
        }

async def get_available_group_years(user_group_code: str):
    url = f"{base_url}/years"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                params={"user_group_code": user_group_code}
            ) as resp:
                response = await resp.json()
                if resp.status != 200:
                    return {
                        "status": resp.status,
                        "data": []
                    }
                return response
    except aiohttp.ClientError:
        return {
            "status": 500,
            "data": []
        }
    except asyncio.TimeoutError:
        return {
            "status": 408,
            "data": []
        }


async def get_available_group_names(user_group_code: str, user_group_year: str):
    url = f"{base_url}/"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                params={
                    "user_group_code": user_group_code,
                    "user_group_year": user_group_year
                }
            ) as resp:
                response = await resp.json()
                if resp.status != 200:
                    return {
                        "status": resp.status,
                        "data": []
                    }
                return response
    except aiohttp.ClientError:
        return {
            "status": 500,
            "data": []
        }
    except asyncio.TimeoutError:
        return {
            "status": 408,
            "data": []
        }