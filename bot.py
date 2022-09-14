"""
Serves as the initial file to launch the bot. Loads all needed extensions and maintains
core functionality.
"""
from __future__ import annotations

import asyncio
import datetime
import uuid
from typing import TYPE_CHECKING, Any, Dict, Optional, Union

import aiohttp

import discord
from discord import app_commands
from discord.ext import commands
from src.discord.globals import (
    BOT_PREFIX,
    CHANNEL_DELETEDM,
    CHANNEL_DMLOG,
    CHANNEL_EDITEDM,
    DEV_TOKEN,
    TOKEN,
    dev_mode,
)
from src.discord.reporter import Reporter
from src.mongo.mongo import MongoDatabase

if TYPE_CHECKING:
    from src.discord.censor import Censor
    from src.discord.logger import Logger
    from src.discord.spam import SpamManager

intents = discord.Intents.all()


class PiBotCommandTree(app_commands.CommandTree):
    def __init__(self, client: PiBot):
        super().__init__(client)

    async def on_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ) -> None:
        # Handle check failures
        if isinstance(error, app_commands.NoPrivateMessage):
            message = (
                "Sorry, but this command does not work in private message. "
                "Please hop on over to the Scioly.org server to use the command!"
            )
        elif isinstance(error, (app_commands.MissingRole, app_commands.MissingAnyRole)):
            message = "Sorry, you don't have the needed role to run this command."
        elif isinstance(error, app_commands.MissingPermissions):
            message = (
                "Sorry, but you aren't allotted the proper permissions "
                "needed by this command."
            )
        elif isinstance(error, app_commands.BotMissingPermissions):
            message = (
                "Oh no! I can't run this command right now. Please contact a developer."
            )
        elif isinstance(error, app_commands.CommandOnCooldown):
            next_time = discord.utils.utcnow() + datetime.timedelta(
                seconds=error.retry_after
            )
            message = (
                "Time to _chill out_ - this command is on cooldown! "
                f"Please try again **{discord.utils.format_dt(next_time, 'R')}.**"
                "\n\n"
                "For future reference, this command is currently limited to "
                f"being executed **{error.cooldown.rate} times per {error.cooldown.per} seconds**."
            )

        # Handle general app command errors
        elif isinstance(error, app_commands.CommandLimitReached):
            message = (
                "Oh no! I've reached my max command limit. Please contact a developer."
            )
        elif isinstance(error, app_commands.CommandInvokeError):
            message = "This command experienced a general error."

            # Report error to staff
            reporter_cog = self.client.get_cog("Reporter")

            assert isinstance(reporter_cog, Reporter)
            await reporter_cog.create_command_error_report(
                error.original, interaction.command
            )

        elif isinstance(error, app_commands.TransformerError):
            message = "This command experienced a transformer error."
        elif isinstance(error, app_commands.CommandAlreadyRegistered):
            message = "This command was already registered."
        elif isinstance(error, app_commands.CommandSignatureMismatch):
            message = (
                "This command is currently out of sync. Please contact a developer."
            )
        elif isinstance(error, app_commands.CommandNotFound):
            message = "Unfortunately, this command could not be found."
        elif isinstance(error, app_commands.MissingApplicationID):
            message = "This application needs an application ID."
        elif isinstance(error, app_commands.CheckFailure):
            message = "You are not allowed to run this command here. Try running it in `#bot-spam` instead."

        else:
            message = "Ooops, there was a command error."
        try:
            await interaction.response.send_message(message, ephemeral=True)
        except discord.InteractionResponded:
            await interaction.followup.send(message, ephemeral=True)


