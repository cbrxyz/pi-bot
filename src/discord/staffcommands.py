import os
import re
import discord
import datetime
import asyncio
from discord.errors import NoEntryPointError

from discord.ext import commands
from discord.app import Option
from commandchecks import is_staff, is_launcher

import dateparser
import pytz

from src.discord.globals import SLASH_COMMAND_GUILDS, TOURNAMENT_INFO, CHANNEL_BOTSPAM, CATEGORY_ARCHIVE, ROLE_AT, ROLE_MUTED, CRON_LIST
from src.discord.globals import CATEGORY_SO, CATEGORY_GENERAL, ROLE_MR, CATEGORY_STATES, ROLE_WM, ROLE_GM, ROLE_AD, ROLE_BT
from src.discord.globals import PI_BOT_IDS, ROLE_EM
from src.discord.globals import CATEGORY_TOURNAMENTS, ROLE_ALL_STATES, ROLE_SELFMUTE, ROLE_QUARANTINE, ROLE_GAMES
from src.discord.globals import SERVER_ID, CHANNEL_WELCOME, ROLE_UC, STOPNUKE, ROLE_LH

from src.discord.utils import harvest_id, refresh_algorithm
from src.wiki.mosteditstable import run_table
from src.mongo.mongo import get_cron, remove_doc

from src.discord.mute import _mute
import matplotlib.pyplot as plt
from embed import assemble_embed

from typing import Type

from tournaments import update_tournament_list

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
            await interaction.response.edit_message(content="Attempting to run operation...")
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

