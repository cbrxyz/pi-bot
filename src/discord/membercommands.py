import discord
import aiohttp
import re
import datetime
from discord.commands import Option
import random
import wikipedia as wikip
from discord.ext import commands
import src.discord.globals
from src.discord.globals import CHANNEL_TOURNAMENTS, CHANNEL_ROLES, CHANNEL_UNSELFMUTE, ROLE_SELFMUTE, TOURNAMENT_INFO, ROLE_PRONOUN_HE, ROLE_PRONOUN_SHE, ROLE_PRONOUN_THEY, PI_BOT_IDS, ROLE_DIV_A, ROLE_DIV_B, ROLE_DIV_C, ROLE_ALUMNI, EMOJI_FAST_REVERSE, EMOJI_FAST_FORWARD, EMOJI_LEFT_ARROW, EMOJI_RIGHT_ARROW, ROLE_GAMES, CHANNEL_GAMES, RULES, CATEGORY_STAFF, SERVER_ID, CHANNEL_REPORTS, REPORTS, EVENT_INFO, ROLE_LH, ROLE_MR, TAGS, SLASH_COMMAND_GUILDS
from embed import assemble_embed
from src.discord.utils import harvest_id
from src.discord.views import YesNo
from src.wiki.wiki import get_page_tables
from src.wiki.scilympiad import make_results_template, get_points
from src.wiki.schools import get_school_listing
from src.mongo.mongo import insert
from commands import get_list, get_quick_list, get_help
from lists import get_state_list
from src.discord.utils import lookup_role
from src.discord.mute import _mute
from commandchecks import is_staff
from commanderrors import SelfMuteCommandStaffInvoke

from typing import Type
from src.discord.tournaments import update_tournament_list
from src.discord.utils import auto_report
from info import get_about
from src.wiki.wiki import implement_command
from aioify import aioify

