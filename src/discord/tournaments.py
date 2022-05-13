from __future__ import annotations

from typing import TYPE_CHECKING, Union

import discord
import src.discord.globals
from discord.ext import commands
from src.discord.globals import (
    CATEGORY_ARCHIVE,
    CATEGORY_TOURNAMENTS,
    CHANNEL_BOTSPAM,
    CHANNEL_COMPETITIONS,
    CHANNEL_SUPPORT,
    CHANNEL_TOURNAMENTS,
    ROLE_AD,
    ROLE_AT,
    ROLE_GM,
    SERVER_ID,
)

if TYPE_CHECKING:
    from bot import PiBot

    from .reporter import Reporter


class Tournament:
    official_name: str
    voters: list

    def __init__(self, objects):
        self._properties = objects
        self.doc_id = objects.get("_id")
        self.official_name = objects.get("official_name")
        self.channel_name = objects.get("channel_name")
        self.emoji = objects.get("emoji")
        self.aliases = objects.get("aliases")
        self.tourney_date = objects.get("tourney_date")
        self.open_days = objects.get("open_days")
        self.closed_days = objects.get("closed_days")
        self.voters = objects.get("voters")
        self.status = objects.get("status")


class AllTournamentsView(discord.ui.View):
    """
    A view class for holding the button to toggle visibility of all tournaments for a user.
    """

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Toggle All Tournaments", style=discord.ButtonStyle.gray)
    async def toggle(self, interaction: discord.Interaction, _: discord.ui.Button):
        # Get the relevant member asking to toggle all tournaments
        member = interaction.user
        guild = interaction.guild
        assert isinstance(member, discord.Member)
        assert isinstance(guild, discord.Guild)

        all_tournaments_role = discord.utils.get(guild.roles, name=ROLE_AT)
        assert isinstance(all_tournaments_role, discord.Role)

        # Add/remove the role from the user
        if all_tournaments_role in member.roles:
            await member.remove_roles(all_tournaments_role)
            await interaction.response.send_message(
                content="I have removed your `All Tournaments` role!", ephemeral=True
            )
        else:
            await member.add_roles(all_tournaments_role)
            await interaction.response.send_message(
                content="I have added the `All Tournaments` role to your profile.",
                ephemeral=True,
            )


class TournamentDropdown(discord.ui.Select):
    def __init__(self, month_tournaments, bot: PiBot, voting=False):

        final_options = []
        for tourney in month_tournaments:
            final_options.append(
                discord.SelectOption(
                    label=tourney.official_name,
                    description=f"Occurs on {str(tourney.tourney_date.date())}.",
                    emoji=tourney.emoji,
                )
            )

        super().__init__(
            options=final_options,
            min_values=1,
            max_values=len(final_options),
            placeholder="Choose a tournament...",
        )

        self.bot = bot
        self.voting = voting
        self.tournaments = month_tournaments

    async def callback(self, interaction: discord.Interaction):
        # Type checking
        member = interaction.user
        assert isinstance(member, discord.Member)

        server = member.guild
        assert isinstance(server, discord.Guild)

        if not self.voting:
            # If this dropdown isn't being used for voting
            for value in self.values:
                # For each tournament selected
                role = discord.utils.get(server.roles, name=value)
                assert isinstance(role, discord.Role)

                if role in member.roles:
                    await member.remove_roles(role)
                    await interaction.response.send_message(
                        f"You have been removed from the `{value}` tournament channel.",
                        ephemeral=True,
                    )
                else:
                    await member.add_roles(role)
                    await interaction.response.send_message(
                        f"You have been added to the `{value}` tournament channel.",
                        ephemeral=True,
                    )

        else:
            # This dropdown is being used for voting
            need_to_update = []
            already_voted_for = []

            for value in self.values:
                # For each tournament selected
                tournament = discord.utils.get(self.tournaments, official_name=value)
                if member.id in tournament.voters:
                    # This user has already voted for this tournament.
                    already_voted_for.append(tournament)
                else:
                    # This user has not already voted for this tournament.
                    tournament.voters.append(member.id)
                    need_to_update.append(tournament)

            # Update invitationals DB
            if len(need_to_update) > 0:
                # Some docs need to be updated
                docs_to_update = [t._properties for t in need_to_update]
                await self.bot.mongo_database.update_many(
                    "data",
                    "invitationals",
                    docs_to_update,
                    {"$push": {"voters": member.id}},
                )

            # Format output
            result_string = ""
            for tourney in need_to_update:
                result_string += f"`{tourney.official_name}` - I added your vote! This tourney now has {len(tourney.voters)} votes!\n"
            for tourney in already_voted_for:
                result_string += f"`{tourney.official_name}` - You already voted for this channel! This channel has {len(tourney.voters)} votes!\n"

            # Send output
            result_string = result_string[:-1]  # Delete last newline character
            await interaction.response.send_message(result_string, ephemeral=True)


