"""
Contains all database models
"""

from datetime import datetime
from typing import Annotated, Literal

from beanie import Document, Indexed
from pydantic import Field


class Cron(Document):
    cron_type: Annotated[
        Literal["UNMUTE", "UNBAN", "UNSELFMUTE", "REMOVE_STATUS"],
        Indexed(),
    ] = Field(
        alias="type",
    )
    time: Annotated[datetime, Indexed()]
    user: int
    tag: str

    class Settings:
        name = "cron"
        use_cache = False


class Ping(Document):
    user_id: Annotated[int, Indexed()]
    word_pings: list[str]
    dnd: bool

    class Settings:
        name = "pings"
        use_cache = False
