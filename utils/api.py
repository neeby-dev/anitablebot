import aiohttp


async def get_schedule(day):
    url = "https://api.anixart.tv/schedule"
    headers = {
        'User-Agent': 'AnixartApp/7.8.1-21090118 (Android 7.1.2; SDK 25; arm64-v8a; Android; en)',
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url=url, headers=headers) as response:
            info = await response.json()
        return info[day]
