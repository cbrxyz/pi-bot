import discord
from discord.ext import commands
from src.discord.globals import TOURNAMENT_INFO, REQUESTED_TOURNAMENTS, ROLE_PRONOUN_HE, ROLE_PRONOUN_SHE, ROLE_PRONOUN_THEY, PI_BOT_IDS, ROLE_DIV_A, ROLE_DIV_B, ROLE_DIV_C, ROLE_ALUMNI, EMOJI_FAST_REVERSE, EMOJI_FAST_FORWARD, EMOJI_LEFT_ARROW, EMOJI_RIGHT_ARROW, ROLE_GAMES, CHANNEL_GAMES
from embed import assemble_embed
from src.discord.utils import harvest_id
from src.wiki.scilympiad import make_results_template
from src.wiki.schools import get_school_listing
from commands import get_list, get_quick_list, get_help
from lists import get_state_list
from src.discord.utils import lookup_role
from src.discord.mute import _mute
from commandchecks import is_staff
from commanderrors import SelfMuteCommandStaffInvoke

from typing import Type
# from tournaments import update_tournament_list

class MemberCommands(commands.Cog, name='Member'):
    def __init__(self, bot):
        self.bot = bot
        print("Member commands loaded")
    
    @commands.Cog.listener()
    async def on_message(self, message):
        pass
        # if message.author.id in PI_BOT_IDS: return
        # print("running member cog")
        # print(message.content)
    
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
            if not await is_staff(ctx):
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
        
        
    # @commands.command(aliases=["tc", "tourney", "tournaments"])
    # async def tournament(self, ctx, *args):
    #     member = ctx.message.author
    #     new_args = list(args)
    #     ignore_terms = ["invitational", "invy", "tournament", "regional", "invite"]
    #     for term in ignore_terms:
    #         if term in new_args:
    #             new_args.remove(term)
    #             await ctx.send(f"Ignoring `{term}` because it is too broad of a term. *(If you need help with this command, please type `!help tournament`)*")
    #     if len(args) == 0:
    #         return await ctx.send("Please specify the tournaments you would like to be added/removed from!")
    #     for arg in new_args:
    #         # Stop users from possibly adding the channel hash in front of arg
    #         arg = arg.replace("#", "")
    #         arg = arg.lower()
    #         found = False
    #         if arg == "all":
    #             role = discord.utils.get(member.guild.roles, name=ROLE_AT)
    #             if role in member.roles:
    #                 await ctx.send(f"Removed your `All Tournaments` role.")
    #                 await member.remove_roles(role)
    #             else:
    #                 await ctx.send(f"Added your `All Tournaments` role.")
    #                 await member.add_roles(role)
    #             continue
    #         for t in TOURNAMENT_INFO:
    #             if arg == t[1]:
    #                 found = True
    #                 role = discord.utils.get(member.guild.roles, name=t[0])
    #                 if role == None:
    #                     return await ctx.send(f"Apologies! The `{t[0]}` channel is currently not available.")
    #                 if role in member.roles:
    #                     await ctx.send(f"Removed you from the `{t[0]}` channel.")
    #                     await member.remove_roles(role)
    #                 else:
    #                     await ctx.send(f"Added you to the `{t[0]}` channel.")
    #                     await member.add_roles(role)
    #                 break
    #         if not found:
    #             uid = member.id
    #             found2 = False
    #             votes = 1
    #             for t in REQUESTED_TOURNAMENTS:
    #                 if arg == t['iden']:
    #                     found2 = True
    #                     if uid in t['users']:
    #                         return await ctx.send("Sorry, but you can only vote once for a specific tournament!")
    #                     t['count'] += 1
    #                     t['users'].append(uid)
    #                     votes = t['count']
    #                     break
    #             if not found2:
    #                 await auto_report("New Tournament Channel Requested", "orange", f"User ID {uid} requested tournament channel `#{arg}`.\n\nTo add this channel to the voting list for the first time, use `!tla {arg} {uid}`.\nIf the channel has already been requested in the list and this was a user mistake, use `!tla [actual name] {uid}`.")
    #                 return await ctx.send(f"Made request for a `#{arg}` channel. Please note your submission may not instantly appear.")
    #             await ctx.send(f"Added a vote for `{arg}`. There " + ("are" if votes != 1 else "is") + f" now `{votes}` " + (f"votes" if votes != 1 else f"vote") + " for this channel.")
    #             await update_tournament_list(self.bot)
        
def setup(bot):
    bot.add_cog(MemberCommands(bot))