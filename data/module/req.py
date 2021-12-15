import asyncio
import aiohttp
import json

async def json_get(q):
    async with aiohttp.ClientSession() as session:
        async with session.get(q) as resp:
            response = await resp.json()

    return response
    
async def json_post(q):
    async with aiohttp.ClientSession() as session:
        async with session.post(q) as resp:
            response = await resp.json()

    return response