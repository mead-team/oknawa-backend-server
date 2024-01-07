import aiohttp


async def fetch(url, session, headers, params):
    async with session.get(url, headers=headers, params=params) as response:
        return await response.json()


async def get_place_info(place_url):
    async with aiohttp.ClientSession() as session:
        async with session.get(place_url) as response:
            return await response.json()
