from __future__ import annotations

import asyncio
import contextlib
import datetime
import logging
import re
from typing import TYPE_CHECKING, Literal

import discord
import matplotlib.pyplot as plt
from beanie.odm.operators.update.general import Set
from discord import app_commands
from discord.ext import commands

import commandchecks
import src.discord.globals
from env import env
from src.discord.globals import (
    CATEGORY_GENERAL,
    CATEGORY_INVITATIONALS,
    CATEGORY_SO,
    CATEGORY_STATES,
    CHANNEL_WELCOME,
    EMOJI_LOADING,
    INVITATIONAL_INFO,
    ROLE_AD,
    ROLE_ALL_STATES,
    ROLE_AT,
    ROLE_BT,
    ROLE_GAMES,
    ROLE_GM,
    ROLE_MR,
    ROLE_MUTED,
    ROLE_QUARANTINE,
    ROLE_SELFMUTE,
    ROLE_STAFF,
    ROLE_UC,
    ROLE_VIP,
    ROLE_WM,
)
from src.discord.invitationals import update_invitational_list
from src.mongo.models import Cron, Ping, Settings
from src.wiki.mosteditstable import run_table

if TYPE_CHECKING:
    from bot import PiBot

    from .tasks import CronTasks


logger = logging.getLogger(__name__)


class SlowMode(app_commands.Group):
    def __init__(self, bot: PiBot):
        self.bot = bot
        super().__init__(
            name="slowmode",
            description="Manages slowmode for a channel.",
            default_permissions=discord.Permissions(manage_channels=True),
            guild_ids=env.slash_command_guilds,
        )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return commandchecks.is_staff_from_ctx(interaction, no_raise=True)

    @app_commands.command(
        name="set",
        description="Sets the slowmode for a particular channel.",
    )
    @app_commands.describe(
        delay="Optional. How long the slowmode delay should be, in seconds. If none, assumed to be 20 seconds.",
        channel="Optional. The channel to enable the slowmode in. If none, assumed in the current channel.",
    )
    async def slowmode_set(
        self,
        interaction,
        delay: int = 20,
        channel: discord.TextChannel = None,
    ):
        commandchecks.is_staff_from_ctx(interaction)

        channel = channel or interaction.channel
        await channel.edit(slowmode_delay=delay)
        await interaction.response.send_message(
            f"Enabled a slowmode delay of {delay} seconds.",
        )

    @app_commands.command(
        name="remove",
        description="Removes the slowmode set on a given channel.",
    )
    @app_commands.describe(
        channel="Optional. The channel to enable the slowmode in. If none, assumed in the current channel.",
    )
    async def slowmode_remove(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel = None,
    ):
        """
        Removes the slowmode set on a particular channel.
        """
        commandchecks.is_staff_from_ctx(interaction)

        channel = channel or interaction.channel
        await channel.edit(slowmode_delay=0)
        await interaction.response.send_message(
            f"Removed the slowmode delay in {channel.mention}.",
        )


class Confirm(discord.ui.View):
    def __init__(self, author, cancel_response):
        super().__init__()
        self.value = None
        self.author = author
        self.cancel_response = cancel_response

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.red)
    async def confirm(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        if interaction.user == self.author:
            await interaction.response.edit_message(
                content=f"{EMOJI_LOADING} Attempting to run operation...",
            )
            self.value = True
            self.interaction = interaction
            self.stop()
        else:
            await interaction.response.send_message(
                "Sorry, you are not the original staff member who called this method.",
                ephemeral=True,
            )

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.grey)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user == self.author:
            await interaction.response.edit_message(
                content=self.cancel_response,
                embed=None,
                view=None,
            )
            self.value = False
            self.stop()
        else:
            await interaction.response.send_message(
                "Sorry, you are not the original staff member who called this method.",
                ephemeral=True,
            )


class NukeStopButton(discord.ui.Button["Nuke"]):
    def __init__(self, nuke):
        super().__init__(label="ABORT", style=discord.ButtonStyle.danger)
        self.nuke = nuke

    async def callback(self, interaction: discord.Interaction):
        self.nuke.stopped = True
        self.style = discord.ButtonStyle.green
        self.label = "ABORTED"
        self.disabled = True
        await interaction.response.send_message(content="NUKE ABORTED, COMMANDER.")
        await interaction.edit_original_response(view=self.nuke)
        self.nuke.stop()


class Nuke(discord.ui.View):
    stopped = False

    def __init__(self):
        super().__init__()
        button = NukeStopButton(self)
        self.add_item(button)


class StaffCommands(commands.Cog):
    def __init__(self, bot: PiBot):
        self.bot = bot

    def time_str_to_datetime(self, time_string: str) -> datetime.datetime:
        times = {
            "10 minutes": discord.utils.utcnow() + datetime.timedelta(minutes=10),
            "30 minutes": discord.utils.utcnow() + datetime.timedelta(minutes=30),
            "1 hour": discord.utils.utcnow() + datetime.timedelta(hours=1),
            "2 hours": discord.utils.utcnow() + datetime.timedelta(hours=2),
            "4 hours": discord.utils.utcnow() + datetime.timedelta(hours=4),
            "8 hours": discord.utils.utcnow() + datetime.timedelta(hours=8),
            "1 day": discord.utils.utcnow() + datetime.timedelta(days=1),
            "4 days": discord.utils.utcnow() + datetime.timedelta(days=4),
            "7 days": discord.utils.utcnow() + datetime.timedelta(days=7),
            "1 month": discord.utils.utcnow() + datetime.timedelta(days=30),
            "1 year": discord.utils.utcnow() + datetime.timedelta(days=365),
        }
        return times[time_string]


