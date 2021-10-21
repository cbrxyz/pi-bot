import os
import asyncio
import motor.motor_asyncio # MongoDB AsyncIO driver
from bson.objectid import ObjectId

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

async def get_cron():
    return await get_entire_collection("data", "cron")

async def get_censor():
    return await get_entire_collection("data", "censor", return_one = True)

async def update(db_name, collection_name, doc_id, update_dict):
    global client
    collection = client[db_name][collection_name]
    await collection.update_one({'_id': doc_id}, update_dict)

async def update_many(db_name, collection_name, docs, update_dict):
    global client
    collection = client[db_name][collection_name]
    ids = [doc.get("_id") for doc in docs]
    await collection.update_many(
        {"_id": {
            "$in": ids
            }
        },
        update_dict
    )

async def remove_doc(db_name, collection_name, doc_id):
    global client
    collection = client[db_name][collection_name]
    await collection.delete_one({'_id': doc_id})

event_loop = asyncio.get_event_loop()
# asyncio.ensure_future(setup(), loop = event_loop)
event_loop.run_until_complete(setup())
