import discord
import datetime
from discord.ext import commands
import src.discord.globals
from src.discord.globals import CENSOR, DISCORD_INVITE_ENDINGS, CHANNEL_SUPPORT, PI_BOT_IDS, ROLE_MUTED
import re

class SpamManager(commands.Cog):

    recent_messages = []

    # Limits
    caps_limit = 8
    mute_limit = 6
    warning_limit = 3

    def __init__(self, bot):
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

    async def store_and_validate(self, message: discord.Message):
        """
        Stores a message in recent_messages and validates whether the message is spam or not.
        """
        # Check to see if the message has caps
        print("Made it here")

        self.recent_messages.insert(0, message)
        self.recent_messages = self.recent_messages[:20] # Only store 20 recent messages at once

        matching_messages = filter(lambda m: m.author == message.author and m.content.lower() == message.content.lower(), self.recent_messages)
        matching_messages_count = len(list(matching_messages))

        if matching_messages_count >= self.mute_limit:
            muted_role = discord.utils.get(message.guild.roles, name = ROLE_MUTED)
            unmute_time = discord.utils.utcnow() + datetime.timedelta(hours = 1)
            # CRON_LIST.append({"date": unmute_time, "do": f"unmute {message.author.id}"})
            await message.author.add_roles(muted_role)
            await message.channel.send(f"Successfully muted {message.author.mention} for 1 hour.")
            #await auto_report(bot, "User was auto-muted (spam)", "red", f"A user ({str(message.author)}) was auto muted in {message.channel.mention} because of repeated spamming.")
        elif matching_messages_count >= self.warning_limit:
            await message.author.send(f"{message.author.mention}, please avoid spamming. Additional spam will lead to your account being temporarily muted.")

        caps_messages = filter(lambda m: m.author == message.author and self.has_caps(m) and len(m.content) > 5, self.recent_messages)
        caps_messages_count = len(list(caps_messages))

        if caps_messages_count >= self.caps_limit and self.has_caps(message):
            muted_role = discord.utils.get(message.guild.roles, name=ROLE_MUTED)
            unmute_time = discord.utils.utcnow() + datetime.timedelta(hours = 1)
            # CRON_LIST.append({"date": parsed, "do": f"unmute {message.author.id}"})
            await message.author.add_roles(muted_role)
            await message.channel.send(f"Successfully muted {message.author.mention} for 1 hour.")
            # await auto_report(bot, "User was auto-muted (caps)", "red", f"A user ({str(message.author)}) was auto muted in {message.channel.mention} because of repeated caps.")
        elif caps_messages_count >= self.warning_limit and self.has_caps(message):
            await message.author.send(f"{message.author.mention}, please avoid using all caps in your messages. Repeatedly doing so will cause your account to be temporarily muted.")

def setup(bot):
    bot.add_cog(SpamManager(bot))
