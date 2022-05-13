"""
Adds all functionality for working with a MongoDB database. This database should
power several core features of the bot, including temporary information, such as a custom
status or a list of relevant events.
"""
from __future__ import annotations

import os
from typing import Any, Dict

import motor.motor_asyncio  # MongoDB AsyncIO driver
from bson.objectid import ObjectId
from dotenv import load_dotenv

load_dotenv()


class MongoDatabase:
    """
    Class for allowing the bot access to an external MongoDB database.
    """

    client: motor.motor_asyncio.AsyncIOMotorClient

    def __init__(self, bot):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(
            os.getenv("MONGO_URL"), tz_aware=True
        )
        self.bot = bot

    async def delete(self, db_name: str, collection_name: str, iden: ObjectId) -> None:
        """
        Deletes a document in a specific collection.

        Args:
            db_name: The name of the database.
            collection_name: The name of the collection.
            iden: The ID of the document.
        """
        collection: motor.motor_asyncio.AsyncIOMotorCollection = self.client[db_name][
            collection_name
        ]
        assert isinstance(collection, motor.motor_asyncio.AsyncIOMotorCollection)

        await collection.delete_one({"_id": iden})

    async def delete_by(
        self, db_name: str, collection_name: str, dict: Dict[str, Any]
    ) -> None:
        """
        Deletes all documents in a collection matching a specific filter.

        Args:
            db_name: The name of the database.
            collection_name: The name of the collection.
            dict: The specification to delete by.
        """
        collection = self.client[db_name][collection_name]
        await collection.delete_many(dict)

    async def get_entire_collection(
        self, db_name: str, collection_name: str, return_one: bool = False
    ):
        """
        Gets an entire collection of documents.

        Args:
            db_name: The name of the database collection.
            collection_name: The name of the collection in the database to use.
            return_one: Whether to return just one document.
        """
        collection = self.client[db_name][collection_name]
        if return_one:
            return await collection.find_one()
        result = []
        async for doc in collection.find():
            result.append(doc)
        return result

    async def get_invitationals(self):
        """
        Gets all documents in the invitationals collection.
        """
        return await self.get_entire_collection("data", "invitationals")

    async def get_cron(self):
        """
        Gets all documents in the CRON collection.
        """
        return await self.get_entire_collection("data", "cron")

    async def get_censor(self):
        """
        Gets the document containing censor information from the censor collection.
        """
        return await self.get_entire_collection("data", "censor", return_one=True)

    async def get_pings(self):
        """
        Gets all documents in the pings collection.
        """
        return await self.get_entire_collection("data", "pings")

    async def get_tags(self):
        """
        Gets all documents in the tags collection.
        """
        return await self.get_entire_collection("data", "tags")

    async def get_reports(self):
        """
        Gets all documents in the reports collection.
        """
        return await self.get_entire_collection("data", "reports")

    async def get_events(self):
        """
        Gets all documents in the events collection.
        """
        return await self.get_entire_collection("data", "events")

    async def get_settings(self):
        """
        Gets the one document containing settings information from the settings
        database collection.
        """
        return await self.get_entire_collection("data", "settings", return_one=True)

    async def insert(
        self, db_name: str, collection_name: str, insert_dict: Dict[str, Any]
    ):
        """
        Inserts a new document into a collection using a dictionary of document to
        add to the document.
        """
        collection = self.client[db_name][collection_name]
        return await collection.insert_one(insert_dict)

    async def update(
        self,
        db_name: str,
        collection_name: str,
        doc_id: ObjectId,
        update_dict: Dict[str, Any],
    ) -> None:
        """
        Updates a document in a specific collection using a specific dictionary holding updates.
        """
        collection = self.client[db_name][collection_name]
        await collection.update_one({"_id": doc_id}, update_dict)

    async def update_many(
        self, db_name: str, collection_name: str, docs: Any, update_dict: Dict[str, Any]
    ) -> None:
        """
        Updates several documents in a collection with a specific dictionary holding
        updates.
        """
        collection = self.client[db_name][collection_name]
        ids = [doc.get("_id") for doc in docs]
        await collection.update_many({"_id": {"$in": ids}}, update_dict)

    async def remove_doc(
        self, db_name: str, collection_name: str, doc_id: ObjectId
    ) -> None:
        """
        Deletes a document (from its ID) from a collection.
        """
        collection = self.client[db_name][collection_name]
        await collection.delete_one({"_id": doc_id})
