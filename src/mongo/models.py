"""
Contains all database models
"""

from datetime import datetime
from typing import Annotated, Literal

from beanie import Document, Indexed
from pydantic import BaseModel, Field


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


class TagPermissions(BaseModel):
    launch_helpers: bool
    members: bool
    staff: bool


class Tag(Document):
    name: str
    permissions: TagPermissions
    output: str

    class Settings:
        name = "tags"
        use_cache = False


class Invitational(Document):
    official_name: str
    channel_name: str
    emoji: str | None
    aliases: list[str]
    tourney_date: datetime
    open_days: int
    closed_days: int
    voters: list[int]
    status: Literal["voting", "open", "archived"]

    class Settings:
        name = "invitationals"
        use_cache = True


class Event(Document):
    name: str
    aliases: list[str]
    emoji: str | None

    class Settings:
        name = "events"
        use_cache = True


class Censor(Document):
    words: list[str]
    emojis: list[str]

    class Settings:
        name = "censor"
        use_cache = True


class Settings(Document):
    custom_bot_status_type: str | None
    custom_bot_status_text: str | None
    invitational_season: int

    class Settings:
        name = "settings"
        use_cache = True
