"""
Holds functionality for the welcome system.
"""
from __future__ import annotations

import logging
from collections.abc import Generator
from typing import TYPE_CHECKING, TypeVar

import discord
from discord.ext import commands, tasks

import src.discord.globals

if TYPE_CHECKING:
    from bot import PiBot


logger = logging.getLogger(__name__)
V = TypeVar("V")


def batch(iter: list[V], n: int) -> Generator[list[V], None, None]:
    length = len(iter)
    for ndx in range(0, length, n):
        yield iter[ndx : min(ndx + n, length)]


class SelectionDropdown(discord.ui.Select["Chooser"]):
    def __init__(self, item_type: str, options: list[discord.SelectOption]):
        first_letter = options[0].label[0].title()
        last_letter = options[-1].label[0].title()
        super().__init__(
            placeholder=f"{item_type.title()}s {first_letter}-{last_letter}...",
            options=options,
            max_values=len(options),
        )

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        self.view.chosen_values = self.values
        self.view.stop()


class AcceptButton(discord.ui.Button["Chooser"]):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.green, label="Accept", row=4)

    async def callback(self, interaction: discord.Interaction):
        if self.view:
            self.view.stop()


class SkipButton(discord.ui.Button["Chooser"]):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.gray, label="Skip", row=4)

    async def callback(self, interaction: discord.Interaction):
        if self.view:
            self.view.chosen_values = []
            self.view.stop()


class Chooser(discord.ui.View):

    chosen_values: list[str]  # List of values the user chose

    def __init__(
        self,
        item_type: str,
        options: list[discord.SelectOption],
        count: int = 25,
    ):
        super().__init__()
        self.chosen_values = []
        for options_batch in batch(options, count):
            self.add_item(SelectionDropdown(item_type, options_batch))
        if self.chosen_values:
            self.add_item(AcceptButton())
        self.add_item(SkipButton())

    async def on_timeout(self):
        pass


class InitialView(discord.ui.View):
    def __init__(self, bot: PiBot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Gain server access", custom_id="welcome:request_access")
    async def request_access(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        STATES_GUILD = 1
        emoji_guild = self.bot.get_guild(STATES_GUILD)
        if emoji_guild is None:
            emoji_guild = await self.bot.fetch_guild(STATES_GUILD)
        assert isinstance(emoji_guild, discord.Guild)

        state_options: list[discord.SelectOption] = []
        for emoji in emoji_guild.emojis:
            if emoji.name != "california":  # handle california later
                state_options.append(
                    discord.SelectOption(
                        label=emoji.name.replace("_", " ").title(),
                        emoji=emoji,
                    ),
                )

        # Handle California
        california_emoji = discord.utils.get(emoji_guild.emojis, name="california")
        assert isinstance(california_emoji, discord.Emoji)
        state_options.append(
            discord.SelectOption(label="California (North)", emoji=california_emoji),
        )
        state_options.append(
            discord.SelectOption(label="California (South)", emoji=california_emoji),
        )
        state_options.sort(key=lambda x: x.label)

        state_chooser = Chooser(
            "state",
            state_options,
            count=19,
        )
        await interaction.response.send_message(
            "Select your state to gain access to the server.",
            view=state_chooser,
            ephemeral=True,
        )
        await state_chooser.wait()
        print(f"User chose: {state_chooser.chosen_values}")


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
        view = InitialView(self.bot)
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
    bot.add_view(InitialView(bot))
