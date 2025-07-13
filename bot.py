"""
Serves as the initial file to launch the bot. Loads all needed extensions and maintains
core functionality.
"""

from __future__ import annotations

import asyncio
import datetime
import logging
import logging.handlers
import re
import subprocess
import traceback
import uuid
from typing import TYPE_CHECKING, Any

import aiohttp
import discord
from beanie import init_beanie
from discord import app_commands
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
from rich.logging import RichHandler

import src.mongo.models
from env import env
from src.discord.globals import (
    CHANNEL_BOTSPAM,
    CHANNEL_DELETEDM,
    CHANNEL_DMLOG,
    CHANNEL_EDITEDM,
    CHANNEL_RULES,
)
from src.discord.reporter import Reporter

if TYPE_CHECKING:
    from src.discord.censor import Censor
    from src.discord.logger import Logger
    from src.discord.spam import SpamManager

intents = discord.Intents.all()
logger = logging.getLogger(__name__)

BOT_PREFIX = "?" if env.dev_mode else "!"


class PiBotCommandTree(app_commands.CommandTree):
    def __init__(self, client: PiBot):
        super().__init__(client)

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError,
    ) -> None:
        # Optional delay for some commands
        delay = None

        # Handle check failures
        if isinstance(error, app_commands.NoPrivateMessage):
            message = (
                "Sorry, but this command does not work in private message. "
                "Please hop on over to the Scioly.org server to use the command!"
            )
        elif isinstance(error, app_commands.MissingRole | app_commands.MissingAnyRole):
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
                seconds=error.retry_after,
            )
            message = (
                "Time to _chill out_ - this command is on cooldown! "
                f"Please try again **{discord.utils.format_dt(next_time, 'R')}.**"
                "\n\n"
                "For future reference, this command is currently limited to "
                f"being executed **{error.cooldown.rate} times every {error.cooldown.per} seconds**."
            )
            delay = error.retry_after - 1 if error.retry_after > 1 else 0

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
                error.original,
                interaction.command,
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

        await interaction.response.defer(ephemeral=True)
        msg = await interaction.followup.send(message, ephemeral=True, wait=True)

        if delay is not None:
            await msg.delete(delay=delay)


