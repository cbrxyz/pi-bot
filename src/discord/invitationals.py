from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord
from beanie import SortDirection
from beanie.odm.operators.update.array import Push
from discord.ext import commands

from env import env
from src.discord.globals import (
    CATEGORY_ARCHIVE,
    CATEGORY_INVITATIONALS,
    CHANNEL_BOTSPAM,
    CHANNEL_COMPETITIONS,
    CHANNEL_INVITATIONALS,
    CHANNEL_SUPPORT,
    DISCORD_AUTOCOMPLETE_MAX_ENTRIES,
    ROLE_AD,
    ROLE_AT,
    ROLE_GM,
)
from src.mongo.models import Invitational

if TYPE_CHECKING:
    from bot import PiBot

    from .reporter import Reporter


logger = logging.getLogger(__name__)


class AllInvitationalsView(discord.ui.View):
    """
    A view class for holding the button to toggle visibility of all invitationals for a user.
    """

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Toggle All Invitationals", style=discord.ButtonStyle.gray)
    async def toggle(self, interaction: discord.Interaction, _: discord.ui.Button):
        # Get the relevant member asking to toggle all invitationals
        member = interaction.user
        guild = interaction.guild
        assert isinstance(member, discord.Member)
        assert isinstance(guild, discord.Guild)

        all_invitationals_role = discord.utils.get(guild.roles, name=ROLE_AT)
        assert isinstance(all_invitationals_role, discord.Role)

        # Add/remove the role from the user
        if all_invitationals_role in member.roles:
            await member.remove_roles(all_invitationals_role)
            await interaction.response.send_message(
                content="I have removed your `All Invitationals` role!",
                ephemeral=True,
            )
        else:
            await member.add_roles(all_invitationals_role)
            await interaction.response.send_message(
                content="I have added the `All Invitationals` role to your profile.",
                ephemeral=True,
            )


class InvitationalDropdown(discord.ui.Select):
    def __init__(
        self,
        month_invitationals: list[Invitational],
        bot: PiBot,
        voting=False,
    ):

        final_options = []
        for tourney in month_invitationals:
            final_options.append(
                discord.SelectOption(
                    label=tourney.official_name
                    if tourney.status != "archived"
                    else f"{tourney.official_name} (archived)",
                    description=f"Occurs on {tourney.tourney_date.date()!s}.",
                    emoji=tourney.emoji,
                ),
            )

        super().__init__(
            options=final_options,
            min_values=1,
            max_values=len(final_options),
            placeholder="Choose an invitational...",
        )

        self.bot = bot
        self.voting = voting
        self.invitationals = month_invitationals

    async def callback(self, interaction: discord.Interaction):
        # Type checking
        member = interaction.user
        assert isinstance(member, discord.Member)

        server = member.guild
        assert isinstance(server, discord.Guild)

        if not self.voting:
            # If this dropdown isn't being used for voting
            for value in self.values:
                # For each invitational selected
                value = value.replace(" (archived)", "")
                role = discord.utils.get(server.roles, name=value)
                assert isinstance(role, discord.Role)

                if role in member.roles:
                    await member.remove_roles(role)
                    await interaction.response.send_message(
                        f"You have been removed from the `{value}` invitational channel.",
                        ephemeral=True,
                    )
                else:
                    await member.add_roles(role)
                    await interaction.response.send_message(
                        f"You have been added to the `{value}` invitational channel.",
                        ephemeral=True,
                    )

                await interaction.message.edit()

        else:
            # This dropdown is being used for voting
            need_to_update: list[Invitational] = []
            already_voted_for = []

            for value in self.values:
                # For each invitational selected
                invitational = discord.utils.get(
                    self.invitationals,
                    official_name=value,
                )
                if not invitational:
                    continue
                if member.id in invitational.voters:
                    # This user has already voted for this invitational.
                    already_voted_for.append(invitational)
                else:
                    # This user has not already voted for this invitational.
                    invitational.voters.append(member.id)
                    need_to_update.append(invitational)

            # Update invitationals DB
            if len(need_to_update) > 0:
                # Some docs need to be updated

                for invy in need_to_update:
                    invy.update(Push({Invitational.voters: member.id}))

            # Format output
            result_string = ""
            for invitational in need_to_update:
                result_string += f"`{invitational.official_name}` - I added your vote! This tourney now has {len(invitational.voters)} votes!\n"
            for invitational in already_voted_for:
                result_string += f"`{invitational.official_name}` - You already voted for this channel! This channel has {len(invitational.voters)} votes!\n"

            # Send output
            result_string = result_string[:-1]  # Delete last newline character
            await interaction.response.send_message(result_string, ephemeral=True)
            await interaction.message.edit()


