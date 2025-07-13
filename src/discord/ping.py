"""
Holds functionality for members to manage their ping subscriptions.
"""

from __future__ import annotations

import asyncio
import collections
import contextlib
import datetime
import logging
import re
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

import src.discord.globals
from commandchecks import is_in_bot_spam
from env import env
from src.discord.globals import CHANNEL_BOTSPAM
from src.mongo.models import Ping

if TYPE_CHECKING:
    from bot import PiBot


logger = logging.getLogger(__name__)


class PingManager(commands.GroupCog, name="ping"):
    """
    Specific cog for holding ping-related functionality.
    """

    recent_messages: dict[int, collections.deque[discord.Message]]

    def __init__(self, bot: PiBot):
        self.bot = bot
        self.recent_messages = {}

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """
        Event listening for new messages in an attempt to send out needed pings.

        Args:
            message (discord.Message): The message that was just sent by a user.
        """
        # Do not ping for messages in a private channel or messages from bots
        if (message.channel.type == discord.ChannelType.private) or message.author.bot:
            return

        # Do not ping if the message is coming from the botspam channel
        botspam_channel = discord.utils.get(
            message.guild.text_channels,
            name=CHANNEL_BOTSPAM,
        )
        if message.channel == botspam_channel:
            return

        # Store the message to generate recent message history
        self.recent_messages.setdefault(
            message.channel.id,
            collections.deque(maxlen=5),
        ).append(message)

        # Send a ping alert to the relevant users
        ids = [m.id for m in message.channel.members]
        for user_pings in src.discord.globals.PING_INFO:
            # Give up event loop to other coroutines in case ping list is long
            await asyncio.sleep(0)

            # Do not ping if:
            #   User was author of message.
            #   User was mentioned in the message.
            #   User cannot see the channel.
            #   User has DND enabled.
            user_is_mentioned = user_pings.user_id in [m.id for m in message.mentions]
            user_can_see_channel = user_pings.user_id in ids
            user_in_dnd = user_pings.dnd
            if (
                user_pings.user_id == message.author.id
                or user_is_mentioned
                or (not user_can_see_channel or user_in_dnd)
            ):
                continue

            # Count the number of pings in the message
            ping_count = 0
            pings = [rf"\b({ping})\b" for ping in user_pings.word_pings]
            for ping in pings:
                try:
                    if len(re.findall(ping, message.content, re.I)):
                        ping_count += 1
                except Exception as e:
                    logger.error(
                        f"Could not evaluate message content with ping {ping} of user {user_pings.user_id}: {e!s}",
                    )

            if ping_count:
                user_obj = self.bot.get_user(user_pings.user_id)
                if user_obj:
                    # Do not throw exception if the user has direct messages disabled
                    with contextlib.suppress(discord.Forbidden):
                        await self.send_ping_pm(user_obj, message, ping_count)

    def format_text(
        self,
        text: str,
        length: int,
        user: discord.Member | discord.User,
    ) -> str:
        """
        Highlights ping expressions in the message and shorten long messages
        with an ellipsis.

        Args:
            text (str): The raw text to format.
            length (int): The length of the string desired - the rest will be split
                off and replaced with a single ellipsis.
            user (Union[discord.Member, discord.User]): The user to highlight the text
                with respect to. This is used to get relevant ping info about the
                specific user.
        """
        user_ping_obj = next(
            user_obj
            for user_obj in src.discord.globals.PING_INFO
            if user_obj.user_id == user.id
        )

        pings = [rf"\b({ping})\b" for ping in user_ping_obj.word_pings]

        for expression in pings:
            try:
                text = re.sub(rf"{expression}", r"**\1**", text, flags=re.I)
            except Exception as e:
                logger.warn(f"Could not bold ping due to unfavored RegEx. Error: {e}")

        # Prevent the text from being too long
        if len(text) > length:
            return text[: length - 3] + "..."
        else:
            return text

    def expire_recent_messages(self) -> None:
        """
        Remove all recent messages older than a specified amount of time.

        Currently, this is called whenever a ping PM is sent.
        """
        for _, messages in self.recent_messages.items():
            for message in messages.copy():
                if (discord.utils.utcnow() - message.created_at) > datetime.timedelta(
                    hours=3,
                ):
                    messages.remove(message)

    async def send_ping_pm(
        self,
        user: discord.User,
        message: discord.Message,
        ping_count: int,
    ) -> None:
        """
        Sends a direct message to the user about a message containing a relevant ping expression.

        Args:
            user (discord.User): The user to send a DM to.
            message (discord.Message): The message which triggered the ping.
            ping_count (int): How many pings were triggered by the specific message.
        """
        # Expire recent messages
        self.expire_recent_messages()

        # Create the alert embed
        description = ""
        if ping_count == 1:
            description = "**One of your pings was mentioned by a user in the Scioly.org Discord server!**"
        elif ping_count > 1:
            description = "**Several of your pings were mentioned by a user in the Scioly.org Discord server!**"

        description = (
            description
            + "\n\n"
            + "\n".join(
                [
                    f"{message.author.mention}: {self.format_text(message.content, 100, user)}"
                    for message in self.recent_messages[message.channel.id]
                ],
            )
        )
        description = (
            description
            + "\n\n"
            + f"Come check out the conversation! [Click here]({message.jump_url}) to be teleported to the message!"
        )
        embed = discord.Embed(
            title=":bellhop: Ping Alert!",
            color=discord.Color.brand_red(),
            description=description,
        )
        embed.set_thumbnail(url=message.author.display_avatar.url)

        embed.set_footer(
            text="If you don't want this ping anymore, use /ping remove in the Scioly.org Discord server!",
        )

        # Send the user an alert message
        await user.send(embed=embed)

    @app_commands.command(description="Toggles 'Do Not Disturb' mode.")
    @app_commands.guilds(*env.slash_command_guilds)
    @app_commands.checks.cooldown(2, 60, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.check(is_in_bot_spam)
    async def dnd(self, interaction: discord.Interaction):
        """
        Discord command allowing members to sent their ping mode to DND.

        Permissions:
            Confirmed members: Unconfirmed members cannot access this command.

        Args:
            interaction (discord.Interaction): The discord app command which triggered
                the command.
        """
        user = [
            u for u in src.discord.globals.PING_INFO if u.user_id == interaction.user.id
        ]

        if len(user):
            user = user[0]
            if user.dnd:
                user.dnd = False
                await user.save()
                return await interaction.response.send_message(
                    "Disabled DND mode for pings.",
                )
            else:
                user.dnd = True
                await user.save()
                return await interaction.response.send_message(
                    "Enabled DND mode for pings.",
                )
        else:
            return await interaction.response.send_message(
                "You can't enter DND mode without any pings!",
            )

    @app_commands.command(
        name="add",
        description="Adds a new ping to notify you about.",
    )
    @app_commands.describe(word="The new word to add a ping for.")
    @app_commands.guilds(*env.slash_command_guilds)
    @app_commands.checks.cooldown(5, 60, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.check(is_in_bot_spam)
    async def pingadd(self, interaction: discord.Interaction, word: str):
        """
        Discord command allowing members to add a ping keyword to their list of
        pings.

        Permissions:
            Confirmed members: Unconfirmed members cannot access this command.

        Args:
            interaction (discord.Interaction): The Discord app command which triggered
                the command.
            word (str): The new word to ping on.
        """
        member = interaction.user
        user = next(
            (u for u in src.discord.globals.PING_INFO if u.user_id == member.id),
            None,
        )
        if user:
            # User already has an object in the PING_INFO dictionary
            pings = user.word_pings
            try:
                re.findall(word, "test phrase")
            except Exception:
                return await interaction.response.send_message(
                    f"Ignoring adding the `{word}` ping because it uses illegal characters.",
                )
            if f"({word})" in pings or f"\\b({word})\\b" in pings or word in pings:
                return await interaction.response.send_message(
                    f"Ignoring adding the `{word}` ping because you already have a ping currently set as that.",
                )
            else:
                logger.debug(f"adding word: {re.escape(word)}")
                # relevant_doc = next(
                #     doc
                #     for doc in src.discord.globals.PING_INFO
                #     if doc.user_id == member.id
                # )
                # relevant_doc.word_pings.append(word)
                user.word_pings.append(word)
                await user.save()
        else:
            # User does not already have an object in the PING_INFO dictionary
            new_user_ping_entry = Ping(user_id=member.id, word_pings=[word], dnd=False)
            src.discord.globals.PING_INFO.append(new_user_ping_entry)
            await new_user_ping_entry.save()
        small_ping_message = ""
        if len(word) < 4:  # FIXME: Magic number
            small_ping_message = (
                "\n\n**Please be "
                'responsible with the pinging feature. Using pings senselessly (such as pinging for "the" or "a") may '
                "result in you being temporarily disallowed from using or receiving pings.**"
            )
        return await interaction.response.send_message(
            f"Great! You will now receive an alert for messages that contain the `{word}` word.{small_ping_message}",
        )

    @app_commands.command(
        name="test",
        description="Tests your pings on an example message.",
    )
    @app_commands.guilds(*env.slash_command_guilds)
    @app_commands.describe(test="The phrase to test your pings against.")
    @app_commands.checks.cooldown(10, 60, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.check(is_in_bot_spam)
    async def pingtest(self, interaction: discord.Interaction, test: str):
        """
        Discord command allowing members to test their ping list against a specific phrase.

        Permissions:
            Confirmed members: Unconfirmed members cannot access this command.

        Args:
            interaction (disord.Interaction): The interaction which triggered the app
                command.
            test (str): The phrase to test the list of pings against.
        """
        member = interaction.user
        user = next(
            (u for u in src.discord.globals.PING_INFO if u.user_id == member.id),
            None,
        )

        if not user or not user.word_pings:
            return await interaction.response.send_message(
                f"Since you have no pings, `{test}` matched `0` pings.",
            )

        # FIXME: Reimplement test and on_message to use same ping detection function
        word_pings = [
            {"new": rf"\b({ping})\b", "original": ping} for ping in user.word_pings
        ]
        user_pings = word_pings
        matched = False
        response = ""

        for ping in user_pings:
            if isinstance(ping, dict):
                if len(re.findall(ping["new"], test, re.I)) > 0:
                    response += f"Your ping `{ping['original']}` matches `{test}`.\n"
                    matched = True
            else:
                if len(re.findall(ping, test, re.I)) > 0:
                    response += f"Your ping `{ping}` matches `{test}`.\n"
                    matched = True

        if not matched:
            return await interaction.response.send_message(
                f"`{test}` matched `0` pings.",
            )
        else:
            return await interaction.response.send_message(response)

    @app_commands.command(
        name="list",
        description="Lists all of your registered pings.",
    )
    @app_commands.guilds(*env.slash_command_guilds)
    @app_commands.checks.cooldown(5, 60, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.check(is_in_bot_spam)
    async def pinglist(self, interaction: discord.Interaction):
        """
        Discord command which lists the user's pings.

        Permissions:
            Confirmed members: Unconfirmed members cannot access this command.

        Args:
            interaction (discord.Interaction): The app command which triggered this
                command.
        """
        member = interaction.user
        user = next(
            (u for u in src.discord.globals.PING_INFO if u.user_id == member.id),
            None,
        )

        # User has no pings
        if user is None or len(user.word_pings) == 0:
            return await interaction.response.send_message(
                "You have no registered pings.",
            )

        else:
            response = "Your pings are: " + ", ".join(
                [f"`{word}`" for word in user.word_pings],
            )
            await interaction.response.send_message(response)

    @app_commands.command(
        name="remove",
        description="Removes a ping from your list of registered pings.",
    )
    @app_commands.describe(
        word="The word to remove a ping for. Or use 'all' to remove all pings.",
    )
    @app_commands.guilds(*env.slash_command_guilds)
    @app_commands.checks.cooldown(5, 60, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.check(is_in_bot_spam)
    async def pingremove(self, interaction: discord.Interaction, word: str):
        """
        Discord command that allows a user to remove a word from their list of pings.

        Permissions:
            Confirmed members: Unconfirmed members cannot access this command.

        Args:
            interaction (discord.Interaction): The app command which triggered this
                command.
            word (str): The word to attempt to remove from the user's list of pings.
        """
        # Get the user's info
        member = interaction.user
        user = next(
            (u for u in src.discord.globals.PING_INFO if u.user_id == member.id),
            None,
        )

        # The user has no pings
        if user is None or len(user.word_pings) == 0:
            return await interaction.response.send_message(
                "You have no registered pings.",
            )

        # Remove all of user's pings
        if word == "all":
            user.word_pings.clear()
            await user.save()
            return await interaction.response.send_message(
                "I removed all of your pings.",
            )

        # Attempt to remove a word ping
        if word in user.word_pings:
            user.word_pings.remove(word)
            await user.save()
            return await interaction.response.send_message(
                f"I removed the `{word}` ping you were referencing.",
            )

        # Attempt to remove a word ping with extra formatting
        elif f"\\b({word})\\b" in user.word_pings:
            user.word_pings.remove(f"\\b({word})\\b")
            await user.save()
            return await interaction.response.send_message(
                f"I removed the `{word}` ping you were referencing.",
            )

        # Attempt to remove a word ping with alternate extra formatting
        elif f"({word})" in user.word_pings:
            user.word_pings.remove(f"({word})")
            await user.save()
            return await interaction.response.send_message(
                f"I removed the `{word}` RegEx ping you were referencing.",
            )

        else:
            return await interaction.response.send_message(
                f"I can't find the **`{word}`** ping you are referencing, sorry. Try another ping, or see all of your "
                f"pings with `/ping list`. ",
            )


async def setup(bot: PiBot):
    await bot.add_cog(PingManager(bot))