class LauncherCommands(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    def if_launcher_in_welcome(self, ctx):
        # This is a method that will accompany the global cog check.
        # Therefore, this check is representing the proposition `(has launcher role) -> (message in #welcome)`
        from src.discord.globals import ROLE_STAFF, ROLE_VIP
        member = ctx.message.author
        lhRole = discord.utils.get(member.guild.roles, name=ROLE_LH)
        if lhRole in member.roles and ctx.message.channel.name != CHANNEL_WELCOME:
            staffRole = discord.utils.get(member.guild.roles, name=ROLE_STAFF)
            vipRole = discord.utils.get(member.guild.roles, name=ROLE_VIP)
            raise discord.ext.commands.MissingAnyRole([staffRole, vipRole])
        return True

    async def cog_check(self, ctx):
        return await is_launcher(ctx) and self.if_launcher_in_welcome(ctx)

    @discord.app.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Staff command. Confirms a user, giving them access to the server."
    )
    async def confirm(self,
        ctx,
        member: Option(discord.Member, "The member to confirm.")
    ):
        """Allows a staff member to confirm a user."""
        channel = ctx.channel
        if channel.name != CHANNEL_WELCOME:
            return await ctx.respond("Sorry! Please confirm the member in the welcoming channel!", ephemeral = True)

        role1 = discord.utils.get(member.guild.roles, name=ROLE_UC)
        role2 = discord.utils.get(member.guild.roles, name=ROLE_MR)
        await member.remove_roles(role1)
        await member.add_roles(role2)
        await ctx.respond(f"Alrighty, confirmed {member.mention}. They now have access to see other channels and send messages in them. :tada:", ephemeral = True)

        await channel.purge(check=lambda m: ((m.author.id in PI_BOT_IDS and not m.embeds and not m.pinned) or (m.author == member and not m.embeds) or (member in m.mentions))) # Assuming first message is pinned (usually is in several cases)

    @discord.app.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Staff command. Nukes a certain amount of messages."
    )
    async def nuke(self,
        ctx,
        count: Option(int, "The amount of messages to nuke.")
    ):
        """Nukes (deletes) a specified amount of messages."""
        global STOPNUKE
        MAX_DELETE = 100
        if int(count) > MAX_DELETE:
            return await ctx.respond("Chill. No more than deleting 100 messages at a time.")
        channel = ctx.channel
        if int(count) < 0:
            history = await channel.history(limit=105).flatten()
            message_count = len(history)
            if message_count > 100:
                count = 100
            else:
                count = message_count + int(count) - 1
            if count <= 0:
                return await ctx.respond("Sorry, you can not delete a negative amount of messages. This is likely because you are asking to save more messages than there are in the channel.")

        original_shown_embed = discord.Embed(
            title = "NUKE COMMAND PANEL",
            color = discord.Color.brand_red(),
            description = f"""
            {count} messages will be deleted from {channel.mention} in 10 seconds...

            To stop this nuke, press the red button below!
            """
        )
        view = Nuke()
        msg = await ctx.respond(embed = original_shown_embed, view = view)
        await asyncio.sleep(1)

        for i in range(9, 0, -1):
            original_shown_embed.description = f"""
            {count} messages will be deleted from {channel.mention} in {i} seconds...

            To stop this nuke, press the red button below!
            """
            await ctx.interaction.edit_original_message(embed = original_shown_embed, view = view)
            if view.stopped:
                return
            await asyncio.sleep(1)

        original_shown_embed.description = f"""
        Now nuking {count} messages from the channel...
        """
        await ctx.interaction.edit_original_message(embed = original_shown_embed, view = None)

        # Nuke has not been stopped, proceed with deleting messages
        def nuke_check(msg: discord.Message):
            return not len(msg.components) and not msg.pinned

        msg = await ctx.interaction.original_message()
        await channel.purge(limit=count + 1, check=nuke_check)

        # Let user know messages have been deleted
        # Waiting to implement until later
        #
        # confirm_embed = discord.Embed(
        #     title = "NUKE COMMAND PANEL",
        #     color = discord.Color.brand_green(),
        #     description = f"""
        #     {count} messages were deleted from the channel commander!

        #     Have a good day!
        #     """
        # )
        # confirm_embed.set_image(url = "https://media.giphy.com/media/XUFPGrX5Zis6Y/giphy.gif")
        # await ctx.interaction.edit_original_message(embed = confirm_embed, view = None)
        # await asyncio.sleep(5)
        # await msg.delete()

    # @commands.command()
    # @commands.check(is_nuke_allowed)
    # async def nukeuntil(self, ctx, msgid):
    #     import datetime
    #     global STOPNUKE
    #     channel = ctx.message.channel
    #     message = await ctx.fetch_message(msgid)
    #     if channel == message.channel:
    #         await self._nuke_countdown(ctx)
    #         if STOPNUKE <= datetime.datetime.utcnow():
    #             await channel.purge(limit=1000, after=message)
    #             msg = await ctx.send("https://media.giphy.com/media/XUFPGrX5Zis6Y/giphy.gif")
    #             await msg.delete(delay=5)
    #     else:
    #         return await ctx.send("MESSAGE ID DOES NOT COME FROM THIS TEXT CHANNEL. ABORTING NUKE.")

    @nuke.error
    async def nuke_error(self, ctx, error):
        ctx.__slots__ = True
        from src.discord.globals import BOT_PREFIX
        print(f"{BOT_PREFIX}nuke error handler: {error}")
        if isinstance(error, discord.ext.commands.MissingAnyRole):
            return await ctx.send("APOLOGIES. INSUFFICIENT RANK FOR NUKE.")

        ctx.__slots__ = False

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
            timeframe = (doc['time'] - datetime.datetime.utcnow()).days
            if abs(timeframe) < 1:
                timeframe = f"{(doc['time'] - datetime.datetime.utcnow()).total_seconds() // 3600} hours"
            else:
                timeframe = f"{(doc['time'] - datetime.datetime.utcnow()).days} days"
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

