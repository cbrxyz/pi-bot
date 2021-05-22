import discord
from discord.ext import commands
from src.discord.globals import CENSORED_WORDS
from src.discord.globals import CENSORED_EMOJIS
from src.discord.globals import DISCORD_INVITE_ENDINGS
from src.discord.globals import CHANNEL_SUPPORT
from src.discord.globals import PI_BOT_IDS
import re
from commandchecks import is_staff
    
class Censor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("Censor cog loaded")
    
    # @commands.Cog.listener()
    # gets called by main on_message in bot.py. A bit scuffed, butthe censor
    #  should be the executed BEFORE commands
    async def on_message(self, message):
        """
        Will censor the message. Will replace any flags in content with "<censored>".
        
        :param message: The message being checked. message.context will be modified
            if censor gets triggered if and only if the author is not a staff member.
        :type message: discord.Message
        """
        content = message.content
        # print(f"content before censor: \"{content}\"")
        for word in CENSORED_WORDS:
            if len(re.findall(fr"\b({word})\b", content, re.I)):
                print(f"Censoring message by {message.author} because of the word: `{word}`")
                await message.delete()
                await self.__censor(message)
        for word in CENSORED_EMOJIS:
            if len(re.findall(fr"{word}", content)):
                print(f"Censoring message by {message.author} because of the emoji: `{word}`")
                await message.delete()
                await self.__censor(message)
        if not any(ending for ending in DISCORD_INVITE_ENDINGS if ending in message.content) and (len(re.findall("discord.gg", content, re.I)) > 0 or len(re.findall("discord.com/invite", content, re.I)) > 0):
            print(f"Censoring message by {message.author} because of the it mentioned a Discord invite link.")
            await message.delete()
            ssChannel = discord.utils.get(message.author.guild.text_channels, name=CHANNEL_SUPPORT)
            await message.channel.send(f"*Links to external Discord servers can not be sent in accordance with rule 12. If you have questions, please ask in {ssChannel.mention}.*")
            
    async def __censor(self, message):
        """Constructs Pi-Bot's censor."""
        channel = message.channel
        ava = message.author.avatar_url
        wh = await channel.create_webhook(name="Censor (Automated)")
        content = message.content
        for word in CENSORED_WORDS:
            content = re.sub(fr'\b({word})\b', "<censored>", content, flags=re.IGNORECASE)
        for word in CENSORED_EMOJIS:
            content = re.sub(fr"{word}", "<censored>", content, flags=re.I)
        author = message.author.nick
        if author == None:
            author = message.author.name
        # Make sure pinging through @everyone, @here, or any role can not happen
        mention_perms = discord.AllowedMentions(everyone=False, users=True, roles=False)
        await wh.send(content, username=(author + " (auto-censor)"), avatar_url=ava, allowed_mentions=mention_perms)
        await wh.delete()
        
        # unless author is staff, replace content for other cogs (allows for staff to then add swears and censored words to pings)
        if not await is_staff(message.author):
            message.content = content # apply to message to not propogate censored words to other things like commands
        
def setup(bot):
    bot.add_cog(Censor(bot))