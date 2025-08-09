"""
Handles all environment variables set by the .env file

Uses pydantic validation to allow for static and runtime type checks. The bot
will not run unless all required fields are set.
"""

from pydantic import (
    Field,
    computed_field,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


class _Env(BaseSettings, extra="ignore"):
    """
    An internal Pydantic settings class that handles validation of environment
    variables. Reads in a .env file and ensures each variable fits the criteria.
    All variables are required unless there is a default value assigned.

    If an error occurs during parsing, then an ValidationError will throw and
    will terminate the program.
    """

    dev_mode: bool = True
    discord_token: str
    discord_dev_token: str = Field(min_length=1)
    dev_server_id: int | None = None
    states_server_id: int = Field(gt=0)
    slash_command_guilds: list[int]
    emoji_guilds: list[int]
    pi_bot_wiki_username: str | None = None
    pi_bot_wiki_password: str | None = None
    mongo_url: str = Field(min_length=1)

    @model_validator(mode="after")
    def verify_server_id(self):
        if self.server_id <= 0:
            raise ValueError("Server id was not set properly")
        return self

    @computed_field
    @property
    def server_id(self) -> int:
        # Use the dev server, else the official Scioly.org server
        if self.dev_mode:
            if self.dev_server_id is None or self.dev_server_id <= 0:
                raise ValueError("dev_server_id must be set if dev_mode is True")
            return self.dev_server_id
        return 698306997287780363  # Official Scioly.org server ID

    @field_validator("slash_command_guilds", "emoji_guilds", mode="before")
    @classmethod
    def split_ids(cls, raw: str | int) -> list[int]:
        if isinstance(raw, int):
            return [raw]
        return [int(id) for id in raw.split(",")]

    model_config = SettingsConfigDict(
        secrets_dir="/run/secrets/",
        env_file=".env",
        env_file_encoding="utf-8",
    )


env = _Env()  # pyright: ignore
