import aiohttp
import asyncio
import json

from lists import getStateList

SCHOOLS_URL="https://inventory.data.gov/api/3/action/datastore_search?resource_id=102fd9bd-4737-401b-b88f-5c5b0fab94ec&q="

async def getRawResponse(searchTerm, state):
    session = aiohttp.ClientSession()
    res = await session.get(SCHOOLS_URL + " " + searchTerm + " " + state)
    text = await res.text()
    await session.close()
    return text

async def getSchoolListing(searchTerm, state):
    returnObj = []
    states = await getStateList()
    jsonObj = json.loads(await getRawResponse(searchTerm, state))
    results = jsonObj['result']['records']
    for r in results:
        latlon = r['Location'].replace("(", "").replace(")", "")
        lat = latlon.split(", ")[0]
        lon = latlon.split(", ")[1]
        returnObj.append({
            'name': r['SCHNAM09'],
            'state': r['MSTATE09'],
            'lat': lat,
            'lon': lon,
            'address': r['LSTREE09'].title() + r" {{break}} " + r['LCITY09'].title() + ", " + r['MSTATE09'] + " " + r['LZIP09'],
            'zip': r['LZIP09']
        })
    for r in returnObj:
        state = r['state']
        for s in states:
            if s.find(r['state']) != -1:
                r['state'] = s[:s.find(" (")]
                break
        r['wikicode'] = f"| state = {r['state']}\n| lat = {r['lat']}\n| long = {r['lon']}\n| location = {r['address']}"
    return returnObj