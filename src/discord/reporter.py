from __future__ import annotations

import datetime
import json
from typing import TYPE_CHECKING, Union

import discord
from discord.ext import commands
from src.discord.globals import CHANNEL_CLOSED_REPORTS, SERVER_ID
from src.discord.tournaments import Tournament

if TYPE_CHECKING:
    from bot import PiBot

"""
Relevant views.
"""


class IgnoreButton(discord.ui.Button):
    """
    A button to mark the report as ignored.
    This causes the report message to be deleted, an informational message to be posted in closed-reports, and the report database to be updated
    """

    view = None

    def __init__(self, view):
        self.view = view
        super().__init__(
            style=discord.ButtonStyle.gray,
            label="Ignore",
            custom_id=f"{view.report_id}:ignore",
        )

    async def callback(self, interaction: discord.Interaction):
        # Delete the original report
        await interaction.message.delete()

        # Send an informational message about the report being ignored
        closed_reports = discord.utils.get(
            interaction.guild.text_channels, name="closed-reports"
        )
        if isinstance(self.view, InnapropriateUsername):
            await closed_reports.send(
                f"**Report was ignored** by {interaction.user.mention} - {self.view.member.mention} had the "
                f"inappropriate username `{self.view.offending_username}`, but the report was ignored. "
            )
        elif isinstance(self.view, InvitationalRequest):
            await closed_reports.send(
                f"**Report was ignored** by {interaction.user.mention} - {self.view.member.mention} requested adding "
                f"a invitational channel for `{self.view.invitational_name}`, but the report was ignored. "
            )

        # Update the report database
        # TODO


class CompletedButton(discord.ui.Button):
    """
    A button to mark a report as completed.
    """

    view = None

    def __init__(self, view):
        self.view = view
        super().__init__(
            style=discord.ButtonStyle.green,
            label="Mark as Completed",
            custom_id=f"{view.report_id}:mark_completed",
        )

    async def callback(self, interaction: discord.Interaction):
        # Delete the original message
        await interaction.message.delete()

        # Send an informational message about the report being updated
        closed_reports: discord.TextChannel = discord.utils.get(
            interaction.guild.text_channels, name="closed-reports"
        )
        await closed_reports.send(
            f"**Invitational channel request was fulfilled** by {interaction.user.mention} - {self.view.member.mention} requested adding a invitational channel for the `{self.view.invitational_name}`, and the request has been fulfilled."
        )

        # Update the report database
        # TODO


class ChangeInappropriateUsername(discord.ui.Button):
    """
    A button that changes the username of a user.
    This caues the report message to be deleted, an informational message to be posted in closed-reports, and the report database to be updated.
    """

    view = None

    def __init__(self, view):
        self.view = view
        super().__init__(
            style=discord.ButtonStyle.green,
            label="Change Username",
            custom_id=f"{view.report_id}:change_username",
        )

    async def callback(self, interaction: discord.Interaction):
        # Delete the original message
        await interaction.message.delete()

        # Check to make sure user is still in server before taking action
        member_still_here = self.view.member in self.view.member.guild.members

        # Send an informational message about the report being updated
        closed_reports = discord.utils.get(
            interaction.guild.text_channels, name="closed-reports"
        )
        if member_still_here:
            await closed_reports.send(
                f"**Member's username was changed** by {interaction.user.mention} - {self.view.member.mention} had the innapropriate username `{self.view.offending_username}`, and their username was changed to `boomilever`."
            )

            # Change the user's username
            await self.view.member.edit(nick="boomilever")

        else:
            await closed_reports.send(
                f"**Member's username was attempted to be changed** by {interaction.user.mention} - {self.view.member.mention} had the innapropriate username `{self.view.offending_username}`, and their username was attempted to be changed to `boomilever`, however, the user had left the server."
            )

        # Update the report database
        # TODO


class KickUserButton(discord.ui.Button):

    view = None

    def __init__(self, view):
        self.view = view
        super().__init__(
            style=discord.ButtonStyle.red,
            label="Kick User",
            custom_id=f"{view.report_id}:kick",
        )

    async def callback(self, interaction: discord.Interaction):
        # Delete the original message
        await interaction.message.delete()

        # Check to make sure user is still in server before taking action
        member_still_here = self.view.member in self.view.member.guild.members

        # Send an informational message about the report being updated
        closed_reports = discord.utils.get(
            interaction.guild.text_channels, name="closed-reports"
        )
        if member_still_here:
            await closed_reports.send(
                f"**Member was kicked** by {interaction.user.mention} - {self.view.member.mention} had the innapropriate username `{self.view.offending_username}`, and the user was kicked from the server."
            )

            # Kick the user
            await self.view.member.kick()

        else:
            await closed_reports.send(
                f"**Attemped to kick member* by {interaction.user.mention} - {self.view.member.mention} had the innapropriate username `{self.view.offending_username}` and a kick was attempted on the user, however, the user had left the server."
            )

        # Update the report database
        # TODO


