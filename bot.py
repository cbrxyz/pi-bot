from __future__ import annotations

import asyncio
import uuid
from typing import TYPE_CHECKING, Any, Dict, Optional, Union

import aiohttp
from discord import app_commands

from commandchecks import *
from src.discord.globals import *
from src.mongo import mongo

if TYPE_CHECKING:
    from src.discord.censor import Censor
    from src.discord.logger import Logger
    from src.discord.spam import SpamManager

intents = discord.Intents.default()
intents.members = True
intents.message_content = True


class PiBotCommandTree(app_commands.CommandTree):
    def __init__(self, client: "PiBot"):
        super().__init__(client)

    async def on_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ) -> None:
        if isinstance(error, app_commands.CheckFailure):
            message = "Sorry, but I don't think you can run that command."
        # Add more here
        else:
            message = "Ooops, there was a command error."
        try:
            await interaction.response.send_message(message, ephemeral=True)
        except discord.InteractionResponded:
            await interaction.followup.send(message, ephemeral=True)


class PiBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=BOT_PREFIX,
            case_insensitive=True,
            intents=intents,
            help_command=None,
            tree_cls=PiBotCommandTree
        )
        self.http.API_VERSION = 9
        self.listeners_: Dict[
            str, Dict[str, Any]
        ] = {}  # name differentiation between internal _listeners attribute
        self.__version__ = "v5.0.0"

    async def setup_hook(self) -> None:
        await mongo.setup()  # initialize MongoDB

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
            except commands.ExtensionError:
                print(f"Failed to load extension {extension}")

    async def on_ready(self) -> None:
        """Called when the bot is enabled and ready to be run."""
        print(f"{self.user} has connected!")

    async def on_message(self, message: discord.Message) -> None:
        # Nothing needs to be done to the bot's own messages
        if message.author.id in PI_BOT_IDS or message.author == self.user:
            return

        # If user is being listened to, return their message
        for listener in self.listeners_.items():
            if message.author.id == listener[1]["follow_id"]:
                self.listeners_[listener[0]]["message"] = message

        # Log incoming direct messages
        if (
            type(message.channel) == discord.DMChannel
            and message.author not in PI_BOT_IDS
            and message.author != bot
        ):
            logger_cog: Union[commands.Cog, Logger] = self.get_cog("Logger")
            await logger_cog.send_to_dm_log(message)
            print(f"Message from {message.author} through DM's: {message.content}")
        else:
            # Print to output
            if not (
                message.author.id in PI_BOT_IDS
                and message.channel.name
                in [CHANNEL_EDITEDM, CHANNEL_DELETEDM, CHANNEL_DMLOG]
            ):
                # avoid sending logs for messages in log channels
                print(
                    f"Message from {message.author} in #{message.channel}: {message.content}"
                )

        # Check if the message contains a censored word/emoji
        is_private = any(
            [
                isinstance(message.channel, discord_class)
                for discord_class in [discord.DMChannel, discord.GroupChannel]
            ]
        )
        if message.content and not is_private:
            censor: Union[commands.Cog, Censor] = bot.get_cog("Censor")
            await censor.on_message(message)

            # Check to see if the message contains repeated content or has too many caps
            spam: Union[commands.Cog, SpamManager] = bot.get_cog("SpamManager")
            await spam.store_and_validate(message)

    async def start(self, token: str, *, reconnect: bool = True) -> None:
        self.session = aiohttp.ClientSession()
        await super().start(token=token, reconnect=reconnect)

    async def close(self) -> None:
        await self.session.close()
        await super().close()

    async def listen_for_response(
        self, follow_id: int, timeout: int
    ) -> Optional[discord.Message]:
        """
        Creates a global listener for a message from a user.
        :param follow_id: the user ID to create the listener for
        :param timeout: the amount of time to wait before returning None, assuming the user abandoned the operation
        :return: the found message or None
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
    async with bot:
        await bot.start(token=token)


if __name__ == "__main__":
    if dev_mode:
        asyncio.run(main(DEV_TOKEN))
    else:
        asyncio.run(main(TOKEN))
