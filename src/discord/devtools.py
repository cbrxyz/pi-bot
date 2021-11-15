import discord
from discord.ext import commands
from discord.commands import Option

from src.discord.globals import SLASH_COMMAND_GUILDS

class DevCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Returns the current channel ID."
    )
    async def getchannelid(self, ctx):
        """Gets the channel ID of the current channel."""
        await ctx.interaction.response.send_message(f"{ctx.channel.mention}: `{ctx.channel.id}`")

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Returns the ID "
    )
    async def getemojiid(self,
        ctx,
        emoji: Option(str, "The emoji to get the ID of.", required = True)
        ):
        """Gets the ID of the given emoji."""
        await ctx.interaction.response.send_message(f"{emoji}: `{emoji}`")

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Returns the ID "
    )
    async def getroleid(self,
        ctx,
        name: Option(str, "The name of the role to get the ID of.", required = True)
        ):
        role = discord.utils.get(ctx.guild.roles, name = name)
        if role != None:
            await ctx.interaction.response.send_message(f"{str(role)}: `{role.mention}`")
        else:
            await ctx.interaction.response.send_message(f"No role named `{name}` was found.")

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Returns the ID of a user."
    )
    async def getuserid(self,
        ctx,
        user: Option(discord.Member, "The member to get the ID of.", required = True)
        ):
        """Gets the user ID of the caller or another user."""
        await ctx.interaction.response.send_message(f"{str(user)}: `{user.id}`")

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Says hello!"
    )
    async def hello(self, ctx):
        """Simply says hello. Used for testing the bot."""
        await ctx.interaction.response.send_message("Well, hello there. Welcome to version 5!")
        
def setup(bot):
    bot.add_cog(DevCommands(bot))
