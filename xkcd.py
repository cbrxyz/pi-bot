import aiohttp
import json

async def get_max():
    session = aiohttp.ClientSession()
    res = await session.get("https://xkcd.com/info.0.json")
    text = await res.text()
    await session.close()
    json_obj = json.loads(text)
    return json_obj['num']