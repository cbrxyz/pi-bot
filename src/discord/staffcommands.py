import os
import re
import json
import discord
import datetime
import asyncio
from discord.commands import slash_command
from discord.errors import NoEntryPointError

from discord.ext import commands
from discord.commands import Option, permissions
from discord.ext.commands.errors import NotOwner
from discord.types.embed import EmbedField
import commandchecks
from commandchecks import is_staff, is_launcher

import dateparser
import pytz
import webcolors

import src.discord.globals
from src.discord.globals import CENSOR, SLASH_COMMAND_GUILDS, INVITATIONAL_INFO, CHANNEL_BOTSPAM, CATEGORY_ARCHIVE, ROLE_AT, ROLE_MUTED, EMOJI_GUILDS, TAGS, EVENT_INFO, EMOJI_LOADING
from src.discord.globals import CATEGORY_SO, CATEGORY_GENERAL, ROLE_MR, CATEGORY_STATES, ROLE_WM, ROLE_GM, ROLE_AD, ROLE_BT
from src.discord.globals import PI_BOT_IDS, ROLE_EM, CHANNEL_TOURNAMENTS
from src.discord.globals import CATEGORY_TOURNAMENTS, ROLE_ALL_STATES, ROLE_SELFMUTE, ROLE_QUARANTINE, ROLE_GAMES
from src.discord.globals import SERVER_ID, CHANNEL_WELCOME, ROLE_UC, ROLE_LH, ROLE_STAFF, ROLE_VIP
from bot import listen_for_response

from src.wiki.mosteditstable import run_table
from src.mongo.mongo import get_cron, remove_doc, get_invitationals, insert, update, delete

from src.discord.views import YesNo

import matplotlib.pyplot as plt

from typing import Type

from src.discord.tournaments import INVITATIONAL_INFO, update_tournament_list

class Confirm(discord.ui.View):
    def __init__(self, author, cancel_response):
        super().__init__()
        self.value = None
        self.author = author
        self.cancel_response = cancel_response

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.red)
    async def confirm(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        if interaction.user == self.author:
            await interaction.response.edit_message(content=f"{EMOJI_LOADING} Attempting to run operation...")
            self.value = True
            self.interaction = interaction
            self.stop()
        else:
            await interaction.response.send_message("Sorry, you are not the original staff member who called this method.", ephemeral = True)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.grey)
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user == self.author:
            await interaction.response.send_message(self.cancel_response, ephemeral=True)
            self.value = False
            self.stop()
        else:
            await interaction.response.send_message("Sorry, you are not the original staff member who called this method.", ephemeral = True)

class NukeStopButton(discord.ui.Button["Nuke"]):

    def __init__(self, nuke):
        super().__init__(label = "ABORT", style = discord.ButtonStyle.danger)
        self.nuke = nuke

    async def callback(self, interaction: discord.Interaction):
        self.nuke.stopped = True
        self.style = discord.ButtonStyle.green
        self.label = "ABORTED"
        self.disabled = True
        await interaction.response.send_message(content = "NUKE ABORTED, COMMANDER.")
        await interaction.edit_original_message(view = self.nuke)
        self.nuke.stop()

class Nuke(discord.ui.View):

    stopped = False

    def __init__(self):
        super().__init__()
        button = NukeStopButton(self)
        self.add_item(button)

class StaffCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # overriding check function
    async def cog_check(self, ctx):
        return is_staff()

class CronConfirm(discord.ui.View):

    def __init__(self, doc, bot):
        super().__init__()
        self.doc = doc
        self.bot = bot

    @discord.ui.button(label = "Remove", style = discord.ButtonStyle.danger)
    async def remove_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        await remove_doc("data", "cron", self.doc["_id"])
        await interaction.response.edit_message(content = "Awesome! I successfully removed the action from the CRON list.", view = None)

    @discord.ui.button(label = "Complete Now", style = discord.ButtonStyle.green)
    async def complete_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        server = self.bot.get_guild(SERVER_ID)
        if self.doc["type"] == "UNBAN":
            # User needs to be unbanned
            try:
                await server.unban(self.doc["user"])
            except:
                pass
            await interaction.response.edit_message(content = "Attempted to unban the user. Checking to see if operation was succesful...", view = None)
            bans = await server.bans()
            for ban in bans:
                if ban.user.id == self.doc["user"]:
                    return await interaction.edit_original_message(content = "Uh oh! The operation was not succesful - the user remains banned.")
            await remove_doc("data", "cron", self.doc["_id"])
            return await interaction.edit_original_message(content = "The operation was verified - the user can now rejoin the server.")
        elif self.doc["type"] == "UNMUTE":
            # User needs to be unmuted.
            member = server.get_member(self.doc["user"])
            if member == None:
                return await interaction.response.edit_message(content = "The user is no longer in the server, so I was not able to unmute them. The task remains in the CRON list in case the user rejoins the server.", view = None)
            else:
                role = discord.utils.get(server.roles, name=ROLE_MUTED)
                try:
                    await member.remove_roles(role)
                except:
                    pass
                await interaction.response.edit_message(content = "Attempted to unmute the user. Checking to see if the operation was succesful...", view = None)
                if role not in member.roles:
                    await remove_doc("data", "cron", self.doc["_id"])
                    return await interaction.edit_original_message(content = "The operation was verified - the user can now speak in the server again.")
                else:
                    return await interaction.edit_original_message(content = "Uh oh! The operation was not successful - the user is still muted.")