class CronConfirm(discord.ui.View):
    def __init__(self, doc: Cron, bot: PiBot):
        super().__init__()
        self.doc = doc
        self.bot = bot

    @discord.ui.button(label="Remove", style=discord.ButtonStyle.danger)
    async def remove_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await self.doc.delete()
        await interaction.response.edit_message(
            content="Awesome! I successfully removed the action from the CRON list.",
            view=None,
        )

    @discord.ui.button(label="Complete Now", style=discord.ButtonStyle.green)
    async def complete_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        server = self.bot.get_guild(env.server_id)
        if self.doc.type == "UNBAN":
            # User needs to be unbanned
            with contextlib.suppress(Exception):
                await server.unban(self.doc.user)
            await interaction.response.edit_message(
                content="Attempted to unban the user. Checking to see if operation was successful...",
                view=None,
            )
            bans = [b async for b in server.bans()]
            for ban in bans:
                if ban.user.id == self.doc.user:
                    return await interaction.edit_original_response(
                        content="Uh oh! The operation was not successful - the user remains banned.",
                    )
            await self.doc.delete()
            return await interaction.edit_original_response(
                content="The operation was verified - the user can now rejoin the server.",
            )
        elif self.doc.type == "UNMUTE":
            # User needs to be unmuted.
            member = server.get_member(self.doc.user)
            if member is None:
                return await interaction.response.edit_message(
                    content="The user is no longer in the server, so I was not able to unmute them. The task remains "
                    "in the CRON list in case the user rejoins the server.",
                    view=None,
                )
            else:
                role = discord.utils.get(server.roles, name=ROLE_MUTED)
                with contextlib.suppress(Exception):
                    await member.remove_roles(role)
                await interaction.response.edit_message(
                    content="Attempted to unmute the user. Checking to see if the operation was successful...",
                    view=None,
                )
                if role not in member.roles:
                    await self.doc.delete()
                    return await interaction.edit_original_response(
                        content="The operation was verified - the user can now speak in the server again.",
                    )
                else:
                    return await interaction.edit_original_response(
                        content="Uh oh! The operation was not successful - the user is still muted.",
                    )


class CronSelect(discord.ui.Select):
    def __init__(self, docs: list[Cron], bot: PiBot):
        options = []
        docs.sort(key=lambda d: d.time)
        counts = {}
        for doc in docs[:20]:  # FIXME: Magic number
            timeframe = (doc.time - discord.utils.utcnow()).days
            if abs(timeframe) < 1:
                timeframe = f"{(doc.time - discord.utils.utcnow()).total_seconds() // 3600} hours"
            else:
                timeframe = f"{(doc.time - discord.utils.utcnow()).days} days"
            tag_name = f"{doc.cron_type.title()} {doc.tag}"
            if tag_name in counts:
                counts[tag_name] = counts[tag_name] + 1
            else:
                counts[tag_name] = 1
            if counts[tag_name] > 1:
                tag_name = f"{tag_name} (#{counts[tag_name]})"
            option = discord.SelectOption(
                label=tag_name,
                description=f"Occurs in {timeframe}.",
            )
            options.append(option)

        super().__init__(
            placeholder="View potential actions to modify...",
            min_values=1,
            max_values=1,
            options=options,
        )
        self.docs = docs
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        value = self.values[0]
        num = re.findall(r"\(#(\d*)", value)
        value = re.sub(r" \(#\d*\)", "", value)
        relevant_doc = [
            d for d in self.docs if f"{d.cron_type.title()} {d.tag}" == value
        ]
        if len(relevant_doc) == 1 or not len(num):
            relevant_doc = relevant_doc[0]
        else:
            num = num[0]
            relevant_doc = relevant_doc[int(num) - 1]
        view = CronConfirm(relevant_doc, self.bot)
        await interaction.response.edit_message(
            content=f"Okay! What would you like me to do with this CRON item?\n> {self.values[0]}",
            view=view,
            embed=None,
        )


class CronView(discord.ui.View):
    def __init__(self, docs: list[Cron], bot: PiBot):
        super().__init__()

        self.add_item(CronSelect(docs, bot))


