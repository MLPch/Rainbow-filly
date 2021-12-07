import aiohttp


async def json_get(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            response = await resp.json()

    return response


async def json_post(url):
    async with aiohttp.ClientSession() as session:
        async with session.post(url) as resp:
            response = await resp.json()

    return response


async def status(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            response = resp.status

    return response