class InvitationalArchiveButton(discord.ui.Button):

    view = None

    def __init__(self, view):
        self.view = view
        super().__init__(
            style=discord.ButtonStyle.red,
            label="Archive",
            custom_id=f"{view.report_id}:invy_archive",
        )

    async def callback(self, interaction: discord.Interaction):
        # Delete the original message
        await interaction.message.delete()

        # Update the tournaments database
        # TODO

        # Send an informational message about the report being updated
        closed_reports = discord.utils.get(
            interaction.guild.text_channels, name="closed-reports"
        )
        await closed_reports.send(
            f"**Invitational channel and role were archived** by {interaction.user.mention} - The {self.view.tournament_obj.official_name} was archived after being open for {self.view.tournament_obj.closed_days} after the tournament date on {discord.utils.format_dt(self.view.tournament_obj.tourney_date, 'D')}."
        )

        # Update the report database
        # TODO


class InvitationalExtendButton(discord.ui.Button):

    view = None

    def __init__(self, view):
        self.view = view
        super().__init__(
            style=discord.ButtonStyle.gray,
            label="Extend",
            custom_id=f"{view.report_id}:invy_extend",
        )

    async def callback(self, interaction: discord.Interaction):
        # Delete the original message
        await interaction.message.delete()

        # Update the tournaments database
        # TODO

        # Send an informational message about the report being updated
        closed_reports = discord.utils.get(
            interaction.guild.text_channels, name="closed-reports"
        )
        await closed_reports.send(
            f"**Invitational archive warning was extended** by {interaction.user.mention} - A warning about the {self.view.tournament_obj.official_name} channel being open too long was sent, but the warning was extended by 15 days. Users are still able to chat in the tournament channel."
        )

        # Update the report database
        # TODO


class InnapropriateUsername(discord.ui.View):

    member: discord.Member
    offending_username: str
    report_id: int

    def __init__(self, member: discord.Member, report_id: int, offending_username: str):
        self.member = member
        self.report_id = report_id
        self.offending_username = offending_username
        super().__init__(timeout=86400)  # Timeout after one day

        # Add relevant buttons
        super().add_item(IgnoreButton(self))
        super().add_item(ChangeInappropriateUsername(self))
        super().add_item(KickUserButton(self))


class InvitationalRequest(discord.ui.View):

    member: discord.Member
    report_id: int
    invitational_name: str

    def __init__(self, member: discord.Member, invitational_name: str, report_id: int):
        self.member = member
        self.report_id = report_id
        self.invitational_name = invitational_name
        super().__init__(timeout=86400)

        # Add relevant buttons
        super().add_item(IgnoreButton(self))
        super().add_item(CompletedButton(self))


class InvitationalArchive(discord.ui.View):

    report_id: int
    tournament_obj: Tournament
    channel: discord.TextChannel
    role: discord.Role

    def __init__(
        self,
        tournament_obj: Tournament,
        channel: discord.TextChannel,
        role: discord.Role,
        report_id: int,
    ):
        self.report_id = report_id
        self.tournament_obj = tournament_obj
        self.channel = channel
        self.role = role
        super().__init__(timeout=86400)

        # Add relevant buttons
        super().add_item(InvitationalArchiveButton(self))
        super().add_item(InvitationalExtendButton(self))


