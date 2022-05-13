from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands
from src.discord.globals import SLASH_COMMAND_GUILDS

if TYPE_CHECKING:
    from bot import PiBot


class DevCommands(commands.Cog):
    """
    Cog responsible for maintaining commands regarding developer-related interactions,
    including getting object IDs.
    """

    def __init__(self, bot: PiBot):
        self.bot = bot

    @app_commands.command(description="Returns the current channel ID.")
    @app_commands.guilds(SLASH_COMMAND_GUILDS)
    @app_commands.describe(channel="The channel to get the ID of.")
    async def getchannelid(
        self, interaction: discord.Interaction, channel: discord.TextChannel = None
    ):
        """
        Gets the channel ID of the requested channel. If no channel is explicitly
        requested, the current channel is used.

        Args:
            channel (discord.Option): The requested channel.
        """
        if not channel:
            # If no channel was specified, assume the user is referring to the current channel
            channel = interaction.channel

        await interaction.response.send_message(f"{channel.mention}: `{channel.id}`")

    @app_commands.command(description="Returns the ID ")
    @app_commands.guilds(SLASH_COMMAND_GUILDS)
    @app_commands.describe(emoji="The emoji to get the ID of.")
    async def getemojiid(self, interaction: discord.Interaction, emoji: str):
        """
        Gets the ID of the given emoji.

        Args:
            emoji (str): The emoji to get the ID of.
        """
        await interaction.response.send_message(f"{emoji}: `{emoji}`")

    @app_commands.command(description="Returns the ID ")
    @app_commands.guilds(SLASH_COMMAND_GUILDS)
    @app_commands.describe(name="The name of the role to get the ID of.")
    async def getroleid(
        self,
        interaction: discord.Interaction,
        name: str,
    ):
        """
        Get the ID of the given role name.

        Args:
            name (sre): The name of the role to get the ID of.
        """
        role = discord.utils.get(interaction.guild.roles, name=name)
        if role is not None:
            await interaction.response.send_message(f"{str(role)}: `{role.mention}`")
        else:
            await interaction.response.send_message(
                f"No role named `{name}` was found."
            )

    @app_commands.command(description="Returns the ID of a user (or yourself).")
    @app_commands.guilds(SLASH_COMMAND_GUILDS)
    @app_commands.describe(member="The member to get the ID of.")
    async def getuserid(
        self, interaction: discord.Interaction, member: discord.Member = None
    ):
        """
        Gets the member ID of the author or another member.

        Args:
            member (discord.Option[discord.Member]): The member to get the ID of.
        """
        if not member:
            member = interaction.user

        await interaction.response.send_message(f"{str(member)}: `{member.id}`")

    @app_commands.command(description="Says hello!")
    @app_commands.guilds(SLASH_COMMAND_GUILDS)
    async def hello(self, interaction: discord.Interaction):
        """
        Simply says hello. Used for testing the bot.
        """
        await interaction.response.send_message(
            "Well, hello there. Welcome to version 5!"
        )


async def setup(bot: PiBot):
    await bot.add_cog(DevCommands(bot))
