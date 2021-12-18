import discord
from discord.ext import commands
import src.discord.globals
from src.discord.globals import CENSOR, DISCORD_INVITE_ENDINGS, CHANNEL_SUPPORT, PI_BOT_IDS
import re
from commandchecks import is_author_staff

class Censor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def on_message(self, message):
        """
        Will censor the message. Will replace any flags in content with "<censored>".

        :param message: The message being checked. message.context will be modified
            if censor gets triggered if and only if the author is not a staff member.
        :type message: discord.Message
        """
        content = message.content
        for word in src.discord.globals.CENSOR['words']:
            if len(re.findall(fr"\b({word})\b", content, re.I)):
                print(f"Censoring message by {message.author} because of the word: `{word}`")
                await message.delete()
                await self.__censor(message)
        for word in src.discord.globals.CENSOR['emojis']:
            if len(re.findall(fr"{word}", content)):
                print(f"Censoring message by {message.author} because of the emoji: `{word}`")
                await message.delete()
                await self.__censor(message)
        if not any(ending for ending in DISCORD_INVITE_ENDINGS if ending in message.content) and (len(re.findall("discord.gg", content, re.I)) > 0 or len(re.findall("discord.com/invite", content, re.I)) > 0):
            print(f"Censoring message by {message.author} because of the it mentioned a Discord invite link.")
            await message.delete()
            support_channel = discord.utils.get(message.author.guild.text_channels, name=CHANNEL_SUPPORT)
            await message.channel.send(f"*Links to external Discord servers can not be sent in accordance with rule 12. If you have questions, please ask in {support_channel.mention}.*")

    def censor_needed(self, message) -> bool:
        """
        Determines whether the message has content that needs to be censored.
        """
        content = message.content
        for word in src.discord.globals.CENSOR['words']:
            if len(re.findall(fr"\b({word})\b", content, re.I)):
                return True
        for word in src.discord.globals.CENSOR['emojis']:
            if len(re.findall(fr"{word}", content)):
                return True
        return False

    def discord_invite_censor_needed(self, message) -> bool:
        """
        Determines whether the Discord invite link censor is needed. In other words, whether this message contains a Discord invite link.
        """
        if not any(ending for ending in DISCORD_INVITE_ENDINGS if ending in message.content) and (len(re.findall("discord.gg", message.content, re.I)) > 0 or len(re.findall("discord.com/invite", message.content, re.I)) > 0):
            return True
        return False

    async def __censor(self, message):
        """Constructs Pi-Bot's censor."""
        channel = message.channel
        ava = message.author.avatar.url
        wh = await channel.create_webhook(name="Censor (Automated)")
        content = message.content
        for word in src.discord.globals.CENSOR['words']:
            content = re.sub(fr'\b({word})\b', "<censored>", content, flags=re.IGNORECASE)
        for word in src.discord.globals.CENSOR['emojis']:
            content = re.sub(fr"{word}", "<censored>", content, flags=re.I)
        author = message.author.nick
        if author == None:
            author = message.author.name
        # Make sure pinging through @everyone, @here, or any role can not happen
        mention_perms = discord.AllowedMentions(everyone=False, users=True, roles=False)
        await wh.send(content, username=(author + " (auto-censor)"), avatar_url=ava, allowed_mentions=mention_perms)
        await wh.delete()

        # unless author is staff, replace content for other cogs (allows for staff to then add swears and censored words to pings)
        if not await is_author_staff(message.author):
            message.content = content # apply to message to not propogate censored words to other things like commands

def setup(bot):
    bot.add_cog(Censor(bot))