class StaffEssential(StaffCommands):
    def __init__(self, bot: PiBot):
        super().__init__(bot)
        self.__cog_app_commands__.append(
            SlowMode(bot),
        )  # Manually add the slowmode group to this cog
        self.confirm_ctx_menu = app_commands.ContextMenu(
            name="Confirm User",
            callback=self.confirm_user,
        )
        self.bot.tree.add_command(self.confirm_ctx_menu)

    async def _confirm_core(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        member: discord.Member,
    ) -> bool:
        """
        Core method responsible for confirming users. Called by /confirm and the
        'Confirm User' user command.

        Args:
            interaction (discord.ApplicationContext): The context relevant to confirming
              the user.
            channel (discord.TextChannel): The #welcome channel.
            member (discord.Member): The member to confirm.

        Returns:
            bool: Whether the member was successfully confirmed.
        """
        if member.bot:
            await interaction.edit_original_response(
                content=":x: You can't confirm a bot!",
            )
            return False

        role1 = discord.utils.get(member.guild.roles, name=ROLE_UC)
        role2 = discord.utils.get(member.guild.roles, name=ROLE_MR)

        if role2 in member.roles:
            await interaction.edit_original_response(
                content=":x: This user is already confirmed.",
            )
            return False

        await member.remove_roles(role1)
        await member.add_roles(role2)
        await channel.purge(
            check=lambda m: (
                (m.author.bot and not m.embeds and not m.pinned)
                or (m.author == member and not m.embeds)
                or (member in m.mentions)
            ),
        )  # Assuming first message is pinned (usually is in several cases)
        return True

    @app_commands.command(
        description="Staff command. Confirms a user, giving them access to the server.",
    )
    @app_commands.checks.has_any_role(ROLE_STAFF, ROLE_VIP)
    @app_commands.default_permissions(manage_roles=True)
    @app_commands.guilds(*env.slash_command_guilds)
    @app_commands.describe(member="The member to confirm.")
    async def confirm(self, interaction: discord.Interaction, member: discord.Member):
        """Allows a staff member to confirm a user."""
        channel = interaction.channel
        if channel.name != CHANNEL_WELCOME:
            return await interaction.response.send_message(
                "Sorry! Please confirm the member in the welcoming channel!",
                ephemeral=True,
            )

        # Confirm member
        await interaction.response.send_message(
            f"{EMOJI_LOADING} Switching roles and cleaning up messages...",
        )
        assert isinstance(channel, discord.TextChannel)
        response = await self._confirm_core(interaction, channel, member)

        # Sends confirmation message
        if response:
            await interaction.edit_original_response(
                content=f":white_check_mark: Alrighty, confirmed {member.mention}. They now have access to see other "
                f"channels and send messages in them. :tada: ",
            )

    @app_commands.checks.has_any_role(ROLE_STAFF, ROLE_VIP)
    @app_commands.default_permissions(manage_roles=True)
    @app_commands.guilds(*env.slash_command_guilds)
    async def confirm_user(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
    ):
        # Confirm member
        channel = discord.utils.get(member.guild.text_channels, name=CHANNEL_WELCOME)
        await interaction.response.send_message(
            f"{EMOJI_LOADING} Switching roles and cleaning up messages...",
            ephemeral=True,
        )
        response = await self._confirm_core(interaction, channel, member)

        # Send confirmation message
        if response:
            await interaction.edit_original_response(
                content=f":white_check_mark: Alrighty, confirmed {member.mention}. They now have access to see other "
                f"channels and send messages in them. :tada: ",
            )

    @app_commands.command(
        description="Staff command. Nukes a certain amount of messages.",
    )
    @app_commands.checks.has_any_role(ROLE_STAFF, ROLE_VIP)
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(count="The amount of messages to nuke.")
    @app_commands.guilds(*env.slash_command_guilds)
    async def nuke(self, interaction, count: app_commands.Range[int, 1, 100]):
        """
        Nukes (deletes) a specified amount of messages in a channel.
        """
        # Verify the calling user is staff
        commandchecks.is_staff_from_ctx(interaction)

        channel = interaction.channel

        original_shown_embed = discord.Embed(
            title="NUKE COMMAND PANEL",
            color=discord.Color.brand_red(),
            description=f"""
            {count} messages will be deleted from {channel.mention} in 10 seconds...

            To stop this nuke, press the red button below!
            """,
        )
        view = Nuke()
        await interaction.response.send_message(embed=original_shown_embed, view=view)
        await asyncio.sleep(1)

        # Show user countdown for nuke
        for i in range(9, 0, -1):
            original_shown_embed.description = f"""
            {count} messages will be deleted from {channel.mention} in {i} seconds...

            To stop this nuke, press the red button below!
            """
            await interaction.edit_original_response(
                embed=original_shown_embed,
                view=view,
            )
            if view.stopped:
                return
            await asyncio.sleep(1)

        # Delete relevant messages
        original_shown_embed.description = f"""
        Now nuking {count} messages from the channel...
        """
        await interaction.edit_original_response(embed=original_shown_embed, view=None)

        def nuke_check(msg: discord.Message):
            return not len(msg.components) and not msg.pinned

        await interaction.original_message()
        await channel.purge(limit=count + 1, check=nuke_check)

    @app_commands.command(description="Staff command. Kicks user from the server.")
    @app_commands.checks.has_any_role(ROLE_STAFF, ROLE_VIP)
    @app_commands.default_permissions(kick_members=True)
    @app_commands.guilds(*env.slash_command_guilds)
    @app_commands.describe(
        member="The user to kick from the server.",
        reason="The reason to kick the member for.",
        quiet="Whether to DM the user that they have been kicked. Defaults to no.",
    )
    async def kick(
        self,
        interaction,
        member: discord.Member,
        reason: str,
        quiet: Literal["yes", "no"] = "no",
    ):
        """Kicks a member for the specified reason."""
        # Verify the caller is a staff member.
        commandchecks.is_staff_from_ctx(interaction)

        # Send confirmation message to staff member.
        original_shown_embed = discord.Embed(
            title="Kick Confirmation",
            color=discord.Color.brand_red(),
            description=f"""
            The member {member.mention} will be kicked from the server for:
            `{reason}`

            {
            "The member will not be notified of being kicked."
            if quiet == "yes" else
            "The member will be notified upon kick with the reason listed above."
            }

            **Staff Member:** {interaction.user.mention}
            """,
        )

        view = Confirm(
            interaction.user,
            "The kick operation was cancelled. The user remains in the server.",
        )
        await interaction.response.send_message(
            "Please confirm that you would like to kick this member from the server.",
            embed=original_shown_embed,
            view=view,
            ephemeral=True,
        )
        await view.wait()

        # Handle response
        if view.value:
            try:
                if quiet == "no":
                    alert_embed = discord.Embed(
                        title="You have been kicked from the Scioly.org server.",
                        color=discord.Color.brand_red(),
                        description=f"""
                        You have been removed from the Scioly.org server, due to the following reason: `{reason}`

                        If you have any concerns about your kick, you may contact a staff member. Please note that repeated violations may result in an account ban, IP ban, or other further action.
                        """,
                    )
                    await member.send(
                        "Notice from the Scioly.org server:",
                        embed=alert_embed,
                    )
                await member.kick(reason=reason)
            except Exception:
                pass

        # Verify that the member was kicked.
        guild = interaction.user.guild
        if member not in guild.members:
            # User was successfully kicked
            await interaction.edit_original_response(
                content="The user was successfully kicked.",
                embed=None,
                view=None,
            )
        else:
            await interaction.edit_original_response(
                content="The user was not successfully kicked because of an error. They remain in the server.",
                embed=None,
                view=None,
            )

    @app_commands.command(
        description="Staff command. Unmutes a user immediately.",
    )
    @app_commands.checks.has_any_role(ROLE_STAFF, ROLE_VIP)
    @app_commands.default_permissions(manage_roles=True)
    @app_commands.guilds(*env.slash_command_guilds)
    @app_commands.describe(member="The user to unmute.")
    async def unmute(self, interaction: discord.Interaction, member: discord.Member):
        """Unmutes a user."""
        # Check caller is staff
        commandchecks.is_staff_from_ctx(interaction)

        role = discord.utils.get(member.guild.roles, name=ROLE_MUTED)
        if role not in member.roles:
            return await interaction.response.send_message(
                "The user can't be unmuted because they aren't currently muted.",
            )

        # Send confirmation to staff
        original_shown_embed = discord.Embed(
            title="Unmute Confirmation",
            color=discord.Color.brand_red(),
            description=f"""
            {member.mention} will be unmuted across the entire server. This will enable the user to message again in all channels they can access.

            **Staff Member:** {interaction.user.mention}
            """,
        )

        view = Confirm(
            interaction.user,
            "The unmute operation was cancelled. The user remains muted.",
        )
        await interaction.response.send_message(
            "Please confirm that you would like to unmute this user.",
            view=view,
            embed=original_shown_embed,
            ephemeral=True,
        )
        await view.wait()

        # Handle response
        if view.value:
            try:
                await member.remove_roles(role)
            except Exception:
                logger.exception("Unable to remove the Muted role from a given user.")

        # Test user was unmuted
        if role not in member.roles:
            await interaction.edit_original_response(
                content="The user was successfully unmuted.",
                embed=None,
                view=None,
            )
        else:
            await interaction.edit_original_response(
                content="The user was not unmuted because of an error. They remain muted. Please contact a bot "
                "developer about this issue.",
                embed=None,
                view=None,
            )

    @app_commands.command(
        description="Staff command. Bans a user from the server.",
    )
    @app_commands.checks.has_any_role(ROLE_STAFF, ROLE_VIP)
    @app_commands.default_permissions(ban_members=True)
    @app_commands.guilds(*env.slash_command_guilds)
    @app_commands.describe(
        member="The user to ban.",
        reason="The reason to ban the user for.",
        ban_length="How long to ban the user for.",
        quiet="Avoids sending an informative DM to the user upon their ban. Defaults to no (default sends the DM).",
        delete_days="The days worth of messages to delete from this user. Defaults to 0.",
    )
    async def ban(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str,
        ban_length: Literal[
            "10 minutes",
            "30 minutes",
            "1 hour",
            "2 hours",
            "8 hours",
            "1 day",
            "4 days",
            "7 days",
            "1 month",
            "1 year",
            "Indefinitely",
        ],
        quiet: Literal["yes", "no"] = "no",
        delete_days: app_commands.Range[int, 0, 7] = 0,
    ):
        """Bans a user."""
        # Check for staff permissions
        commandchecks.is_staff_from_ctx(interaction)

        # Get selected time
        selected_time = self.time_str_to_datetime(ban_length)

        # Generate time statement
        time_statement = None
        if ban_length == "Indefinitely":
            time_statement = f"{member.mention} will never be automatically unbanned."
        else:
            time_statement = f"{member.mention} will be banned until {discord.utils.format_dt(selected_time)}."

        # Create confirmation embed to show to staff member
        original_shown_embed = discord.Embed(
            title="Ban Confirmation",
            color=discord.Color.brand_red(),
            description=f"""
            {member.mention} will be banned from the entire server. They will not be able to re-enter the server until the ban is lifted or the time expires. {delete_days} days worth of this users' messages will be deleted upon banning.

            {time_statement}
            """,
        )

        # Show view to staff member
        view = Confirm(
            interaction.user,
            "The ban operation was cancelled. They remain in the server.",
        )
        await interaction.response.send_message(
            "Please confirm that you would like to ban this user.",
            view=view,
            embed=original_shown_embed,
            ephemeral=True,
        )

        await view.wait()
        # If staff member selects yes
        if view.value:
            try:
                # If not quiet, generate embed to send to member
                if quiet == "no":
                    alert_embed = discord.Embed(
                        title="You have been banned from the Scioly.org server.",
                        color=discord.Color.brand_red(),
                        description=f"""
                        You have been {"permanently" if ban_length == "Indefinitely" else "temporarily"} banned from the Scioly.org server, due to the following reason: `{reason}`

                        If you have any concerns about your ban, you may contact a staff member through the Scioly.org website. Please note that repeated violations may result in an IP ban or other further action. Thank you!
                        """,
                    )
                    await member.send(
                        "Notice from the Scioly.org server:",
                        embed=alert_embed,
                    )

                # Ban member
                await interaction.guild.ban(
                    member,
                    reason=reason,
                    delete_message_days=delete_days,
                )
            except Exception:
                pass

        if ban_length != "Indefinitely":
            cron_tasks_cog = self.bot.get_cog("CronTasks")
            await cron_tasks_cog.schedule_unban(member, selected_time)

        # Test
        guild = interaction.user.guild
        if member not in guild.members:
            # User was successfully banned
            await interaction.edit_original_response(
                content="The user was successfully banned.",
                embed=None,
                view=None,
            )
        else:
            await interaction.edit_original_response(
                content="The user was not successfully banned because of an error. They remain in the server.",
                embed=None,
                view=None,
            )

    @app_commands.command(description="Staff command. Mutes a user.")
    @app_commands.checks.has_any_role(ROLE_STAFF, ROLE_VIP)
    @app_commands.default_permissions(manage_roles=True)
    @app_commands.guilds(*env.slash_command_guilds)
    @app_commands.describe(
        member="The user to mute.",
        reason="The reason to mute the user.",
        mute_length="How long to mute the user for.",
        quiet="Does not DM the user upon mute. Defaults to no.",
    )
    async def mute(
        self,
        interaction,
        member: discord.Member,
        reason: str,
        mute_length: Literal[
            "10 minutes",
            "30 minutes",
            "1 hour",
            "2 hours",
            "8 hours",
            "1 day",
            "4 days",
            "7 days",
            "1 month",
            "1 year",
            "Indefinitely",
        ],
        quiet: Literal["yes", "no"] = "no",
    ):
        """
        Mutes a user.
        """
        commandchecks.is_staff_from_ctx(interaction)

        selected_time = self.time_str_to_datetime(mute_length)
        if mute_length == "Indefinitely":
            time_statement = "The user will never be automatically unmuted."
        else:
            time_statement = f"The user will be muted until {discord.utils.format_dt(selected_time)}."

        original_shown_embed = discord.Embed(
            title="Mute Confirmation",
            color=discord.Color.brand_red(),
            description=f"""
            {member.mention} will be muted across the entire server. The user will no longer be able to communicate in any channels they can read.
            {
            "The user will not be notified upon mute."
            if quiet == "no" else
            "The user will be notified upon mute."
            }

            {time_statement}
            """,
        )

        view = Confirm(
            interaction.user,
            "The mute operation was cancelled. They remain able to communicate.",
        )
        await interaction.response.send_message(
            "Please confirm that you would like to mute this user.",
            view=view,
            embed=original_shown_embed,
            ephemeral=True,
        )

        await view.wait()
        role = discord.utils.get(member.guild.roles, name=ROLE_MUTED)
        if view.value:
            try:
                if quiet == "no":
                    alert_embed = discord.Embed(
                        title="You have been muted in the Scioly.org server.",
                        color=discord.Color.brand_red(),
                        description=f"""
                        You have been {"permanently" if mute_length == "Indefinitely" else "temporarily"} muted from the Scioly.org server, due to the following reason: `{reason}`

                        If you have any concerns about your mute, you may contact a staff member through the Scioly.org website. Please note that repeated violations may result in a ban, IP ban, or other further action. Thank you!
                        """,
                    )
                    await member.send(
                        "Notice from the Scioly.org server:",
                        embed=alert_embed,
                    )
                await member.add_roles(role)
            except Exception:
                pass

        if mute_length != "Indefinitely":
            cron_tasks_cog: commands.Cog | CronTasks = self.bot.get_cog("CronTasks")
            await cron_tasks_cog.schedule_unmute(member, selected_time)

        # Test
        if role in member.roles:
            # User was successfully muted
            await interaction.edit_original_response(
                content="The user was successfully muted.",
                embed=None,
                view=None,
            )

    @app_commands.command(
        description="Staff command. Allows staff to manipulate the CRON list.",
    )
    @app_commands.checks.has_any_role(ROLE_STAFF, ROLE_VIP)
    @app_commands.default_permissions(manage_roles=True)
    @app_commands.guilds(*env.slash_command_guilds)
    async def cron(self, interaction: discord.Interaction):
        """
        Allows staff to manipulate the CRON list.

        Steps:
            1. Parse the cron list.
            2. Create relevant action rows.
            3. Perform steps as staff request.
        """
        commandchecks.is_staff_from_ctx(interaction)

        cron_list = await Cron.find_all().to_list()
        if not len(cron_list):
            return await interaction.response.send_message(
                "Unfortunately, there are no items in the CRON list to manage.",
            )

        cron_embed = discord.Embed(
            title="Managing the CRON list",
            color=discord.Color.blurple(),
            description="""
            Hello! Managing the CRON list gives you the power to change when or how Pi-Bot automatically executes commands.

            **Completing a task:** Do you want to instantly unmute a user who is scheduled to be unmuted later? Sure, select the CRON entry from the dropdown, and then select *"Complete Now"*!

            **Removing a task:** Want to completely remove a task so Pi-Bot will never execute it? No worries, select the CRON entry from the dropdown and select *"Remove"*!
            """,
        )

        await interaction.response.send_message(
            "See information below for how to manage the CRON list.",
            view=CronView(cron_list, self.bot),
            ephemeral=True,
            embed=cron_embed,
        )


