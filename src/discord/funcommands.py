import random
import asyncio

from discord.ext import commands

from commandchecks import not_blacklisted_channel
from src.discord.utils import sanitize_mention
from src.discord.globals import CHANNEL_WELCOME, STEALFISH_BAN

import xkcd as xkcd_module # not to interfere with xkcd method

class FunCommands(commands.Cog, name='Fun'):
    def __init__(self, bot):
        self.bot = bot
        self.BEAR_ID = 353730886577160203
        self.BEAR_MESSAGES = [
            r"*{1} eats {2}* :fork_and_knife:",
            r"*{1} consumes {2}!* :fork_knife_plate:",
            r"*{1} thinks that {2} tasted pretty good...* :yum:",
            r"*{1} thinks that {2} tasted pretty awful...* :face_vomiting:",
            r"*{1} enjoyed eating {2}!* :yum:",
            r"*{1} hopes he gets to eat {2} again!* :smile:",
            r"*{1} thinks that {2} is delicious!* :yum:",
            r"*{1} likes eating {2} better than fish* :yum:",
            r"*{1} thinks that {2} was yummy!!* :blush:",
            r"*{1} is pretty full after eating {2}* :blush:",
            r"*{1} liked eating {2}* :heart:",
            r"*{1} isn't cuckoo for Cocoa Puffs, but rather {2}* :zany_face:",
            r"*{1} wonders when he gets to eat more {2}* :thinking:",
            r"*{1} has a hot take: {2} tastes pretty bomb* :fire:",
            r"*{1} can't believe he doesn't eat {2} more often!* :exploding_head:",
            r"*{1} would be lying to say he didn't like eating {2}* :liar:",
            r"*{1} would eat {2} at any time of the day!* :candy:",
            r"*{1} wonders where he can get more of {2}* :spoon:",
            r"*{1} thinks that {2} tastes out of this world* :alien:",
        ]
    

    async def get_bear_message(self, user):
        message = random.choice(self.BEAR_MESSAGES)
        message = message.replace(r"{1}", fr"<@{self.BEAR_ID}>").replace(r"{2}", f"{user}")
        return message

    @commands.command(aliases=["eats", "beareats"])
    async def eat(self, ctx, user):
        """Allows bear to eat users >:D"""
        if ctx.author.id == self.BEAR_ID:
            # author is bearasauras
            message = await self.get_bear_message(user)
            await ctx.message.delete()
            await ctx.send(message)
        else:
            await ctx.message.reply("rawr! only bear can eat users!")
    
    @commands.command(aliases=["slap", "trouts", "slaps", "troutslaps"])
    @not_blacklisted_channel(blacklist=[CHANNEL_WELCOME])
    async def trout(self, ctx, member:str=False):
        if await sanitize_mention(member) == False:
            return await ctx.send("Woah... looks like you're trying to be a little sneaky with what you're telling me to do. Not so fast!")
        if member == False:
            await ctx.send(f"{ctx.message.author.mention} trout slaps themselves!")
        else:
            await ctx.send(f"{ctx.message.author.mention} slaps {member} with a giant trout!")
        await ctx.send("http://gph.is/1URFXN9")
    
    @commands.command(aliases=["givecookie"])
    @not_blacklisted_channel(blacklist=[CHANNEL_WELCOME])
    async def cookie(self, ctx, member:str=False):
        if await sanitize_mention(member) == False:
            return await ctx.send("Woah... looks like you're trying to be a little sneaky with what you're telling me to do. You can't ping roles or everyone.")
        if member == False:
            await ctx.send(f"{ctx.message.author.mention} gives themselves a cookie.")
        else:
            await ctx.send(f"{ctx.message.author.mention} gives {member} a cookie!")
        await ctx.send("http://gph.is/1UOaITh")
    
    @commands.command()
    @not_blacklisted_channel(blacklist=[CHANNEL_WELCOME])
    async def treat(self, ctx):
        await ctx.send("You give bernard one treat!")
        await ctx.send("http://gph.is/11nJAH5")
    
    @commands.command(aliases=["givehershey", "hershey"])
    @not_blacklisted_channel(blacklist=[CHANNEL_WELCOME])
    async def hersheybar(self, ctx, member:str=False):
        if await sanitize_mention(member) == False:
            return await ctx.send("Woah... looks like you're trying to be a little sneaky with what you're telling me to do. You can't ping roles or everyone.")
        if member == False:
            await ctx.send(f"{ctx.message.author.mention} gives themselves a Hershey bar.")
        else:
            await ctx.send(f"{ctx.message.author.mention} gives {member} a Hershey bar!")
        await ctx.send("http://gph.is/2rt64CX")
    
    @commands.command(aliases=["giveicecream"])
    @not_blacklisted_channel(blacklist=[CHANNEL_WELCOME])
    async def icecream(self, ctx, member:str=False):
        if await sanitize_mention(member) == False:
            return await ctx.send("Woah... looks like you're trying to be a little sneaky with what you're telling me to do. You can't ping roles or everyone.")
        if member == False:
            await ctx.send(f"{ctx.message.author.mention} gives themselves some ice cream.")
        else:
            await ctx.send(f"{ctx.message.author.mention} gives {member} ice cream!")
        await ctx.send("http://gph.is/YZLMMs")
    
    @commands.command(aliases=["feedbear"])
    @not_blacklisted_channel(blacklist=[CHANNEL_WELCOME])
    async def fish(self, ctx):
        """Gives a fish to bear."""
        global fish_now
        r = random.random()
        if len(str(fish_now)) > 1500:
            fish_now = round(pow(fish_now, 0.5))
            if fish_now == 69: fish_now = 70
            return await ctx.send("Woah! Bear's fish is a little too high, so it unfortunately has to be square rooted.")
        if r > 0.9:
            fish_now += 10
            if fish_now == 69: fish_now = 70
            return await ctx.send(f"Wow, you gave bear a super fish! Added 10 fish! Bear now has {fish_now} fish!")
        if r > 0.1:
            fish_now += 1
            if fish_now == 69: 
                fish_now = 70
                return await ctx.send(f"You feed bear two fish. Bear now has {fish_now} fish!")
            else:
                return await ctx.send(f"You feed bear one fish. Bear now has {fish_now} fish!")
        if r > 0.02:
            fish_now += 0
            return await ctx.send(f"You can't find any fish... and thus can't feed bear. Bear still has {fish_now} fish.")
        else:
            fish_now = round(pow(fish_now, 0.5))
            if fish_now == 69: fish_now = 70
            return await ctx.send(f":sob:\n:sob:\n:sob:\nAww, bear's fish was accidentally square root'ed. Bear now has {fish_now} fish. \n:sob:\n:sob:\n:sob:")
    
    @commands.command(aliases=["badbear"])
    @not_blacklisted_channel(blacklist=[CHANNEL_WELCOME])
    async def stealfish(self, ctx):
        global fish_now
        member = ctx.message.author
        r = random.random()
        if member.id in STEALFISH_BAN:
            return await ctx.send("Hey! You've been banned from stealing fish for now.")
        if r >= 0.75:
            ratio = r - 0.5
            fish_now = round(fish_now * (1 - ratio))
            per = round(ratio * 100)
            return await ctx.send(f"You stole {per}% of bear's fish!")
        if r >= 0.416:
            parsed = dateparser.parse("1 hour", settings={"PREFER_DATES_FROM": "future"})
            STEALFISH_BAN.append(member.id)
            CRON_LIST.append({"date": parsed, "do": f"unstealfishban {member.id}"})
            return await ctx.send(f"Sorry {member.mention}, but it looks like you're going to be banned from using this command for 1 hour!")
        if r >= 0.25:
            parsed = dateparser.parse("1 day", settings={"PREFER_DATES_FROM": "future"})
            STEALFISH_BAN.append(member.id)
            CRON_LIST.append({"date": parsed, "do": f"unstealfishban {member.id}"})
            return await ctx.send(f"Sorry {member.mention}, but it looks like you're going to be banned from using this command for 1 day!")
        if r >= 0.01:
            return await ctx.send("Hmm, nothing happened. *crickets*")
        else:
            STEALFISH_BAN.append(member.id)
            return await ctx.send("You are banned from using `!stealfish` until the next version of Pi-Bot is released.")
    
    @commands.command(aliases=["doggobomb"])
    @not_blacklisted_channel(blacklist=[CHANNEL_WELCOME])
    async def dogbomb(self, ctx, member:str=False):
        """Dog bombs someone!"""
        if member == False:
            return await ctx.send("Tell me who you want to dog bomb!! :dog:")
        doggo = await get_doggo()
        await ctx.send(doggo)
        await ctx.send(f"{member}, <@{ctx.message.author.id}> dog bombed you!!")
    
    @commands.command()
    @not_blacklisted_channel(blacklist=[CHANNEL_WELCOME])
    async def shibabomb(self, ctx, member:str=False):
        """Shiba bombs a user!"""
        if member == False:
            return await ctx.send("Tell me who you want to shiba bomb!! :dog:")
        doggo = await get_shiba()
        await ctx.send(doggo)
        await ctx.send(f"{member}, <@{ctx.message.author.id}> shiba bombed you!!")
    
    @commands.command()
    @not_blacklisted_channel(blacklist=[CHANNEL_WELCOME])
    async def magic8ball(self, ctx):
        msg = await ctx.send("Swishing the magic 8 ball...")
        await ctx.channel.trigger_typing()
        await asyncio.sleep(3)
        await msg.delete()
        sayings = [
            "Yes.",
            "Ask again later.",
            "Not looking good.",
            "Cannot predict now.",
            "It is certain.",
            "Try again.",
            "Without a doubt.",
            "Don't rely on it.",
            "Outlook good.",
            "My reply is no.",
            "Don't count on it.",
            "Yes - definitely.",
            "Signs point to yes.",
            "I believe so.",
            "Nope.",
            "Concentrate and ask later.",
            "Try asking again.",
            "For sure not.",
            "Definitely no."
        ]
        response = random.choice(sayings)
        await ctx.message.reply(f"**{response}**")
        
    @commands.command()
    @not_blacklisted_channel(blacklist=[CHANNEL_WELCOME])
    async def xkcd(self, ctx, num = None):
        max_num = await xkcd_module.get_max()
        if num == None:
            rand = random.randrange(1, int(max_num))
            return await xkcd(ctx, str(rand))
        if num.isdigit() and 1 <= int(num) <= int(max_num):
            return await ctx.send(f"https://xkcd.com/{num}")
        else:
            return await ctx.send("Invalid attempted number for xkcd.")

def setup(bot):
    bot.add_cog(FunCommands(bot))