class StaffEssential(StaffCommands, name="StaffEsntl"):
    def __init__(self, bot):
        super().__init__(bot)

    @discord.app.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Staff command. Kicks user from the server."
    )
    async def kick(self,
        ctx,
        member: Option(discord.Member, "The user to kick from the server."),
        reason: Option(str, "The reason to kick the member for.")
    ):
        """Kicks a member for the specified reason."""
        original_shown_embed = discord.Embed(
            title = "Kick Confirmation",
            color = discord.Color.brand_red(),
            description = f"""
            The member {member.mention} will be kicked from the server for:
            `{reason}`

            **Staff Member:** {ctx.author.mention}
            """
        )

        view = Confirm(ctx.author, "The kick operation was cancelled. The user remains in the server.")
        await ctx.respond("Please confirm that you would like to kick this member from the server.", embed = original_shown_embed, view = view, ephemeral = True)
        await view.wait()
        if view.value:
            try:
                await member.kick(reason = reason)
            except:
                pass

        # Test
        guild = ctx.author.guild
        if member not in guild.members:
            # User was successfully kicked
            await ctx.interaction.edit_original_message(content = "The user was successfully kicked.", embed = None, view = None)
        else:
            await ctx.interaction.edit_original_message(content = "The user was not successfully kicked because of an error. They remain in the server.", embed = None, view = None)

    # Need to find a way to share _mute() between StaffEssential and MemberCommands

    @discord.app.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Staff command. Unmutes a user immediately."
    )
    async def unmute(self,
        ctx,
        member: Option(discord.Member, "The user to unmute.")
    ):
        """Unmutes a user."""
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
        role = discord.utils.get(member.guild.roles, name=ROLE_MUTED)
        if view.value:
            try:
                await member.remove_roles(role)
            except:
                pass

        # Test
        if role not in member.roles:
            await ctx.interaction.edit_original_message(content = "The user was succesfully unmuted.", embed = None, view = None)
        else:
            await ctx.interaction.edit_original_message(content = "The user was not unmuted because of an error. They remain muted. Please contact a bot developer about this issue.", embed = None, view = None)

    @discord.app.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Staff command. Bans a user from the server."
    )
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
        ])
    ):
        """Bans a user."""
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
            {member.mention} will be banned from the entire server. They will not be able to re-enter the server until the ban is lifted or the time expires.

            {time_statement}
            """
        )

        view = Confirm(ctx.author, "The ban operation was cancelled. They remain in the server.")
        await ctx.respond("Please confirm that you would like to ban this user.", view = view, embed = original_shown_embed, ephemeral = True)

        message = f"You have been banned from the Scioly.org Discord server for {reason}."
        await member.send(message)

        await view.wait()
        if view.value:
            try:
                await ctx.guild.ban(member, reason=reason)
            except:
                pass

        if ban_length != "Indefinitely":
            CRON_LIST.append({"date": times[ban_length], "do": f"unban {member.id}"})

        # Test
        guild = ctx.author.guild
        if member not in guild.members:
            # User was successfully banned
            await ctx.interaction.edit_original_message(content = "The user was successfully banned.", embed = None, view = None)
        else:
            await ctx.interaction.edit_original_message(content = "The user was not successfully banned because of an error. They remain in the server.", embed = None, view = None)

    @discord.app.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Staff command. Mutes a user."
    )
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
        ])
    ):
        """
        Mutes a user.

        :param user: User to be muted.
        :type user: discord.Member
        :param *args: The time to mute the user for.
        :type *args: str
        """
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

            {time_statement}
            """
        )

        view = Confirm(ctx.author, "The mute operation was cancelled. They remain able to communicate.")
        await ctx.respond("Please confirm that you would like to mute this user.", view = view, embed = original_shown_embed, ephemeral = True)

        message = f"You have been muted from the Scioly.org Discord server for {reason}."
        await member.send(message)

        await view.wait()
        role = discord.utils.get(member.guild.roles, name=ROLE_MUTED)
        if view.value:
            try:
                await member.add_roles(role)
            except:
                pass

        if mute_length != "Indefinitely":
            CRON_LIST.append({"date": times[mute_length], "do": f"unmute {member.id}"})

        # Test
        if role in member.roles:
            # User was successfully muted
            await ctx.interaction.edit_original_message(content = "The user was successfully muted.", embed = None, view = None)
        else:
            await ctx.interaction.edit_original_message(content = "The user was not successfully muted because of an error. They remain able to communicate.", embed = None, view = None)

    @discord.app.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Staff command. Enables slowmode in the current channel, or an alternate channel."
    )
    async def slowmode(self,
        ctx,
        mode: Option(str, "How to change the slowmode in the channel.", choices = ["set", "remove"]),
        delay: Option(int, "Optional. How long the slowmode delay should be, in seconds. If none, assumed to be 20 seconds.", required = False, default = 20),
        channel: Option(discord.TextChannel, "Optional. The channel to enable the slowmode in. If none, assumed in the current channel.", required = False)
    ):
        true_channel = channel or ctx.channel
        if mode == "remove":
            await true_channel.edit(slowmode_delay = 0)
            await ctx.respond("The slowmode was removed.")
        elif mode == "set":
            await true_channel.edit(slowmode_delay = delay)
            await ctx.respond(f"Enabled a slowmode delay of {delay} seconds.")

    @discord.app.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Staff command. Allows staff to manipulate the CRON list."
    )
    async def cron(self, ctx):
        """
        Allows staff to manipulate the CRON list.

        Steps:
            1. Parse the cron list.
            2. Create relevant action rows.
            3. Perform steps as staff request.
        """
        cron_list = await get_cron()

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

    @discord.app.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Staff command. Opens a voice channel clone of a channel."
    )
    async def vc(self, ctx):
        server = ctx.author.guild
        if ctx.channel.category.name == CATEGORY_TOURNAMENTS:
            test_vc = discord.utils.get(server.voice_channels, name=ctx.channel.name)
            if test_vc == None:
                # Voice channel needs to be opened
                new_vc = await server.create_voice_channel(ctx.channel.name, category=ctx.channel.category)
                await new_vc.edit(sync_permissions=True)
                # Make the channel invisible to normal members
                await new_vc.set_permissions(server.default_role, view_channel=False)
                at = discord.utils.get(server.roles, name=ROLE_AT)
                for t in TOURNAMENT_INFO:
                    if ctx.channel.name == t[1]:
                        tourney_role = discord.utils.get(server.roles, name=t[0])
                        await new_vc.set_permissions(tourney_role, view_channel=True)
                        break
                await new_vc.set_permissions(at, view_channel=True)
                return await ctx.respond("Created a voice channel. **Please remember to follow the rules! No doxxing or cursing is allowed.**")
            else:
                # Voice channel needs to be closed
                await test_vc.delete()
                return await ctx.respond("Closed the voice channel.")
        elif ctx.message.channel.category.name == CATEGORY_STATES:
            test_vc = discord.utils.get(server.voice_channels, name=ctx.channel.name)
            if test_vc == None:
                # Voice channel does not currently exist
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
                new_vc = await server.create_voice_channel(ctx.channel.name, category=ctx.channel.category)
                await new_vc.edit(sync_permissions=True)
                await new_vc.set_permissions(server.default_role, view_channel=False)
                muted_role = discord.utils.get(server.roles, name=ROLE_MUTED)
                all_states_role = discord.utils.get(server.roles, name=ROLE_ALL_STATES)
                self_muted_role = discord.utils.get(server.roles, name=ROLE_SELFMUTE)
                quarantine_role = discord.utils.get(server.roles, name=ROLE_QUARANTINE)
                state_role_name = await lookup_role(ctx.channel.name.replace("-", " "))
                state_role = discord.utils.get(server.roles, name = state_role_name)
                await new_vc.set_permissions(muted_role, connect=False)
                await new_vc.set_permissions(self_muted_role, connect=False)
                await new_vc.set_permissions(quarantine_role, connect=False)
                await new_vc.set_permissions(state_role, view_channel = True, connect=True)
                await new_vc.set_permissions(all_states_role, view_channel = True, connect=True)
                current_pos = ctx.channel.position
                return await ctx.respond("Created a voice channel. **Please remember to follow the rules! No doxxing or cursing is allowed.**")
            else:
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
        elif ctx.message.channel.name == "games":
            # Support for opening a voice channel for #games
            test_vc = discord.utils.get(server.voice_channels, name="games")
            if test_vc == None:
                # Voice channel needs to be opened/doesn't exist already
                new_vc = await server.create_voice_channel("games", category=ctx.channel.category)
                await new_vc.edit(sync_permissions=True)
                await new_vc.set_permissions(server.default_role, view_channel=False)
                games_role = discord.utils.get(server.roles, name=ROLE_GAMES)
                member_role = discord.utils.get(server.roles, name=ROLE_MR)
                await new_vc.set_permissions(games_role, view_channel=True)
                await new_vc.set_permissions(member_role, view_channel=False)
                return await ctx.respond("Created a voice channel. **Please remember to follow the rules! No doxxing or cursing is allowed.**")
            else:
                # Voice channel needs to be closed
                await test_vc.delete()
                return await ctx.respond("Closed the voice channel.")
        else:
            return await ctx.respond("Apologies... voice channels can currently be opened for tournament channels and the games channel.")

    @discord.app.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Staff command. Finds a user by their ID."
    )
    async def userfromid(self,
        ctx,
        iden: Option(str, "The ID to lookup.")
    ):
        """Mentions a user with the given ID."""
        user = self.bot.get_user(int(iden))
        await ctx.respond(user.mention, ephemeral = True)

    @discord.app.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Staff command. Locks a channel, preventing members from sending messages."
    )
    async def lock(self, ctx):
        """Locks a channel to Member access."""
        member = ctx.author
        channel = ctx.channel

        if (channel.category.name in ["beta", "staff", "Pi-Bot"]):
            return await ctx.respond("This command is not suitable for this channel because of its category.")

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
        await ctx.respond("Locked the channel to Member access.")

    @discord.app.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Staff command. Unlocks a channel, allowing members to speak after the channel was originally locked."
    )
    async def unlock(self, ctx):
        """Unlocks a channel to Member access."""
        member = ctx.author
        channel = ctx.channel

        if (channel.category.name in ["beta", "staff", "Pi-Bot"]):
            return await ctx.respond("This command is not suitable for this channel because of its category.")

        if (channel.category.name == CATEGORY_SO or channel.category.name == CATEGORY_GENERAL):
            await ctx.respond("Synced permissions with channel category.")
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
        await ctx.respond("Unlocked the channel to Member access. Please check if permissions need to be synced.")

    @discord.app.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Staff command. Runs Pi-Bot's Most Edits Table wiki functionality."
    )
    async def met(self, ctx):
        """Runs Pi-Bot's Most Edits Table"""
        msg1 = await ctx.respond("Attemping to run the Most Edits Table.")
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
        await msg1.delete()
        msg2 = await ctx.send("Generating graph...")
        await asyncio.sleep(3)
        await msg2.delete()

        file = discord.File("met.png", filename="met.png")
        embed = assemble_embed(
            title="**Top wiki editors for the past week!**",
            desc=("Check out the past week's top wiki editors! Thank you all for your contributions to the wiki! :heart:\n\n" +
            f"`1st` - **{names[0]}** ({data[0]} edits)\n" +
            f"`2nd` - **{names[1]}** ({data[1]} edits)\n" +
            f"`3rd` - **{names[2]}** ({data[2]} edits)\n" +
            f"`4th` - **{names[3]}** ({data[3]} edits)\n" +
            f"`5th` - **{names[4]}** ({data[4]} edits)"),
            imageUrl="attachment://met.png",
        )
        await ctx.send(file=file, embed=embed)

    @commands.command()
    async def prepembed(self, ctx, channel:discord.TextChannel, *, jsonInput):
        """Helps to create an embed to be sent to a channel."""
        jso = json.loads(jsonInput)
        title = jso['title'] if 'title' in jso else ""
        desc = jso['description'] if 'description' in jso else ""
        titleUrl = jso['titleUrl'] if 'titleUrl' in jso else ""
        hexcolor = jso['hexColor'] if 'hexColor' in jso else "#2E66B6"
        webcolor = jso['webColor'] if 'webColor' in jso else ""
        thumbnailUrl = jso['thumbnailUrl'] if 'thumbnailUrl' in jso else ""
        authorName = jso['authorName'] if 'authorName' in jso else ""
        authorUrl = jso['authorUrl'] if 'authorUrl' in jso else ""
        authorIcon = jso['authorIcon'] if 'authorIcon' in jso else ""
        if 'author' in jso:
            authorName = ctx.message.author.name
            authorIcon = ctx.message.author.avatar_url_as(format="jpg")
        fields = jso['fields'] if 'fields' in jso else ""
        footerText = jso['footerText'] if 'footerText' in jso else ""
        footerUrl = jso['footerUrl'] if 'footerUrl' in jso else ""
        imageUrl = jso['imageUrl'] if 'imageUrl' in jso else ""
        embed = assemble_embed(
            title=title,
            desc=desc,
            titleUrl=titleUrl,
            hexcolor=hexcolor,
            webcolor=webcolor,
            thumbnailUrl=thumbnailUrl,
            authorName=authorName,
            authorUrl=authorUrl,
            authorIcon=authorIcon,
            fields=fields,
            footerText=footerText,
            footerUrl=footerUrl,
            imageUrl=imageUrl
        )
        await channel.send(embed=embed)

    @discord.app.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Staff command. Archives a tournament channel, preventing members from sending messages."
    )
    async def archive(self, ctx):
        tournament = [t for t in TOURNAMENT_INFO if t[1] == ctx.channel.name]
        bot_spam = discord.utils.get(ctx.guild.text_channels, name = CHANNEL_BOTSPAM)
        archive_cat = discord.utils.get(ctx.guild.categories, name = CATEGORY_ARCHIVE)
        tournament_name, tournament_formal = None, None
        if len(tournament) > 0:
            tournament_name = tournament[0][1]
            tournament_formal = tournament[0][0]
        tournament_role = discord.utils.get(ctx.guild.roles, name = tournament_formal)
        all_tourney_role = discord.utils.get(ctx.guild.roles, name = ROLE_AT)
        embed = assemble_embed(
            title = 'This channel is now archived.',
            desc = (f'Thank you all for your discussion around the {tournament_formal}. Now that we are well past the tournament date, we are going to close this channel to help keep tournament discussions relevant and on-topic.\n\n' +
            f'If you have more questions/comments related to this tournament, you are welcome to bring them up in {ctx.channel.mention}. This channel is now read-only.\n\n' +
            f'If you would like to no longer view this channel, you are welcome to type `!tournament {tournament_name}` into {bot_spam}, and the channel will disappear for you. Members with the `All Tournaments` role will continue to see the channel.'),
            webcolor='red'
        )
        await ctx.channel.set_permissions(tournament_role, send_messages = False, view_channel = True)
        await ctx.channel.set_permissions(all_tourney_role, send_messages = False, view_channel = True)
        await ctx.channel.edit(category = archive_cat, position = 1000)
        await ctx.channel.send(embed = embed)
        await ctx.channel.respond(content = "The channel is now archived, and members can no longer speak in the channel.", ephemeral = True)

    @discord.app.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Staff command. Refreshes data from the bot's database."
    )
    async def refresh(self, ctx):
        """Refreshes data from the sheet."""
        await update_tournament_list(ctx.bot)
        res = await refresh_algorithm()
        if res == True:
            await ctx.respond("Successfully refreshed data from sheet.")
        else:
            await ctx.respond(":warning: Unsuccessfully refreshed data from sheet.")

    @commands.command()
    async def tla(self, ctx, iden, uid):
        global REQUESTED_TOURNAMENTS
        for t in REQUESTED_TOURNAMENTS:
            if t['iden'] == iden:
                t['count'] += 1
                await ctx.send(f"Added a vote for {iden} from {uid}. Now has `{t['count']}` votes.")
                return await update_tournament_list(ctx.bot)
        REQUESTED_TOURNAMENTS.append({'iden': iden, 'count': 1, 'users': [uid]})
        await update_tournament_list(ctx.bot)
        return await ctx.send(f"Added a vote for {iden} from {uid}. Now has `1` vote.")

    @commands.command()
    async def tlr(self, ctx, iden):
        global REQUESTED_TOURNAMENTS
        for t in REQUESTED_TOURNAMENTS:
            if t['iden'] == iden:
                REQUESTED_TOURNAMENTS.remove(t)
        await update_tournament_list(ctx.bot)
        return await ctx.send(f"Removed `#{iden}` from the tournament list.")

def setup(bot):
    bot.add_cog(StaffEssential(bot))
    bot.add_cog(StaffNonessential(bot))
    bot.add_cog(LauncherCommands(bot))