class CronSelect(discord.ui.Select):

    def __init__(self, docs, bot):
        options = []
        docs.sort(key = lambda d: d['time'])
        print([d['time'] for d in docs])
        counts = {}
        for doc in docs[:20]:
            timeframe = (doc['time'] - discord.utils.utcnow()).days
            if abs(timeframe) < 1:
                timeframe = f"{(doc['time'] - discord.utils.utcnow()).total_seconds() // 3600} hours"
            else:
                timeframe = f"{(doc['time'] - discord.utils.utcnow()).days} days"
            tag_name = f"{doc['type'].title()} {doc['tag']}"
            if tag_name in counts:
                counts[tag_name] = counts[tag_name] + 1
            else:
                counts[tag_name] = 1
            if counts[tag_name] > 1:
                tag_name = f"{tag_name} (#{counts[tag_name]})"
            option = discord.SelectOption(
                label = tag_name,
                description = f"Occurs in {timeframe}."
            )
            options.append(option)

        super().__init__(
            placeholder = "View potential actions to modify...",
            min_values = 1,
            max_values = 1,
            options = options
        )
        self.docs = docs
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        value = self.values[0]
        num = re.findall(r'\(#(\d*)', value)
        value = re.sub(r' \(#\d*\)', '', value)
        relevant_doc = [d for d in self.docs if f"{d['type'].title()} {d['tag']}" == value]
        if len(relevant_doc) == 1:
            relevant_doc = relevant_doc[0]
        else:
            if not len(num):
                relevant_doc = relevant_doc[0]
            else:
                num = num[0]
                relevant_doc = relevant_doc[int(num) - 1]
        view = CronConfirm(relevant_doc, self.bot)
        await interaction.response.edit_message(content = f"Okay! What would you like me to do with this CRON item?\n> {self.values[0]}", view = view, embed = None)

class CronView(discord.ui.View):

    def __init__(self, docs, bot):
        super().__init__()

        self.add_item(CronSelect(docs, bot))

