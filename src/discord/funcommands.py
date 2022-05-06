import asyncio
import json
import random

import aiohttp
from src.discord.globals import SLASH_COMMAND_GUILDS

import discord
from discord.commands import Option
from discord.ext import commands


class FunCommands(commands.Cog, name="Fun"):
    """
    Cog for holding fun, non-important commands.
    """

    fish_count: int

    def __init__(self, bot):
        self.bot = bot
        self.fish_count = 0
        print("Initialized Fun cog.")

    @discord.commands.slash_command(
        guild_ids=[SLASH_COMMAND_GUILDS],
        description="Trout slaps yourself or another user!",
    )
    async def trout(
        self,
        ctx,
        member: Option(
            discord.Member,
            "The member to trout slap! If not given, Pi-Bot will trout slap you!",
            required=False,
        ),
    ):
        """
        Command which displays a trout-slapping gif and related message.

        Args:
            member (discord.Option[discord.Member]): The optional member to include
              in the message. If not provided, assumed to be the caller.
        """
        if not member or member == ctx.author:
            member = "themselves"
        else:
            member = member.mention

        await ctx.interaction.response.send_message(
            f"{ctx.author.mention} slaps {member} with a giant trout!"
        )
        await ctx.send("http://gph.is/1URFXN9")

    @discord.commands.slash_command(
        guild_ids=[SLASH_COMMAND_GUILDS],
        description="Gives a treat to yourself or another user!",
    )
    async def treat(
        self,
        ctx,
        type: Option(
            str,
            "The type of treat to give!",
            choices=[
                "chocolate bar",
                "cookie",
                "ice cream",
                "pizza",
                "boba",
                "a slice of cake",
                "chips and salsa",
                "brownie",
                "cotton candy",
            ],
            required=True,
        ),
        member: Option(
            discord.Member,
            "The member to give the treat to! Defaults to yourself!",
            required=False,
        ),
    ):
        """
        Command which displays a snack gif and related message.

        Args:
            type (discord.Option[str]): The type of snack to include in the gif/message.
            member (discord.Option[discord.Member]): The optional member to include
              in the message. If not provided, assumed to be the caller.
        """
        snacks = {
            "chocolate bar": {
                "name": "a chocolate bar",
                "gifs": [
                    "http://gph.is/2rt64CX",
                    "https://media.giphy.com/media/Wrscj8qsDogR4QHx2j/giphy.gif",
                    "https://media.giphy.com/media/gIqguY2jmB31LZqWip/giphy.gif",
                    "https://media.giphy.com/media/xUA7aUV3sYqsCkRLa0/giphy.gif",
                    "https://media.giphy.com/media/gGwL4lMFOdSsGQlJEG/giphy.gif",
                ],
            },
            "ice cream": {
                "name": "ice cream",
                "gifs": [
                    "http://gph.is/YZLMMs",
                    "https://media.giphy.com/media/PB5E8c20NXslUuIxna/giphy.gif",
                    "https://media.giphy.com/media/CqS6nhPTCu6e5v2R03/giphy.gif",
                    "https://media.giphy.com/media/GB91uLrgyuul2/giphy.gif",
                    "https://media.giphy.com/media/uUs14eCA2SBgs/giphy-downsized-large.gif",
                    "https://media.giphy.com/media/26uf7yJapo82e48yA/giphy.gif",
                ],
            },
            "cookie": {
                "name": "a cookie",
                "gifs": [
                    "http://gph.is/1UOaITh",
                    "https://media.giphy.com/media/59Ve1fnBdol8c/giphy.gif",
                    "https://media.giphy.com/media/JIPEUnwfxjtT0OapJb/giphy.gif",
                    "https://media.giphy.com/media/26FeXTOe2R9kfpObC/giphy.gif",
                    "https://media.giphy.com/media/EKUvB9uFnm2Xe/giphy.gif",
                    "https://media.giphy.com/media/38a2gPetE4RuE/giphy-downsized-large.gif",
                    "https://media.giphy.com/media/c7maSqDI7j2ww/giphy.gif",
                ],
            },
            "pizza": {
                "name": "pizza",
                "gifs": [
                    "https://media.giphy.com/media/3osxYoufeOGOA7xiX6/giphy.gif",
                    "https://media.giphy.com/media/1108D2tVaUN3eo/giphy.gif",
                    "https://media.giphy.com/media/QR7ci2sbhrkzxAuMHH/giphy.gif",
                    "https://media.giphy.com/media/hmzAcor7gBsbK/giphy-downsized-large.gif",
                    "https://media.giphy.com/media/aCKMaeduKfFXG/giphy.gif",
                ],
            },
            "boba": {
                "name": "boba",
                "gifs": [
                    "https://media.giphy.com/media/7SZzZO5EG1S6QLJeUL/giphy.gif",
                    "https://media.giphy.com/media/r6P5BC5b4SS2Y/giphy.gif",
                    "https://media.giphy.com/media/cRLPmyXQhtRXnRXfDX/giphy.gif",
                    "https://media.giphy.com/media/h8CD39vtPVoMEoqZZ3/giphy.gif",
                    "https://media.giphy.com/media/Y4VNo2dIdW8bpDgRXt/giphy.gif",
                ],
            },
            "a slice of cake": {
                "name": "a slice of cake",
                "gifs": [
                    "https://media.giphy.com/media/He4wudo59enf2/giphy.gif",
                    "https://media.giphy.com/media/l0Iy4ppWvwQ4SXPxK/giphy.gif",
                    "https://media.giphy.com/media/zBU43ZvUVj37a/giphy.gif",
                    "https://media.giphy.com/media/wPamPmbGkWkQE/giphy.gif",
                    "https://media.giphy.com/media/JMfzwxEIbd6zC/giphy.gif",
                ],
            },
            "chips and salsa": {
                "name": "chips and salsa, I suppose",
                "gifs": [
                    "https://media.giphy.com/media/xThuWwvZWJ4NOB6j6w/giphy.gif",
                    "https://media.giphy.com/media/wZOF08rE9knDTYsY4G/giphy.gif",
                    "https://media.giphy.com/media/1O3nlwRXcOJYLv1Neh/giphy.gif",
                    "https://media.giphy.com/media/YrN8O2eGl2f5GucpEf/giphy.gif",
                ],
            },
            "brownie": {
                "name": "a brownie",
                "gifs": [
                    "https://media.giphy.com/media/BkWHoSRB6gR2M/giphy.gif",
                    "https://media.giphy.com/media/abOlz9ygIm9Es/giphy.gif",
                    "https://media.giphy.com/media/l0MYEU0YyoTEpTDby/giphy-downsized-large.gif",
                    "https://media.giphy.com/media/VdQ8b54TJZ9kXClaSw/giphy.gif",
                    "https://media.giphy.com/media/ziuCU2H0DdtGoZdJu3/giphy.gif",
                ],
            },
            "cotton candy": {
                "name": "cotton candy",
                "gifs": [
                    "https://media.giphy.com/media/1X7A3s673cLWovCQCE/giphy.gif",
                    "https://media.giphy.com/media/dXKH2jCT9tINyVWlUp/giphy.gif",
                    "https://media.giphy.com/media/V83Khg0lCKyOc/giphy.gif",
                    "https://media.giphy.com/media/ZcVI712Fcol3EeLltH/giphy-downsized-large.gif",
                ],
            },
        }
        if not member or member == ctx.author:
            member = "themselves"
        else:
            member = member.mention

        await ctx.interaction.response.send_message(
            f"{ctx.author.mention} gives {member} {snacks[type]['name']}!"
        )
        await ctx.send(random.choice(snacks[type]["gifs"]))

    @discord.commands.slash_command(
        guild_ids=[SLASH_COMMAND_GUILDS], description="Gives some fish to bear!"
    )
    async def fish(self, ctx):
        """
        Command which changes bear's fish count. May add or subtract from the total,
        depending on what the random value in the method resolves to.
        """
        r = random.random()

        if len(str(self.fish_count)) > 1000000:
            self.fish_count = round(pow(self.fish_count, 0.5))
            if self.fish_count == 69:
                self.fish_count = 70
            return await ctx.interaction.response.send_message(
                "Woah! Bear's fish is a little too high, so it unfortunately has to be square rooted."
            )

        if r > 0.9:
            self.fish_count += 10
            if self.fish_count == 69:
                self.fish_count = 70
            return await ctx.interaction.response.send_message(
                f"Wow, you gave bear a super fish! Added 10 fish! Bear now has {self.fish_count} fish!"
            )

        elif r > 0.1:
            self.fish_count += 1
            if self.fish_count == 69:
                self.fish_count = 70
                return await ctx.interaction.response.send_message(
                    f"You feed bear two fish. Bear now has {self.fish_count} fish!"
                )
            else:
                return await ctx.interaction.response.send_message(
                    f"You feed bear one fish. Bear now has {self.fish_count} fish!"
                )

        elif r > 0.02:
            self.fish_count += 0
            return await ctx.interaction.response.send_message(
                f"You can't find any fish... and thus can't feed bear. Bear still has {self.fish_count} fish."
            )

        else:
            self.fish_count = round(pow(self.fish_count, 0.5))
            if self.fish_count == 69:
                self.fish_count = 70
            return await ctx.interaction.response.send_message(
                f":sob:\n:sob:\n:sob:\nAww, bear's fish was accidentally square root'ed. Bear now has {self.fish_count} fish. \n:sob:\n:sob:\n:sob:"
            )

    @discord.commands.slash_command(
        guild_ids=[SLASH_COMMAND_GUILDS], description="Steals some fish from bear!"
    )
    async def stealfish(self, ctx):
        """
        Command which removes from bear's fish count.
        """
        r = random.random()

        if r >= 0.75:
            ratio = r - 0.5
            self.fish_count = round(self.fish_count * (1 - ratio))
            per = round(ratio * 100)
            return await ctx.interaction.response.send_message(
                f"You stole {per}% of bear's fish!"
            )

        elif r >= 0.416:
            self.fish_count = round(self.fish_count * 0.99)
            return await ctx.interaction.response.send_message(
                f"You stole just 1% of bear's fish!"
            )

        elif r >= 0.25:
            ratio = r + 0.75
            self.fish_count = round(self.fish_count * ratio)
            per = round(ratio * 100) - 100
            return await ctx.interaction.response.send_message(
                f"Uhh... something went wrong! You gave bear another {per}% of his fish!"
            )

        if r >= 0.01:
            return await ctx.interaction.response.send_message(
                "Hmm, nothing happened. *crickets*"
            )

    @discord.commands.slash_command(
        guild_ids=[SLASH_COMMAND_GUILDS], description="Dog bombs another user!"
    )
    async def dogbomb(
        self,
        ctx,
        member: Option(discord.Member, "The member to dog bomb!", required=True),
    ):
        """
        Displays a random dog gif and related message.

        Args:
            member (discord.Option[discord.Member]): The member to ping in the message.
        """
        session = aiohttp.ClientSession()
        page = await session.get(f"https://dog.ceo/api/breeds/image/random")
        await session.close()
        if page.status > 400:
            return await ctx.interaction.response.send_message(
                content=f"Sorry, I couldn't find a doggo to bomb with..."
            )
        text = await page.content.read()
        text = text.decode("utf-8")
        jso = json.loads(text)

        doggo = jso["message"]
        if member == ctx.author:
            await ctx.interaction.response.send_message(
                f"{member.mention} dog bombed themselves!!"
            )
        else:
            await ctx.interaction.response.send_message(
                f"{member.mention}, {ctx.author.mention} dog bombed you!!"
            )
        await ctx.send(doggo)

    @discord.commands.slash_command(
        guild_ids=[SLASH_COMMAND_GUILDS], description="Shiba bombs another user!"
    )
    async def shibabomb(
        self,
        ctx,
        member: Option(discord.Member, "The member to shiba bomb!", required=True),
    ):
        """
        Displays a random shiba gif and related message.

        Args:
            member (discord.Option[discord.Member]): The member to ping in the message.
        """
        session = aiohttp.ClientSession()
        page = await session.get(f"https://dog.ceo/api/breed/shiba/images/random")
        await session.close()
        if page.status > 400:
            return await ctx.interaction.response.send_message(
                content=f"Sorry, I couldn't find a shiba to bomb with..."
            )
        text = await page.content.read()
        text = text.decode("utf-8")
        jso = json.loads(text)

        doggo = jso["message"]
        if member == ctx.author:
            await ctx.interaction.response.send_message(
                f"{member.mention} shiba bombed themselves!!"
            )
        else:
            await ctx.interaction.response.send_message(
                f"{member.mention}, {ctx.author.mention} shiba bombed you!!"
            )
        await ctx.send(doggo)

    @discord.commands.slash_command(
        guild_ids=[SLASH_COMMAND_GUILDS], description="Rolls the magic 8 ball..."
    )
    async def magic8ball(self, ctx):
        """
        Calls the magic 8 ball.
        """
        await ctx.interaction.response.send_message("Swishing the magic 8 ball...")
        await asyncio.sleep(1)
        await ctx.interaction.edit_original_message(
            content="Swishing the magic 8 ball.."
        )
        await asyncio.sleep(1)
        await ctx.interaction.edit_original_message(
            content="Swishing the magic 8 ball."
        )
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
            "Definitely no.",
        ]
        response = random.choice(sayings)
        await ctx.interaction.edit_original_message(content=f"**{response}**")

    @discord.commands.slash_command(
        guild_ids=[SLASH_COMMAND_GUILDS], description="Gets an xkcd comic!"
    )
    async def xkcd(
        self,
        ctx,
        num: Option(
            int,
            "The number of the xkcd comic to get. If not provided, gets a random comic.",
            required=False,
        ),
    ):
        """
        Gets a specific (or random if num is not provided) xkcd comic.
        """
        session = aiohttp.ClientSession()
        res = await session.get("https://xkcd.com/info.0.json")
        text = await res.text()
        await session.close()
        json_obj = json.loads(text)
        max_num = json_obj["num"]

        if num == None:
            num = random.randrange(1, max_num)
        if 1 <= num <= max_num:
            return await ctx.interaction.response.send_message(
                f"https://xkcd.com/{num}"
            )
        else:
            return await ctx.interaction.response.send_message(
                "Invalid attempted number for xkcd."
            )


def setup(bot):
    bot.add_cog(FunCommands(bot))