class InvitationalDropdownView(discord.ui.View):
    def __init__(self, month_invitationals, bot, voting=False):
        super().__init__(timeout=None)
        self.voting = voting
        self.add_item(
            InvitationalDropdown(month_invitationals, bot, voting=self.voting),
        )


async def update_invitational_list(bot: PiBot, rename_dict: dict = {}) -> None:
    """
    Update the list of invitationals in #invitationals.

    :param rename_dict: A dictionary containing renames of channels and roles that need to be completed.
    """
    # Fetch invitationals
    invitationals = await Invitational.find_all(
        sort=[(Invitational.official_name, SortDirection.ASCENDING)],
        ignore_cache=True,
    ).to_list()

    # Update global invitational info
    global INVITATIONAL_INFO
    INVITATIONAL_INFO = invitationals

    # Get guild and channels
    server = bot.get_guild(env.server_id)
    assert isinstance(server, discord.Guild)

    invitational_channel = discord.utils.get(
        server.text_channels,
        name=CHANNEL_INVITATIONALS,
    )
    invitational_category = discord.utils.get(
        server.categories,
        name=CATEGORY_INVITATIONALS,
    )
    bot_spam_channel = discord.utils.get(server.text_channels, name=CHANNEL_BOTSPAM)
    server_support_channel = discord.utils.get(
        server.text_channels,
        name=CHANNEL_SUPPORT,
    )
    assert isinstance(invitational_channel, discord.TextChannel)
    assert isinstance(invitational_category, discord.CategoryChannel)
    assert isinstance(bot_spam_channel, discord.TextChannel)
    assert isinstance(server_support_channel, discord.TextChannel)

    # Get roles
    global_moderator_role = discord.utils.get(server.roles, name=ROLE_GM)
    admin_role = discord.utils.get(server.roles, name=ROLE_AD)
    all_invitationals_role = discord.utils.get(server.roles, name=ROLE_AT)
    assert isinstance(global_moderator_role, discord.Role)
    assert isinstance(admin_role, discord.Role)
    assert isinstance(all_invitationals_role, discord.Role)

    now = discord.utils.utcnow()

    # Rename channels if needed
    if "channels" in rename_dict:
        for item in rename_dict["channels"].items():
            channel = discord.utils.get(server.text_channels, name=item[0])
            if channel is not None:
                # If old-named channel exists, then rename
                await channel.edit(name=item[1])

    # Rename roles if needed
    if "roles" in rename_dict:
        for item in rename_dict["roles"].items():
            role = discord.utils.get(server.roles, name=item[0])
            if role is not None:
                # If old-named role exists, then rename
                await role.edit(name=item[1])

    for t in invitationals:  # For each invitational in the sheet
        channel = discord.utils.get(server.text_channels, name=t.channel_name)
        role = discord.utils.get(server.roles, name=t.official_name)

        tourney_date_str = str(t.tourney_date.date())
        after_days = int(t.closed_days)
        day_diff = (t.tourney_date - now).days

        logger.info(
            f"Invitational List: Handling {t.official_name} (Day diff: {day_diff} days)",
        )

        if isinstance(channel, discord.TextChannel) and t.status == "archived":
            # Invitational channel should be archived
            logger.info(f"Attempting to archive #{t.official_name}.")
            channel_category = channel.category
            assert isinstance(channel_category, discord.CategoryChannel)

            if channel_category.name != CATEGORY_ARCHIVE:
                # If channel is not in category archive, then archive it
                archive_category = discord.utils.get(
                    server.categories,
                    name=CATEGORY_ARCHIVE,
                )
                competitions_channel = discord.utils.get(
                    server.text_channels,
                    name=CHANNEL_COMPETITIONS,
                )
                invitational_role = discord.utils.get(
                    server.roles,
                    name=t.official_name,
                )

                # Type checking
                assert isinstance(archive_category, discord.CategoryChannel)
                assert isinstance(competitions_channel, discord.TextChannel)
                assert isinstance(invitational_role, discord.Role)

                embed = discord.Embed(
                    title="This channel is now archived.",
                    description=(
                        f"Thank you all for your discussion around the **{t.official_name}**. Now that we are well past the invitational date, we are going to close this channel to help keep invitational discussions relevant and on-topic.\n\n"
                        + f"If you have more questions/comments related to this invitational, you are welcome to bring them up in {competitions_channel.mention}. This channel is now read-only.\n\n"
                        + f"If you would like to no longer view this channel, you are welcome to remove the role using the dropdowns in {invitational_channel.mention}, and the channel will disappear for you. Members with the `All Invitationals` role will continue to see the channel."
                    ),
                    color=discord.Color.brand_red(),
                )

                # Send embed and update channel permissions
                await channel.set_permissions(
                    invitational_role,
                    send_messages=False,
                    view_channel=True,
                )
                await channel.set_permissions(
                    all_invitationals_role,
                    send_messages=False,
                    view_channel=True,
                )
                await channel.edit(category=archive_category, position=1000)
                await channel.send(embed=embed)

        elif isinstance(channel, discord.TextChannel) and t.status == "open":
            logger.debug(f"Ensuring #{t.official_name} is up-to-date.")
            # Type checking
            channel_category = channel.category
            assert isinstance(channel_category, discord.CategoryChannel)
            assert isinstance(role, discord.Role)

            if day_diff < -after_days and channel_category.name != CATEGORY_ARCHIVE:
                # If past invitational date, now out of range - make warning report to archive
                reporter_cog: commands.Cog | Reporter = bot.get_cog("Reporter")
                await reporter_cog.create_invitational_archive_report(
                    t,
                    channel,
                    role,
                )

            # Fix channel attributes in case changed/broken
            to_change = {}
            if (
                channel.topic
                != f"{t.emoji} - Discussion around the {t.official_name} occurring on {tourney_date_str}."
            ):
                to_change[
                    "topic"
                ] = f"{t.emoji} - Discussion around the {t.official_name} occurring on {tourney_date_str}."

            if channel_category.name == CATEGORY_ARCHIVE:
                to_change["category"] = discord.utils.get(
                    server.categories,
                    name=CATEGORY_INVITATIONALS,
                )

            if len(to_change):
                await channel.edit(**to_change)

            # Fix permissions in case the channel was previously archived
            invitational_role_perms = channel.permissions_for(role)
            if (
                not invitational_role_perms.read_messages
                or not invitational_role_perms.send_messages
            ):
                await channel.set_permissions(
                    role,
                    send_messages=True,
                    read_messages=True,
                )

            all_tourney_role_perms = channel.permissions_for(all_invitationals_role)
            if (
                not all_tourney_role_perms.read_messages
                or not all_tourney_role_perms.send_messages
            ):
                await channel.set_permissions(
                    all_invitationals_role,
                    send_messages=True,
                    read_messages=True,
                )

        elif channel is None and t.status == "open":
            # If invitational needs to be created
            logger.info(f"Creating new channel for #{t.channel_name}.")
            new_role = await server.create_role(name=t.official_name)
            new_channel = await server.create_text_channel(
                t.channel_name,
                category=invitational_category,
            )

            await new_channel.edit(
                topic=f"{t.emoji} - Discussion around the {t.official_name} occurring on {tourney_date_str}.",
                sync_permissions=True,
            )
            await new_channel.set_permissions(new_role, read_messages=True)
            await new_channel.set_permissions(
                all_invitationals_role,
                read_messages=True,
            )
            await new_channel.set_permissions(server.default_role, read_messages=False)
            logger.info(f"Created new channel for #{t.channel_name}.")

        else:
            logger.debug(f"No action was taken for the {t.official_name} invitational.")

    help_embed = discord.Embed(
        title=":first_place: Join a Invitational Channel!",
        color=discord.Color(0x2E66B6),
        description=f"""
        Below is a list of **invitational channels**. Some are available right now, while others have been requested, but have not received enough support to be considered for a channel.

        To join an invitational channel, use the dropdowns below! Dropdowns are split up by date! If you would like to leave an invitational channel you previously joined, please re-select the invitational from the appropriate dropdown.

        To request a new invitational channel, please use the `/request` command in {bot_spam_channel.mention}. If you need help, feel free to let a {admin_role.mention} or {global_moderator_role.mention} know!
        """,
    )
    await invitational_channel.purge()  # Delete all messages to make way for new messages/views
    await invitational_channel.send(embed=help_embed)

    first_year = bot.settings.invitational_season - 1
    second_year = bot.settings.invitational_season
    months = [
        {"name": "September", "number": 9, "year": first_year, "optional": True},
        {"name": "October", "number": 10, "year": first_year, "optional": False},
        {"name": "November", "number": 11, "year": first_year, "optional": False},
        {"name": "December", "number": 12, "year": first_year, "optional": False},
        {"name": "January", "number": 1, "year": second_year, "optional": False},
        {"name": "February", "number": 2, "year": second_year, "optional": False},
        {"name": "March", "number": 3, "year": second_year, "optional": False},
        {"name": "April", "number": 4, "year": second_year, "optional": True},
        {"name": "May", "number": 5, "year": second_year, "optional": True},
        {"name": "June", "number": 6, "year": second_year, "optional": True},
        {"name": "July", "number": 7, "year": second_year, "optional": True},
        {"name": "August", "number": 8, "year": second_year, "optional": True},
    ]
    for month in months:
        month_invitationals = [
            t
            for t in invitationals
            if t.tourney_date.month == month["number"]
            and t.tourney_date.year == month["year"]
            and t.status in ["open", "archived"]
        ][:DISCORD_AUTOCOMPLETE_MAX_ENTRIES]
        if len(month_invitationals) > 0:
            await invitational_channel.send(
                f"Invitationals in **{month['name']} {month['year']}**:",
                view=InvitationalDropdownView(month_invitationals, bot),
            )
        else:
            # No invitationals in the given month :(
            if not month["optional"]:
                await invitational_channel.send(
                    f"Sorry, there are no channels opened for invitationals in **{month['name']} {month['year']}**.",
                )

    voting_invitationals = [t for t in invitationals if t.status == "voting"]
    voting_embed = discord.Embed(
        title=":second_place: Vote for an Invitational Channel!",
        color=discord.Color(0x2E66B6),
        description="Below are invitational channels that are in the **voting phase**. These invitationals have been requested by users but have not received enough support to become official channels.\n\nIf you vote for these invitational channels to become official, you will automatically be added to these channels upon their creation.",
    )
    await invitational_channel.send(embed=voting_embed)
    if len(voting_invitationals):
        await invitational_channel.send(
            "Vote on a requested invitational:",
            view=InvitationalDropdownView(voting_invitationals, bot, voting=True),
        )
    else:
        await invitational_channel.send(
            "Sorry, there no invitationals are currently being voted on.",
        )

    # Give user option to enable/disable visibility of all invitationals
    await invitational_channel.send(
        "Additionally, you can toggle visibility of all invitationals by using the button below:",
        view=AllInvitationalsView(),
    )