class StaffEssential(StaffCommands):
    def __init__(self, bot):
        super().__init__(bot)

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Staff command. Confirms a user, giving them access to the server."
    )
    @permissions.has_any_role(ROLE_STAFF, ROLE_VIP, guild_id = SERVER_ID)
    async def confirm(self,
                      ctx,
                      member: Option(discord.Member, "The member to confirm.")
                     ):
        """Allows a staff member to confirm a user."""
        channel = ctx.channel
        if channel.name != CHANNEL_WELCOME:
            return await ctx.interaction.response.send_message("Sorry! Please confirm the member in the welcoming channel!", ephemeral = True)

        await ctx.interaction.response.send_message(f"{EMOJI_LOADING} Switching roles and cleaning up messages...")
        role1 = discord.utils.get(member.guild.roles, name=ROLE_UC)
        role2 = discord.utils.get(member.guild.roles, name=ROLE_MR)
        await member.remove_roles(role1)
        await member.add_roles(role2)
        await channel.purge(check=lambda m: ((m.author.id in PI_BOT_IDS and not m.embeds and not m.pinned) or (m.author == member and not m.embeds) or (member in m.mentions))) # Assuming first message is pinned (usually is in several cases)
        await ctx.interaction.edit_original_message(content = f":white_check_mark: Alrighty, confirmed {member.mention}. They now have access to see other channels and send messages in them. :tada:")

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Staff command. Nukes a certain amount of messages."
    )
    @permissions.has_any_role(ROLE_STAFF, ROLE_VIP, guild_id = SERVER_ID)
    async def nuke(self,
        ctx,
        count: Option(int, "The amount of messages to nuke.", min_value = 1, max_value = 100)
    ):
        """
        Nukes (deletes) a specified amount of messages in a channel.
        """
        # Verify the calling user is staff
        commandchecks.is_staff_from_ctx(ctx)

        channel = ctx.channel

        original_shown_embed = discord.Embed(
            title = "NUKE COMMAND PANEL",
            color = discord.Color.brand_red(),
            description = f"""
            {count} messages will be deleted from {channel.mention} in 10 seconds...

            To stop this nuke, press the red button below!
            """
        )
        view = Nuke()
        await ctx.respond(embed = original_shown_embed, view = view)
        await asyncio.sleep(1)

        # Show user countdown for nuke
        for i in range(9, 0, -1):
            original_shown_embed.description = f"""
            {count} messages will be deleted from {channel.mention} in {i} seconds...

            To stop this nuke, press the red button below!
            """
            await ctx.interaction.edit_original_message(embed = original_shown_embed, view = view)
            if view.stopped:
                return
            await asyncio.sleep(1)

        # Delete relevant messages
        original_shown_embed.description = f"""
        Now nuking {count} messages from the channel...
        """
        await ctx.interaction.edit_original_message(embed = original_shown_embed, view = None)

        def nuke_check(msg: discord.Message):
            return not len(msg.components) and not msg.pinned

        await ctx.interaction.original_message()
        await channel.purge(limit = count + 1, check = nuke_check)

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Staff command. Kicks user from the server."
    )
    @permissions.has_any_role(ROLE_STAFF, ROLE_VIP, guild_id = SERVER_ID)
    async def kick(self,
                   ctx,
                   member: Option(discord.Member, "The user to kick from the server."),
                   reason: Option(str, "The reason to kick the member for."),
                   quiet: Option(str, "Whether to DM the user that they have been kicked. Defaults to no.", choices = ["yes", "no"], default = "no")
                  ):
        """Kicks a member for the specified reason."""
        # Verify the caller is a staff member.
        commandchecks.is_staff_from_ctx(ctx)

        # Send confirmation message to staff member.
        original_shown_embed = discord.Embed(
            title = "Kick Confirmation",
            color = discord.Color.brand_red(),
            description = f"""
            The member {member.mention} will be kicked from the server for:
            `{reason}`

            {
                "The member will not be notified of being kicked."
                if quiet == "yes" else
                "The member will be notified upon kick with the reason listed above."
            }

            **Staff Member:** {ctx.author.mention}
            """
        )

        view = Confirm(ctx.author, "The kick operation was cancelled. The user remains in the server.")
        await ctx.respond("Please confirm that you would like to kick this member from the server.", embed = original_shown_embed, view = view, ephemeral = True)
        await view.wait()

        # Handle response
        if view.value:
            try:
                if quiet == "no":
                    alert_embed = discord.Embed(
                        title = "You have been kicked from the Scioly.org server.",
                        color = discord.Color.brand_red(),
                        description = f"""
                        You have been removed from the Scioly.org server, due to the following reason: `{reason}`

                        If you have any concerns about your kick, you may contact a staff member. Please note that repeated violations may result in an account ban, IP ban, or other further action.
                        """
                    )
                    await member.send("Notice from the Scioly.org server:", embed = alert_embed)
                await member.kick(reason = reason)
            except:
                pass

        # Verify that the member was kicked.
        guild = ctx.author.guild
        if member not in guild.members:
            # User was successfully kicked
            await ctx.interaction.edit_original_message(content = "The user was successfully kicked.", embed = None, view = None)
        else:
            await ctx.interaction.edit_original_message(content = "The user was not successfully kicked because of an error. They remain in the server.", embed = None, view = None)

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Staff command. Unmutes a user immediately."
    )
    @permissions.has_any_role(ROLE_STAFF, ROLE_VIP, guild_id = SERVER_ID)
    async def unmute(self,
                     ctx,
                     member: Option(discord.Member, "The user to unmute.")
                    ):
        """Unmutes a user."""
        # Check caller is staff
        commandchecks.is_staff_from_ctx(ctx)

        role = discord.utils.get(member.guild.roles, name=ROLE_MUTED)
        if role not in member.roles:
            return await ctx.respond("The user can't be unmuted because they aren't currently muted.")

        # Send confirmation to staff
        original_shown_embed = discord.Embed(
            title = "Unmute Confirmation",
            color = discord.Color.brand_red(),
            description = f"""
            {member.mention} will be unmuted across the entire server. This will enable the user to message again in all channels they can access.

            **Staff Member:** {ctx.author.mention}
            """
        )

        view = Confirm(ctx.author, "The unmute operation was cancelled. The user remains muted.")
        await ctx.respond("Please confirm that you would like to unmute this user.", view = view, embed = original_shown_embed, ephemeral = True)
        await view.wait()

        # Handle response
        if view.value:
            try:
                await member.remove_roles(role)
            except:
                pass

        # Test user was unmuted
        if role not in member.roles:
            await ctx.interaction.edit_original_message(content = "The user was succesfully unmuted.", embed = None, view = None)
        else:
            await ctx.interaction.edit_original_message(content = "The user was not unmuted because of an error. They remain muted. Please contact a bot developer about this issue.", embed = None, view = None)

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Staff command. Bans a user from the server."
    )
    @permissions.has_any_role(ROLE_STAFF, ROLE_VIP, guild_id = SERVER_ID)
    async def ban(self,
                  ctx,
                  member: Option(discord.Member, "The user to ban."),
                  reason: Option(str, "The reason to ban the user for."),
                  ban_length: Option(str, "How long to ban the user for.", choices = [
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
                      "Indefinitely"
                  ]),
                  quiet: Option(str, "Avoids sending an informative DM to the user upon their ban. Defaults to no (default sends the DM).", choices = ["yes", "no"], default = "no", required = False),
                  delete_days: Option(int, "The days worth of messages to delete from this user. Defaults to 0.", min_value = 0, max_value = 7, default = 0)
                 ):
        """Bans a user."""
        commandchecks.is_staff_from_ctx(ctx)

        times = {
            "10 minutes": datetime.datetime.now() + datetime.timedelta(minutes=10),
            "30 minutes": datetime.datetime.now() + datetime.timedelta(minutes=30),
            "1 hour": datetime.datetime.now() + datetime.timedelta(hours=1),
            "2 hours": datetime.datetime.now() + datetime.timedelta(hours=2),
            "4 hours": datetime.datetime.now() + datetime.timedelta(hours=4),
            "8 hours": datetime.datetime.now() + datetime.timedelta(hours=8),
            "1 day": datetime.datetime.now() + datetime.timedelta(days=1),
            "4 days": datetime.datetime.now() + datetime.timedelta(days=4),
            "7 days": datetime.datetime.now() + datetime.timedelta(days=7),
            "1 month": datetime.datetime.now() + datetime.timedelta(days=30),
            "1 year": datetime.datetime.now() + datetime.timedelta(days=365),
        }
        time_statement = None
        if ban_length == "Indefinitely":
            time_statement = f"{member.mention} will never be automatically unbanned."
        else:
            time_statement = f"{member.mention} will be banned until {discord.utils.format_dt(times[ban_length], 'F')}."

        original_shown_embed = discord.Embed(
            title = "Ban Confirmation",
            color = discord.Color.brand_red(),
            description = f"""
            {member.mention} will be banned from the entire server. They will not be able to re-enter the server until the ban is lifted or the time expires. {delete_days} days worth of this users' messages will be deleted upon banning.

            {time_statement}
            """
        )

        view = Confirm(ctx.author, "The ban operation was cancelled. They remain in the server.")
        await ctx.respond("Please confirm that you would like to ban this user.", view = view, embed = original_shown_embed, ephemeral = True)

        await view.wait()
        if view.value:
            try:
                if quiet == "no":
                    alert_embed = discord.Embed(
                        title = "You have been banned from the Scioly.org server.",
                        color = discord.Color.brand_red(),
                        description = f"""
                        You have been {"permanently" if ban_length == "Indefinitely" else "temporarily"} banned from the Scioly.org server, due to the following reason: `{reason}`

                        If you have any concerns about your ban, you may contact a staff member through the Scioly.org website. Please note that repeated violations may result in an IP ban or other further action. Thank you!
                        """
                    )
                    await member.send("Notice from the Scioly.org server:", embed = alert_embed)
                await ctx.guild.ban(member, reason=reason)
            except:
                pass

        if ban_length != "Indefinitely":
            await insert("data", "cron", {"date": times[ban_length], "do": f"unban {member.id}"})

        # Test
        guild = ctx.author.guild
        if member not in guild.members:
            # User was successfully banned
            await ctx.interaction.edit_original_message(content = "The user was successfully banned.", embed = None, view = None)
        else:
            await ctx.interaction.edit_original_message(content = "The user was not successfully banned because of an error. They remain in the server.", embed = None, view = None)

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Staff command. Mutes a user."
    )
    @permissions.has_any_role(ROLE_STAFF, ROLE_VIP, guild_id = SERVER_ID)
    async def mute(self,
                   ctx,
                   member: Option(discord.Member, "The user to mute."),
                   reason: Option(str, "The reason to mute the user."),
                   mute_length: Option(str, "How long to mute the user for.", choices = [
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
                       "Indefinitely"
                   ]),
                   quiet: Option(str, "Does not DM the user upon mute. Defaults to no.", choices = ["yes", "no"], default = "no")
                  ):
        """
        Mutes a user.
        """
        commandchecks.is_staff_from_ctx(ctx)

        times = {
            "10 minutes": datetime.datetime.now() + datetime.timedelta(minutes=10),
            "30 minutes": datetime.datetime.now() + datetime.timedelta(minutes=30),
            "1 hour": datetime.datetime.now() + datetime.timedelta(hours=1),
            "2 hours": datetime.datetime.now() + datetime.timedelta(hours=2),
            "4 hours": datetime.datetime.now() + datetime.timedelta(hours=4),
            "8 hours": datetime.datetime.now() + datetime.timedelta(hours=8),
            "1 day": datetime.datetime.now() + datetime.timedelta(days=1),
            "4 days": datetime.datetime.now() + datetime.timedelta(days=4),
            "7 days": datetime.datetime.now() + datetime.timedelta(days=7),
            "1 month": datetime.datetime.now() + datetime.timedelta(days=30),
            "1 year": datetime.datetime.now() + datetime.timedelta(days=365),
        }
        time_statement = None
        if mute_length == "Indefinitely":
            time_statement = "The user will never be automatically unmuted."
        else:
            time_statement = f"The user will be muted until {discord.utils.format_dt(times[mute_length], 'F')}."

        original_shown_embed = discord.Embed(
            title = "Mute Confirmation",
            color = discord.Color.brand_red(),
            description = f"""
            {member.mention} will be muted across the entire server. The user will no longer be able to communicate in any channels they can read.
            {
                "The user will not be notified upon mute."
                if quiet == "no" else
                "The user will be notified upon mute."
            }

            {time_statement}
            """
        )

        view = Confirm(ctx.author, "The mute operation was cancelled. They remain able to communicate.")
        await ctx.respond("Please confirm that you would like to mute this user.", view = view, embed = original_shown_embed, ephemeral = True)

        await view.wait()
        role = discord.utils.get(member.guild.roles, name=ROLE_MUTED)
        if view.value:
            try:
                if quiet == "no":
                    alert_embed = discord.Embed(
                        title = "You have been muted in the Scioly.org server.",
                        color = discord.Color.brand_red(),
                        description = f"""
                        You have been {"permanently" if mute_length == "Indefinitely" else "temporarily"} muted from the Scioly.org server, due to the following reason: `{reason}`

                        If you have any concerns about your mute, you may contact a staff member through the Scioly.org website. Please note that repeated violations may result in a ban, IP ban, or other further action. Thank you!
                        """
                    )
                    await member.send("Notice from the Scioly.org server:", embed = alert_embed)
                await member.add_roles(role)
            except:
                pass

        if mute_length != "Indefinitely":
            await insert("data", "cron", {"date": times[mute_length], "do": f"unmute {member.id}"})

        # Test
        if role in member.roles:
            # User was successfully muted
            await ctx.interaction.edit_original_message(content = "The user was successfully muted.", embed = None, view = None)
        else:
            await ctx.interaction.edit_original_message(content = "The user was not successfully muted because of an error. They remain able to communicate.", embed = None, view = None)

    slowmode_group = discord.commands.SlashCommandGroup(
        "slowmode",
        "Manages slowmode for a channel.",
        guild_ids = [SLASH_COMMAND_GUILDS],
        permissions = [
            discord.commands.CommandPermission(ROLE_STAFF, 1, True),
            discord.commands.CommandPermission(ROLE_VIP, 1, True),
        ]
    )

    @slowmode_group.command(
        name = "set",
        description = "Sets the slowmode for a particular channel."
    )
    async def slowmode_set(self,
                           ctx,
                           delay: Option(int, "Optional. How long the slowmode delay should be, in seconds. If none, assumed to be 20 seconds.", required = False, default = 20),
                           channel: Option(discord.TextChannel, "Optional. The channel to enable the slowmode in. If none, assumed in the current channel.", required = False)
                          ):
        commandchecks.is_staff_from_ctx(ctx)

        channel = channel or ctx.channel
        await channel.edit(slowmode_delay = delay)
        await ctx.respond(f"Enabled a slowmode delay of {delay} seconds.")

    @slowmode_group.command(
        name = "remove",
        description = "Removes the slowmode set on a given channel."
    )
    async def slowmode_remove(self,
                           ctx,
                           channel: Option(discord.TextChannel, "Optional. The channel to enable the slowmode in. If none, assumed in the current channel.", required = False)
                          ):
        """
        Removes the slowmode set on a particular channel.
        """
        commandchecks.is_staff_from_ctx(ctx)

        channel = channel or ctx.channel
        await channel.edit(slowmode_delay = 0)
        await ctx.respond(f"Removed the slowmode delay in {channel.mention}.")

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Staff command. Allows staff to manipulate the CRON list."
    )
    @permissions.has_any_role(ROLE_STAFF, ROLE_VIP, guild_id = SERVER_ID)
    async def cron(self, ctx):
        """
        Allows staff to manipulate the CRON list.

        Steps:
            1. Parse the cron list.
            2. Create relevant action rows.
            3. Perform steps as staff request.
        """
        commandchecks.is_staff_from_ctx(ctx)

        cron_list = await get_cron()
        if not len(cron_list):
            return await ctx.respond(f"Unfortunately, there are no items in the CRON list to manage.")

        cron_embed = discord.Embed(
            title = "Managing the CRON list",
            color = discord.Color.blurple(),
            description = f"""
            Hello! Managing the CRON list gives you the power to change when or how Pi-Bot automatically executes commands.

            **Completing a task:** Do you want to instantly unmute a user who is scheduled to be unmuted later? Sure, select the CRON entry from the dropdown, and then select *"Complete Now"*!

            **Removing a task:** Want to completely remove a task so Pi-Bot will never execute it? No worries, select the CRON entry from the dropdown and select *"Remove"*!
            """
        )

        await ctx.respond("See information below for how to manage the CRON list.", view = CronView(cron_list, self.bot), ephemeral = True, embed = cron_embed)

