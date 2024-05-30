"""
Contains all database models
"""
from datetime import datetime
from typing import Annotated, Literal

from beanie import Document, Indexed
from pydantic import Field


class Cron(Document):
    cron_type: Literal["UNMUTE", "UNBAN", "UNSELFMUTE", "REMOVE_STATUS"] = Field(
        alias="type",
    )
    time: Annotated[datetime, Indexed()]
    user: Annotated[int, Indexed()]
    tag: str

    class Settings:
        name = "cron"
        use_cache = False
