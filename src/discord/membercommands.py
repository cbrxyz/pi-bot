import discord
import random
import wikipedia as wikip
from discord.ext import commands
from src.discord.globals import TOURNAMENT_INFO, REQUESTED_TOURNAMENTS, ROLE_PRONOUN_HE, ROLE_PRONOUN_SHE, ROLE_PRONOUN_THEY, PI_BOT_IDS, ROLE_DIV_A, ROLE_DIV_B, ROLE_DIV_C, ROLE_ALUMNI, EMOJI_FAST_REVERSE, EMOJI_FAST_FORWARD, EMOJI_LEFT_ARROW, EMOJI_RIGHT_ARROW, ROLE_GAMES, CHANNEL_GAMES, RULES, CATEGORY_STAFF, SERVER_ID, CHANNEL_REPORTS, REPORT_IDS, EVENT_INFO, ROLE_LH, ROLE_MR
from embed import assemble_embed
from src.discord.utils import harvest_id
from src.wiki.wiki import get_page_tables
from src.wiki.scilympiad import make_results_template, get_points
from src.wiki.schools import get_school_listing
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

    @commands.command(aliases=["man"])
    async def help(self, ctx, command:str=None):
        """Allows a user to request help for a command."""
        if command == None:
            embed = assemble_embed(
                title="Looking for help?",
                desc=("Hey there, I'm a resident bot of Scioly.org!\n\n" +
                "On Discord, you can send me commands using `!` before the command name, and I will process it to help you! " +
                "For example, `!states`, `!events`, and `!fish` are all valid commands that can be used!\n\n" +
                "If you want to see some commands that you can use on me, just type `!list`! " +
                "If you need more help, please feel free to reach out to a staff member!")
            )
            return await ctx.send(embed=embed)
        hlp = await get_help(ctx, command)
        await ctx.send(embed=hlp)

    @commands.command()
    async def pronouns(self, ctx, *args):
        """Assigns or removes pronoun roles from a user."""
        member = ctx.message.author
        if len(args) < 1:
            await ctx.send(f"{member.mention}, please specify a pronoun to add/remove. Current options include `!pronouns he`, `!pronouns she`, and `!pronouns they`.")
        he_role = discord.utils.get(member.guild.roles, name=ROLE_PRONOUN_HE)
        she_role = discord.utils.get(member.guild.roles, name=ROLE_PRONOUN_SHE)
        they_role = discord.utils.get(member.guild.roles, name=ROLE_PRONOUN_THEY)
        for arg in args:
            if arg.lower() in ["he", "him", "his", "he / him / his"]:
                if he_role in member.roles:
                    await ctx.send("Oh, looks like you already have the He / Him / His role. Removing it.")
                    await member.remove_roles(he_role)
                else:
                    await member.add_roles(he_role)
                    await ctx.send("Added the He / Him / His role.")
            elif arg.lower() in ["she", "her", "hers", "she / her / hers"]:
                if she_role in member.roles:
                    await ctx.send("Oh, looks like you already have the She / Her / Hers role. Removing it.")
                    await member.remove_roles(she_role)
                else:
                    await member.add_roles(she_role)
                    await ctx.send("Added the She / Her / Hers role.")
            elif arg.lower() in ["they", "them", "their", "they / them / their"]:
                if they_role in member.roles:
                    await ctx.send("Oh, looks like you already have the They / Them / Theirs role. Removing it.")
                    await member.remove_roles(they_role)
                else:
                    await member.add_roles(they_role)
                    await ctx.send("Added the They / Them / Theirs role.")
            elif arg.lower() in ["remove", "clear", "delete", "nuke"]:
                await member.remove_roles(he_role, she_role, they_role)
                return await ctx.send("Alrighty, your pronouns have been removed.")
            elif arg.lower() in ["help", "what"]:
                return await ctx.send("For help with pronouns, please use `!help pronouns`.")
            else:
                return await ctx.send(f"Sorry, I don't recognize the `{arg}` pronoun. The pronoun roles we currently have are:\n" +
                "> `!pronouns he  ` (which gives you *He / Him / His*)\n" +
                "> `!pronouns she ` (which gives you *She / Her / Hers*)\n" +
                "> `!pronouns they` (which gives you *They / Them / Theirs*)\n" +
                "To remove pronouns, use `!pronouns remove`.\n" +
                "Feel free to request alternate pronouns, by opening a report, or reaching out a staff member.")

    # Never understood why this exists when there's the built in /me
    @commands.command()
    async def me(self, ctx, *args):
        """Replaces the good ol' /me"""
        await ctx.message.delete()
        if len(args) < 1:
            return await ctx.send(f"*{ctx.message.author.mention} " + "is cool!*")
        else:
            await ctx.send(f"*{ctx.message.author.mention} " + " ".join(arg for arg in args) + "*")

    @commands.command()
    async def profile(self, ctx, name:str=False):
        if name == False:
            member = ctx.message.author
            name = member.nick
            if name == None:
                name = member.name
        elif name.find("<@") != -1:
            iden = await harvest_id(name)
            member = ctx.message.author.guild.get_member(int(iden))
            name = member.nick
            if name == None:
                name = member.name
        embed = assemble_embed(
            title=f"Scioly.org Information for {name}",
            desc=(f"[`Forums`](https://scioly.org/forums/memberlist.php?mode=viewprofile&un={name}) | [`Wiki`](https://scioly.org/wiki/index.php?title=User:{name})"),
            hexcolor="#2E66B6"
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def latex(self, ctx, *args):
        new_args = " ".join(args)
        print(new_args)
        new_args = new_args.replace(" ", r"&space;")
        print(new_args)
        await ctx.send(r"https://latex.codecogs.com/png.latex?\dpi{150}{\color{Gray}" + new_args + "}")

    @commands.command(aliases=["membercount"])
    async def count(self, ctx):
        guild = ctx.message.author.guild
        await ctx.send(f"Currently, there are `{len(guild.members)}` members in the server.")

    @commands.command()
    async def resultstemplate(self, ctx, url):
        if url.find("scilympiad.com") == -1:
            return await ctx.send("The URL must be a Scilympiad results link.")
        await ctx.send("**Warning:** Because Scilympiad is constantly evolving, this command may break. Please preview the template on the wiki before saving! If this command breaks, please DM pepperonipi or open an issue on GitHub. Thanks!")
        res = await make_results_template(url)
        with open("resultstemplate.txt", "w+") as t:
            t.write(res)
        file = discord.File("resultstemplate.txt", filename="resultstemplate.txt")
        await ctx.send(file=file)

    @commands.command()
    async def school(self, ctx, title, state):
        lists = await get_school_listing(title, state)
        fields = []
        if len(lists) > 20:
            return await ctx.send(f"Woah! Your query returned `{len(lists)}` schools, which is too much to send at once. Try narrowing your query!")
        for l in lists:
            fields.append({'name': l['name'], 'value': f"```{l['wikicode']}```", 'inline': "False"})
        embed = assemble_embed(
            title="School Data",
            desc=f"Your query for `{title}` in `{state}` returned `{len(lists)}` results. Thanks for contribtuing to the wiki!",
            fields=fields,
            hexcolor="#2E66B6"
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def alumni(self, ctx):
        """Removes or adds the alumni role from a user."""
        member = ctx.message.author
        div_a_role = discord.utils.get(member.guild.roles, name=ROLE_DIV_A)
        div_b_role = discord.utils.get(member.guild.roles, name=ROLE_DIV_B)
        div_c_role = discord.utils.get(member.guild.roles, name=ROLE_DIV_C)
        await member.remove_roles(div_a_role, div_b_role, div_c_role)
        role = discord.utils.get(member.guild.roles, name=ROLE_ALUMNI)
        if role in member.roles:
            await member.remove_roles(role)
            await ctx.send("Removed your alumni status.")
        else:
            await member.add_roles(role)
            await ctx.send(f"Added the alumni role, and removed all other division roles.")

    @commands.command(aliases=["div"])
    async def division(self, ctx, div):
        if div.lower() == "a":
            res = await self.__assign_div(ctx, "Division A")
            await ctx.send("Assigned you the Division A role, and removed all other divison/alumni roles.")
        elif div.lower() == "b":
            res = await self.__assign_div(ctx, "Division B")
            await ctx.send("Assigned you the Division B role, and removed all other divison/alumni roles.")
        elif div.lower() == "c":
            res = await self.__assign_div(ctx, "Division C")
            await ctx.send("Assigned you the Division C role, and removed all other divison/alumni roles.")
        elif div.lower() == "d":
            await ctx.send("This server does not have a Division D role. Instead, use the `!alumni` command!")
        elif div.lower() in ["remove", "clear", "none", "x"]:
            member = ctx.message.author
            div_a_role = discord.utils.get(member.guild.roles, name=ROLE_DIV_A)
            div_b_role = discord.utils.get(member.guild.roles, name=ROLE_DIV_B)
            div_c_role = discord.utils.get(member.guild.roles, name=ROLE_DIV_C)
            await member.remove_roles(div_a_role, div_b_role, div_c_role)
            await ctx.send("Removed all of your division/alumni roles.")
        else:
            return await ctx.send("Sorry, I don't seem to see that division. Try `!division c` to assign the Division C role, or `!division d` to assign the Division D role.")

    async def __assign_div(self, ctx, div):
        """Assigns a user a div"""
        member = ctx.message.author
        role = discord.utils.get(member.guild.roles, name=div)
        div_a_role = discord.utils.get(member.guild.roles, name=ROLE_DIV_A)
        div_b_role = discord.utils.get(member.guild.roles, name=ROLE_DIV_B)
        div_c_role = discord.utils.get(member.guild.roles, name=ROLE_DIV_C)
        alumni_role = discord.utils.get(member.guild.roles, name=ROLE_ALUMNI)
        await member.remove_roles(div_a_role, div_b_role, div_c_role, alumni_role)
        await member.add_roles(role)
        return True

    @commands.command()
    async def list(self, ctx, cmd:str=False):
        """Lists all of the commands a user may access."""
        if cmd == False: # for quick list of commands
            ls = await get_quick_list(ctx)
            await ctx.send(embed=ls)
        if cmd == "all" or cmd == "commands":
            ls = await get_list(ctx.message.author, 1)
            sent_list = await ctx.send(embed=ls)
            await sent_list.add_reaction(EMOJI_FAST_REVERSE)
            await sent_list.add_reaction(EMOJI_LEFT_ARROW)
            await sent_list.add_reaction(EMOJI_RIGHT_ARROW)
            await sent_list.add_reaction(EMOJI_FAST_FORWARD)
        elif cmd == "states":
            states_list = await get_state_list()
            list = assemble_embed(
                title="List of all states",
                desc="\n".join([f"`{state}`" for state in states_list])
            )
            await ctx.send(embed=list)
        elif cmd == "events":
            events_list = [r['eventName'] for r in EVENT_INFO]
            list = assemble_embed(
                title="List of all events",
                desc="\n".join([f"`{name}`" for name in events_list])
            )
            await ctx.send(embed=list)

    @commands.command()
    async def games(self, ctx):
        """Removes or adds someone to the games channel."""
        games_channel = discord.utils.get(ctx.message.author.guild.text_channels, name=CHANNEL_GAMES)
        member = ctx.message.author
        role = discord.utils.get(member.guild.roles, name=ROLE_GAMES)
        if role in member.roles:
            await member.remove_roles(role)
            await ctx.send("Removed you from the games club... feel free to come back anytime!")
            await games_channel.send(f"{member.mention} left the party.")
        else:
            await member.add_roles(role)
            await ctx.send(f"You are now in the channel. Come and have fun in {games_channel.mention}! :tada:")
            await games_channel.send(f"Please welcome {member.mention} to the party!!")

    @commands.command(aliases=["state"])
    async def states(self, ctx, *args):
        """Assigns someone with specific states."""
        new_args = [str(arg).lower() for arg in args]

        # Fix commas as possible separator
        if len(new_args) == 1:
            new_args = new_args[0].split(",")
        new_args = [re.sub("[;,]", "", arg) for arg in new_args]

        member = ctx.message.author
        states = await get_state_list()
        states = [s[:s.rfind(" (")] for s in states]
        triple_word_states = [s for s in states if len(s.split(" ")) > 2]
        double_word_states = [s for s in states if len(s.split(" ")) > 1]
        removed_roles = []
        added_roles = []
        for term in ["california", "ca", "cali"]:
            if term in [arg.lower() for arg in args]:
                return await ctx.send("Which California, North or South? Try `!state norcal` or `!state socal`.")
        if len(new_args) < 1:
            return await ctx.send("Sorry, but you need to specify a state (or multiple states) to add/remove.")
        elif len(new_args) > 10:
            return await ctx.send("Sorry, you are attempting to add/remove too many states at once.")
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
                return await ctx.send(f"Sorry, the {arg} state could not be found. Try again.")
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
        await ctx.send(state_res)

    def is_not_staff(exception: Type[commands.CommandError], message: str):
        async def predicate(ctx):
            if not is_staff():
                return True
            raise exception(message)
        return commands.check(predicate)

    @commands.command()
    @is_not_staff(SelfMuteCommandStaffInvoke, "A staff member attempted to invoke selfmute.")
    async def selfmute(self, ctx, *args):
        """
        Self mutes the user that invokes the command.

        :param *args: The time to mute the user for.
        :type *args: str
        """
        user = ctx.message.author

        time = " ".join(args)
        await _mute(ctx, user, time, self=True)

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
                for t in REQUESTED_TOURNAMENTS:
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
                await update_tournament_list(ctx.bot)

    @commands.command(aliases=["what"])
    async def about(self, ctx):
        """Prints information about the bot."""
        await ctx.send(get_about())

    @commands.command(aliases=["server", "link", "invitelink"])
    async def invite(self, ctx):
        await ctx.send("https://discord.gg/C9PGV6h")

    @commands.command()
    async def forums(self, ctx):
        await ctx.send("<https://scioly.org/forums>")

    @commands.command()
    async def obb(self, ctx):
        await ctx.send("<https://scioly.org/obb>")

    @commands.command(aliases=["tests", "testexchange"])
    async def exchange(self, ctx):
        await ctx.send("<https://scioly.org/tests>")

    @commands.command()
    async def gallery(self, ctx):
        await ctx.send("<https://scioly.org/gallery>")

    @commands.command(aliases=["random"])
    async def rand(self, ctx, a=1, b=10):
        r = random.randrange(a, b + 1)
        await ctx.send(f"Random number between `{a}` and `{b}`: `{r}`")

    @commands.command()
    async def rule(self, ctx, num):
        """Gets a specified rule."""
        if not num.isdigit() or int(num) < 1 or int(num) > 13:
            # If the rule number is not actually a number
            return await ctx.send("Please use a valid rule number, from 1 through 13. (Ex: `!rule 7`)")
        rule = RULES[int(num) - 1]
        return await ctx.send(f"**Rule {num}:**\n> {rule}")

    @commands.command()
    async def coach(self, ctx):
        """Gives an account the coach role."""
        await ctx.send("If you would like to apply for the `Coach` role, please fill out the form here: <https://forms.gle/UBKpWgqCr9Hjw9sa6>.")

    @commands.command()
    async def info(self, ctx):
        """Gets information about the Discord server."""
        server = ctx.message.guild
        name = server.name
        owner = server.owner
        creation_date = server.created_at
        emoji_count = len(server.emojis)
        icon = server.icon_url_as(format=None, static_format='jpeg')
        animated_icon = server.is_icon_animated()
        iden = server.id
        banner = server.banner_url
        desc = server.description
        mfa_level = server.mfa_level
        verification_level = server.verification_level
        content_filter = server.explicit_content_filter
        default_notifs = server.default_notifications
        features = server.features
        splash = server.splash_url
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
        discovery_splash_url = server.discovery_splash_url
        member_percentage = round(member_count/max_members * 100, 3)
        emoji_percentage = round(emoji_count/emoji_limit * 100, 3)
        channel_percentage = round(channel_count/500 * 100, 3)
        role_percenatege = round(role_count/250 * 100, 3)

        staff_member = await is_staff()
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
        if staff_member and ctx.channel.category.name == CATEGORY_STAFF:
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
        embed = assemble_embed(
            title=f"Information for `{name}`",
            desc=f"**Description:** {desc}",
            thumbnailUrl=icon,
            fields=fields
        )
        await ctx.send(embed=embed)

    @commands.command(aliases=["r"])
    async def report(self, ctx, *args):
        """Creates a report that is sent to staff members."""
        server = ctx.bot.get_guild(SERVER_ID)
        reports_channel = discord.utils.get(server.text_channels, name=CHANNEL_REPORTS)
        message = args[0]
        if len(args) > 1:
            message = ' '.join(args)
        poster = str(ctx.message.author)
        embed = assemble_embed(
            title=f"Report Received (using `!report`)",
            webcolor="red",
            authorName = poster,
            authorIcon = ctx.message.author.avatar_url_as(format="jpg"),
            fields = [{
                "name": "Message",
                "value": message,
                "inline": False
            }]
        )
        message = await reports_channel.send(embed=embed)
        REPORT_IDS.append(message.id)
        await message.add_reaction("\U00002705")
        await message.add_reaction("\U0000274C")
        await ctx.send("Thanks, report created.")

    # TODO: NOT TESTED
    @commands.command()
    async def wiki(self, ctx, command:str=False, *args):
        # Check to make sure not too much at once
        if not command:
            return await ctx.send("<https://scioly.org/wiki>")
        if len(args) > 7:
            return await ctx.send("Slow down there buster. Please keep the command to 12 or less arguments at once.")
        multiple = False
        for arg in args:
            if arg[:1] == "-":
                multiple = arg.lower() == "-multiple"
        if command in ["summary"]:
            if multiple:
                for arg in [arg for arg in args if arg[:1] != "-"]:
                    text = await implement_command("summary", arg)
                    if text == False:
                        await ctx.send(f"The `{arg}` page does not exist!")
                    else:
                        await ctx.send(" ".join(text))
            else:
                string_sum = " ".join([arg for arg in args if arg[:1] != "-"])
                text = await implement_command("summary", string_sum)
                if text == False:
                    await ctx.send(f"The `{arg}` page does not exist!")
                else:
                    await ctx.send(" ".join(text))
        elif command in ["search"]:
            if multiple:
                return await ctx.send("Ope! No multiple searches at once yet!")
            searches = await implement_command("search", " ".join([arg for arg in args]))
            await ctx.send("\n".join([f"`{s}`" for s in searches]))
        else:
            # Assume link
            if multiple:
                new_args = [command] + list(args)
                for arg in [arg for arg in new_args if arg[:1] != "-"]:
                    url = await implement_command("link", arg)
                    if url == False:
                        await ctx.send(f"The `{arg}` page does not exist!")
                    await ctx.send(f"<{self.wiki_url_fix(url)}>")
            else:
                string_sum = " ".join([arg for arg in args if arg[:1] != "-"])
                if len(args) > 0 and command.rstrip() != "link":
                    string_sum = f"{command} {string_sum}"
                elif command.rstrip() != "link":
                    string_sum = command
                url = await implement_command("link", string_sum)
                if url == False:
                    await ctx.send(f"The `{string_sum}` page does not exist!")
                else:
                    await ctx.send(f"<{self.wiki_url_fix(url)}>")

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

    @commands.command(aliases=["event"])
    async def events(self, ctx, *args):
        """Adds or removes event roles from a user."""
        if len(args) < 1:
            return await ctx.send("You need to specify at least one event to add/remove!")
        elif len(args) > 10:
            return await ctx.send("Woah, that's a lot for me to handle at once. Please separate your requests over multiple commands.")
        member = ctx.message.author
        new_args = [str(arg).lower() for arg in args]

        # Fix commas as possible separator
        if len(new_args) == 1:
            new_args = new_args[0].split(",")
        new_args = [re.sub("[;,]", "", arg) for arg in new_args]

        event_info = EVENT_INFO
        event_names = []
        removed_roles = []
        added_roles = []
        could_not_handle = []
        multi_word_events = []

        if type(EVENT_INFO) == int:
            # When the bot starts up, EVENT_INFO is initialized to 0 before receiving the data from the sheet a few seconds later. This lets the user know this.
            return await ctx.send("Apologies... refreshing data currently. Try again in a few seconds.")

        for i in range(7, 1, -1):
            # Supports adding 7-word to 2-word long events
            multi_word_events += [e['eventName'] for e in event_info if len(e['eventName'].split(" ")) == i]
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
                aliases = [abbr.lower() for abbr in event['event_abbreviations']]
                if arg.lower() in aliases or arg.lower() == event['eventName'].lower():
                    event_names.append(event['eventName'])
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
        await ctx.send(event_res)

    @commands.command(aliases=["tags", "t"])
    async def tag(self, ctx, name):
        member = ctx.message.author
        if len(TAGS) == 0:
            return await ctx.send("Apologies, tags do not appear to be working at the moment. Please try again in one minute.")
        staff = is_staff()
        lh_role = discord.utils.get(member.guild.roles, name=ROLE_LH)
        member_role = discord.utils.get(member.guild.roles, name=ROLE_MR)
        for t in TAGS:
            if t['name'] == name:
                if staff or (t['launch_helpers'] and lh_role in member.roles) or (t['members'] and member_role in member.roles):
                    await ctx.message.delete()
                    return await ctx.send(t['text'])
                else:
                    return await ctx.send("Unfortunately, you do not have the permissions for this tag.")
        return await ctx.send("Tag not found.")

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
