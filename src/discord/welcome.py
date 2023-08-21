"""
Holds functionality for the welcome system.
"""
from __future__ import annotations

import datetime
import logging
from collections.abc import Callable, Generator
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, TypeVar

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


@dataclass()
class RoleItem:
    name: str
    emoji: discord.Emoji | discord.PartialEmoji


class SelectionDropdown(discord.ui.Select["Chooser"]):
    def __init__(self, item_type: str, options: list[discord.SelectOption]):
        self.item_type = item_type
        first_letter = options[0].label[0].title()
        last_letter = options[-1].label[0].title()
        super().__init__(
            placeholder=f"{item_type.title()}s {first_letter}-{last_letter}...",
            options=options,
            max_values=len(options),
        )

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        for value in self.values:
            if value in [x.name for x in self.view.chosen_values]:
                self.view.chosen_values = [
                    x for x in self.view.chosen_values if x.name != value
                ]
            else:
                option = discord.utils.get(self.options, value=value)
                assert option is not None and option.emoji is not None
                self.view.chosen_values.append(RoleItem(value, option.emoji))
        self.view.update_values(self.item_type.title(), self.view.chosen_values)

        # Update accept/skip buttons
        if self.view.chosen_values:
            if not any(isinstance(child, AcceptButton) for child in self.view.children):
                self.view.add_item(AcceptButton())
        else:
            for child in self.view.children:
                if isinstance(child, AcceptButton):
                    self.view.remove_item(child)

        # Actually update message
        await interaction.response.edit_message(
            **self.view.profile_message(interaction),
            view=self.view,
        )


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
            self.view.stop()


class Chooser(discord.ui.View):

    chosen_values: list[RoleItem]  # List of values the user chose

    def __init__(
        self,
        item_type: str,
        options: list[discord.SelectOption],
        profile_message: Callable[
            [discord.Interaction],
            dict[Literal["content", "embed"], str | discord.Embed],
        ],
        update_values: Callable[[str, list[RoleItem]], None],
        count: int = 25,
    ):
        super().__init__()
        self.chosen_values = []
        self.profile_message = profile_message
        self.update_values = update_values
        for options_batch in batch(options, count):
            self.add_item(SelectionDropdown(item_type, options_batch))
        if self.chosen_values:
            self.add_item(AcceptButton())
        self.add_item(SkipButton())

    async def on_timeout(self):
        pass


