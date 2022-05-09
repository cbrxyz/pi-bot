from __future__ import annotations

import os
import motor.motor_asyncio  # MongoDB AsyncIO driver

from dotenv import load_dotenv

load_dotenv()

client: motor.motor_asyncio.AsyncIOMotorClient


async def setup():
    global client
    client = motor.motor_asyncio.AsyncIOMotorClient(
        os.getenv("MONGO_URL"), tz_aware=True
    )


async def delete(db_name, collection_name, iden):
    global client
    collection = client[db_name][collection_name]
    await collection.delete_one({"_id": iden})


async def delete_by(db_name, collection_name, dict):
    global client
    collection = client[db_name][collection_name]
    await collection.delete_many(dict)


async def get_entire_collection(db_name, collection_name, return_one=False):
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
    return await get_entire_collection("data", "censor", return_one=True)


async def get_pings():
    return await get_entire_collection("data", "pings")


async def get_tags():
    return await get_entire_collection("data", "tags")


async def get_reports():
    return await get_entire_collection("data", "reports")


async def get_events():
    return await get_entire_collection("data", "events")


async def get_settings():
    return await get_entire_collection("data", "settings", return_one=True)


async def insert(db_name, collection_name, insert_dict):
    global client
    collection = client[db_name][collection_name]
    return await collection.insert_one(insert_dict)


async def update(db_name, collection_name, doc_id, update_dict):
    global client
    collection = client[db_name][collection_name]
    await collection.update_one({"_id": doc_id}, update_dict)


async def update_many(db_name, collection_name, docs, update_dict):
    global client
    collection = client[db_name][collection_name]
    ids = [doc.get("_id") for doc in docs]
    await collection.update_many({"_id": {"$in": ids}}, update_dict)


async def remove_doc(db_name, collection_name, doc_id):
    global client
    collection = client[db_name][collection_name]
    await collection.delete_one({"_id": doc_id})