class StaffNonessential(StaffCommands, name="StaffNonesntl"):
    def __init__(self, bot: PiBot):
        super().__init__(bot)

    @app_commands.command(
        description="Staff command. Opens a voice channel clone of a channel.",
    )
    @app_commands.checks.has_any_role(ROLE_STAFF, ROLE_VIP)
    @app_commands.default_permissions(manage_channels=True)
    @app_commands.guilds(*env.slash_command_guilds)
    async def vc(self, interaction: discord.Interaction):
        commandchecks.is_staff_from_ctx(interaction)

        server = interaction.user.guild
        if (
            interaction.channel.category
            and interaction.channel.category.name == CATEGORY_INVITATIONALS
        ):
            # Handle for tournament channels
            test_vc: discord.VoiceChannel | None = discord.utils.get(
                server.voice_channels,
                name=interaction.channel.name,
            )
            if not test_vc:
                # Voice channel needs to be opened
                await interaction.response.send_message(
                    f"{EMOJI_LOADING} Attempting to open a voice channel...",
                )
                new_vc = await server.create_voice_channel(
                    interaction.channel.name,
                    category=interaction.channel.category,
                )
                await new_vc.edit(sync_permissions=True)

                # Make the channel invisible to normal members and give permissions
                await new_vc.set_permissions(server.default_role, view_channel=False)
                for t in INVITATIONAL_INFO:
                    if interaction.channel.name == t[1]:
                        tourney_role = discord.utils.get(server.roles, name=t[0])
                        await new_vc.set_permissions(tourney_role, view_channel=True)
                        break

                # Give permissions to All Invitationals role
                at = discord.utils.get(server.roles, name=ROLE_AT)
                await new_vc.set_permissions(at, view_channel=True)

                return await interaction.edit_original_response(
                    content=f"Created a voice channel: {new_vc.mention}. **Please remember to follow the rules! "
                    f"No doxxing or cursing is allowed.** ",
                )
            else:
                # Voice channel needs to be closed
                await test_vc.delete()
                return await interaction.response.send_message(
                    "Closed the voice channel.",
                )

        elif (
            interaction.channel and interaction.channel.category.name == CATEGORY_STATES
        ):
            # Handle for state channels

            test_vc = discord.utils.get(
                server.voice_channels,
                name=interaction.channel.name,
            )
            if not test_vc:
                # Voice channel does not currently exist
                await interaction.response.send_message(
                    f"{EMOJI_LOADING} Attempting to open a voice channel...",
                )

                if len(interaction.channel.category.channels) == 50:
                    # Too many voice channels in the state category
                    # Let's move one state to the next category
                    new_cat = filter(lambda x: x.name == "states", server.categories)
                    new_cat = list(new_cat)
                    if len(new_cat) < 2:
                        return await interaction.response.send_message(
                            "Could not find alternate states channel to move overflowed channels to.",
                        )
                    else:
                        # Success, we found the other category
                        current_cat = interaction.channel.category
                        await current_cat.channels[-1].edit(
                            category=new_cat[1],
                            position=0,
                        )

                # Create new voice channel
                new_vc = await server.create_voice_channel(
                    interaction.channel.name,
                    category=interaction.channel.category,
                )
                await new_vc.edit(sync_permissions=True)
                await new_vc.set_permissions(server.default_role, view_channel=False)

                # Give various roles permissions
                muted_role = discord.utils.get(server.roles, name=ROLE_MUTED)
                all_states_role = discord.utils.get(server.roles, name=ROLE_ALL_STATES)
                self_muted_role = discord.utils.get(server.roles, name=ROLE_SELFMUTE)
                quarantine_role = discord.utils.get(server.roles, name=ROLE_QUARANTINE)

                # Get official state name to give permissions to role
                state_role_name = interaction.channel.name.replace("-", " ").title()
                if state_role_name == "California North":
                    state_role_name = "California (North)"
                elif state_role_name == "California South":
                    state_role_name = "California (South)"

                state_role = discord.utils.get(server.roles, name=state_role_name)

                await new_vc.set_permissions(muted_role, connect=False)
                await new_vc.set_permissions(self_muted_role, connect=False)
                await new_vc.set_permissions(quarantine_role, connect=False)
                await new_vc.set_permissions(
                    state_role,
                    view_channel=True,
                    connect=True,
                )
                await new_vc.set_permissions(
                    all_states_role,
                    view_channel=True,
                    connect=True,
                )

                return await interaction.edit_original_response(
                    content=f"Created a voice channel: {new_vc.mention}. **Please remember to follow the rules! "
                    "No doxxing or cursing is allowed.**",
                )
            else:
                # Voice channel needs to be closed
                await test_vc.delete()
                if len(interaction.channel.category.channels) == 49:
                    # If we had to move a channel out of category to make room, move it back
                    # Let's move one state to the next category
                    new_cat = filter(lambda x: x.name == "states", server.categories)
                    new_cat = list(new_cat)
                    if len(new_cat) < 2:
                        return await interaction.response.send_message(
                            "Could not find alternate states channel to move overflowed channels to.",
                        )
                    else:
                        # Success, we found the other category
                        current_cat = interaction.channel.category
                        await new_cat[1].channels[0].edit(
                            category=current_cat,
                            position=1000,
                        )

                return await interaction.response.send_message(
                    "Closed the voice channel.",
                )
        elif interaction.channel.name == "games":
            # Support for opening a voice channel for #games

            test_vc = discord.utils.get(server.voice_channels, name="games")
            if not test_vc:
                # Voice channel needs to be opened/doesn't exist already
                await interaction.response.send_message(
                    f"{EMOJI_LOADING} Attempting to open a voice channel...",
                )

                # Create a new voice channel
                new_vc = await server.create_voice_channel(
                    "games",
                    category=interaction.channel.category,
                )
                await new_vc.edit(sync_permissions=True)
                await new_vc.set_permissions(server.default_role, view_channel=False)

                # Give out various permissions
                games_role = discord.utils.get(server.roles, name=ROLE_GAMES)
                member_role = discord.utils.get(server.roles, name=ROLE_MR)
                await new_vc.set_permissions(games_role, view_channel=True)
                await new_vc.set_permissions(member_role, view_channel=False)

                return await interaction.edit_original_response(
                    content=f"Created a voice channel: {new_vc.mention}. **Please remember to follow the rules! "
                    "No doxxing or cursing is allowed.**",
                )
            else:
                # Voice channel needs to be closed
                await test_vc.delete()
                return await interaction.response.send_message(
                    "Closed the voice channel.",
                )
        else:
            return await interaction.response.send_message(
                "Apologies... voice channels can currently be opened for tournament channels and the games channel.",
            )

    @app_commands.command(
        description="Staff command. Finds a user by their ID.",
    )
    @app_commands.checks.has_any_role(ROLE_STAFF, ROLE_VIP)
    @app_commands.guilds(*env.slash_command_guilds)
    @app_commands.describe(iden="The ID to lookup.")
    async def userfromid(self, interaction: discord.Interaction, iden: str):
        """Mentions a user with the given ID."""
        commandchecks.is_staff_from_ctx(interaction)

        user = self.bot.get_user(int(iden))
        await interaction.response.send_message(user.mention, ephemeral=True)

    @app_commands.command(
        description="Staff command. Locks a channel, preventing members from sending messages.",
    )
    @app_commands.checks.has_any_role(ROLE_STAFF, ROLE_VIP)
    @app_commands.default_permissions(manage_channels=True)
    @app_commands.guilds(*env.slash_command_guilds)
    async def lock(self, interaction: discord.Interaction):
        """Locks a channel to Member access."""
        # Check permissions
        commandchecks.is_staff_from_ctx(interaction)
        await interaction.response.send_message(
            f"{EMOJI_LOADING} Attempting to lock channel...",
        )

        # Get variables
        member = interaction.user
        channel = interaction.channel

        # Check channel category
        if channel.category.name in ["beta", "staff", "Pi-Bot"]:
            return await interaction.edit_original_response(
                content="This command is not suitable for this channel because of its category.",
            )

        # Update permissions
        member_role = discord.utils.get(member.guild.roles, name=ROLE_MR)
        if channel.category.name == CATEGORY_STATES:
            await interaction.channel.set_permissions(
                member_role,
                add_reactions=False,
                send_messages=False,
            )
        else:
            await interaction.channel.set_permissions(
                member_role,
                add_reactions=False,
                send_messages=False,
                read_messages=True,
            )

        wiki_role = discord.utils.get(member.guild.roles, name=ROLE_WM)
        gm_role = discord.utils.get(member.guild.roles, name=ROLE_GM)
        admin_role = discord.utils.get(member.guild.roles, name=ROLE_AD)
        bot_role = discord.utils.get(member.guild.roles, name=ROLE_BT)
        await interaction.channel.set_permissions(
            wiki_role,
            add_reactions=True,
            send_messages=True,
            read_messages=True,
        )
        await interaction.channel.set_permissions(
            gm_role,
            add_reactions=True,
            send_messages=True,
            read_messages=True,
        )
        await interaction.channel.set_permissions(
            admin_role,
            add_reactions=True,
            send_messages=True,
            read_messages=True,
        )
        await interaction.channel.set_permissions(
            bot_role,
            add_reactions=True,
            send_messages=True,
            read_messages=True,
        )

        # Edit to final message
        await interaction.edit_original_response(
            content="Locked the channel to Member access.",
        )

    @app_commands.command(
        description="Staff command. Unlocks a channel, allowing members to speak after the channel was originally locked.",
    )
    @app_commands.default_permissions(manage_channels=True)
    @app_commands.checks.has_any_role(ROLE_STAFF, ROLE_VIP)
    @app_commands.guilds(*env.slash_command_guilds)
    async def unlock(self, interaction: discord.Interaction):
        """Unlocks a channel to Member access."""
        # Check permissions
        commandchecks.is_staff_from_ctx(interaction)
        await interaction.response.send_message(
            f"{EMOJI_LOADING} Attempting to unlock channel...",
        )

        # Get variable
        member = interaction.user
        channel = interaction.channel

        # Check channel category
        if channel.category.name in ["beta", "staff", "Pi-Bot"]:
            return await interaction.edit_original_response(
                content="This command is not suitable for this channel because of its category.",
            )

        # Update permissions
        if (
            channel.category.name == CATEGORY_SO
            or channel.category.name == CATEGORY_GENERAL
        ):
            await interaction.edit_original_response(
                content="Synced permissions with channel category.",
            )
            return await channel.edit(sync_permissions=True)

        member_role = discord.utils.get(member.guild.roles, name=ROLE_MR)
        if channel.category.name != CATEGORY_STATES:
            await interaction.channel.set_permissions(
                member_role,
                add_reactions=True,
                send_messages=True,
                read_messages=True,
            )
        else:
            await interaction.channel.set_permissions(
                member_role,
                add_reactions=True,
                send_messages=True,
            )

        wiki_role = discord.utils.get(member.guild.roles, name=ROLE_WM)
        gm_role = discord.utils.get(member.guild.roles, name=ROLE_GM)
        aRole = discord.utils.get(member.guild.roles, name=ROLE_AD)
        bRole = discord.utils.get(member.guild.roles, name=ROLE_BT)
        await interaction.channel.set_permissions(
            wiki_role,
            add_reactions=True,
            send_messages=True,
            read_messages=True,
        )
        await interaction.channel.set_permissions(
            gm_role,
            add_reactions=True,
            send_messages=True,
            read_messages=True,
        )
        await interaction.channel.set_permissions(
            aRole,
            add_reactions=True,
            send_messages=True,
            read_messages=True,
        )
        await interaction.channel.set_permissions(
            bRole,
            add_reactions=True,
            send_messages=True,
            read_messages=True,
        )

        # Edit to final message
        await interaction.edit_original_response(
            content="Unlocked the channel to Member access. Please check if permissions need to be synced.",
        )

    @app_commands.command(
        description="Staff command. Runs Pi-Bot's Most Edits Table wiki functionality.",
    )
    @app_commands.checks.has_any_role(ROLE_STAFF, ROLE_VIP)
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.guilds(*env.slash_command_guilds)
    async def met(self, interaction: discord.Interaction):
        """Runs Pi-Bot's Most Edits Table"""
        commandchecks.is_staff_from_ctx(interaction)

        await interaction.response.send_message(
            f"{EMOJI_LOADING} Generating the Most Edits Table...",
        )
        res = await run_table()
        names = [v["name"] for v in res]
        data = [v["increase"] for v in res]
        names = names[:10]
        data = data[:10]

        plt.figure()
        plt.bar(names, data, color="#2E66B6")
        plt.xlabel("Usernames")
        plt.xticks(rotation=90)
        plt.ylabel("Edits past week")
        plt.title("Top wiki editors for the past week!")
        plt.tight_layout()
        plt.savefig("met.png")
        plt.close()
        await interaction.edit_original_response(
            content=f"{EMOJI_LOADING} Generating graph...",
        )
        await asyncio.sleep(3)

        file = discord.File("met.png", filename="met.png")
        embed = discord.Embed(
            title="**Top wiki editors for the past week!**",
            description=(
                "Check out the past week's top wiki editors! "
                "Thank you all for your contributions to the wiki! :heart:\n\n"
                + f"`1st` - **{names[0]}** ({data[0]} edits)\n"
                + f"`2nd` - **{names[1]}** ({data[1]} edits)\n"
                + f"`3rd` - **{names[2]}** ({data[2]} edits)\n"
                + f"`4th` - **{names[3]}** ({data[3]} edits)\n"
                + f"`5th` - **{names[4]}** ({data[4]} edits)"
            ),
        )
        embed.set_image(url="attachment://met.png")
        await interaction.edit_original_response(
            content="The Most Edits Table for the week:",
            attachments=[file],
            embed=embed,
        )

    @app_commands.command(
        description="Staff command. Refreshes data from the bot's database.",
    )
    @app_commands.checks.has_any_role(ROLE_STAFF, ROLE_VIP)
    @app_commands.default_permissions(manage_webhooks=True)
    @app_commands.guilds(*env.slash_command_guilds)
    @app_commands.describe(system="The system to refresh.")
    async def refresh(
        self,
        interaction: discord.Interaction,
        system: Literal["all", "invitationals", "pings"],
    ):
        """Refreshes data from the sheet."""
        # Check for staff permissions again
        commandchecks.is_staff_from_ctx(interaction)

        # Send initial message...
        await interaction.response.send_message(
            f"{EMOJI_LOADING} Refreshing `{system}`...",
        )

        if system in ["all"]:
            await interaction.edit_original_response(
                content=f"{EMOJI_LOADING} Pulling all updated database information...",
            )
            tasks_cog: commands.Cog | CronTasks = self.bot.get_cog("CronTasks")
            await tasks_cog.pull_prev_info()

        if system in ["invitationals", "all"]:
            await interaction.edit_original_response(
                content=f"{EMOJI_LOADING} Updating the invitationals list.",
            )
            await update_invitational_list(self.bot)
            await interaction.edit_original_response(
                content=":white_check_mark: Updated the invitationals list.",
            )

        if system in ["pings", "all"]:
            await interaction.edit_original_response(
                content=f"{EMOJI_LOADING} Updating all users' pings.",
            )
            src.discord.globals.PING_INFO = Ping.find_all().to_list()
            await interaction.edit_original_response(
                content=":white_check_mark: Updated all users' pings.",
            )

    change_status_group = app_commands.Group(
        name="status",
        description="Updates the bot's status.",
        guild_ids=env.slash_command_guilds,
        default_permissions=discord.Permissions(manage_webhooks=True),
    )

    @change_status_group.command(
        name="set",
        description="Staff command. Sets Pi-Bot's status to a custom tagline.",
    )
    @app_commands.describe(
        activity="The activity the bot will be doing.",
        message="The message to display after the activity type in the bot's status, shown as bold text.",
        length="How long the status should remain before being auto-updated to a recurring status.",
    )
    @app_commands.checks.has_any_role(ROLE_STAFF, ROLE_VIP)
    @app_commands.default_permissions(manage_webhooks=True)
    async def change_status(
        self,
        interaction: discord.Interaction,
        activity: Literal["playing", "listening", "watching"],
        message: str,
        length: Literal[
            "10 minutes",
            "30 minutes",
            "1 hour",
            "2 hours",
            "8 hours",
            "1 day",
            "4 days",
            "7 days",
            "1 month",
            "1 year",
        ],
    ):
        # Check again to make sure caller is staff
        commandchecks.is_staff_from_ctx(interaction)

        # CRON functionality
        selected_time = self.time_str_to_datetime(length)

        # Change settings
        await self.bot.settings.update(
            Set(
                {
                    Settings.custom_bot_status_text: message,
                    Settings.custom_bot_status_type: activity,
                },
            ),
        )

        # Delete any relevant documents
        await Cron.find(Cron.cron_type == "REMOVE_STATUS").delete()

        # Insert time length into CRON
        cron_cog: commands.Cog | CronTasks = self.bot.get_cog("CronTasks")
        await cron_cog.schedule_status_remove(selected_time)

        # Update activity
        status_text = None
        if activity == "playing":
            await self.bot.change_presence(activity=discord.Game(name=message))
            status_text = f"Playing {message}"
        elif activity == "listening":
            await self.bot.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.listening,
                    name=message,
                ),
            )
            status_text = f"Listening to {message}"
        elif activity == "watching":
            await self.bot.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.watching,
                    name=message,
                ),
            )
            status_text = f"Watching {message}"

        await interaction.response.send_message(
            content=f"The status was updated to: `{status_text}`. This status will stay in effect until {discord.utils.format_dt(selected_time, 'F')}.",
        )

    @change_status_group.command(
        name="reset",
        description="Staff command. Resets Pi-Bot's status to a custom value.",
    )
    @app_commands.checks.has_any_role(ROLE_STAFF, ROLE_VIP)
    @app_commands.default_permissions(manage_webhooks=True)
    async def reset_status(self, interaction: discord.Interaction):
        # Reset status
        await interaction.response.send_message(
            f"{EMOJI_LOADING} Attempting to resetting status...",
        )

        await self.bot.settings.update(
            Set(
                {
                    Settings.custom_bot_status_text: None,
                    Settings.custom_bot_status_type: None,
                },
            ),
        )
        await interaction.edit_original_response(content="Reset the bot's status.")

        # Delete any relevant documents
        await Cron.find(Cron.cron_type == "REMOVE_STATUS").delete()

        # Reset bot status to regularly update
        cron_cog: commands.Cog | CronTasks = self.bot.get_cog("CronTasks")
        cron_cog.change_bot_status.restart()


async def setup(bot: PiBot):
    await bot.add_cog(StaffEssential(bot))
    await bot.add_cog(StaffNonessential(bot))
