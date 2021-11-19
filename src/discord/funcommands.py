import random
import asyncio
import aiohttp
import json

import discord
from discord.ext import commands
from discord.commands import Option

from commandchecks import not_blacklisted_channel
from src.discord.utils import sanitize_mention
from src.discord.globals import CHANNEL_WELCOME, SLASH_COMMAND_GUILDS

fish_now = 0

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

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Trout slaps yourself or another user!"
    )
    async def trout(self,
        ctx,
        member: Option(discord.Member, "The member to trout slap! If not given, Pi-Bot will trout slap you!", required = False)
        ):
        if member == None:
            await ctx.interaction.response.send_message(f"{ctx.author.mention} trout slaps themselves!")
        else:
            await ctx.interaction.response.send_message(f"{ctx.author.mention} slaps {member.mention} with a giant trout!")
        await ctx.send("http://gph.is/1URFXN9")

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Gives a cookie to yourself or another user!"
    )
    async def cookie(self,
        ctx,
        member: Option(discord.Member, "The member to give a cookie to. If not provided, gives a cookie to yourself.", required = False)
        ):
        if member == None:
            await ctx.interaction.response.send_message(f"{ctx.author.mention} gives themselves a cookie.")
        else:
            await ctx.interaction.response.send_message(f"{ctx.author.mention} gives {member.mention} a cookie!")
        await ctx.send("http://gph.is/1UOaITh")

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Gives a cookie to yourself or another user!"
    )
    async def treat(self, ctx):
        await ctx.interaction.response.send_message("You give bernard one treat!")
        await ctx.send("http://gph.is/11nJAH5")

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Gives a cookie to yourself or another user!"
    )
    async def hersheybar(self,
        ctx,
        member: Option(discord.Member, "The member to give a Hershey Bar to! If not provided, gives a Hershey Bar to yourself!", required = False)
        ):
        if member == None:
            await ctx.interaction.response.send_message(f"{ctx.author.mention} gives themselves a Hershey bar.")
        else:
            await ctx.interaction.response.send_message(f"{ctx.author.mention} gives {member.mention} a Hershey bar!")
        await ctx.send("http://gph.is/2rt64CX")

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Gives a cookie to yourself or another user!"
    )
    async def icecream(self,
        ctx,
        member: Option(discord.Member, "The member to give ice cream to. If not provided, gives ice cream to yourself!", required = False)
        ):
        if member == None:
            await ctx.interaction.response.send_message(f"{ctx.author.mention} gives themselves some ice cream.")
        else:
            await ctx.interaction.response.send_message(f"{ctx.author.mention} gives {member.mention} ice cream!")
        await ctx.send("http://gph.is/YZLMMs")

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Gives some fish to bear!"
    )
    async def fish(self, ctx):
        """Gives a fish to bear."""
        global fish_now
        r = random.random()
        if len(str(fish_now)) > 1500:
            fish_now = round(pow(fish_now, 0.5))
            if fish_now == 69: fish_now = 70
            return await ctx.interaction.response.send_message("Woah! Bear's fish is a little too high, so it unfortunately has to be square rooted.")
        if r > 0.9:
            fish_now += 10
            if fish_now == 69: fish_now = 70
            return await ctx.interaction.response.send_message(f"Wow, you gave bear a super fish! Added 10 fish! Bear now has {fish_now} fish!")
        if r > 0.1:
            fish_now += 1
            if fish_now == 69:
                fish_now = 70
                return await ctx.interaction.response.send_message(f"You feed bear two fish. Bear now has {fish_now} fish!")
            else:
                return await ctx.interaction.response.send_message(f"You feed bear one fish. Bear now has {fish_now} fish!")
        if r > 0.02:
            fish_now += 0
            return await ctx.interaction.response.send_message(f"You can't find any fish... and thus can't feed bear. Bear still has {fish_now} fish.")
        else:
            fish_now = round(pow(fish_now, 0.5))
            if fish_now == 69: fish_now = 70
            return await ctx.interaction.response.send_message(f":sob:\n:sob:\n:sob:\nAww, bear's fish was accidentally square root'ed. Bear now has {fish_now} fish. \n:sob:\n:sob:\n:sob:")

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Steals some fish from bear!"
    )
    async def stealfish(self, ctx):
        global fish_now
        r = random.random()
        if r >= 0.75:
            ratio = r - 0.5
            fish_now = round(fish_now * (1 - ratio))
            per = round(ratio * 100)
            return await ctx.interaction.response.send_message(f"You stole {per}% of bear's fish!")
        if r >= 0.416:
            fish_now = round(fish_now * 0.99)
            return await ctx.interaction.response.send_message(f"You stole just 1% of bear's fish!")
        if r >= 0.25:
            ratio = r + 0.75
            fish_now = round(fish_now * ratio)
            per = round(ratio * 100) - 100
            return await ctx.interaction.response.send_message(f"Uhh... something went wrong! You gave bear another {per}% of his fish!")
        if r >= 0.01:
            return await ctx.interaction.response.send_message("Hmm, nothing happened. *crickets*")

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Dog bombs another user!"
    )
    async def dogbomb(self,
        ctx,
        member: Option(discord.Member, "The member to dog bomb!", required = True)
        ):
        """Dog bombs someone!"""
        session = aiohttp.ClientSession()
        page = await session.get(f"https://dog.ceo/api/breeds/image/random")
        await session.close()
        if page.status > 400:
            return await ctx.interaction.response.send_message(content = f"Sorry, I couldn't find a doggo to bomb with...")
        text = await page.content.read()
        text = text.decode('utf-8')
        jso = json.loads(text)

        doggo = jso['message']
        await ctx.interaction.response.send_message(f"{member.mention}, {ctx.author.mention} dog bombed you!!")
        await ctx.send(doggo)

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Shiba bombs another user!"
    )
    async def shibabomb(self,
        ctx,
        member: Option(discord.Member, "The member to shiba bomb!", required = True)
        ):
        """Shiba bombs a user!"""
        session = aiohttp.ClientSession()
        page = await session.get(f"https://dog.ceo/api/breed/shiba/images/random")
        await session.close()
        if page.status > 400:
            return await ctx.interaction.response.send_message(content = f"Sorry, I couldn't find a shiba to bomb with...")
        text = await page.content.read()
        text = text.decode('utf-8')
        jso = json.loads(text)

        doggo = jso['message']
        await ctx.interaction.response.send_message(f"{member.mention}, {ctx.author.mention} shiba bombed you!!")
        await ctx.send(doggo)

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Rolls the magic 8 ball..."
    )
    async def magic8ball(self, ctx):
        await ctx.interaction.response.send_message("Swishing the magic 8 ball...")
        await asyncio.sleep(1)
        await ctx.interaction.edit_original_message(content="Swishing the magic 8 ball..")
        await asyncio.sleep(1)
        await ctx.interaction.edit_original_message(content="Swishing the magic 8 ball.")
        await asyncio.sleep(1)
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
        await ctx.interaction.edit_original_message(content = f"**{response}**")

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Gets an xkcd comic!"
    )
    async def xkcd(self,
        ctx,
        num: Option(int, "The number of the xkcd comic to get. If not provided, gets a random comic.", required = False)
        ):
        session = aiohttp.ClientSession()
        res = await session.get("https://xkcd.com/info.0.json")
        text = await res.text()
        await session.close()
        json_obj = json.loads(text)
        max_num = json_obj['num']

        if num == None:
            num = random.randrange(1, max_num)
        if 1 <= num <= max_num:
            return await ctx.interaction.response.send_message(f"https://xkcd.com/{num}")
        else:
            return await ctx.interaction.response.send_message("Invalid attempted number for xkcd.")

def setup(bot):
    bot.add_cog(FunCommands(bot))
