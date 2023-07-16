"""
Holds functionality for the welcome system.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord
from discord.ext import commands, tasks

import src.discord.globals

if TYPE_CHECKING:
    from bot import PiBot


logger = logging.getLogger(__name__)


class SelectionDropdown(discord.ui.Select):
    def __init__(self, item_type: str, options: list[str]):
        first_letter = options[0][0].title()
        last_letter = options[-1][0].title()
        prepared_options = [
            discord.SelectOption(label=option, value=option) for option in options
        ]
        super().__init__(
            placeholder=f"{item_type.title()}s {first_letter}-{last_letter}...",
            options=prepared_options,
            max_values=len(prepared_options),
        )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"Selected {self.values[0]}",
            ephemeral=True,
        )


class Chooser(discord.ui.View):
    def __init__(self, item_type: str, options: list[str]):
        super().__init__()
        self.add_item(SelectionDropdown(item_type, options))

    async def on_timeout(self):
        pass


class InitialView(discord.ui.View):
    menus = [
        Chooser("state", ["Alabama", "Alaska", "Arizona", "Arkansas"]),
    ]

    @discord.ui.button(label="Gain server access")
    async def request_access(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await interaction.response.send_message(
            "Select your state to gain access to the server.",
            view=self.menus[0],
            ephemeral=True,
        )


class WelcomeCog(commands.GroupCog, name="welcome"):
    def __init__(self, bot: PiBot):
        self.bot = bot
        self.update_welcome_channel.start()

    def get_guild(self) -> discord.Guild:
        guild = self.bot.get_guild(src.discord.globals.SERVER_ID)
        assert isinstance(guild, discord.Guild)
        return guild

    def get_channel(self, name: str) -> discord.TextChannel:
        guild = self.get_guild()
        channel = discord.utils.get(guild.channels, name=name)
        assert isinstance(channel, discord.TextChannel)
        return channel

    def generate_welcome_embed(self) -> discord.Embed:
        rules_channel = self.get_channel(src.discord.globals.CHANNEL_RULES)
        embed = discord.Embed(
            title="Welcome to the Scioly.org chat server!",
            description=f"We're so excited to have you here; we hope this community can help advance your passion for Science Olympiad.\n\nPlease read the rules in {rules_channel.mention}.",
            color=discord.Color(0xFEE372),
        )
        embed.set_thumbnail(url=self.get_guild().icon.url)
        return embed

    @tasks.loop(seconds=5)
    async def update_welcome_channel(self):
        print("running")
        guild = self.bot.get_guild(src.discord.globals.SERVER_ID)
        if not guild:
            return  # bot is still starting up
        assert isinstance(guild, discord.Guild)
        channel = discord.utils.get(
            guild.channels,
            name=src.discord.globals.CHANNEL_WELCOME,
        )
        assert isinstance(channel, discord.TextChannel)

        history = [m async for m in channel.history(limit=1)]
        embed = self.generate_welcome_embed()
        view = InitialView()
        if not history:
            await channel.send(embed=embed, view=view)
        elif (
            not history[0].embeds
            or history[0].embeds[0].description != embed.description
        ):
            await history[0].edit(embed=embed, view=view)


async def setup(bot: PiBot):
    cog = WelcomeCog(bot)
    await bot.add_cog(cog)
