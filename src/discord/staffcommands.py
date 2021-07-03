import discord
import asyncio

from discord.ext import commands
from commandchecks import is_staff, is_launcher

import dateparser
import pytz

from src.discord.globals import TOURNAMENT_INFO, CHANNEL_BOTSPAM, CATEGORY_ARCHIVE, ROLE_AT, ROLE_MUTED, CRON_LIST
from src.discord.globals import CATEGORY_SO, CATEGORY_GENERAL, ROLE_MR, CATEGORY_STATES, ROLE_WM, ROLE_GM, ROLE_AD, ROLE_BT
from src.discord.globals import PI_BOT_IDS, ROLE_EM
from src.discord.globals import CATEGORY_TOURNAMENTS, ROLE_ALL_STATES, ROLE_SELFMUTE, ROLE_QUARANTINE, ROLE_GAMES
from src.discord.globals import SERVER_ID, CHANNEL_WELCOME, ROLE_UC, STOPNUKE, ROLE_LH

from src.discord.utils import harvest_id
from src.wiki.mosteditstable import run_table

from src.discord.mute import _mute
import matplotlib.pyplot as plt
from embed import assemble_embed

from typing import Type

from bot import refresh_algorithm
from tournaments import update_tournament_list

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
        
    @commands.command()
    async def confirm(self, ctx, *args: discord.Member):
        """Allows a staff member to confirm a user."""
        await self._confirm(args)
        
    # @confirm.error
    # async def confirm_error(self, ctx, error):
    #     from src.discord.globals import BOT_PREFIX
    #     print(f"{BOT_PREFIX}confirm error handler: {error}")
    #     # if isinstance(error, NukeMissingPermssions):
    #     #     return await ctx.send("APOLOGIES. INSUFFICIENT RANK FOR NUKE.")

    async def _confirm(self, members):
        server = self.bot.get_guild(SERVER_ID)
        channel = discord.utils.get(server.text_channels, name=CHANNEL_WELCOME)
        for member in members:
            role1 = discord.utils.get(member.guild.roles, name=ROLE_UC)
            role2 = discord.utils.get(member.guild.roles, name=ROLE_MR)
            await member.remove_roles(role1)
            await member.add_roles(role2)
            message = await channel.send(f"Alrighty, confirmed {member.mention}. Welcome to the server! :tada:")
            await message.delete(delay=3)
            # before_message = None
            # f = 0
            
            await channel.purge(check=lambda m: m != message and ((m.author.id in PI_BOT_IDS and not m.embeds and not m.pinned) or (m.author == member and not m.embeds) or (member in m.mentions))) # Assuming first message is pinned (usually is in several cases)
            # async for message in channel.history(oldest_first=True):
            #     # Delete any messages sent by Pi-Bot where message before is by member
            #     if f > 0:
            #         if message.author.id in PI_BOT_IDS and before_message.author == member and len(message.embeds) == 0:
            #             await message.delete()
            # 
            #         # Delete any messages by user
            #         if message.author == member and len(message.embeds) == 0:
            #             await message.delete()
            # 
            #         if member in message.mentions:
            #             await message.delete()
            # 
            #     before_message = message
            #     f += 1
    
    def is_nuke_allowed(ctx):
        import datetime
        global STOPNUKE
        time_delta = STOPNUKE - datetime.datetime.utcnow()
        if time_delta > datetime.timedelta():
            raise discord.ext.commands.CommandOnCooldown(None, time_delta.total_seconds())
        return True
    
    async def _nuke_countdown(self, ctx, count = -1):
        import datetime
        global STOPNUKE
        await ctx.send("=====\nINCOMING TRANSMISSION.\n=====")
        await ctx.send("PREPARE FOR IMPACT.")
        for i in range(10, 0, -1):
            if count < 0:
                await ctx.send(f"NUKING MESSAGES IN {i}... TYPE `!stopnuke` AT ANY TIME TO STOP ALL TRANSMISSION.")
            else:
                await ctx.send(f"NUKING {count} MESSAGES IN {i}... TYPE `!stopnuke` AT ANY TIME TO STOP ALL TRANSMISSION.")
            await asyncio.sleep(1)
            if STOPNUKE > datetime.datetime.utcnow():
                return await ctx.send("A COMMANDER HAS PAUSED ALL NUKES FOR 20 SECONDS. NUKE CANCELLED.") # magic number MonkaS
    
    # Problems with this !nuke:
    #  Can only nuke one channel at a time (ideally should be on a per channel basis).
    #  No real integrated cooldown using `commands.cooldown` with !stopnuke (unfortunately i believe it's simply a library limitation :( )
    @commands.command()
    @commands.check(is_nuke_allowed)
    async def nuke(self, ctx, count):
        """Nukes (deletes) a specified amount of messages."""
        import datetime
        global STOPNUKE
        # launcher = await is_launcher(ctx)
        # staff = await is_staff(ctx)
        # if not (staff or (launcher and ctx.message.channel.name == "welcome")):
        #     return await ctx.send("APOLOGIES. INSUFFICIENT RANK FOR NUKE.")
        # if STOPNUKE:
        #     return await ctx.send("TRANSMISSION FAILED. ALL NUKES ARE CURRENTLY PAUSED. TRY AGAIN LATER.")
        MAX_DELETE = 100
        if int(count) > MAX_DELETE:
            return await ctx.send("Chill. No more than deleting 100 messages at a time.")
        channel = ctx.message.channel
        if int(count) < 0: count = MAX_DELETE
            # Since we are just trying to see the history and purge doesn't care
            #  if we have a limit over the total num of actual messages, we will
            #  just set the count to MAX_DELETE
            
            # history = await channel.history(limit=105).flatten()
            # message_count = len(history)
            # print(message_count)
            # if message_count > 100:
            #     count = 100
            # else:
            #     count = message_count + int(count) - 1
            # if count <= 0:
            #     return await ctx.send("Sorry, you can not delete a negative amount of messages. This is likely because you are asking to save more messages than there are in the channel.")
        await self._nuke_countdown(ctx, count)
        if STOPNUKE <= datetime.datetime.utcnow():
            await channel.purge(limit=int(count) + 13, check=lambda m: not m.pinned)
            
            msg = await ctx.send("https://media.giphy.com/media/XUFPGrX5Zis6Y/giphy.gif")
            await msg.delete(delay=5)
        
    @commands.command()
    @commands.check(is_nuke_allowed)
    async def nukeuntil(self, ctx, msgid): # prob can use converters to convert the msgid to a Message object
        # TODO: should prob use reply feature to show the message the id is referencing
        # remember, the message is excluded in the nuke
        import datetime
        global STOPNUKE
        channel = ctx.message.channel
        message = await ctx.fetch_message(msgid)
        if channel == message.channel:
            await self._nuke_countdown(ctx)
            if STOPNUKE <= datetime.datetime.utcnow():
                await channel.purge(limit=1000, after=message)
                msg = await ctx.send("https://media.giphy.com/media/XUFPGrX5Zis6Y/giphy.gif")
                await msg.delete(delay=5)
        else:
            return await ctx.send("MESSAGE ID DOES NOT COME FROM THIS TEXT CHANNEL. ABORTING NUKE.")
            
    @nuke.error
    @nukeuntil.error
    async def nuke_error(self, ctx, error):
        ctx.__slots__ = True
        from src.discord.globals import BOT_PREFIX
        print(f"{BOT_PREFIX}nuke error handler: {error}")
        if isinstance(error, discord.ext.commands.MissingAnyRole):
            return await ctx.send("APOLOGIES. INSUFFICIENT RANK FOR NUKE.")
        if isinstance(error, discord.ext.commands.CommandOnCooldown):
            return await ctx.send(f"TRANSMISSION FAILED. ALL NUKES ARE CURRENTLY PAUSED FOR ANOTHER {'%.3f' % error.retry_after} SECONDS. TRY AGAIN LATER.")
        
        ctx.__slots__ = False
    
    @commands.command()
    async def stopnuke(self, ctx):
        import datetime
        global STOPNUKE
        # launcher = await is_launcher(ctx)
        # staff = is_staff()
        # if not (staff or (launcher and ctx.message.channel.name == CHANNEL_WELCOME)):
        #     return await ctx.send("APOLOGIES. INSUFFICIENT RANK FOR STOPPING NUKE.")
        NUKE_COOLDOWN = 20
        STOPNUKE = datetime.datetime.utcnow() + datetime.timedelta(seconds=NUKE_COOLDOWN) # True
        await ctx.send(f"TRANSMISSION RECEIVED. STOPPED ALL CURRENT NUKES FOR {NUKE_COOLDOWN} SECONDS.")
        
        # await asyncio.sleep(15)
        # for i in range(5, 0, -1):
        #     await ctx.send(f"NUKING WILL BE ALLOWED IN {i}. BE WARNED COMMANDER.") # seems a bit much, u think?
        #     await asyncio.sleep(1)
        # STOPNUKE = False
    
    @stopnuke.error
    async def stopnuke_error(self, ctx, error):
        ctx.__slots__ = True
        from src.discord.globals import BOT_PREFIX
        print(f"{BOT_PREFIX}nuke error handler: {error}")
        if isinstance(error, discord.ext.commands.MissingAnyRole):
            return await ctx.send("APOLOGIES. INSUFFICIENT RANK FOR STOPPING NUKE.")
        ctx.__slots__ = False

class StaffCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    # overriding check function
    async def cog_check(self, ctx):
        return is_staff()

class StaffEssential(StaffCommands, name="StaffEsntl"):
    def __init__(self, bot):
        super().__init__(bot)
    
    @commands.command()
    async def kick(self, ctx, user:discord.Member, reason:str=False):
        """Kicks a user for the specified reason."""
        if reason == False:
            return await ctx.send("Please specify a reason why you want to kick this user!")
        if user.id in PI_BOT_IDS:
            return await ctx.send("Hey! You can't kick me!!")
        await user.kick(reason=reason)
        await ctx.send("The user was kicked.")
    
    @commands.command()
    async def exalt(self, ctx, user):
        """Exalts a user."""
        member = ctx.message.author
        role = discord.utils.get(member.guild.roles, name=ROLE_EM)
        iden = await harvest_id(user)
        user_obj = member.guild.get_member(int(iden))
        await user_obj.add_roles(role)
        await ctx.send(f"Successfully exalted. Congratulations {user}! :tada: :tada:")
    
    @commands.command()
    async def unexalt(self, ctx, user):
        """Unexalts a user."""
        member = ctx.message.author
        role = discord.utils.get(member.guild.roles, name=ROLE_EM)
        iden = await harvest_id(user)
        user_obj = member.guild.get_member(int(iden))
        await user_obj.remove_roles(role)
        await ctx.send(f"Successfully unexalted.")    
    
    # Need to find a way to share _mute() between StaffEssential and MemberCommands
    
    @commands.command()
    async def unmute(self, ctx, user):
        """Unmutes a user."""
        member = ctx.message.author
        role = discord.utils.get(member.guild.roles, name=ROLE_MUTED)
        iden = await harvest_id(user)
        user_obj = member.guild.get_member(int(iden))
        await user_obj.remove_roles(role)
        await ctx.send(f"Successfully unmuted {user}.")
        
    @commands.command()
    async def ban(self, ctx, member:discord.User=None, reason=None, *args):
        """Bans a user."""
        time = " ".join(args)
        if member == None or member == ctx.message.author:
            return await ctx.channel.send("You cannot ban yourself! >:(")
        if reason == None:
            return await ctx.send("You need to give a reason for you banning this user.")
        if time == None:
            return await ctx.send("You need to specify a length that this used will be banned. Examples are: `1 day`, `2 months, 1 day`, or `indef` (aka, forever).")
        if member.id in PI_BOT_IDS:
            return await ctx.send("Hey! You can't ban me!!")
        message = f"You have been banned from the Scioly.org Discord server for {reason}."
        parsed = "indef"
        if time != "indef":
            parsed = dateparser.parse(time, settings={"PREFER_DATES_FROM": "future"})
            if parsed == None:
                return await ctx.send(f"Sorry, but I don't understand the length of time: `{time}`.")
            CRON_LIST.append({"date": parsed, "do": f"unban {member.id}"})
        await member.send(message)
        await ctx.guild.ban(member, reason=reason)
        eastern = pytz.timezone("US/Eastern")
        await ctx.channel.send(f"**{member}** is banned until `{str(eastern.localize(parsed))} EST`.")
    
    @commands.command()
    async def unban(self, ctx, member:discord.User=None):
        """Unbans a user."""
        if member == None:
            await ctx.channel.send("Please give either a user ID or mention a user.")
            return
        await ctx.guild.unban(member)
        await ctx.channel.send(f"Inverse ban hammer applied, user unbanned. Please remember that I cannot force them to re-join the server, they must join themselves.")
        
    @commands.command()
    async def clrreact(self, ctx, msg: discord.Message, *args: discord.Member):
        """
        Clears all reactions from a given message.
    
        :param msg: the message containing the reactions
        :type msg: discord.Message
        :param *args: list of users to clear reactions of
        :type *args: List[discord.Member], optional
        """
        users = args
        if (not users):
            await msg.clear_reactions()
            await ctx.send("Cleared all reactions on message.")
        else:
            for u in users:
                for r in msg.reactions:
                    await r.remove(u)
            await ctx.send(f"Cleared reactions on message from {len(users)} user(s).")
            
    @commands.command()
    async def mute(self, ctx, user:discord.Member, *args):
        """
        Mutes a user.
    
        :param user: User to be muted.
        :type user: discord.Member
        :param *args: The time to mute the user for.
        :type *args: str
        """
        time = " ".join(args)
        await _mute(ctx, user, time, self=False)
        
    @commands.command(aliases=["slow", "sm"])
    async def slowmode(self, ctx, arg:int=None):
        if arg == None:
            if ctx.channel.slowmode_delay == 0:
                await ctx.channel.edit(slowmode_delay=10)
                await ctx.send("Enabled a 10 second slowmode.")
            else:
                await ctx.channel.edit(slowmode_delay=0)
                await ctx.send("Removed slowmode.")
        else:
            await ctx.channel.edit(slowmode_delay=arg)
            if arg != 0:
                await ctx.send(f"Enabled a {arg} second slowmode.")
            else:
                await ctx.send(f"Removed slowmode.")

