import os
import asyncio
import motor.motor_asyncio # MongoDB AsyncIO driver
import rich

from dotenv import load_dotenv

load_dotenv()

client: motor.motor_asyncio.AsyncIOMotorClient

async def setup():
    global client
    client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv('MONGO_URL'))

async def get_entire_collection(db_name, collection_name, return_one = False):
    global client
    collection = client[db_name][collection_name]
    if return_one:
        return await collection.find_one()
    result = []
    async for doc in collection.find():
        result.append(doc)
    return result

async def get_invitationals():
    return await get_entire_collection("data", "invitationals")

async def get_censor():
    return await get_entire_collection("data", "censor", return_one = True)

event_loop = asyncio.get_event_loop()
# asyncio.ensure_future(setup(), loop = event_loop)
event_loop.run_until_complete(setup())