class PiBot(commands.Bot):
    """
    The bot itself. Controls all functionality needed for core operations.
    """

    session: aiohttp.ClientSession | None
    mongo_client: AsyncIOMotorClient
    settings: src.mongo.models.Settings

    def __init__(self):
        super().__init__(
            command_prefix=BOT_PREFIX,
            case_insensitive=True,
            intents=intents,
            help_command=None,
            tree_cls=PiBotCommandTree,
        )
        self.listeners_: dict[
            str,
            dict[str, Any],
        ] = {}  # name differentiation between internal _listeners attribute
        self.__version__ = "v5.1.0"
        self.__commit__ = self.get_commit()
        self.session = None
        self.mongo_client = AsyncIOMotorClient(
            env.mongo_url,
            tz_aware=True,
        )

    def get_commit(self) -> str | None:
        with subprocess.Popen(
            ["git", "rev-parse", "--short", "HEAD"],
            stdout=subprocess.PIPE,
        ) as proc:
            if proc.stdout:
                hash = proc.stdout.read()
                return hash.decode("utf-8")
        return None

    async def setup_hook(self) -> None:
        """
        Called when the bot is being setup. Currently sets up a connection to the
        database and initializes all extensions.
        """
        await init_beanie(
            database=self.mongo_client["data"],
            document_models=[
                src.mongo.models.Cron,
                src.mongo.models.Ping,
                src.mongo.models.Tag,
                src.mongo.models.Invitational,
                src.mongo.models.Event,
                src.mongo.models.Censor,
                src.mongo.models.Settings,
                # TODO
            ],
        )
        extensions = (
            "src.discord.censor",
            "src.discord.ping",
            "src.discord.welcome",
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
        for i, extension in enumerate(extensions):
            try:
                await self.load_extension(extension)
                logger.info(f"Enabled extension: {extension} {i + 1}/{len(extensions)}")
            except commands.ExtensionError:
                logger.error(f"Failed to load extension {extension}!")
                traceback.print_exc()

    async def on_ready(self) -> None:
        """
        Called when the bot is enabled and ready to be run.
        """
        # try:
        #     await self.tree.sync(guild=discord.Object(749057176756027414))
        # except:
        #     import traceback
        #     traceback.print_exc()
        logger.info(f"{self.user} has connected!")

        # Add message to rules channel
        server = self.get_guild(env.dev_server_id)
        assert isinstance(server, discord.Guild)
        rules_channel = discord.utils.get(server.text_channels, name=CHANNEL_RULES)
        assert isinstance(rules_channel, discord.TextChannel)
        rules_message = [m async for m in rules_channel.history(limit=1)]
        if rules_message:
            rules_message = rules_message[0]
            view = discord.ui.View()
            view.add_item(
                discord.ui.Button(
                    url="https://scioly.org/rules",
                    label="Complete Scioly.org rules",
                    style=discord.ButtonStyle.link,
                ),
            )
            await rules_message.edit(view=view)

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
            logger.info(
                f"Message from {message.author} through DM's: {message.content}",
            )
        else:
            # Print to output
            if not (
                message.author.bot
                and message.channel.name
                in [CHANNEL_EDITEDM, CHANNEL_DELETEDM, CHANNEL_DMLOG]
            ):
                # avoid sending logs for messages in log channels
                logger.info(
                    f"Message from {message.author} in #{message.channel}: {message.content}",
                )

        # Check if the message contains a censored word/emoji
        is_private = isinstance(
            message.channel,
            discord.DMChannel | discord.GroupChannel,
        )

        if message.content and not is_private:
            censor: commands.Cog | Censor = self.get_cog("Censor")
            await censor.on_message(message)

            # Check to see if the message contains repeated content or has too many caps
            spam: commands.Cog | SpamManager = self.get_cog("SpamManager")
            await spam.store_and_validate(message)

        if message.content and len(re.findall(r"^[!\?]\s*\w+$", message.content)):
            botspam_channel = discord.utils.get(
                message.guild.channels,
                name=CHANNEL_BOTSPAM,
            )
            reply_message = await message.reply(
                f"Hola {message.author.mention}, please use slash commands now! Try typing `/` in {botspam_channel.mention}!",
            )
            await reply_message.delete(delay=10)

    async def start(self, token: str, *, reconnect: bool = True) -> None:
        if self.__commit__ is None:
            # Logging is set up at this point so we can now prompt a warning message for a missing commit hash
            logging.warning("Version commit could not be found")
        self.session = aiohttp.ClientSession()
        await super().start(token=token, reconnect=reconnect)

    async def close(self) -> None:
        if self.session:
            await self.session.close()
        await super().close()

    async def listen_for_response(
        self,
        follow_id: int,
        timeout: int,
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
                message = self.listeners_[my_id]["message"]
                del self.listeners_[my_id]
                return message
        return None


bot = PiBot()
KB = 1024
MB = 1024 * KB
handler = logging.handlers.RotatingFileHandler(
    filename="pibot.log",
    encoding="utf-8",
    maxBytes=32 * MB,
    backupCount=5,
)
discord.utils.setup_logging(handler=handler)


async def main(token: str):
    """
    Main event loop for the bot.

    Args:
        token (str): The bot token.
    """
    async with bot:
        await bot.start(token=token)


if __name__ == "__main__":
    if env.dev_mode:
        # If in development, also print to console
        logger = logging.getLogger()
        logger.addHandler(RichHandler(rich_tracebacks=True))

        asyncio.run(main(env.discord_dev_token))
    else:
        asyncio.run(main(env.discord_token))
