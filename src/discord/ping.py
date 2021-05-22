import discord
from discord.ext import commands
import re
from src.discord.globals import PING_INFO, PI_BOT_IDS, CHANNEL_BOTSPAM
from embed import assemble_embed

import time

class PingManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("Ping manager enabled")
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id in PI_BOT_IDS: return
        pingable = True
        if message.content[:1] == "!" or message.content[:1] == "?" or message.content[:2] == "pb" or message.content[:2] == "bp":
            pingable = False
        botspam = discord.utils.get(message.guild.text_channels, name = CHANNEL_BOTSPAM)
        if message.channel.id == botspam.id: #724125653212987454:
            # If the message is coming from #bot-spam
            pingable = False
        if pingable:
            for user in PING_INFO:
                if user['id'] == message.author.id:
                    continue
                pings = user['pings']
                for ping in pings:
                    if len(re.findall(ping, message.content, re.I)) > 0 and message.author.discriminator != "0000":
                        # Do not send a ping if the user is mentioned
                        user_is_mentioned = user['id'] in [m.id for m in message.mentions]
                        if user['id'] in [m.id for m in message.channel.members] and ('dnd' not in user or user['dnd'] != True) and not user_is_mentioned:
                            # Check that the user can actually see the message
                            name = message.author.nick
                            if name == None:
                                name = message.author.name
                            await self.__ping_pm(user['id'], name, ping, message.channel.name, message.content, message.jump_url)

    async def __ping_pm(self, user_id, pinger, ping_exp, channel, content, jump_url):
        """Allows Pi-Bot to PM a user about a ping."""
        user_to_send = self.bot.get_user(user_id)
        try:
            content = re.sub(rf'{ping_exp}', r'**\1**', content, flags=re.I)
        except Exception as e:
            print(f"Could not bold ping due to unfavored RegEx. Error: {e}")
        ping_exp = ping_exp.replace(r"\b(", "").replace(r")\b", "")
        warning = f"\n\nIf you don't want this ping anymore, in `#bot-spam` on the server, send `!ping remove {ping_exp}`"
        embed = assemble_embed(
            title=":bellhop: Ping Alert!",
            desc=(f"Looks like `{pinger}` pinged a ping expression of yours in the Scioly.org Discord Server!" + warning),
            fields=[
                {"name": "Expression Matched", "value": f" `{ping_exp}`", "inline": "True"},
                {"name": "Jump To Message", "value": f"[Click here!]({jump_url})", "inline": "True"},
                {"name": "Channel", "value": f"`#{channel}`", "inline": "True"},
                {"name": "Content", "value": content, "inline": "False"}
            ],
            hexcolor="#2E66B6"
        )
        await user_to_send.send(embed=embed)
    
    @commands.command(aliases=["donotdisturb"])
    async def dnd(self, ctx):
        member = ctx.message.author.id
        if any([True for u in PING_INFO if u['id'] == member]):
            user = next((u for u in PING_INFO if u['id'] == member), None)
            if 'dnd' not in user:
                user['dnd'] = True
                return await ctx.send("Enabled DND mode for pings.")
            elif user['dnd'] == True:
                user['dnd'] = False
                return await ctx.send("Disabled DND mode for pings.")
            else:
                user['dnd'] = True
                return await ctx.send("Enabled DND mode for pings.")
        else:
            return await ctx.send("You can't enter DND mode without any pings!")
    
    @commands.command()
    async def ping(self, ctx, command=None, *args):
        """Controls Pi-Bot's ping interface."""
        if command is None:
            return await ctx.send("Uh, I need a command you want to run.")
        member = ctx.message.author.id
        if len(args) > 8:
            return await ctx.send("You are giving me too many pings at once! Please separate your requests over multiple commands.")
        if command.lower() in ["add", "new", "addregex", "newregex", "addregexp", "newregexp", "delete", "remove", "test", "try"] and len(args) < 1:
            return await ctx.send(f"In order to {command} a ping, you must supply a regular expression or word.")
        if command.lower() in ["add", "new", "addregex", "newregex", "addregexp", "newregexp"]:
            # Check to see if author in ping info already
            ignored_list = []
            if any([True for u in PING_INFO if u['id'] == member]):
                #yes
                user = next((u for u in PING_INFO if u['id'] == member), None)
                pings = user['pings']
                for arg in args:
                    try:
                        re.findall(arg, "test phrase")
                    except:
                        await ctx.send(f"Ignoring adding the `{arg}` ping because it uses illegal characters.")
                        ignored_list.append(arg)
                        continue
                    if f"({arg})" in pings or f"\\b({arg})\\b" in pings or arg in pings:
                        await ctx.send(f"Ignoring adding the `{arg}` ping because you already have a ping currently set as that.")
                        ignored_list.append(arg)
                    else:
                        if command.lower() in ["add", "new"]:
                            print(f"adding word: {re.escape(arg)}")
                            pings.append(fr"\b({re.escape(arg)})\b")
                        else:
                            print(f"adding regexp: {arg}")
                            pings.append(fr"({arg})")
            else:
                # nope
                if command.lower() in ["add", "new"]:
                    PING_INFO.append({
                        "id": member,
                        "pings": [fr"\b({re.escape(arg)})\b" for arg in args]
                    })
                else:
                    PING_INFO.append({
                        "id": member,
                        "pings": [fr"({arg})" for arg in args]
                    })
            return await ctx.send(f"Alrighty... I've got you all set up for the following pings: " + (" ".join([f"`{arg}`" for arg in args if arg not in ignored_list])))
        elif command.lower() in ["delete", "remove"]:
            user = next((u for u in PING_INFO if u['id'] == member), None)
            if user == None or len(user['pings']) == 0:
                return await ctx.send("You have no registered pings.")
            for arg in args:
                if arg == "all":
                    user['pings'] = []
                    return await ctx.send("I removed all of your pings.")
                if arg in user['pings']:
                    user['pings'].remove(arg)
                    await ctx.send(f"I removed the `{arg}` RegExp ping you were referencing.")
                elif f"\\b({arg})\\b" in user['pings']:
                    user['pings'].remove(f"\\b({arg})\\b")
                    await ctx.send(f"I removed the `{arg}` word ping you were referencing.")
                elif f"({arg})" in user['pings']:
                    user['pings'].remove(f"({arg})")
                    await ctx.send(f"I removed the `{arg}` RegExp ping you were referencing.")
                else:
                    return await ctx.send(f"I can't find my phone or the **`{arg}`** ping you are referencing, sorry. Try another ping, or see all of your pings with `!ping list`.")
            return await ctx.send("I removed all pings you requested.")
        elif command.lower() in ["list", "all"]:
            user = next((u for u in PING_INFO if u['id'] == member), None)
            if user == None or len(user['pings']) == 0:
                return await ctx.send("You have no registered pings.")
            else:
                pings = user['pings']
                regex_pings = []
                word_pings = []
                for ping in pings:
                    if ping[:2] == "\\b":
                        word_pings.append(ping)
                    else:
                        regex_pings.append(ping)
                if len(regex_pings) > 0:
                    await ctx.send("Your RegEx pings are: " + ", ".join([f"`{regex}`" for regex in regex_pings]))
                if len(word_pings) > 0:
                    await ctx.send("Your word pings are: " + ", ".join([f"`{word[3:-3]}`" for word in word_pings]))
        elif command.lower() in ["test", "try"]:
            user = next((u for u in PING_INFO if u['id'] == member), None)
            user_pings = user['pings']
            matched = False
            for arg in args:
                for ping in user_pings:
                    if len(re.findall(ping, arg, re.I)) > 0:
                        await ctx.send(f"Your ping `{ping}` matches `{arg}`.")
                        matched = True
            if not matched:
                await ctx.send("Your test matched no pings of yours.")
        else:
            return await ctx.send("Sorry, I can't find that command.")

def setup(bot):
    bot.add_cog(PingManager(bot))