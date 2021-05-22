import discord
from discord.ext import commands
from globals import TOURNAMENT_INFO
from globals import REQUESTED_TOURNAMENTS
from globals import ROLE_PRONOUN_HE
from globals import ROLE_PRONOUN_SHE
from globals import ROLE_PRONOUN_THEY
from globals import PI_BOT_IDS
# from tournaments import update_tournament_list

class MemberCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("Member commands loaded")
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id in PI_BOT_IDS: return
        print("running member cog")
        print(message.content)
    
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