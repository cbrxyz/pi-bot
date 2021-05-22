import discord
from discord.ext import commands
import time

class FunCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("Fun commands loaded")
    
    @commands.Cog.listener()
    async def on_message(self, message):
        pass