class StaffNonessential(StaffCommands, name="StaffNonesntl"):
    def __init__(self, bot):
        super().__init__(bot)

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Staff command. Opens a voice channel clone of a channel."
    )
    @permissions.has_any_role(ROLE_STAFF, ROLE_VIP, guild_id = SERVER_ID)
    async def vc(self, ctx):
        commandchecks.is_staff_from_ctx(ctx)

        server = ctx.author.guild
        if ctx.channel.category != None and ctx.channel.category.name == CATEGORY_TOURNAMENTS:
            # Handle for tournament channels

            test_vc = discord.utils.get(server.voice_channels, name=ctx.channel.name)
            if not test_vc:
                # Voice channel needs to be opened
                await ctx.respond(f"{EMOJI_LOADING} Attempting to open a voice channel...")
                new_vc = await server.create_voice_channel(ctx.channel.name, category=ctx.channel.category)
                await new_vc.edit(sync_permissions=True)

                # Make the channel invisible to normal members and give permissions
                await new_vc.set_permissions(server.default_role, view_channel=False)
                for t in INVITATIONAL_INFO:
                    if ctx.channel.name == t[1]:
                        tourney_role = discord.utils.get(server.roles, name=t[0])
                        await new_vc.set_permissions(tourney_role, view_channel=True)
                        break

                # Give permissions to All Tournaments role
                at = discord.utils.get(server.roles, name=ROLE_AT)
                await new_vc.set_permissions(at, view_channel=True)

                return await ctx.interaction.edit_original_message(content = "Created a voice channel. **Please remember to follow the rules! No doxxing or cursing is allowed.**")
            else:
                # Voice channel needs to be closed
                await test_vc.delete()
                return await ctx.respond("Closed the voice channel.")

        elif ctx.channel != None and ctx.channel.category.name == CATEGORY_STATES:
            # Handle for state channels

            test_vc = discord.utils.get(server.voice_channels, name=ctx.channel.name)
            if not test_vc:
                # Voice channel does not currently exist
                await ctx.respond(f"{EMOJI_LOADING} Attempting to open a voice channel...")

                if len(ctx.channel.category.channels) == 50:
                    # Too many voice channels in the state category
                    # Let's move one state to the next category
                    new_cat = filter(lambda x: x.name == "states", server.categories)
                    new_cat = list(new_cat)
                    if len(new_cat) < 2:
                        return await ctx.respond("Could not find alternate states channel to move overflowed channels to.")
                    else:
                        # Success, we found the other category
                        current_cat = ctx.channel.category
                        await current_cat.channels[-1].edit(category = new_cat[1], position = 0)

                # Create new voice channel
                new_vc = await server.create_voice_channel(ctx.channel.name, category=ctx.channel.category)
                await new_vc.edit(sync_permissions=True)
                await new_vc.set_permissions(server.default_role, view_channel=False)

                # Give various roles permissions
                muted_role = discord.utils.get(server.roles, name=ROLE_MUTED)
                all_states_role = discord.utils.get(server.roles, name=ROLE_ALL_STATES)
                self_muted_role = discord.utils.get(server.roles, name=ROLE_SELFMUTE)
                quarantine_role = discord.utils.get(server.roles, name=ROLE_QUARANTINE)

                # Get official state name to give permissions to role
                state_role_name = ctx.channel.name.replace("-", " ").title()
                if state_role_name == "California North":
                    state_role_name = "California (North)"
                elif state_role_name == "California South":
                    state_role_name = "California (South)"

                state_role = discord.utils.get(server.roles, name = state_role_name)

                await new_vc.set_permissions(muted_role, connect=False)
                await new_vc.set_permissions(self_muted_role, connect=False)
                await new_vc.set_permissions(quarantine_role, connect=False)
                await new_vc.set_permissions(state_role, view_channel = True, connect=True)
                await new_vc.set_permissions(all_states_role, view_channel = True, connect=True)

                return await ctx.interaction.edit_original_message(content = "Created a voice channel. **Please remember to follow the rules! No doxxing or cursing is allowed.**")
            else:
                # Voice channel needs to be closed
                await test_vc.delete()
                if len(ctx.channel.category.channels) == 49:
                    # If we had to move a channel out of category to make room, move it back
                    # Let's move one state to the next category
                    new_cat = filter(lambda x: x.name == "states", server.categories)
                    new_cat = list(new_cat)
                    if len(new_cat) < 2:
                        return await ctx.respond("Could not find alternate states channel to move overflowed channels to.")
                    else:
                        # Success, we found the other category
                        current_cat = ctx.channel.category
                        await new_cat[1].channels[0].edit(category = current_cat, position = 1000)

                return await ctx.respond("Closed the voice channel.")
        elif ctx.channel.name == "games":
            # Support for opening a voice channel for #games

            test_vc = discord.utils.get(server.voice_channels, name="games")
            if not test_vc:
                # Voice channel needs to be opened/doesn't exist already
                await ctx.respond(f"{EMOJI_LOADING} Attempting to open a voice channel...")

                # Create a new voice channel
                new_vc = await server.create_voice_channel("games", category=ctx.channel.category)
                await new_vc.edit(sync_permissions=True)
                await new_vc.set_permissions(server.default_role, view_channel=False)

                # Give out various permissions
                games_role = discord.utils.get(server.roles, name=ROLE_GAMES)
                member_role = discord.utils.get(server.roles, name=ROLE_MR)
                await new_vc.set_permissions(games_role, view_channel=True)
                await new_vc.set_permissions(member_role, view_channel=False)

                return await ctx.interaction.edit_original_message(content = "Created a voice channel. **Please remember to follow the rules! No doxxing or cursing is allowed.**")
            else:
                # Voice channel needs to be closed
                await test_vc.delete()
                return await ctx.respond("Closed the voice channel.")
        else:
            return await ctx.respond("Apologies... voice channels can currently be opened for tournament channels and the games channel.")

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Staff command. Finds a user by their ID."
    )
    @permissions.has_any_role(ROLE_STAFF, ROLE_VIP, guild_id = SERVER_ID)
    async def userfromid(self,
        ctx,
        iden: Option(str, "The ID to lookup.")
    ):
        """Mentions a user with the given ID."""
        commandchecks.is_staff_from_ctx(ctx)

        user = self.bot.get_user(int(iden))
        await ctx.respond(user.mention, ephemeral = True)

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Staff command. Locks a channel, preventing members from sending messages."
    )
    @permissions.has_any_role(ROLE_STAFF, ROLE_VIP, guild_id = SERVER_ID)
    async def lock(self, ctx):
        """Locks a channel to Member access."""
        # Check permissions
        commandchecks.is_staff_from_ctx(ctx)
        await ctx.interaction.response.send_message(f"{EMOJI_LOADING} Attempting to lock channel...")

        # Get variables
        member = ctx.author
        channel = ctx.channel

        # Check channel category
        if (channel.category.name in ["beta", "staff", "Pi-Bot"]):
            return await ctx.interaction.edit_original_message(content = "This command is not suitable for this channel because of its category.")

        # Update permissions
        member_role = discord.utils.get(member.guild.roles, name=ROLE_MR)
        if (channel.category.name == CATEGORY_STATES):
            await ctx.channel.set_permissions(member_role, add_reactions=False, send_messages=False)
        else:
            await ctx.channel.set_permissions(member_role, add_reactions=False, send_messages=False, read_messages=True)

        wiki_role = discord.utils.get(member.guild.roles, name=ROLE_WM)
        gm_role = discord.utils.get(member.guild.roles, name=ROLE_GM)
        admin_role = discord.utils.get(member.guild.roles, name=ROLE_AD)
        bot_role = discord.utils.get(member.guild.roles, name=ROLE_BT)
        await ctx.channel.set_permissions(wiki_role, add_reactions=True, send_messages=True, read_messages=True)
        await ctx.channel.set_permissions(gm_role, add_reactions=True, send_messages=True, read_messages=True)
        await ctx.channel.set_permissions(admin_role, add_reactions=True, send_messages=True, read_messages=True)
        await ctx.channel.set_permissions(bot_role, add_reactions=True, send_messages=True, read_messages=True)

        # Edit to final message
        await ctx.interaction.edit_original_message(content = "Locked the channel to Member access.")

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Staff command. Unlocks a channel, allowing members to speak after the channel was originally locked."
    )
    @permissions.has_any_role(ROLE_STAFF, ROLE_VIP, guild_id = SERVER_ID)
    async def unlock(self, ctx):
        """Unlocks a channel to Member access."""
        # Check permissions
        commandchecks.is_staff_from_ctx(ctx)
        await ctx.interaction.response.send_message(f"{EMOJI_LOADING} Attempting to unlock channel...")

        # Get variable
        member = ctx.author
        channel = ctx.channel

        # Check channel category
        if (channel.category.name in ["beta", "staff", "Pi-Bot"]):
            return await ctx.interaction.edit_original_message(content = "This command is not suitable for this channel because of its category.")

        # Update permissions
        if (channel.category.name == CATEGORY_SO or channel.category.name == CATEGORY_GENERAL):
            await ctx.interaction.edit_original_message(content = "Synced permissions with channel category.")
            return await channel.edit(sync_permissions=True)

        member_role = discord.utils.get(member.guild.roles, name=ROLE_MR)
        if (channel.category.name != CATEGORY_STATES):
            await ctx.channel.set_permissions(member_role, add_reactions=True, send_messages=True, read_messages=True)
        else:
            await ctx.channel.set_permissions(member_role, add_reactions=True, send_messages=True)

        wiki_role = discord.utils.get(member.guild.roles, name=ROLE_WM)
        gm_role = discord.utils.get(member.guild.roles, name=ROLE_GM)
        aRole = discord.utils.get(member.guild.roles, name=ROLE_AD)
        bRole = discord.utils.get(member.guild.roles, name=ROLE_BT)
        await ctx.channel.set_permissions(wiki_role, add_reactions=True, send_messages=True, read_messages=True)
        await ctx.channel.set_permissions(gm_role, add_reactions=True, send_messages=True, read_messages=True)
        await ctx.channel.set_permissions(aRole, add_reactions=True, send_messages=True, read_messages=True)
        await ctx.channel.set_permissions(bRole, add_reactions=True, send_messages=True, read_messages=True)

        # Edit to final message
        await ctx.interaction.edit_original_message(content = "Unlocked the channel to Member access. Please check if permissions need to be synced.")

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Staff command. Runs Pi-Bot's Most Edits Table wiki functionality."
    )
    @permissions.has_any_role(ROLE_STAFF, ROLE_VIP, guild_id = SERVER_ID)
    async def met(self, ctx):
        """Runs Pi-Bot's Most Edits Table"""
        commandchecks.is_staff_from_ctx(ctx)

        await ctx.respond(f"{EMOJI_LOADING} Generating the Most Edits Table...")
        res = await run_table()
        print(res)
        names = [v['name'] for v in res]
        data = [v['increase'] for v in res]
        names = names[:10]
        data = data[:10]

        fig = plt.figure()
        plt.bar(names, data, color="#2E66B6")
        plt.xlabel("Usernames")
        plt.xticks(rotation=90)
        plt.ylabel("Edits past week")
        plt.title("Top wiki editors for the past week!")
        plt.tight_layout()
        plt.savefig("met.png")
        plt.close()
        await ctx.interaction.edit_original_message(content = f"{EMOJI_LOADING} Generating graph...")
        await asyncio.sleep(3)

        file = discord.File("met.png", filename="met.png")
        embed = discord.Embed(
            title = "**Top wiki editors for the past week!**",
            description = ("Check out the past week's top wiki editors! Thank you all for your contributions to the wiki! :heart:\n\n" +
            f"`1st` - **{names[0]}** ({data[0]} edits)\n" +
            f"`2nd` - **{names[1]}** ({data[1]} edits)\n" +
            f"`3rd` - **{names[2]}** ({data[2]} edits)\n" +
            f"`4th` - **{names[3]}** ({data[3]} edits)\n" +
            f"`5th` - **{names[4]}** ({data[4]} edits)"),
        )
        embed.set_image(url = "attachment://met.png")
        await ctx.interaction.edit_original_message(content = f"The Most Edits Table for the week:", file=file, embed=embed)

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Staff command. Refreshes data from the bot's database."
    )
    @permissions.has_any_role(ROLE_STAFF, ROLE_VIP, guild_id = SERVER_ID)
    async def refresh(self,
                      ctx,
                      system: Option(str, "The system to refresh.", choices = ["all", "invitationals"])
                     ):
        """Refreshes data from the sheet."""
        commandchecks.is_staff_from_ctx(ctx)

        if system in ["all", "invitationals"]:
            await ctx.interaction.response.send_message(f"{EMOJI_LOADING} Updating the invitationals list.")
            await update_tournament_list(ctx.bot)
            await ctx.interaction.edit_original_message(content = ":white_check_mark: Updated the invitationals list.")

    change_status_group = discord.commands.SlashCommandGroup(
        "status",
        "Updates the bot's status.",
        guild_ids = [SLASH_COMMAND_GUILDS],
        permissions = [
            discord.commands.CommandPermission(ROLE_STAFF, 1, True),
            discord.commands.CommandPermission(ROLE_VIP, 1, True),
        ]
    )

    @change_status_group.command(
        name = "set",
        description = "Staff command. Sets Pi-Bot's status to a custom tagline."
    )
    @permissions.has_any_role(ROLE_STAFF, ROLE_VIP, guild_id = SERVER_ID)
    async def change_status(self,
        ctx,
        activity: Option(str, "The activity the bot will be doing.", choices = ["playing", "listening", "watching"], required = True),
        message: Option(str, "The message to display after the activity type in the bot's status, shown as bold text.", required = True),
        length: Option(str, "How long the status should remain before being auto-updated to a recurring status.", choices = [
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
            ])
        ):
        # Check again to make sure caller is staff
        commandchecks.is_staff_from_ctx(ctx)

        # CRON functionality
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
        selected_time = times[length]

        # Change settings
        await src.discord.globals.update_setting(
            {
                'custom_bot_status_text': message,
                'custom_bot_status_type': activity
            }
        )

        # Insert time length into CRON
        cron_cog = self.bot.get_cog("CronTasks")
        await cron_cog.schedule_status_remove(selected_time)

        # Update activity
        status_text = None
        if activity == "playing":
            await self.bot.change_presence(activity = discord.Game(name = message))
            status_text = f"Playing {message}"
        elif activity == "listening":
            await self.bot.change_presence(activity = discord.Activity(type = discord.ActivityType.listening, name = message))
            status_text = f"Listening to {message}"
        elif activity == "watching":
            await self.bot.change_presence(activity = discord.Activity(type = discord.ActivityType.watching, name = message))
            status_text = f"Watching {message}"

        await ctx.interaction.response.send_message(content = f"The status was updated to: `{status_text}`. This status will stay in effect until {discord.utils.format_dt(selected_time, 'F')}.")

    @change_status_group.command(
        name = "reset",
        description = "Staff command. Resets Pi-Bot's status to a custom value."
    )
    @permissions.has_any_role(ROLE_STAFF, ROLE_VIP, guild_id = SERVER_ID)
    async def reset_status(self, ctx):
        # Reset status
        await ctx.interaction.response.send_message(f"{EMOJI_LOADING} Attempting to resetting status...")
        await src.discord.globals.update_setting(
            {
                'custom_bot_status_text': None,
                'custom_bot_status_type': None
            }
        )
        await ctx.interaction.edit_original_message(content = "Reset the bot's status.")

        # Reset bot status to regularly update
        cron_cog = self.bot.get_cog("CronTasks")
        cron_cog.change_bot_status.restart()

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        name = "tagadd",
        description = "Staff command. Adds a new tag."
    )
    @permissions.has_any_role(ROLE_STAFF, ROLE_VIP, guild_id = SERVER_ID)
    async def tag_add(self,
        ctx,
        tag_name: Option(str, "The name of the tag to add.", required = True),
        launch_helpers: Option(str, "Whether launch helpers can use. Defaults to yes.", choices = ["yes", "no"], default = "yes"),
        members: Option(str, "Whether all members can use this tag. Defaults to yes.", choices = ["yes", "no"], default = "yes")
        ):
        commandchecks.is_staff_from_ctx(ctx)

        if tag_name in [t['name'] for t in src.discord.globals.TAGS]:
            await ctx.interaction.response.send_message(content = f"The `{tag_name}` tag has already been added. To edit this tag, please use `/tagedit` instead.")
        else:
            await ctx.interaction.response.defer()

            succesful = False
            while not succesful:
                info_message = await ctx.send("Please send the new text for the tag enclosed in a preformatted block. The block should begin and end with three backticks, with no content on the line of the backticks. If no response is found in 2 minutes, the operation will be cancelled.")
                content_message = await listen_for_response(
                    follow_id = ctx.user.id,
                    timeout = 120,
                )

                if content_message == None:
                    await ctx.interaction.edit_original_message(content = "No message was found within 2 minutes. Operation cancelled.")
                    return

                text = content_message.content
                await content_message.delete()
                await info_message.delete()
                matches = re.findall(r"(?<=```\n)(.*)(?=\n```)", text, flags = re.MULTILINE | re.DOTALL)
                if len(matches) < 0:
                    await ctx.interaction.edit_original_message(content = "No matching preformatted block was found. Operation cancelled.")
                    return
                else:
                    new_dict = {
                        'name': tag_name,
                        'output': matches[0],
                        'permissions': {
                            'staff': True,
                            'launch_helpers': True if launch_helpers == "yes" else False,
                            'members': True if members == "yes" else False
                        }
                    }

                    src.discord.globals.TAGS.append(new_dict)
                    await insert("data", "tags", new_dict)
                    succesful = True
                    await ctx.interaction.edit_original_message(content = f"The `{tag_name}` tag was added!")

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        name = "tagedit",
        description = "Staff command. Edits an existing tag."
    )
    @permissions.has_any_role(ROLE_STAFF, ROLE_VIP, guild_id = SERVER_ID)
    async def tag_edit(self,
        ctx,
        tag_name: Option(str, "The tag name to edit the text of.", required = True),
        launch_helpers: Option(str, "Whether launch helpers can use. Defaults to 'do not change'.", choices = ["yes", "no", "do not change"], default = "do not change"),
        members: Option(str, "Whether all members can use this tag. Defaults to 'do not change'.", choices = ["yes", "no", "do not change"], default = "do not change")
        ):
        commandchecks.is_staff_from_ctx(ctx)

        if tag_name not in [t['name'] for t in src.discord.globals.TAGS]:
            return await ctx.interaction.response.send_message(content = f"No tag with name `{tag_name}` could be found.")

        tag = [t for t in src.discord.globals.TAGS if t['name'] == tag_name][0]

        await ctx.interaction.response.defer()
        info_message = await ctx.send(f"The current content of the tag is:\n```\n{tag['output']}\n```\nPlease enclose a new message to associate with the tag by entering a message in a preformatted block (a block of text between three backticks).")

        content_message = await listen_for_response(
            follow_id = ctx.user.id,
            timeout = 120,
        )

        if content_message == None:
            await ctx.interaction.edit_original_message(content = "No message was found within 2 minutes. Operation cancelled.")
            return

        text = content_message.content
        await content_message.delete()
        await info_message.delete()

        matches = re.findall(r"(?<=```\n)(.*)(?=\n```)", text, flags = re.MULTILINE | re.DOTALL)
        if len(matches) < 0:
            await ctx.interaction.edit_original_message(content = "No matching preformatted block was found. Operation cancelled.")
            return
        else:
            update_dict = {}

            tag['output'] = matches[0]
            update_dict['output'] = matches[0]
            if launch_helpers != "do not change":
                tag['permissions']['launch_helpers'] = True if launch_helpers == "yes" else False
                update_dict['permissions.launch_helpers'] = True if launch_helpers == "yes" else False
            if members != "do not change":
                tag['permissions']['members'] = True if members == "yes" else False
                update_dict['permissions.members'] = True if members == "yes" else False

            await update("data", "tags", tag['_id'], {"$set": update_dict})
            await ctx.interaction.edit_original_message(content = f"The `{tag_name}` tag was updated.")

    @discord.commands.slash_command(
        guildids = [SLASH_COMMAND_GUILDS],
        name = "tagremove",
        description = "Staff command. Removes a tag completely."
    )
    @permissions.has_any_role(ROLE_STAFF, ROLE_VIP, guild_id = SERVER_ID)
    async def tag_remove(self,
        ctx,
        tag_name: Option(str, "The name of the tag to remove.", required = True)
        ):
        commandchecks.is_staff_from_ctx(ctx)

        if tag_name not in [t['name'] for t in src.discord.globals.TAGS]:
            return await ctx.interaction.response.send_message(content = f"No tag with the name of `{tag_name}` was found.")

        tag = [t for t in src.discord.globals.TAGS if t['name'] == tag_name][0]
        src.discord.globals.TAGS.remove(tag)
        await delete("data", "tags", tag['_id'])
        return await ctx.interaction.response.send_message(content = f"The `{tag_name}` tag was deleted.")

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        name = "eventadd",
        description = "Staff command. Adds a new event."
    )
    @permissions.has_any_role(ROLE_STAFF, ROLE_VIP, guild_id = SERVER_ID)
    async def event_add(self,
        ctx,
        event_name: Option(str, "The name of the new event.", required = True),
        event_aliases: Option(str, "The aliases for the new event. Format as 'alias1, alias2'.")
        ):
        commandchecks.is_staff_from_ctx(ctx)

        if event_name in [e['name'] for e in src.discord.globals.EVENT_INFO]:
            return await ctx.interaction.response.send_message(content = f"The `{event_name}` event has already been added.")

        aliases_array = re.findall(r'\w+', event_aliases)
        new_dict = {
            'name': event_name,
            'aliases': aliases_array
        }

        src.discord.globals.EVENT_INFO.append(new_dict)
        await insert("data", "events", new_dict)

        server = self.bot.get_guild(SERVER_ID)
        await server.create_role(
            name = event_name,
            color = discord.Color(0x82A3D3),
            reason = f"Created by {str(ctx.author)} using /eventadd with Pi-Bot."
            )
        await ctx.interaction.response.send_message(content = f"The `{event_name}` event was added.")

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        name = 'eventremove',
        description = "Removes an event's availability and optionally, its role from all users."
    )
    @permissions.has_any_role(ROLE_STAFF, ROLE_VIP, guild_id = SERVER_ID)
    async def event_remove(self,
        ctx,
        event_name: Option(str, "The name of the event to remove.", required = True),
        delete_role: Option(str, "Whether to delete the event role from all users. 'no' allows role to remain.", choices = ["no", "yes"], default = "no", required = True)
        ):
        commandchecks.is_staff_from_ctx(ctx)

        if event_name not in [e['name'] for e in src.discord.globals.EVENT_INFO]:
            return await ctx.interaction.response.send_message(content = f"The `{event_name}` event does not exist.")

        if delete_role == "yes":
            server = self.bot.get_guild(SERVER_ID)
            role = discord.utils.get(server.roles, name = event_name)
            await role.delete()

        event = [e for e in src.discord.globals.EVENT_INFO if e['name'] == event_name][0]
        src.discord.globals.EVENT_INFO.remove(event)
        await delete("data", "events", event['_id'])
        await ctx.interaction.response.send_message(content = f"The `{event_name}` event was deleted.")

def setup(bot):
    bot.add_cog(StaffEssential(bot))
    bot.add_cog(StaffNonessential(bot))