class MemberCommands(commands.Cog, name='Member'):
    def __init__(self, bot):
        self.bot = bot
        self.aiowikip = aioify(obj=wikip)
        print("Member commands loaded")

    @commands.Cog.listener()
    async def on_message(self, message):
        pass

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Looking for help? Try this!"
    )
    async def help(self,
        ctx
        ):
        """Allows a user to request help for a command."""
        server = self.bot.get_guild(SERVER_ID)
        invitationals_channel = discord.utils.get(server.text_channels, name = CHANNEL_TOURNAMENTS)
        roles_channel = discord.utils.get(server.text_channels, name = CHANNEL_ROLES)

        help_embed = discord.Embed(
            title = "Looking for help?",
            color = discord.Color(0x2E66B6),
            description = f"""
            Hey there, I'm Scioly.org's resident bot, and I'm here to assist with all of your needs.

            To interact with me, use _slash commands_ by typing `/` and the name of the command into the text bar below. You can also use the dropdowns in the {invitationals_channel.mention} and {roles_channel.mention} channels to assign yourself roles!

            If you're looking for more help, feel free to ask other members (including our helpful staff members) for more information.
            """
        )

        return await ctx.interaction.response.send_message(embed = help_embed)

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Toggles your pronoun roles."
    )
    async def pronouns(self,
        ctx,
        pronouns: Option(str, "The pronoun to add/remove from your account.", choices = [ROLE_PRONOUN_HE, ROLE_PRONOUN_SHE, ROLE_PRONOUN_THEY], required = True)
        ):
        """Assigns or removes pronoun roles from a user."""
        member = ctx.author
        pronoun_role = discord.utils.get(member.guild.roles, name=pronouns)
        if pronoun_role in member.roles:
            await member.remove_roles(pronoun_role)
            await ctx.interaction.response.send_message(content = f"Removed your `{pronouns}` role.")
        else:
            await member.add_roles(pronoun_role)
            await ctx.interaction.response.send_message(content = f"Added the `{pronouns}` role to your profile.")

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Gets the profile information for a username."
    )
    async def profile(self,
        ctx,
        username: Option(str, "The username to get information about. Defaults to your nickname/username.", required = True)
        ):
        if username == None:
            member = ctx.author
            username = member.nick
            if username == None:
                username = member.name

        session = aiohttp.ClientSession()
        page = await session.get(f"https://scioly.org/forums/memberlist.php?mode=viewprofile&un={username}")
        await session.close()
        if page.status > 400:
            return await ctx.interaction.response.send_message(content = f"Sorry, I couldn't find a user by the username of `{username}`.")
        text = await page.content.read()
        text = text.decode('utf-8')

        description = ""
        total_posts_matches = re.search(r"(?:<dt>Total posts:<\/dt>\s+<dd>)(\d+)", text, re.MULTILINE)
        if total_posts_matches == None:
            return await ctx.interaction.response.send_message(content = f"Sorry, I couldn't find a user by the username of `{username}`.")
        else:
            description += f"**Total Posts:** `{total_posts_matches.group(1)} posts`\n"

        has_thanked_matches = re.search(r"Has thanked: <a.*?>(\d+)", text, re.MULTILINE)
        description += f"**Has Thanked:** `{has_thanked_matches.group(1)} times`\n"

        been_thanked_matches = re.search(r"Been(?:&nbsp;)?thanked: <a.*?>(\d+)", text, re.MULTILINE)
        description += f"**Been Thanked:** `{been_thanked_matches.group(1)} times`\n"

        date_regexes = [
            {"name": "Joined", "regex": r"<dt>Joined:</dt>\s+<dd>(.*?)</dd>"},
            {"name": "Last Active", "regex": r"<dt>Last active:</dt>\s+<dd>(.*?)</dd>"},
        ]
        for pattern in date_regexes:
            try:
                matches = re.search(pattern["regex"], text, re.MULTILINE)
                raw_dt_string = matches.group(1)
                raw_dt_string = raw_dt_string.replace("st", "")
                raw_dt_string = raw_dt_string.replace("nd", "")
                raw_dt_string = raw_dt_string.replace("rd", "")
                raw_dt_string = raw_dt_string.replace("th", "")

                raw_dt = datetime.datetime.strptime(raw_dt_string, "%B %d, %Y, %I:%M %p")
                description += f"**{pattern['name']}:** {discord.utils.format_dt(raw_dt, 'R')}\n"
            except:
                # Occurs if the time can't be parsed/found
                pass

        for i in range(1, 7):
            stars_matches = re.search(rf"<img src=\"./images/ranks/stars{i}\.gif\"", text, re.MULTILINE)
            if stars_matches != None:
                description += f"\n**Stars:** {i * ':star:'}"
                break
            exalts_matches = re.search(rf"<img src=\"./images/ranks/exalt{i}\.gif\"", text, re.MULTILINE)
            if exalts_matches != None:
                description += f"\n**Stars:** {4 * ':star:'}\n" # All exalts have 4 stars
                description += f"**Medals:** {i * ':medal:'}"
                break

        profile_embed = discord.Embed(
            title = f"`{username}`",
            color = discord.Color(0x2E66B6),
            description = description
        )

        avatar_matches = re.search(r"<img class=\"avatar\" src=\"(.*?)\"", text, re.MULTILINE)
        if avatar_matches != None:
            profile_embed.set_thumbnail(url = "https://scioly.org/forums" + avatar_matches.group(1)[1:])

        await ctx.interaction.response.send_message(embed = profile_embed)

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Returns the number of members in the server."
    )
    async def count(self, ctx):
        guild = ctx.author.guild
        await ctx.interaction.response.send_message(content = f"Currently, there are `{len(guild.members)}` members in the server.")

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Toggles the Alumni role."
    )
    async def alumni(self, ctx):
        """Removes or adds the alumni role from a user."""
        member = ctx.author
        div_a_role = discord.utils.get(member.guild.roles, name=ROLE_DIV_A)
        div_b_role = discord.utils.get(member.guild.roles, name=ROLE_DIV_B)
        div_c_role = discord.utils.get(member.guild.roles, name=ROLE_DIV_C)
        await member.remove_roles(div_a_role, div_b_role, div_c_role)
        role = discord.utils.get(member.guild.roles, name=ROLE_ALUMNI)
        if role in member.roles:
            await member.remove_roles(role)
            await ctx.interaction.response.send_message(content = "Removed your alumni status.")
        else:
            await member.add_roles(role)
            await ctx.interaction.response.send_message(content = f"Added the alumni role, and removed all other division roles.")

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Toggles division roles for the user."
    )
    async def division(self,
        ctx,
        div: Option(str, "The division to assign the user with.", choices = ["Division A", "Division B", "Division C", "Alumni", "None"], required = True)
        ):
        if div == "Division A":
            res = await self._assign_div(ctx, "Division A")
            await ctx.interaction.response.send_message(content = "Assigned you the Division A role, and removed all other divison/alumni roles.")
        elif div == "Division B":
            res = await self._assign_div(ctx, "Division B")
            await ctx.interaction.response.send_message(content = "Assigned you the Division B role, and removed all other divison/alumni roles.")
        elif div == "Division C":
            res = await self._assign_div(ctx, "Division C")
            await ctx.interaction.response.send_message(content = "Assigned you the Division C role, and removed all other divison/alumni roles.")
        elif div == "Alumni":
            res = await self._assign_div(ctx, "Alumni")
            await ctx.interaction.response.send_message(content = "Assigned you the Alumni role, and removed all other divison/alumni roles.")
        elif div == "None":
            member = ctx.author
            div_a_role = discord.utils.get(member.guild.roles, name=ROLE_DIV_A)
            div_b_role = discord.utils.get(member.guild.roles, name=ROLE_DIV_B)
            div_c_role = discord.utils.get(member.guild.roles, name=ROLE_DIV_C)
            alumni_role = discord.utils.get(member.guild.roles, name=ROLE_ALUMNI)
            await member.remove_roles(div_a_role, div_b_role, div_c_role, alumni_role)
            await ctx.interaction.response.send_message(content = "Removed all of your division/alumni roles.")

    async def _assign_div(self, ctx, div):
        """Assigns a user a div"""
        member = ctx.author
        role = discord.utils.get(member.guild.roles, name=div)
        div_a_role = discord.utils.get(member.guild.roles, name=ROLE_DIV_A)
        div_b_role = discord.utils.get(member.guild.roles, name=ROLE_DIV_B)
        div_c_role = discord.utils.get(member.guild.roles, name=ROLE_DIV_C)
        alumni_role = discord.utils.get(member.guild.roles, name=ROLE_ALUMNI)
        await member.remove_roles(div_a_role, div_b_role, div_c_role, alumni_role)
        await member.add_roles(role)
        return True

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Toggles the visibility of the #games channel."
    )
    async def games(self, ctx):
        """Removes or adds someone to the games channel."""
        games_channel = discord.utils.get(ctx.author.guild.text_channels, name=CHANNEL_GAMES)
        member = ctx.author
        role = discord.utils.get(member.guild.roles, name=ROLE_GAMES)
        if role in member.roles:
            await member.remove_roles(role)
            await ctx.interaction.response.send_message(content = "Removed you from the games club... feel free to come back anytime!")
            await games_channel.send(f"{member.mention} left the party.")
        else:
            await member.add_roles(role)
            await ctx.interaction.response.send_message(content = f"You are now in the channel. Come and have fun in {games_channel.mention}! :tada:")
            await games_channel.send(f"Please welcome {member.mention} to the party!!")

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Toggles the visibility of state roles and channels."
    )
    async def states(self,
        ctx,
        states: Option(str, "The states to toggle. For example 'Missouri, Iowa, South Dakota'.`", required = True)
        ):
        """Assigns someone with specific states."""
        new_args = states.split(",")
        new_args = [re.sub("[;,]", "", arg) for arg in new_args]
        new_args = [arg.strip() for arg in new_args]

        member = ctx.author
        states = await get_state_list()
        states = [s[:s.rfind(" (")] for s in states]
        triple_word_states = [s for s in states if len(s.split(" ")) > 2]
        double_word_states = [s for s in states if len(s.split(" ")) > 1]
        removed_roles = []
        added_roles = []
        for term in ["california", "ca", "cali"]:
            if term in [arg.lower() for arg in new_args]:
                return await ctx.interaction.response.send_message("Which California, North or South? Try `/state norcal` or `/state socal`.")
        if len(new_args) > 10:
            return await ctx.interaction.response.send_message("Sorry, you are attempting to add/remove too many states at once.")
        for string in ["South", "North"]:
            california_list = [f"California ({string})", f"California-{string}", f"California {string}", f"{string}ern California", f"{string} California", f"{string} Cali", f"Cali {string}", f"{string} CA", f"CA {string}"]
            if string == "North":
                california_list.append("NorCal")
            else:
                california_list.append("SoCal")
            for listing in california_list:
                words = listing.split(" ")
                all_here = sum(1 for word in words if word.lower() in new_args)
                if all_here == len(words):
                    role = discord.utils.get(member.guild.roles, name=f"California ({string})")
                    if role in member.roles:
                        await member.remove_roles(role)
                        removed_roles.append(f"California ({string})")
                    else:
                        await member.add_roles(role)
                        added_roles.append(f"California ({string})")
                    for word in words:
                        new_args.remove(word.lower())
        for triple in triple_word_states:
            words = triple.split(" ")
            all_here = 0
            all_here = sum(1 for word in words if word.lower() in new_args)
            if all_here == 3:
                # Word is in args
                role = discord.utils.get(member.guild.roles, name=triple)
                if role in member.roles:
                    await member.remove_roles(role)
                    removed_roles.append(triple)
                else:
                    await member.add_roles(role)
                    added_roles.append(triple)
                for word in words:
                    new_args.remove(word.lower())
        for double in double_word_states:
            words = double.split(" ")
            all_here = 0
            all_here = sum(1 for word in words if word.lower() in new_args)
            if all_here == 2:
                # Word is in args
                role = discord.utils.get(member.guild.roles, name=double)
                if role in member.roles:
                    await member.remove_roles(role)
                    removed_roles.append(double)
                else:
                    await member.add_roles(role)
                    added_roles.append(double)
                for word in words:
                    new_args.remove(word.lower())
        for arg in new_args:
            role_name = await lookup_role(arg)
            if role_name == False:
                return await ctx.interaction.response.send_message(f"Sorry, the `{arg}` state could not be found. Try again.")
            role = discord.utils.get(member.guild.roles, name=role_name)
            if role in member.roles:
                await member.remove_roles(role)
                removed_roles.append(role_name)
            else:
                await member.add_roles(role)
                added_roles.append(role_name)
        if len(added_roles) > 0 and len(removed_roles) == 0:
            state_res = "Added states " + (' '.join([f'`{arg}`' for arg in added_roles])) + "."
        elif len(removed_roles) > 0 and len(added_roles) == 0:
            state_res = "Removed states " + (' '.join([f'`{arg}`' for arg in removed_roles])) + "."
        else:
            state_res = "Added states " + (' '.join([f'`{arg}`' for arg in added_roles])) + ", and removed states " + (' '.join([f'`{arg}`' for arg in removed_roles])) + "."
        await ctx.interaction.response.send_message(state_res)

    def is_not_staff(exception: Type[commands.CommandError], message: str):
        async def predicate(ctx):
            if not is_staff():
                return True
            raise exception(message)
        return commands.check(predicate)

    #@is_not_staff(SelfMuteCommandStaffInvoke, "A staff member attempted to invoke selfmute.")
    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Mutes yourself."
    )
    async def selfmute(self,
        ctx,
        mute_length: Option(str, "How long to mute yourself for.", choices = [
            "10 minutes",
            "30 minutes",
            "1 hour",
            "2 hours",
            "8 hours",
            "1 day",
            "4 days",
            "7 days",
            "1 month",
            "1 year"
        ])
        ):
        """
        Self mutes the user that invokes the command.
        """
        member = ctx.author

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
        selected_time = times[mute_length]

        original_shown_embed = discord.Embed(
            title = "Mute Confirmation",
            color = discord.Color.brand_red(),
            description = f"""
            You will be muted across the entire server. You will no longer be able to communicate in any channels you can read until {discord.utils.format_dt(selected_time)}.
            """
        )

        view = YesNo()
        await ctx.interaction.response.send_message(content = "Please confirm that you would like to mute yourself.", view = view, embed = original_shown_embed, ephemeral = True)

        await view.wait()
        if view.value:
            try:
                role = discord.utils.get(member.guild.roles, name=ROLE_SELFMUTE)
                unselfmute_channel = discord.utils.get(member.guild.text_channels, name = CHANNEL_UNSELFMUTE)
                await member.add_roles(role)
                await insert("data", "cron",
                    {
                        "type": "UNSELFMUTE",
                        "user": member.id,
                        "time": times[mute_length],
                        "tag": str(member)
                    }
                )
                return await ctx.interaction.edit_original_message(content = f"You have been muted. You may use the button in the {unselfmute_channel} channel to unmute.", embed = None, view = None)
            except:
                pass

        return await ctx.interaction.edit_original_message(content = f"The operation was cancelled, and you can still speak throughout the server.", embed = None, view = None)

    async def cog_command_error(self, ctx, error):
        if isinstance(error, SelfMuteCommandStaffInvoke):
            return await ctx.send("Staff members can't self mute.")

    @commands.command(aliases=["tc", "tourney", "tournaments"])
    async def tournament(self, ctx, *args):
        member = ctx.message.author
        new_args = list(args)
        ignore_terms = ["invitational", "invy", "tournament", "regional", "invite"]
        for term in ignore_terms:
            if term in new_args:
                new_args.remove(term)
                await ctx.send(f"Ignoring `{term}` because it is too broad of a term. *(If you need help with this command, please type `!help tournament`)*")
        if len(args) == 0:
            return await ctx.send("Please specify the tournaments you would like to be added/removed from!")
        for arg in new_args:
            # Stop users from possibly adding the channel hash in front of arg
            arg = arg.replace("#", "")
            arg = arg.lower()
            found = False
            if arg == "all":
                role = discord.utils.get(member.guild.roles, name=ROLE_AT)
                if role in member.roles:
                    await ctx.send(f"Removed your `All Tournaments` role.")
                    await member.remove_roles(role)
                else:
                    await ctx.send(f"Added your `All Tournaments` role.")
                    await member.add_roles(role)
                continue
            for t in TOURNAMENT_INFO:
                if arg == t[1]:
                    found = True
                    role = discord.utils.get(member.guild.roles, name=t[0])
                    if role == None:
                        return await ctx.send(f"Apologies! The `{t[0]}` channel is currently not available.")
                    if role in member.roles:
                        await ctx.send(f"Removed you from the `{t[0]}` channel.")
                        await member.remove_roles(role)
                    else:
                        await ctx.send(f"Added you to the `{t[0]}` channel.")
                        await member.add_roles(role)
                    break
            if not found:
                uid = member.id
                found2 = False
                votes = 1
                # for t in REQUESTED_TOURNAMENTS: TODO Fix this for v5
                for t in range(0, 1):
                    if arg == t['iden']:
                        found2 = True
                        if uid in t['users']:
                            return await ctx.send("Sorry, but you can only vote once for a specific tournament!")
                        t['count'] += 1
                        t['users'].append(uid)
                        votes = t['count']
                        break
                if not found2:
                    await auto_report(ctx.bot, "New Tournament Channel Requested", "orange", f"User ID {uid} requested tournament channel `#{arg}`.\n\nTo add this channel to the voting list for the first time, use `!tla {arg} {uid}`.\nIf the channel has already been requested in the list and this was a user mistake, use `!tla [actual name] {uid}`.")
                    return await ctx.send(f"Made request for a `#{arg}` channel. Please note your submission may not instantly appear.")
                await ctx.send(f"Added a vote for `{arg}`. There " + ("are" if votes != 1 else "is") + f" now `{votes}` " + (f"votes" if votes != 1 else f"vote") + " for this channel.")
                await update_tournament_list(ctx.bot, {})

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Returns information about the bot and server."
    )
    async def about(self, ctx):
        """Prints information about the bot."""
        avatar_url = self.bot.user.display_avatar.url
        await ctx.interaction.response.send_message(embed = get_about(avatar_url))

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Returns the Discord server invite."
    )
    async def invite(self, ctx):
        await ctx.interaction.response.send_message("https://discord.gg/C9PGV6h")

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Returns a link to the Scioly.org forums."
    )
    async def link(self,
        ctx,
        destination: Option(str, "The area of the site to link to.", choices = ["forums", "exchange", "gallery", "obb", "wiki", "tests"], required = True)
        ):
        if destination == "forums":
            await ctx.interaction.response.send_message("<https://scioly.org/forums>")
        elif destination == "wiki":
            await ctx.interaction.response.send_message("<https://scioly.org/wiki>")
        elif destination == "tests":
            await ctx.interaction.response.send_message("<https://scioly.org/tests>")
        elif destination == "exchange":
            await ctx.interaction.response.send_message("<https://scioly.org/tests>")
        elif destination == "gallery":
            await ctx.interaction.response.send_message("<https://scioly.org/gallery>")
        elif destination == "obb":
            await ctx.interaction.response.send_message("<https://scioly.org/obb>")

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Returns a random number, inclusively."
    )
    async def random(self,
        ctx,
        minimum: Option(int, "The minimum number to choose from. Defaults to 0.", required = False),
        maximum: Option(int, "The maximum number to choose from. Defaults to 10.", required = False),
        ):
        if minimum == None:
            minimum = 0
        if maximum == None:
            maximum = 10
        num = random.randrange(minimum, maximum + 1)
        await ctx.interaction.response.send_message(f"Random number between `{minimum}` and `{maximum}`: `{num}`")

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Returns information about a given rule."
    )
    async def rule(self, 
        ctx, 
        rule: Option(str, "The rule to cite.", choices = [
            "Rule #1: Treat all with respect.",
            "Rule #2: No profanity/innapropriateness.",
            "Rule #3: Treat delicate subjects carefully.",
            "Rule #4: Do not spam or flood.",
            "Rule #5: Avoid excessive pinging.",
            "Rule #6: Avoid excessive caps.",
            "Rule #7: No doxxing/name-dropping.",
            "Rule #8: No witch-hunting.",
            "Rule #9: No impersonating.",
            "Rule #10: Do not use alts.",
            "Rule #11: Do not violate SOINC copyrights.",
            "Rule #12: No advertising.",
            "Rule #13: Use good judgement."
        ])
        ):
        """Gets a specified rule."""
        num = re.findall(r'Rule #(\d+)', rule)
        num = int(num[0])
        rule = RULES[int(num) - 1]
        return await ctx.interaction.response.send_message(f"**Rule {num}:**\n> {rule}")

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Information about gaining the @Coach role."
    )
    async def coach(self, ctx):
        """Gives an account the coach role."""
        await ctx.interaction.response.send_message("If you would like to apply for the `Coach` role, please fill out the form here: <https://forms.gle/UBKpWgqCr9Hjw9sa6>.", ephemeral = True)

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Information about the current server."
    )
    async def info(self, ctx):
        """Gets information about the Discord server."""
        server = ctx.guild
        name = server.name
        owner = server.owner
        creation_date = discord.utils.format_dt(server.created_at, 'R')
        emoji_count = len(server.emojis)
        icon = server.icon.url
        animated_icon = server.icon.is_animated()
        iden = server.id
        banner = server.banner.url if server.banner != None else "None"
        desc = server.description
        mfa_level = server.mfa_level
        verification_level = server.verification_level
        content_filter = server.explicit_content_filter
        default_notifs = server.default_notifications
        features = server.features
        splash = server.splash.url if server.splash != None else "None"
        premium_level = server.premium_tier
        boosts = server.premium_subscription_count
        channel_count = len(server.channels)
        text_channel_count = len(server.text_channels)
        voice_channel_count = len(server.voice_channels)
        category_count = len(server.categories)
        system_channel = server.system_channel
        if type(system_channel) == discord.TextChannel: system_channel = system_channel.mention
        rules_channel = server.rules_channel
        if type(rules_channel) == discord.TextChannel: rules_channel = rules_channel.mention
        public_updates_channel = server.public_updates_channel
        if type(public_updates_channel) == discord.TextChannel: public_updates_channel = public_updates_channel.mention
        emoji_limit = server.emoji_limit
        bitrate_limit = server.bitrate_limit
        filesize_limit = round(server.filesize_limit/1000000, 3)
        boosters = server.premium_subscribers
        for i, b in enumerate(boosters):
            # convert user objects to mentions
            boosters[i] = b.mention
        boosters = ", ".join(boosters)
        print(boosters)
        role_count = len(server.roles)
        member_count = len(server.members)
        max_members = server.max_members
        discovery_splash_url = server.discovery_splash.url if server.discovery_splash != None else "None"
        member_percentage = round(member_count/max_members * 100, 3)
        emoji_percentage = round(emoji_count/emoji_limit * 100, 3)
        channel_percentage = round(channel_count/500 * 100, 3)
        role_percenatege = round(role_count/250 * 100, 3)

        fields = [
                {
                    "name": "Basic Information",
                    "value": (
                        f"**Creation Date:** {creation_date}\n" +
                        f"**ID:** {iden}\n" +
                        f"**Animated Icon:** {animated_icon}\n" +
                        f"**Banner URL:** {banner}\n" +
                        f"**Splash URL:** {splash}\n" +
                        f"**Discovery Splash URL:** {discovery_splash_url}"
                    ),
                    "inline": False
                },
                {
                    "name": "Nitro Information",
                    "value": (
                        f"**Nitro Level:** {premium_level} ({boosts} individual boosts)\n" +
                        f"**Boosters:** {boosters}"
                    ),
                    "inline": False
                }
            ]
        if ctx.channel.category.name == CATEGORY_STAFF:
            fields.extend(
                [{
                    "name": "Staff Information",
                    "value": (
                        f"**Owner:** {owner}\n" +
                        f"**MFA Level:** {mfa_level}\n" +
                        f"**Verification Level:** {verification_level}\n" +
                        f"**Content Filter:** {content_filter}\n" +
                        f"**Default Notifications:** {default_notifs}\n" +
                        f"**Features:** {features}\n" +
                        f"**Bitrate Limit:** {bitrate_limit}\n" +
                        f"**Filesize Limit:** {filesize_limit} MB"
                    ),
                    "inline": False
                },
                {
                    "name": "Channels",
                    "value": (
                        f"**Public Updates Channel:** {public_updates_channel}\n" +
                        f"**System Channel:** {system_channel}\n" +
                        f"**Rules Channel:** {rules_channel}\n" +
                        f"**Text Channel Count:** {text_channel_count}\n" +
                        f"**Voice Channel Count:** {voice_channel_count}\n" +
                        f"**Category Count:** {category_count}\n"
                    ),
                    "inline": False
                },
                {
                    "name": "Limits",
                    "value": (
                        f"**Channels:** *{channel_percentage}%* ({channel_count}/500 channels)\n" +
                        f"**Members:** *{member_percentage}%* ({member_count}/{max_members} members)\n" +
                        f"**Emoji:** *{emoji_percentage}%* ({emoji_count}/{emoji_limit} emojis)\n" +
                        f"**Roles:** *{role_percenatege}%* ({role_count}/250 roles)"
                    ),
                    "inline": False
                }
            ])

        embed = discord.Embed(
            title=f"Information for `{name}`",
            description=f"**Description:** {desc}",
        )
        embed.set_thumbnail(url = icon)
        for field in fields:
            embed.add_field(**field)

        await ctx.interaction.response.send_message(embed=embed)

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Returns a summary of a wiki page."
    )
    async def wikisummary(
        self,
        ctx,
        page: Option(str, "The name of the page to return a summary about. Correct caps must be used.", required = True)
    ):
        command = await implement_command("summary", page)
        if command == False:
            await ctx.interaction.response.send_message(f"Unfortunately, the `{page}` page does not exist.")
        else:
            await ctx.interaction.response.send_message(" ".join(command))

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Searches the wiki for a particular page."
    )
    async def wikisearch(
        self,
        ctx,
        term: Option(str, "The term to search for across the wiki.", required = True)
    ):
        command = await implement_command("search", term)
        if len(command):
            await ctx.interaction.response.send_message("\n".join([f"`{search}`" for search in command]))
        else:
            await ctx.interaction.response.send_message(f"No pages matching `{term}` were found.")

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Links to a particular wiki page."
    )
    async def wikilink(
        self,
        ctx,
        page: Option(str, "The wiki page to link to. Correct caps must be used.", required = True)
    ):
        command = await implement_command("link", page)
        if command == False:
            await ctx.interaction.response.send_message(f"The `{page}` page does not yet exist.")
        else:
            await ctx.interaction.response.send_message(f"<{self.wiki_url_fix(command)}>")

    def wiki_url_fix(self, url):
        return url.replace("%3A", ":").replace(r"%2F","/")

    @commands.command(aliases=["wp"])
    async def wikipedia(self, ctx, request:str=False, *args):
        term = " ".join(args)
        if request == False:
            return await ctx.send("You must specifiy a command and keyword, such as `!wikipedia search \"Science Olympiad\"`")
        if request == "search":
            return await ctx.send("\n".join([f"`{result}`" for result in self.aiowikip.search(term, results=5)]))
        elif request == "summary":
            try:
                term = term.title()
                page = await self.aiowikip.page(term)
                return await ctx.send(self.aiowikip.summary(term, sentences=3) + f"\n\nRead more on Wikipedia here: <{page.url}>!")
            except wikip.exceptions.DisambiguationError as e:
                return await ctx.send(f"Sorry, the `{term}` term could refer to multiple pages, try again using one of these terms:" + "\n".join([f"`{o}`" for o in e.options]))
            except wikip.exceptions.PageError as e:
                return await ctx.send(f"Sorry, but the `{term}` page doesn't exist! Try another term!")
        else:
            try:
                term = f"{request} {term}".strip()
                term = term.title()
                page = await self.aiowikip.page(term)
                return await ctx.send(f"Sure, here's the link: <{page.url}>")
            except wikip.exceptions.PageError as e:
                return await ctx.send(f"Sorry, but the `{term}` page doesn't exist! Try another term!")
            except wikip.exceptions.DisambiguationError as e:
                return await ctx.send(f"Sorry, but the `{term}` page is a disambiguation page. Please try again!")

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Toggles event roles."
    )
    async def events(self,
        ctx,
        events: Option(str, "The events to toggle. For example, 'anatomy, astro, wq'.")
        ):
        """Adds or removes event roles from a user."""
        if len(events) > 100:
            return await ctx.interaction.response.send_message("Woah, that's a lot for me to handle at once. Please separate your requests over multiple commands.")
        member = ctx.author

        # Fix commas as possible separator
        new_args = events.split(",")
        new_args = [re.sub("[;,]", "", arg) for arg in new_args]
        new_args = [arg.strip() for arg in new_args]

        event_info = src.discord.globals.EVENT_INFO
        event_names = []
        removed_roles = []
        added_roles = []
        could_not_handle = []
        multi_word_events = []

        print(event_info)
        if type(event_info) == int:
            # When the bot starts up, EVENT_INFO is initialized to 0 before receiving the data from the sheet a few seconds later. This lets the user know this.
            return await ctx.interaction.response.send_message("Apologies... refreshing data currently. Try again in a few seconds.")

        for i in range(7, 1, -1):
            # Supports adding 7-word to 2-word long events
            multi_word_events += [e['name'] for e in event_info if len(e['name'].split(" ")) == i]
            for event in multi_word_events:
                words = event.split(" ")
                all_here = 0
                all_here = sum(1 for word in words if word.lower() in new_args)
                if all_here == i:
                    # Word is in args
                    role = discord.utils.get(member.guild.roles, name=event)
                    if role in member.roles:
                        await member.remove_roles(role)
                        removed_roles.append(event)
                    else:
                        await member.add_roles(role)
                        added_roles.append(event)
                    for word in words:
                        new_args.remove(word.lower())
        for arg in new_args:
            found_event = False
            for event in event_info:
                aliases = [alias.lower() for alias in event['aliases']]
                if arg.lower() in aliases or arg.lower() == event['name'].lower():
                    event_names.append(event['name'])
                    found_event = True
                    break
            if not found_event:
                could_not_handle.append(arg)
        for event in event_names:
            role = discord.utils.get(member.guild.roles, name=event)
            if role in member.roles:
                await member.remove_roles(role)
                removed_roles.append(event)
            else:
                await member.add_roles(role)
                added_roles.append(event)
        if len(added_roles) > 0 and len(removed_roles) == 0:
            event_res = "Added events " + (' '.join([f'`{arg}`' for arg in added_roles])) + ((", and could not handle: " + " ".join([f"`{arg}`" for arg in could_not_handle])) if len(could_not_handle) else "") + "."
        elif len(removed_roles) > 0 and len(added_roles) == 0:
            event_res = "Removed events " + (' '.join([f'`{arg}`' for arg in removed_roles])) + ((", and could not handle: " + " ".join([f"`{arg}`" for arg in could_not_handle])) if len(could_not_handle) else "") + "."
        else:
            event_res = "Added events " + (' '.join([f'`{arg}`' for arg in added_roles])) + ", " + ("and " if not len(could_not_handle) else "") + "removed events " + (' '.join([f'`{arg}`' for arg in removed_roles])) + ((", and could not handle: " + " ".join([f"`{arg}`" for arg in could_not_handle])) if len(could_not_handle) else "") + "."
        await ctx.interaction.response.send_message(event_res)

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Staff command. Allows staff to manipulate the CRON list."
    )
    async def tag(self,
        ctx,
        tag_name: Option(str, "The name of the tag to get.", required = True)
        ):
        member = ctx.author
        print(src.discord.globals.TAGS)
        if not len(src.discord.globals.TAGS):
            return await ctx.interaction.response.send_message("Apologies, tags do not appear to be working at the moment. Please try again in one minute.")
        staff = is_staff()
        lh_role = discord.utils.get(member.guild.roles, name=ROLE_LH)
        member_role = discord.utils.get(member.guild.roles, name=ROLE_MR)
        for t in src.discord.globals.TAGS:
            if t['name'] == tag_name:
                if staff or (t['launch_helpers'] and lh_role in member.roles) or (t['members'] and member_role in member.roles):
                    return await ctx.interaction.response.send_message(content = t['output'])
                else:
                    return await ctx.interaction.response.send_message(content = "Unfortunately, you do not have the permissions for this tag.")
        return await ctx.interaction.response.send_message("Tag not found.")

    @commands.command()
    async def graphpage(self, ctx, title, temp_format, table_index, div, place_col=0):
        temp = temp_format.lower() in ["y", "yes", "true"]
        await ctx.send(
            "*Inputs read:*\n" +
            f"Page title: `{title}`\n" +
            f"Template: `{temp}`\n" +
            f"Table index (staring at 0): `{table_index}`\n" +
            f"Division: `{div}`\n" +
            (f"Column with point values: `{place_col}`" if not temp else "")
        )
        points = []
        table_index = int(table_index)
        place_col = int(place_col)
        if temp:
            template = await get_page_tables(title, True)
            template = [t for t in template if t.normal_name() == "State results box"]
            template = template[table_index]
            ordinal = lambda n: "%d%s" % (n,"tsnrhtdd"[(n//10%10!=1)*(n%10<4)*n%10::4]) # Thanks https://codegolf.stackexchange.com/questions/4707/outputting-ordinal-numbers-1st-2nd-3rd#answer-4712
            for i in range(100):
                if template.has_arg(ordinal(i) + "_points"):
                    points.append(template.get_arg(ordinal(i) + "_points").value.replace("\n", ""))
        else:
            tables = await get_page_tables(title, False)
            tables = tables[table_index]
            data = tables.data()
            points = [r[place_col] for r in data]
            del points[0]
        points = [int(p) for p in points]
        await _graph(points, title + " - Division " + div, title + "Div" + div + ".svg")
        with open(title + "Div" + div + ".svg") as f:
            pic = discord.File(f)
            await ctx.send(file=pic)
        return await ctx.send("Attempted to graph.")

    @commands.command()
    async def graphscilympiad(self, ctx, url, title):
        points = await get_points(url)
        await _graph(points, title, "graph1.svg")
        with open("graph1.svg") as f:
            pic = discord.File(f)
            await ctx.send(file=pic)
        return await ctx.send("Attempted to graph.")

async def _graph(points, graph_title, title):
    plt.plot(range(1, len(points) + 1), points, marker='o', color='#2E66B6')
    z = np.polyfit(range(1, len(points) + 1), points, 1)
    p = np.poly1d(z)
    plt.plot(range(1, len(points) + 1), p(range(1, len(points) + 1)), "--", color='#CCCCCC')
    plt.xlabel("Place")
    plt.ylabel("Points")
    plt.title(graph_title)
    plt.savefig(title)
    plt.close()
    await asyncio.sleep(2)

def setup(bot):
    bot.add_cog(MemberCommands(bot))
