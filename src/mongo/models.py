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