class StaffNonessential(StaffCommands, name="StaffNonesntl"):
    def __init__(self, bot):
        super().__init__(bot)
    
    @commands.command()
    async def vc(self, ctx):
        server = ctx.message.guild
        if ctx.message.channel.category.name == CATEGORY_TOURNAMENTS:
            test_vc = discord.utils.get(server.voice_channels, name=ctx.message.channel.name)
            if test_vc == None:
                # Voice channel needs to be opened
                new_vc = await server.create_voice_channel(ctx.message.channel.name, category=ctx.message.channel.category)
                await new_vc.edit(sync_permissions=True)
                # Make the channel invisible to normal members
                await new_vc.set_permissions(server.default_role, view_channel=False)
                at = discord.utils.get(server.roles, name=ROLE_AT)
                for t in TOURNAMENT_INFO:
                    if ctx.message.channel.name == t[1]:
                        tourney_role = discord.utils.get(server.roles, name=t[0])
                        await new_vc.set_permissions(tourney_role, view_channel=True)
                        break
                await new_vc.set_permissions(at, view_channel=True)
                return await ctx.send("Created a voice channel. **Please remember to follow the rules! No doxxing or cursing is allowed.**")
            else:
                # Voice channel needs to be closed
                await test_vc.delete()
                return await ctx.send("Closed the voice channel.")
        elif ctx.message.channel.category.name == CATEGORY_STATES:
            test_vc = discord.utils.get(server.voice_channels, name=ctx.message.channel.name)
            if test_vc == None:
                # Voice channel does not currently exist
                if len(ctx.message.channel.category.channels) == 50:
                    # Too many voice channels in the state category
                    # Let's move one state to the next category
                    new_cat = filter(lambda x: x.name == "states", server.categories)
                    new_cat = list(new_cat)
                    if len(new_cat) < 2: 
                        return await ctx.send("Could not find alternate states channel to move overflowed channels to.")
                    else:
                        # Success, we found the other category
                        current_cat = ctx.message.channel.category
                        await current_cat.channels[-1].edit(category = new_cat[1], position = 0)
                new_vc = await server.create_voice_channel(ctx.message.channel.name, category=ctx.message.channel.category)
                await new_vc.edit(sync_permissions=True)
                await new_vc.set_permissions(server.default_role, view_channel=False)
                muted_role = discord.utils.get(server.roles, name=ROLE_MUTED)
                all_states_role = discord.utils.get(server.roles, name=ROLE_ALL_STATES)
                self_muted_role = discord.utils.get(server.roles, name=ROLE_SELFMUTE)
                quarantine_role = discord.utils.get(server.roles, name=ROLE_QUARANTINE)
                state_role_name = await lookup_role(ctx.message.channel.name.replace("-", " "))
                state_role = discord.utils.get(server.roles, name = state_role_name)
                await new_vc.set_permissions(muted_role, connect=False)
                await new_vc.set_permissions(self_muted_role, connect=False)
                await new_vc.set_permissions(quarantine_role, connect=False)
                await new_vc.set_permissions(state_role, view_channel = True, connect=True)
                await new_vc.set_permissions(all_states_role, view_channel = True, connect=True)
                current_pos = ctx.message.channel.position
                return await ctx.send("Created a voice channel. **Please remember to follow the rules! No doxxing or cursing is allowed.**")
            else:
                await test_vc.delete()
                if len(ctx.message.channel.category.channels) == 49:
                    # If we had to move a channel out of category to make room, move it back
                    # Let's move one state to the next category
                    new_cat = filter(lambda x: x.name == "states", server.categories)
                    new_cat = list(new_cat)
                    if len(new_cat) < 2: 
                        return await ctx.send("Could not find alternate states channel to move overflowed channels to.")
                    else:
                        # Success, we found the other category
                        current_cat = ctx.message.channel.category
                        await new_cat[1].channels[0].edit(category = current_cat, position = 1000)
                return await ctx.send("Closed the voice channel.")
        elif ctx.message.channel.name == "games":
            # Support for opening a voice channel for #games
            test_vc = discord.utils.get(server.voice_channels, name="games")
            if test_vc == None:
                # Voice channel needs to be opened/doesn't exist already
                new_vc = await server.create_voice_channel("games", category=ctx.message.channel.category)
                await new_vc.edit(sync_permissions=True)
                await new_vc.set_permissions(server.default_role, view_channel=False)
                games_role = discord.utils.get(server.roles, name=ROLE_GAMES)
                member_role = discord.utils.get(server.roles, name=ROLE_MR)
                await new_vc.set_permissions(games_role, view_channel=True)
                await new_vc.set_permissions(member_role, view_channel=False)
                return await ctx.send("Created a voice channel. **Please remember to follow the rules! No doxxing or cursing is allowed.**")
            else:
                # Voice channel needs to be closed
                await test_vc.delete()
                return await ctx.send("Closed the voice channel.")
        else:
            return await ctx.send("Apologies... voice channels can currently be opened for tournament channels and the games channel.")
    
    @commands.command()
    async def getVariable(self, ctx, var):
        """Fetches a local variable."""
        if ctx.message.channel.name != "staff":
            await ctx.send("You can only fetch variables from the staff channel.")
        else:
            await ctx.send("Attempting to find variable.")
            try:
                variable = globals()[var]
                await ctx.send(f"Variable value: `{variable}`")
            except:
                await ctx.send(f"Can't find that variable!")
    
    @commands.command(aliases=["ufi"])
    async def userfromid(self, ctx, iden:int):
        """Mentions a user with the given ID."""
        user = bot.get_user(iden)
        await ctx.send(user.mention)
    
    @commands.command()
    async def lock(self, ctx):
        """Locks a channel to Member access."""
        member = ctx.message.author
        channel = ctx.message.channel

        if (channel.category.name in ["beta", "staff", "Pi-Bot"]):
            return await ctx.send("This command is not suitable for this channel because of its category.")

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
        await ctx.send("Locked the channel to Member access.")
    
    @commands.command()
    async def unlock(self, ctx):
        """Unlocks a channel to Member access."""
        member = ctx.message.author
        channel = ctx.message.channel
    
        if (channel.category.name in ["beta", "staff", "Pi-Bot"]):
            return await ctx.send("This command is not suitable for this channel because of its category.")
    
        if (channel.category.name == CATEGORY_SO or channel.category.name == CATEGORY_GENERAL):
            await ctx.send("Synced permissions with channel category.")
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
        await ctx.send("Unlocked the channel to Member access. Please check if permissions need to be synced.")
    
    @commands.command()
    async def met(self, ctx):
        """Runs Pi-Bot's Most Edits Table"""
        msg1 = await ctx.send("Attemping to run the Most Edits Table.")
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
    
    @commands.command()
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
        await ctx.message.delete()
    
    # cant fully test this command due to lack of access
    @commands.command()
    async def refresh(self, ctx):
        """Refreshes data from the sheet."""
        await update_tournament_list(ctx.bot)
        res = await refresh_algorithm()
        if res == True:
            await ctx.send("Successfully refreshed data from sheet.")
        else:
            await ctx.send(":warning: Unsuccessfully refreshed data from sheet.")
    
    # cant fully test this command due to lack of access
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
        
    # cant fully test this command due to lack of access
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