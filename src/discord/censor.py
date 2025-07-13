"""
Contains all functionality related to censoring users' actions in the Scioly.org Discord
server.
"""
from __future__ import annotations

import asyncio
import contextlib
import logging
import re
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

import src.discord.globals
from src.discord.globals import (
    CATEGORY_STAFF,
    CHANNEL_SUPPORT,
    DISCORD_INVITE_ENDINGS,
    ROLE_UC,
)

if TYPE_CHECKING:
    from bot import PiBot

    from .reporter import Reporter

logger = logging.getLogger(__name__)


class Censor(commands.Cog):
    """
    Responsible for censoring innapropriate words' and emojis in user content.
    """

    def __init__(self, bot: PiBot):
        self.bot = bot

    async def on_message(self, message: discord.Message) -> None:
        """
        Will censor the message. Will replace any flags in content with "<censored>".

        :param message: The message being checked. message.context will be modified
            if censor gets triggered if and only if the author is not a staff member.
        :type message: discord.Message
        """
        # Type checking - Assume messages come from a text channel where the author
        # is a member of the server
        if not isinstance(message.channel, discord.TextChannel) or not isinstance(
            message.author,
            discord.Member,
        ):
            return

        # Do not act on messages in staff channels
        if (
            message.channel.category is not None
            and message.channel.category.name == CATEGORY_STAFF
        ):
            return

        # Get the content and attempt to find any words on the censor list
        content = message.content
        if await self.censor_needed(content):
            logger.debug(
                f"Censoring message by {message.author} because it contained "
                "a word or emoji on the censor list.",
            )

            await message.delete()
            await self.__censor(message)

        # Check for invalid Discord invite endings
        if self.discord_invite_censor_needed(content):
            logger.debug(
                f"Censoring message by {message.author} because of the it mentioned "
                "a Discord invite link.",
            )

            await message.delete()
            support_channel = discord.utils.get(
                message.author.guild.text_channels,
                name=CHANNEL_SUPPORT,
            )
            assert isinstance(support_channel, discord.TextChannel)
            await message.channel.send(
                f"*Links to external Discord servers can not be sent in accordance "
                "with rule 12. If you have "
                f"questions, please ask in {support_channel.mention}.* ",
            )

    def word_present(self, content: str) -> bool:
        with contextlib.suppress(asyncio.CancelledError):
            for word in src.discord.globals.CENSOR.words:
                if re.findall(rf"\b({word})\b", content, re.I):
                    return True
            for emoji in src.discord.globals.CENSOR.emojis:
                if len(re.findall(emoji, content)):
                    return True
        return False

    async def censor_needed(self, content: str) -> bool:
        """
        Determines whether the message has content that needs to be censored.
        """
        try:
            if await asyncio.wait_for(
                asyncio.to_thread(self.word_present, content),
                timeout=1.5,
            ):
                return True
        except asyncio.TimeoutError:
            logger.warn(f"TimeoutError while checking for censored words in {content}")
        return False

    def discord_invite_censor_needed(self, content: str) -> bool:
        """
        Determines whether the Discord invite link censor is needed. In other
        words, whether this content contains a Discord invite link.
        """
        if not any(
            ending for ending in DISCORD_INVITE_ENDINGS if ending in content
        ) and (
            len(re.findall("discord.gg", content, re.I)) > 0
            or len(re.findall("discord.com/invite", content, re.I)) > 0
        ):
            return True
        return False

    async def __censor(self, message: discord.Message):
        """Constructs Pi-Bot's censor."""
        # Type checking
        assert isinstance(message.channel, discord.TextChannel)
        assert isinstance(message.author, discord.Member)

        channel = message.channel
        avatar = message.author.display_avatar.url
        webhook = await channel.create_webhook(name="Censor (Automated)")
        content = message.content
        author = message.author.nick or message.author.name

        # Actually replace content found on the censored words/emojis list
        for word in src.discord.globals.CENSOR.words:
            content = re.sub(
                rf"\b({word})\b",
                "<censored>",
                content,
                flags=re.IGNORECASE,
            )
        for emoji in src.discord.globals.CENSOR.emojis:
            content = re.sub(emoji, "<censored>", content, flags=re.I)

        reply = (
            (message.reference.resolved or message.reference.cached_message)
            if message.reference
            else None
        )
        if isinstance(reply, discord.Message):
            post_bar = "╭────────"
            logger.warn(reply.content)
            if reply.content.startswith(post_bar):
                reply.content = reply.content[reply.content.find("\n") + 1 :]
            stripped_content = (
                f"{reply.content[:50]}..." if len(reply.content) > 50 else reply.content
            )
            remove_chars = ["\n", "\t", post_bar, r"*"]
            for char in remove_chars:
                stripped_content = stripped_content.replace(char, " ")
            stripped_content = stripped_content.strip()
            logger.warn(repr(stripped_content))
            content = (
                f"{post_bar} {reply.author.mention}: *{stripped_content}*\n{content}"
            )

        # Make sure pinging through @everyone, @here, or any role can not happen
        mention_perms = discord.AllowedMentions(everyone=False, users=True, roles=False)
        await webhook.send(
            content,
            username=f"{author} (auto-censor)",
            avatar_url=avatar,
            allowed_mentions=mention_perms,
            silent=isinstance(reply, discord.Message),
        )
        await webhook.delete()

        # Replace content with censored content for other cogs
        message.content = content

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """
        Listens for message edit events, and executes the censor if needed.

        Args:
            before (discord.Message): The message before it was edited.
            after (discord.Message): The message after it was edited.
        """
        # Do not trigger the message edit event for newly-created messages
        if (discord.utils.utcnow() - after.created_at).total_seconds() < 2:
            return

        # Log edit event
        logger.info(
            "Message from {0.author} edited to: {0.content}, from: {1.content}".format(
                after,
                before,
            ),
        )

        # Stop the event here for DM's (no need to censor, as author is the
        # only one who can see them)
        if isinstance(after.channel, discord.DMChannel):
            return

        # Stop here for messages from Pi-Bot (no need to do anything else)
        if after.author.bot:
            return

        # Delete messages that contain censored words
        censor_found = await self.censor_needed(after.content)
        if censor_found:
            await after.delete()
            await after.author.send(
                "You recently edited a message, but it **contained a censored "
                "word**! Therefore, I unfortunately had to delete it. In the "
                "future, please do not edit innapropriate words into your "
                "messages, and they will not be deleted.",
            )

        # Delete messages that have Discord invite links in them
        discord_invite_found = self.discord_invite_censor_needed(after.content)
        if discord_invite_found:
            await after.delete()
            await after.author.send(
                "You recently edited a message, but it **contained a link to "
                "another Discord server**! Therefore, I unfortunately had to "
                "delete it. In the future, please do not edit Discord invite "
                "links into your messages and they will not be deleted.",
            )

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        # Give new user confirmed role
        unconfirmed_role = discord.utils.get(member.guild.roles, name=ROLE_UC)
        assert isinstance(unconfirmed_role, discord.Role)
        await member.add_roles(unconfirmed_role)

        # Check to see if user's name is innapropriate
        name = member.name
        if await self.censor_needed(name):
            # If name contains a censored link
            reporter_cog = self.bot.get_cog("Reporter")
            assert isinstance(reporter_cog, Reporter)
            await reporter_cog.create_inappropriate_username_report(member, member.name)

    @commands.Cog.listener()
    async def on_member_update(self, _, after):
        """
        When a member updates their presence on the Discord server, check to see
        if their name contains an innapropriate term, and if so, open a report.

        Args:
            after (discord.Member): The member who changed their name, after they've
                changed it.
        """
        # Notify staff if the user updated their name to include an innapropriate name
        if after.nick is None:
            return  # No need to check if user does not have a new nickname set

        # Get the Censor cog
        censor_found = await self.censor_needed(after.nick)
        if censor_found:
            # If name contains a censored link
            reporter_cog = self.bot.get_cog("Reporter")
            assert isinstance(reporter_cog, Reporter)
            await reporter_cog.create_inappropriate_username_report(after, after.nick)

    @commands.Cog.listener()
    async def on_user_update(self, _, after):
        """
        When a user updates their global Discord profile, check to see if their
        name contains an inappropriate term, and if so, open a report.

        Args:
            after (discord.Member): The member after updating their profile.
        """
        # Get the Censor cog and see if user's new username is offending censor
        censor_found = await self.censor_needed(after.name)
        if censor_found:
            # If name contains a censored link
            reporter_cog = self.bot.get_cog("Reporter")
            assert isinstance(reporter_cog, Reporter)
            await reporter_cog.create_inappropriate_username_report(after, after.name)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """
        Handles reaction add events. Currently, just used to suppress offensive emojis.

        Args:
            payload (discord.RawReactionActionEvent): The payload to use for the message.
        """
        if str(payload.emoji) in src.discord.globals.CENSOR.emojis:
            channel = self.bot.get_channel(payload.channel_id)
            assert isinstance(channel, discord.TextChannel)

            partial_message = channel.get_partial_message(payload.message_id)
            assert isinstance(partial_message, discord.PartialMessage)

            await partial_message.clear_reaction(payload.emoji)


async def setup(bot: PiBot):
    """
    Sets up the Censor cog.
    """
    await bot.add_cog(Censor(bot))