class TournamentDropdownView(discord.ui.View):
    def __init__(self, month_tournaments, bot, voting=False):
        super().__init__(timeout=None)
        self.voting = voting
        self.add_item(TournamentDropdown(month_tournaments, bot, voting=self.voting))


async def update_tournament_list(bot: PiBot, rename_dict: dict = {}) -> None:
    """
    Update the list of invitationals in #invitationals.

    :param rename_dict: A dictionary containing renames of channels and roles that need to be completed.
    """
    # Fetch invitationals
    invitationals = await bot.mongo_database.get_invitationals()
    invitationals = [Tournament(t) for t in invitationals]
    invitationals.sort(key=lambda t: t.official_name)

    # Update global invitational info
    global INVITATIONAL_INFO
    INVITATIONAL_INFO = invitationals

    # Get guild and channels
    server = bot.get_guild(SERVER_ID)
    assert isinstance(server, discord.Guild)

    tourney_channel = discord.utils.get(server.text_channels, name=CHANNEL_TOURNAMENTS)
    tournament_category = discord.utils.get(
        server.categories, name=CATEGORY_TOURNAMENTS
    )
    bot_spam_channel = discord.utils.get(server.text_channels, name=CHANNEL_BOTSPAM)
    server_support_channel = discord.utils.get(
        server.text_channels, name=CHANNEL_SUPPORT
    )
    assert isinstance(tourney_channel, discord.TextChannel)
    assert isinstance(tournament_category, discord.CategoryChannel)
    assert isinstance(bot_spam_channel, discord.TextChannel)
    assert isinstance(server_support_channel, discord.TextChannel)

    # Get roles
    global_moderator_role = discord.utils.get(server.roles, name=ROLE_GM)
    admin_role = discord.utils.get(server.roles, name=ROLE_AD)
    all_tournaments_role = discord.utils.get(server.roles, name=ROLE_AT)
    assert isinstance(global_moderator_role, discord.Role)
    assert isinstance(admin_role, discord.Role)
    assert isinstance(all_tournaments_role, discord.Role)

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

    for t in invitationals:  # For each tournament in the sheet
        channel = discord.utils.get(server.text_channels, name=t.channel_name)
        role = discord.utils.get(server.roles, name=t.official_name)

        tourney_date_str = str(t.tourney_date.date())
        after_days = int(t.closed_days)
        day_diff = (t.tourney_date - now).days

        print(
            f"Tournament List: Handling {t.official_name} (Day diff: {day_diff} days)"
        )

        if isinstance(channel, discord.TextChannel) and t.status == "archived":
            # Tournament channel should be archived
            channel_category = channel.category
            assert isinstance(channel_category, discord.CategoryChannel)

            if channel_category.name != CATEGORY_ARCHIVE:
                # If channel is not in category archive, then archive it
                archive_category = discord.utils.get(
                    server.categories, name=CATEGORY_ARCHIVE
                )
                competitions_channel = discord.utils.get(
                    server.text_channels, name=CHANNEL_COMPETITIONS
                )
                tournament_role = discord.utils.get(server.roles, name=t.official_name)

                # Type checking
                assert isinstance(archive_category, discord.CategoryChannel)
                assert isinstance(competitions_channel, discord.TextChannel)
                assert isinstance(tournament_role, discord.Role)

                embed = discord.Embed(
                    title="This channel is now archived.",
                    description=(
                        f"Thank you all for your discussion around the **{t.official_name}**. Now that we are well past the tournament date, we are going to close this channel to help keep tournament discussions relevant and on-topic.\n\n"
                        + f"If you have more questions/comments related to this tournament, you are welcome to bring them up in {competitions_channel.mention}. This channel is now read-only.\n\n"
                        + f"If you would like to no longer view this channel, you are welcome to remove the role using the dropdowns in {tourney_channel.mention}, and the channel will disappear for you. Members with the `All Tournaments` role will continue to see the channel."
                    ),
                    color=discord.Color.brand_red(),
                )

                # Send embed and update channel permissions
                await channel.set_permissions(
                    tournament_role, send_messages=False, view_channel=True
                )
                await channel.set_permissions(
                    all_tournaments_role, send_messages=False, view_channel=True
                )
                await channel.edit(category=archive_category, position=1000)
                await channel.send(embed=embed)

        if isinstance(channel, discord.TextChannel) and t.status == "open":
            # Type checking
            channel_category = channel.category
            assert isinstance(channel_category, discord.CategoryChannel)
            assert isinstance(role, discord.Role)

            if day_diff < -after_days:
                # If past tournament date, now out of range - make warning report to archive
                if channel_category.name != CATEGORY_ARCHIVE:
                    reporter_cog: Union[commands.Cog, Reporter] = bot.get_cog(
                        "Reporter"
                    )
                    await reporter_cog.create_invitational_archive_report(
                        t, channel, role
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
                    server.categories, name=CATEGORY_TOURNAMENTS
                )

            if len(to_change):
                await channel.edit(**to_change)

            # Fix permissions in case the channel was previously archived
            tourney_role_perms = channel.permissions_for(role)
            if (
                not tourney_role_perms.read_messages
                or not tourney_role_perms.send_messages
            ):
                await channel.set_permissions(
                    role, send_messages=True, read_messages=True
                )

            all_tourney_role_perms = channel.permissions_for(all_tournaments_role)
            if (
                not all_tourney_role_perms.read_messages
                or not all_tourney_role_perms.send_messages
            ):
                await channel.set_permissions(
                    all_tournaments_role, send_messages=True, read_messages=True
                )

        elif channel is None and t.status == "open":
            # If tournament needs to be created
            new_role = await server.create_role(name=t.official_name)
            new_channel = await server.create_text_channel(
                t.channel_name, category=tournament_category
            )

            await new_channel.edit(
                topic=f"{t.emoji} - Discussion around the {t.official_name} occurring on {tourney_date_str}.",
                sync_permissions=True,
            )
            await new_channel.set_permissions(new_role, read_messages=True)
            await new_channel.set_permissions(all_tournaments_role, read_messages=True)
            await new_channel.set_permissions(server.default_role, read_messages=False)

    help_embed = discord.Embed(
        title=":first_place: Join a Tournament Channel!",
        color=discord.Color(0x2E66B6),
        description=f"""
        Below is a list of **tournament channels**. Some are available right now, some will be available soon, and others have been requested, but have not received enough support to be considered for a channel.

        To join a tournament channel, use the dropdowns below! Dropdowns are split up by date!

        To request a new tournament channel, please use the `/request` command in {bot_spam_channel.mention}. If you need help, feel free to let a {admin_role.mention} or {global_moderator_role.mention} know!
        """,
    )
    await tourney_channel.purge()  # Delete all messages to make way for new messages/views
    await tourney_channel.send(embed=help_embed)

    assert isinstance(src.discord.globals.SETTINGS["invitational_season"], int)
    first_year = src.discord.globals.SETTINGS["invitational_season"] - 1
    second_year = src.discord.globals.SETTINGS["invitational_season"]
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
        month_tournaments = [
            t
            for t in invitationals
            if t.tourney_date.month == month["number"]
            and t.tourney_date.year == month["year"]
            and t.status == "open"
        ]
        if len(month_tournaments) > 0:
            await tourney_channel.send(
                f"Join a channel for a tournament in **{month['name']} {month['year']}**:",
                view=TournamentDropdownView(month_tournaments, bot),
            )
        else:
            # No tournaments in the given month :(
            if not month["optional"]:
                await tourney_channel.send(
                    f"Sorry, there are no channels opened for tournaments in **{month['name']} {month['year']}**."
                )

    voting_tournaments = [t for t in invitationals if t.status == "voting"]
    voting_embed = discord.Embed(
        title=":second_place: Vote for a Tournament Channel!",
        color=discord.Color(0x2E66B6),
        description="Below are tournament channels that are in the **voting phase**. These tournaments have been requested by users but have not received enough support to become official channels.\n\nIf you vote for these tournament channels to become official, you will automatically be added to these channels upon their creation.",
    )
    await tourney_channel.send(embed=voting_embed)
    if len(voting_tournaments):
        await tourney_channel.send(
            "Please choose from the requested tournaments below:",
            view=TournamentDropdownView(voting_tournaments, bot, voting=True),
        )
    else:
        await tourney_channel.send(
            "Sorry, there no invitationals are currently being voted on."
        )

    # Give user option to enable/disable visibility of all tournaments
    await tourney_channel.send(
        "Additionally, you can toggle visibility of all tournaments by using the button below:",
        view=AllTournamentsView(),
    )