class PiBot(commands.Bot):
    """
    The bot itself. Controls all functionality needed for core operations.
    """

    session: aiohttp.ClientSession | None
    mongo_database: MongoDatabase
    settings = {
        "_id": None,
        "custom_bot_status_type": None,
        "custom_bot_status_text": None,
        "invitational_season": None,
    }

    def __init__(self):
        super().__init__(
            command_prefix=BOT_PREFIX,
            case_insensitive=True,
            intents=intents,
            help_command=None,
            tree_cls=PiBotCommandTree,
        )
        self.listeners_: dict[
            str, dict[str, Any]
        ] = {}  # name differentiation between internal _listeners attribute
        self.__version__ = "v5.0.0"
        self.session = None
        self.mongo_database = MongoDatabase(self)

    async def setup_hook(self) -> None:
        """
        Called when the bot is being setup. Currently sets up a connection to the
        database and initializes all extensions.
        """
        extensions = (
            "src.discord.censor",
            "src.discord.ping",
            "src.discord.staffcommands",
            "src.discord.staff.invitationals",
            "src.discord.staff.censor",
            "src.discord.staff.tags",
            "src.discord.staff.events",
            "src.discord.embed",
            "src.discord.membercommands",
            "src.discord.devtools",
            "src.discord.funcommands",
            "src.discord.tasks",
            "src.discord.spam",
            "src.discord.reporter",
            "src.discord.logger",
        )
        for extension in extensions:
            try:
                await self.load_extension(extension)
            except commands.ExtensionError as e:
                print(f"Failed to load extension {extension}: {e}")

    async def update_setting(self, values: dict[str, Any]):
        for k, v in values.items():
            self.settings[k] = v
            await self.mongo_database.update(
                "data", "settings", self.settings["_id"], {"$set": values}
            )

    async def on_ready(self) -> None:
        """
        Called when the bot is enabled and ready to be run.
        """
        # try:
        #     await self.tree.sync(guild=discord.Object(749057176756027414))
        # except:
        #     import traceback
        #     traceback.print_exc()
        print(f"{self.user} has connected!")

    async def on_message(self, message: discord.Message) -> None:
        # Nothing needs to be done to the bot's own messages
        if message.author.bot:
            return

        # If user is being listened to, return their message
        for listener in self.listeners_.items():
            if message.author.id == listener[1]["follow_id"]:
                listener[1]["message"] = message

        # Log incoming direct messages
        if isinstance(message.channel, discord.DMChannel) and message.author != bot:
            logger_cog: commands.Cog | Logger = self.get_cog("Logger")
            await logger_cog.send_to_dm_log(message)
            print(f"Message from {message.author} through DM's: {message.content}")
        else:
            # Print to output
            if not (
                message.author.bot
                and message.channel.name
                in [CHANNEL_EDITEDM, CHANNEL_DELETEDM, CHANNEL_DMLOG]
            ):
                # avoid sending logs for messages in log channels
                print(
                    f"Message from {message.author} in #{message.channel}: {message.content}"
                )

        # Check if the message contains a censored word/emoji
        is_private = isinstance(
            message.channel, (discord.DMChannel, discord.GroupChannel)
        )

        if message.content and not is_private:
            censor: commands.Cog | Censor = self.get_cog("Censor")
            await censor.on_message(message)

            # Check to see if the message contains repeated content or has too many caps
            spam: commands.Cog | SpamManager = self.get_cog("SpamManager")
            await spam.store_and_validate(message)

    async def start(self, token: str, *, reconnect: bool = True) -> None:
        self.session = aiohttp.ClientSession()
        await super().start(token=token, reconnect=reconnect)

    async def close(self) -> None:
        await self.session.close()
        await super().close()

    async def listen_for_response(
        self, follow_id: int, timeout: int
    ) -> discord.Message | None:
        """
        Creates a global listener for a message from a user.

        Args:
            follow_id: the user ID to create the listener for
            timeout: the amount of time to wait before returning None, assuming
                the user abandoned the operation

        Returns:
            the found message or None
        """
        my_id = str(uuid.uuid4())
        self.listeners_[my_id] = {
            "follow_id": follow_id,
            "timeout": timeout,
            "message": None,
        }
        count = timeout
        while count > 0:
            await asyncio.sleep(1)
            count -= 1
            if self.listeners_[my_id]["message"] is not None:
                return self.listeners_[my_id]["message"]
        return None


bot = PiBot()


async def main(token: str):
    """
    Main event loop for the bot.

    Args:
        token (str): The bot token.
    """
    async with bot:
        await bot.start(token=token)


if __name__ == "__main__":
    if dev_mode:
        asyncio.run(main(DEV_TOKEN))
    else:
        asyncio.run(main(TOKEN))