class InitialView(discord.ui.View):

    emoji_guild: discord.Guild
    chosen_roles: dict[str, list[RoleItem]]

    def __init__(self, bot: PiBot):
        super().__init__(timeout=None)
        self.bot = bot
        self.chosen_roles = {}

    def update_chosen_roles(self, name: str, roles: list[RoleItem]) -> None:
        self.chosen_roles[name] = roles

    def get_guild(self) -> discord.Guild:
        guild = self.bot.get_guild(src.discord.globals.SERVER_ID)
        assert isinstance(guild, discord.Guild)
        return guild

    def get_channel(self, name: str) -> discord.TextChannel:
        guild = self.get_guild()
        channel = discord.utils.get(guild.channels, name=name)
        assert isinstance(channel, discord.TextChannel)
        return channel

    def generate_profile_message(
        self,
        interaction: discord.Interaction,
    ) -> dict[Literal["content", "embed"], str | discord.Embed]:
        profile_embed = discord.Embed(
            title="Your Profile",
            description="This is your server profile. You can change your roles using the dropdowns below.\n\nClicking on a role in a dropdown will add it to your profile if you do not have it already, or it will remove it if you already have it.",
            color=discord.Color(0x2E66B6),
        )
        profile_embed.set_thumbnail(url=interaction.user.display_avatar.url)
        interaction.user.display_avatar
        for k, v in self.chosen_roles.items():
            formatted_items = []
            v.sort(key=lambda x: x.name)
            items_added = 0
            for item in v:
                total_length = sum(len(format) for format in formatted_items)
                if total_length < 925:
                    formatted_items.append(f"{item.emoji} **{item.name}**")
                    items_added += 1
            items_list = "\n".join(formatted_items)
            if items_added < len(v):
                items_list += f"\n_... {len(v) - items_added} not shown_"
            profile_embed.add_field(
                name=k if len(v) == 1 else f"{k}s",
                value=items_list,
            )
        return {
            "content": "Great start to your profile!",
            "embed": profile_embed,
        }

    @discord.ui.button(
        label="Enter the server",
        custom_id="welcome:request_access",
        emoji="✅",
        style=discord.ButtonStyle.green,
    )
    async def request_access(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        # Make sure user has been in server for 10 minutes
        assert isinstance(interaction.user, discord.Member)
        if (
            interaction.user.joined_at
            and (discord.utils.utcnow() - interaction.user.joined_at).total_seconds()
            < 600
        ):
            available_time = interaction.user.joined_at + datetime.timedelta(minutes=10)
            return await interaction.response.send_message(
                f"Again, welcome! To prevent spam, you must wait 10 minutes after joining before you can complete your confirmation. You can complete your confirmation at {discord.utils.format_dt(available_time, 't')} ({discord.utils.format_dt(available_time, 'R')})!",
            )

        STATES_GUILD = 1
        emoji_guild = self.bot.get_guild(STATES_GUILD)
        self.emoji_guild = emoji_guild or await self.bot.fetch_guild(STATES_GUILD)

        state_options: list[discord.SelectOption] = []
        for emoji in self.emoji_guild.emojis:
            if emoji.name != "california":  # handle california later
                state_options.append(
                    discord.SelectOption(
                        label=emoji.name.replace("_", " ").title(),
                        emoji=emoji,
                    ),
                )

        # Handle California
        california_emoji = discord.utils.get(self.emoji_guild.emojis, name="california")
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
            self.generate_profile_message,
            self.update_chosen_roles,
            count=19,
        )
        await interaction.response.send_message(
            "Select your state to gain access to the server.",
            view=state_chooser,
            ephemeral=True,
        )
        await state_chooser.wait()

        event_options: list[discord.SelectOption] = []
        for event in src.discord.globals.EVENT_INFO:
            event_options.append(
                discord.SelectOption(label=event["name"], emoji=event["emoji"]),
            )
        event_chooser = Chooser(
            "event",
            event_options,
            self.generate_profile_message,
            self.update_chosen_roles,
            count=19,
        )
        await interaction.edit_original_response(
            content="Good job adding some states to your profile. Now, how about adding some events that you participate in or enjoy? Event roles allow you to show off your interests on your profile!",
            view=event_chooser,
        )
        await event_chooser.wait()

        pronoun_options = [
            discord.SelectOption(label="He/Him", emoji="👨"),
            discord.SelectOption(label="She/Her", emoji="👩"),
            discord.SelectOption(label="They/Them", emoji="🧑"),
        ]
        pronouns_chooser = Chooser(
            "pronoun",
            pronoun_options,
            self.generate_profile_message,
            self.update_chosen_roles,
            count=19,
        )
        await interaction.edit_original_response(
            content="Now, how about adding your pronouns to your profile? Pronouns help others identify you correctly.",
            view=pronouns_chooser,
        )
        await pronouns_chooser.wait()

        division_options = [
            discord.SelectOption(label="Division A", emoji="\U0001F1E6"),
            discord.SelectOption(label="Division B", emoji="\U0001F1E7"),
            discord.SelectOption(label="Division C", emoji="\U0001F1E8"),
            discord.SelectOption(label="Division D", emoji="\U0001F1E9"),
        ]
        divisions_chooser = Chooser(
            "division",
            division_options,
            self.generate_profile_message,
            self.update_chosen_roles,
            count=19,
        )
        await interaction.edit_original_response(
            content="Finally, do you want to add the division you compete in?",
            view=divisions_chooser,
        )
        await divisions_chooser.wait()

        # Finalize user's request
        member_role = discord.utils.get(self.get_guild().roles, name="Member")
        assert isinstance(member_role, discord.Role)
        self.needed_roles: list[discord.Role] = [member_role]
        for role_list in self.chosen_roles.values():
            for role in role_list:
                role_obj = discord.utils.get(self.get_guild().roles, name=role.name)
                if role_obj:
                    self.needed_roles.append(role_obj)

        assert isinstance(interaction.user, discord.Member)
        await interaction.user.edit(roles=self.needed_roles)

        bot_spam_channel = self.get_channel("bot-spam")
        await interaction.edit_original_response(
            content=f"{interaction.user.mention}, you are now confirmed. Welcome to the Scioly.org Discord chat server! To make further adjustments to your roles, please visit the {bot_spam_channel.mention} channel.",
            view=None,
            embed=None,
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
            title="Welcome to the Scioly.org Discord chat server!",
            description=f"We're so excited to have you here; we hope this community can help advance your passion for Science Olympiad.\n\nRight now, you don't have access to all channels and messages. To get access to these resources, please click the big green button below.\n\nPlease read the rules in {rules_channel.mention} before starting the verification process. The verification process helps to ensure you are a legitimate user, and allows you to get some roles for your new profile!",
            color=discord.Color(0x2E66B6),
        )
        embed.set_image(
            url="https://cdn.discordapp.com/attachments/743632821448474706/1140487039704383508/Scioly.org_Google_Forms_Banner.png",
        )
        return embed

    @tasks.loop(seconds=5)
    async def update_welcome_channel(self):
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
