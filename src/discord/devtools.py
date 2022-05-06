from src.discord.globals import SLASH_COMMAND_GUILDS

import discord
from discord.commands import Option
from discord.ext import commands


class DevCommands(commands.Cog):
    """
    Cog responsible for maintaining commands regarding developer-related interactions,
    including getting object IDs.
    """

    def __init__(self, bot):
        self.bot = bot

    @discord.commands.slash_command(
        guild_ids=[SLASH_COMMAND_GUILDS], description="Returns the current channel ID."
    )
    async def getchannelid(
        self,
        ctx,
        channel: Option(
            discord.TextChannel, "The channel to get the ID of.", required=False
        ),
    ):
        """
        Gets the channel ID of the requested channel. If no channel is explicitly
        requested, the current channel is used.

        Args:
            channel (discord.Option): The requested channel.
        """
        if not channel:
            # If no channel was specified, assume the user is referring to the current channel
            channel = ctx.channel

        await ctx.interaction.response.send_message(
            f"{channel.mention}: `{channel.id}`"
        )

    @discord.commands.slash_command(
        guild_ids=[SLASH_COMMAND_GUILDS], description="Returns the ID "
    )
    async def getemojiid(
        self, ctx, emoji: Option(str, "The emoji to get the ID of.", required=True)
    ):
        """
        Gets the ID of the given emoji.

        Args:
            emoji (discord.Option): The emoji to get the ID of.
        """
        await ctx.interaction.response.send_message(f"{emoji}: `{emoji}`")

    @discord.commands.slash_command(
        guild_ids=[SLASH_COMMAND_GUILDS], description="Returns the ID "
    )
    async def getroleid(
        self,
        ctx,
        name: Option(str, "The name of the role to get the ID of.", required=True),
    ):
        """
        Get the ID of the given role name.

        Args:
            role (discord.Option): The name of the role to get the ID of.
        """
        role = discord.utils.get(ctx.guild.roles, name=name)
        if role != None:
            await ctx.interaction.response.send_message(
                f"{str(role)}: `{role.mention}`"
            )
        else:
            await ctx.interaction.response.send_message(
                f"No role named `{name}` was found."
            )

    @discord.commands.slash_command(
        guild_ids=[SLASH_COMMAND_GUILDS],
        description="Returns the ID of a user (or yourself).",
    )
    async def getuserid(
        self,
        ctx,
        member: Option(discord.Member, "The member to get the ID of.", required=False),
    ):
        """
        Gets the member ID of the author or another member.

        Args:
            member (discord.Option[discord.Member]): The member to get the ID of.
        """
        if not member:
            member = ctx.author

        await ctx.interaction.response.send_message(f"{str(member)}: `{member.id}`")

    @discord.commands.slash_command(
        guild_ids=[SLASH_COMMAND_GUILDS], description="Says hello!"
    )
    async def hello(self, ctx):
        """
        Simply says hello. Used for testing the bot.
        """
        await ctx.interaction.response.send_message(
            "Well, hello there. Welcome to version 5!"
        )


def setup(bot):
    bot.add_cog(DevCommands(bot))
