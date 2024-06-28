import aiohttp


async def fetch(session, url, headers=None, params=None):
    async with session.get(url, headers=headers, params=params) as response:
        return await response.json()


async def post(session, url, headers=None, json=None):
    async with session.post(url, headers=headers, json=json) as response:
        return await response.json()
