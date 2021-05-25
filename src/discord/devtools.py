import discord
from discord.ext import commands

class DevCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(aliases=["gci", "cid", "channelid"])
    async def getchannelid(self, ctx):
        """Gets the channel ID of the current channel."""
        await ctx.send("Hey <@" + str(ctx.message.author.id) + ">! The channel ID is `" + str(ctx.message.channel.id) + "`. :)")

    @commands.command(aliases=["gei", "eid"])
    async def getemojiid(self, ctx, emoji: discord.Emoji):
        """Gets the ID of the given emoji."""
        return await ctx.send(f"{emoji} - `{emoji}`")

    @commands.command(aliases=["rid"])
    async def getroleid(self, ctx, name):
        role = discord.utils.get(ctx.message.author.guild.roles, name=name)
        return await ctx.send(f"`{role.mention}`")

    @commands.command(aliases=["gui", "ui", "userid"])
    async def getuserid(self, ctx, user=None):
        """Gets the user ID of the caller or another user."""
        if user == None:
            await ctx.send(f"Your user ID is `{ctx.message.author.id}`.")
        elif user[:3] != "<@!":
            member = ctx.message.guild.get_member_named(user)
            await ctx.send(f"The user ID of {user} is: `{member.id}`")
        else:
            user = user.replace("<@!", "").replace(">", "")
            await ctx.send(f"The user ID of <@{user}> is `{user}`.")

    @commands.command(aliases=["hi"])
    async def hello(self, ctx):
        """Simply says hello. Used for testing the bot."""
        await ctx.send("Well, hello there.")
        
def setup(bot):
    bot.add_cog(DevCommands(bot))