class Reporter(commands.Cog):
    def __init__(self, bot: PiBot):
        self.bot = bot
        print("Initialized Reporter cog.")

    async def create_staff_message(self, embed: discord.Embed):
        guild: discord.Guild = self.bot.get_guild(SERVER_ID)
        reports_channel: discord.TextChannel = discord.utils.get(
            guild.text_channels, name="reports"
        )
        await reports_channel.send(embed=embed)

    async def create_inappropriate_username_report(
        self, member: Union[discord.Member, discord.User], offending_username: str
    ):
        guild: discord.Guild = self.bot.get_guild(SERVER_ID)
        reports_channel: discord.TextChannel = discord.utils.get(
            guild.text_channels, name="reports"
        )

        # Turn User into Member - if not possible, ignore the report, as no action needs to be taken
        member = guild.get_member(member.id)
        if member is None:
            return

        # Assemble relevant embed
        embed = discord.Embed(
            title="Inappropriate Username Detected",
            color=discord.Color.brand_red(),
            description=f"""{member.mention} was found to have the offending username: `{offending_username}`.
            You can take some action by using the buttons below.
            """,
        )
        await reports_channel.send(
            embed=embed, view=InnapropriateUsername(member, 123, offending_username)
        )

    async def create_cron_task_report(self, task: dict):
        guild: discord.Guild = self.bot.get_guild(SERVER_ID)
        reports_channel: discord.TextChannel = discord.utils.get(
            guild.text_channels, name="reports"
        )

        # Serialize values
        task["_id"] = str(task["_id"])  # ObjectID is not serializable by default
        if "time" in task:
            task["time"] = datetime.datetime.strftime(
                task["time"], "%m/%d/%Y, %H:%M:%S"
            )  # datetime.datetime is not serializable by default

        # Assemble the embed
        embed = discord.Embed(
            title="Error with CRON Task",
            description=f"""
            There was an error with the following CRON task:
            ```python
            {json.dumps(task, indent = 4)}
            ```
            Because this likely a development error, no actions can immediately be taken. Please contact a developer to learn more.
            """,
            color=discord.Color.brand_red(),
        )
        await reports_channel.send(embed=embed)

    async def create_invitational_request_report(
        self, user: discord.Member, invitational_name: str
    ):
        guild: discord.Guild = self.bot.get_guild(SERVER_ID)
        reports_channel: discord.TextChannel = discord.utils.get(
            guild.text_channels, name="reports"
        )

        # Assemble the embed
        embed = discord.Embed(
            title="New Invitational Channel Request",
            description=f"""
            {user.mention} has requested adding a new invitational channel for: `{invitational_name}`.
            If this report is unhelpful (the invitational already exists, the report is spam), then please ignore this report.
            To proceed with adding the invitational channel, please use the `/invyadd` command.
            """,
            color=discord.Color.yellow(),
        )
        await reports_channel.send(
            embed=embed, view=InvitationalRequest(user, invitational_name, 123)
        )

    async def create_invitational_archive_report(
        self,
        tournament_obj: Tournament,
        channel: discord.TextChannel,
        role: discord.Role,
    ):
        guild: discord.Guild = self.bot.get_guild(SERVER_ID)
        reports_channel: discord.TextChannel = discord.utils.get(
            guild.text_channels, name="reports"
        )

        embed = discord.Embed(
            title="Invitational Channel Suggested to be Archived",
            description=f"""
            The `{tournament_obj.official_name}` occurred on {discord.utils.format_dt(tournament_obj.tourney_date, 'D')}. Because it has been {tournament_obj.closed_days} days since that date, the tournament channel should potentially be archived.
            Archiving tournaments helps to prevent spam in tournament channels where competitors may be looking for updates. If tournamnet events are still occurring (such as waiting on results or event notifications), consider extending this warning.
            """,
            color=discord.Color.orange(),
        )
        # TODO Fix report ID generation
        await reports_channel.send(
            embed=embed, view=InvitationalArchive(tournament_obj, channel, role, 123)
        )

    async def create_cron_unban_auto_notice(
        self, user: discord.User, is_present: bool, already_unbanned: bool = None
    ) -> None:
        """
        Creates a notice (as a closed report) that a user was automatically unbanned through CRON.
        :param user: The user to make the auto notice about.
        :param is_present: Whether the user was present in the server when the unbanning occurred.
        """
        guild = self.bot.get_guild(SERVER_ID)
        closed_reports_channel = discord.utils.get(
            guild.text_channels, name=CHANNEL_CLOSED_REPORTS
        )

        # Type checking
        assert isinstance(guild, discord.Guild)
        assert isinstance(closed_reports_channel, discord.TextChannel)

        if is_present:
            await closed_reports_channel.send(
                f"**Attempt to automatically unban user by CRON.** A previous timed ban set on {user.mention} expired, therefore CRON attempted to unban the user. However, the user is already in the server, and therefore the user has already been unbanned by a previous staff member. The user is now free to rejoin the server."
            )
        elif not is_present and not already_unbanned:
            await closed_reports_channel.send(
                f"**User was automatically unbanned by CRON.** A previous timed ban on {str(user)} expired, and therefore, CRON has unbanned the user. The user is free to join the server at any time."
            )
        elif not is_present and already_unbanned:
            await closed_reports_channel.send(
                f"**Attempt to automatically unban user by CRON.** A previous timed ban on {str(user)} expired, and therefore, CRON attempted to unban the user. However, the user was already unbanned. The user remains free to join the server at any time."
            )

    async def create_cron_unmute_auto_notice(
        self, user: Union[discord.Member, discord.User], is_present: bool
    ) -> None:
        """
        Creates a notice (as a closed report) that a user was automatically unmuted through CRON.
        :param user: The user to make the auto notice about.
        :param is_present: Whether the user was present in the server when the unmuting occurred.
        """
        guild = self.bot.get_guild(SERVER_ID)
        closed_reports_channel = discord.utils.get(
            guild.text_channels, name=CHANNEL_CLOSED_REPORTS
        )

        # Type checking
        assert isinstance(guild, discord.Guild)
        assert isinstance(closed_reports_channel, discord.TextChannel)

        if is_present:
            await closed_reports_channel.send(
                f"**User was automatically unmuted by CRON.** A previous timed mute set on {user.mention} expired, "
                f"therefore CRON unmuted the user. The user is now free to communicate in the server."
            )
        elif not is_present:
            await closed_reports_channel.send(
                f"**Attempt to automatically unmute user by CRON.** A previous timed mute on {str(user)} expired, "
                f"and therefore, CRON attempted to unmute the user. "
                f"However, because the user is no longer present in the server, no unmute could occur."
            )


async def setup(bot: PiBot):
    await bot.add_cog(Reporter(bot))
