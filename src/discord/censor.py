from __future__ import annotations

import re
from typing import TYPE_CHECKING

import discord
import src.discord.globals
from discord.ext import commands
from src.discord.globals import CATEGORY_STAFF, CHANNEL_SUPPORT, DISCORD_INVITE_ENDINGS

if TYPE_CHECKING:
    from bot import PiBot


class Censor(commands.Cog):
    def __init__(self, bot: PiBot):
        self.bot = bot
        print("Initialized Censor cog.")

    async def on_message(self, message: discord.Message) -> None:
        """
        Will censor the message. Will replace any flags in content with "<censored>".
        :param message: The message being checked. message.context will be modified
            if censor gets triggered if and only if the author is not a staff member.
        :type message: discord.Message
        """
        # Type checking - Assume messages come from a text channel where the author is a member of the server
        assert isinstance(message.channel, discord.TextChannel)
        assert isinstance(message.author, discord.Member)

        # Do not act on messages in staff channels
        if (
            message.channel.category is not None
            and message.channel.category.name == CATEGORY_STAFF
        ):
            return

        # Get the content and attempt to find any words on the censor list
        content = message.content
        if self.censor_needed(content):
            print(
                f"Censoring message by {message.author} because it contained a word or emoji on the censor list."
            )

            await message.delete()
            await self.__censor(message)

        # Check for invalid Discord invite endings
        if self.discord_invite_censor_needed(content):
            print(
                f"Censoring message by {message.author} because of the it mentioned a Discord invite link."
            )

            await message.delete()
            support_channel = discord.utils.get(
                message.author.guild.text_channels, name=CHANNEL_SUPPORT
            )
            assert isinstance(support_channel, discord.TextChannel)
            await message.channel.send(
                f"*Links to external Discord servers can not be sent in accordance with rule 12. If you have "
                f"questions, please ask in {support_channel.mention}.* "
            )

    def censor_needed(self, content: str) -> bool:
        """
        Determines whether the message has content that needs to be censored.
        """
        for word in src.discord.globals.CENSOR["words"]:
            if len(re.findall(rf"\b({word})\b", content, re.I)):
                return True
        for emoji in src.discord.globals.CENSOR["emojis"]:
            if len(re.findall(emoji, content)):
                return True
        return False

    def discord_invite_censor_needed(self, content: str) -> bool:
        """
        Determines whether the Discord invite link censor is needed. In other words, whether this content contains a
        Discord invite link.
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
        wh = await channel.create_webhook(name="Censor (Automated)")
        content = message.content
        author = message.author.nick or message.author.name

        # Actually replace content found on the censored words/emojis list
        for word in src.discord.globals.CENSOR["words"]:
            content = re.sub(
                rf"\b({word})\b", "<censored>", content, flags=re.IGNORECASE
            )
        for emoji in src.discord.globals.CENSOR["emojis"]:
            content = re.sub(emoji, "<censored>", content, flags=re.I)

        # Make sure pinging through @everyone, @here, or any role can not happen
        mention_perms = discord.AllowedMentions(everyone=False, users=True, roles=False)
        await wh.send(
            content,
            username=f"{author} (auto-censor)",
            avatar_url=avatar,
            allowed_mentions=mention_perms,
        )
        await wh.delete()

        # Replace content with censored content for other cogs
        message.content = content  # apply to message to not propagate censored words to other things like commands


async def setup(bot: PiBot):
    await bot.add_cog(Censor(bot))
