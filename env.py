"""
Handles all environment variables set by the .env file

Uses pydantic validation to allow for static and runtime type checks. The bot
will not run unless all required fields are set.
"""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class _Env(BaseSettings):
    """
    THIS IS AN INTERNAL CLASS. DO NOT IMPORT THIS. INSTEAD USE THE `env`
    INSTANCE FROM THIS SAME MODULE LIKE SO:

    ```
    from env import env
    ```

    A Pydantic settings class that handles validation of environment variables.
    Reads in a .env file and ensures each variable fits the criteria. All
    variables are required unless there is a default value assigned.

    If an error occurs during parsing, then an ValidationError will throw and
    will terminate the program.
    """

    dev_mode: bool = True
    discord_token: str
    discord_dev_token: str = Field(min_length=1)
    dev_server_id: int = Field(gt=0)
    states_server_id: int = Field(gt=0)
    slash_command_guilds: list[int]
    emoji_guilds: list[int]
    pi_bot_wiki_username: str | None = None
    pi_bot_wiki_password: str | None = None
    mongo_url: str = Field(min_length=1)

    @field_validator("slash_command_guilds", "emoji_guilds", mode="before")
    @classmethod
    def split_ids(cls, raw: str | int) -> list[int]:
        if isinstance(raw, int):
            return [raw]
        return [int(id) for id in raw.split(",")]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


env = _Env()  # pyright: ignore
