import asyncio
import json

import aiohttp

from src.lists import get_state_list

SCHOOLS_URL = "https://inventory.data.gov/api/3/action/datastore_search?resource_id=102fd9bd-4737-401b-b88f-5c5b0fab94ec&q="


async def get_raw_response(searchTerm, state):
    session = aiohttp.ClientSession()
    res = await session.get(SCHOOLS_URL + " " + searchTerm + " " + state)
    text = await res.text()
    await session.close()
    return text


async def get_school_listing(searchTerm, state):
    return_obj = []
    states = await get_state_list()
    json_obj = json.loads(await get_raw_response(searchTerm, state))
    results = json_obj["result"]["records"]
    for r in results:
        lat_lon = r["Location"].replace("(", "").replace(")", "")
        lat = lat_lon.split(", ")[0]
        lon = lat_lon.split(", ")[1]
        return_obj.append(
            {
                "name": r["SCHNAM09"],
                "state": r["MSTATE09"],
                "lat": lat,
                "lon": lon,
                "address": r["LSTREE09"].title()
                + r" {{break}} "
                + r["LCITY09"].title()
                + ", "
                + r["MSTATE09"]
                + " "
                + r["LZIP09"],
                "zip": r["LZIP09"],
            }
        )
    for r in return_obj:
        state = r["state"]
        for s in states:
            if s.find(r["state"]) != -1:
                r["state"] = s[: s.find(" (")]
                break
        r[
            "wikicode"
        ] = f"| state = {r['state']}\n| lat = {r['lat']}\n| long = {r['lon']}\n| location = {r['address']}"
    return return_obj
