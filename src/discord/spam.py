from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Union

import discord
from discord.ext import commands
from src.discord.globals import ROLE_MUTED, SERVER_ID

if TYPE_CHECKING:
    from bot import PiBot
    from src.discord.reporter import Reporter
    from src.discord.tasks import CronTasks


class SpamManager(commands.Cog):

    recent_messages = []

    # Limits
    recent_messages_limit = 20  # The number of recent messages that are stored
    caps_limit = 8  # The number of messages that can be sent containing caps before a mute is issued
    mute_limit = 6  # The number of messages that can be sent containing the same content before a mute is issued
    warning_limit = 3  # The number of messages that can be sent containing caps or the same content before a warning is issued to the offending user

    def __init__(self, bot: PiBot):
        self.bot = bot
        self.recent_messages = []

    def has_caps(self, message: discord.Message) -> bool:
        """
        Returns true if the message has caps (more capitalized letters than lowercase letters)
        """
        caps = False
        upper_count = sum(1 for c in message.content if c.isupper())
        lower_count = sum(1 for c in message.content if c.islower())
        if upper_count > (lower_count + 3):
            caps = True

        return caps

    async def check_for_repetition(self, message: discord.Message) -> None:
        """
        Checks to see if the message has often been repeated recently, and takes action if action is needed.
        """
        # Type checking
        assert isinstance(message.author, discord.Member)

        matching_messages = filter(
            lambda m: m.author == message.author
            and m.content.lower() == message.content.lower(),
            self.recent_messages,
        )
        matching_messages_count = len(list(matching_messages))

        if matching_messages_count >= self.mute_limit:
            await self.mute(message.author)

            # Send info message to channel about mute
            info_message = await message.channel.send(
                f"Successfully muted {message.author.mention} for 1 hour."
            )

            # Send info message to staff about mute
            staff_embed_message = discord.Embed(
                title=f"Automatic mute occurred",
                color=discord.Color.yellow(),
                description=f"""
                {message.author.mention} was automatically muted in {message.channel} for **repeatedly spamming similar messages**. The user was **repeatedly warned**, and sent **{self.mute_limit} messages** before a mute was applied.

                Their mute will automatically expire in: {discord.utils.format_dt(discord.utils.utcnow() + datetime.timedelta(hours = 1), 'R')}.

                No further action needs to be taken. To teleport to the issue, please [click here]({info_message.jump_url}). Please know that the offending messages may have been deleted by the author or staff.
                """,
            )
            reporter_cog: Union[commands.Cog, Reporter] = self.bot.get_cog("Reporter")
            await reporter_cog.create_staff_message(staff_embed_message)
        elif matching_messages_count >= self.warning_limit:
            await message.author.send(
                f"{message.author.mention}, please avoid spamming. Additional spam will lead to your account being temporarily muted."
            )

    async def check_for_caps(self, message: discord.Message) -> None:
        """
        Checks the message to see if it and recent messages contain a lot of capital letters.
        """
        # Type checking
        assert isinstance(message.author, discord.Member)

        caps_messages = filter(
            lambda m: m.author == message.author
            and self.has_caps(m)
            and len(m.content) > 5,
            self.recent_messages,
        )
        caps_messages_count = len(list(caps_messages))

        if caps_messages_count >= self.caps_limit and self.has_caps(message):
            await self.mute(message.author)

            # Send info message to channel about mute
            info_message = await message.channel.send(
                f"Successfully muted {message.author.mention} for 1 hour."
            )

            # Send info message to staff about mute
            staff_embed_message = discord.Embed(
                title=f"Automatic mute occurred",
                color=discord.Color.yellow(),
                description=f"""
                {message.author.mention} was automatically muted in {message.channel} for **repeatedly using caps** in their messages. The user was **repeatedly warned**, and sent **{self.caps_limit} messages** before a mute was applied.

                Their mute will automatically expire in: {discord.utils.format_dt(discord.utils.utcnow() + datetime.timedelta(hours = 1), 'R')}.

                No further action needs to be taken. To teleport to the issue, please [click here]({info_message.jump_url}). Please know that the offending messages may have been deleted by the author or staff.
                """,
            )
            reporter_cog: Union[commands.Cog, Reporter] = self.bot.get_cog("Reporter")
            await reporter_cog.create_staff_message(staff_embed_message)
        elif caps_messages_count >= self.warning_limit and self.has_caps(message):
            await message.author.send(
                f"{message.author.mention}, please avoid using all caps in your messages. Repeatedly doing so will cause your account to be temporarily muted."
            )

    async def mute(self, member: discord.Member) -> None:
        """
        Mutes the user and schedules an unmute for an hour later in CRON.
        """
        guild: discord.Guild = self.bot.get_guild(SERVER_ID)
        muted_role = discord.utils.get(guild.roles, name=ROLE_MUTED)
        unmute_time = discord.utils.utcnow() + datetime.timedelta(hours=1)

        # Type checking
        assert isinstance(muted_role, discord.Role)

        cron_cog: Union[commands.Cog, CronTasks] = self.bot.get_cog("CronTasks")
        await cron_cog.schedule_unmute(member, unmute_time)
        await member.add_roles(muted_role)

    async def store_and_validate(self, message: discord.Message) -> None:
        """
        Stores a message in recent_messages and validates whether the message is spam or not.
        """
        # No need to take action for bots
        if message.author.bot:
            return

        # Store message
        self.recent_messages.insert(0, message)
        self.recent_messages = self.recent_messages[
            : self.recent_messages_limit
        ]  # Only store 20 recent messages at once

        await self.check_for_repetition(message)
        await self.check_for_caps(message)


async def setup(bot: PiBot):
    await bot.add_cog(SpamManager(bot))
