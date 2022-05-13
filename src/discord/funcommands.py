from __future__ import annotations

import asyncio
import json
import random
from typing import TYPE_CHECKING, Literal

import discord
from discord import app_commands
from discord.ext import commands
from src.discord.globals import SLASH_COMMAND_GUILDS

if TYPE_CHECKING:
    from bot import PiBot


class FunCommands(commands.Cog, name="Fun"):
    fish_count: int

    def __init__(self, bot: PiBot):
        self.bot = bot
        self.fish_count = 0
        print("Initialized Fun cog.")

    @app_commands.command(description="Trout slaps yourself or another user!")
    @app_commands.describe(
        member="The member to trout slap! If not given, Pi-Bot will trout slap you!"
    )
    @app_commands.guilds(SLASH_COMMAND_GUILDS)
    async def trout(self, interaction: discord.Interaction, member: discord.Member):
        if not member or member == interaction.user:
            member = "themselves"
        else:
            member = member.mention

        await interaction.response.send_message(
            f"{interaction.user.mention} slaps {member} with a giant trout!"
        )
        await interaction.channel.send("http://gph.is/1URFXN9")

    @app_commands.command(description="Gives a treat to yourself or another user!")
    @app_commands.describe(
        member="The member to give the treat to! Defaults to yourself!"
    )
    @app_commands.guilds(SLASH_COMMAND_GUILDS)
    async def treat(
        self,
        interaction: discord.Interaction,
        type: Literal[
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
        member: discord.Member = None,
    ):
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
        if not member or member == interaction.user:
            member = "themselves"
        else:
            member = member.mention

        await interaction.response.send_message(
            f"{interaction.user.mention} gives {member} {snacks[type]['name']}!"
        )
        await interaction.channel.send(random.choice(snacks[type]["gifs"]))

    @app_commands.command(description="Gives some fish to bear!")
    @app_commands.guilds(SLASH_COMMAND_GUILDS)
    async def fish(self, interaction: discord.Interaction):
        """Gives a fish to bear."""
        r = random.random()

        if len(str(self.fish_count)) > 1000000:
            self.fish_count = round(pow(self.fish_count, 0.5))
            if self.fish_count == 69:
                self.fish_count = 70
            return await interaction.response.send_message(
                "Woah! Bear's fish is a little too high, so it unfortunately has to be square rooted."
            )

        if r > 0.9:
            self.fish_count += 10
            if self.fish_count == 69:
                self.fish_count = 70
            return await interaction.response.send_message(
                f"Wow, you gave bear a super fish! Added 10 fish! Bear now has {self.fish_count} fish!"
            )

        elif r > 0.1:
            self.fish_count += 1
            if self.fish_count == 69:
                self.fish_count = 70
                return await interaction.response.send_message(
                    f"You feed bear two fish. Bear now has {self.fish_count} fish!"
                )
            else:
                return await interaction.response.send_message(
                    f"You feed bear one fish. Bear now has {self.fish_count} fish!"
                )

        elif r > 0.02:
            self.fish_count += 0
            return await interaction.response.send_message(
                f"You can't find any fish... and thus can't feed bear. Bear still has {self.fish_count} fish."
            )

        else:
            self.fish_count = round(pow(self.fish_count, 0.5))
            if self.fish_count == 69:
                self.fish_count = 70
            return await interaction.response.send_message(
                f":sob:\n:sob:\n:sob:\nAww, bear's fish was accidentally square root'ed. Bear now has {self.fish_count}"
                f" fish. \n:sob:\n:sob:\n:sob: "
            )

    @app_commands.command(description="Steals some fish from bear!")
    @app_commands.guilds(SLASH_COMMAND_GUILDS)
    async def stealfish(self, interaction: discord.Interaction):
        r = random.random()

        if r >= 0.75:
            ratio = r - 0.5
            self.fish_count = round(self.fish_count * (1 - ratio))
            per = round(ratio * 100)
            return await interaction.response.send_message(
                f"You stole {per}% of bear's fish!"
            )

        elif r >= 0.416:
            self.fish_count = round(self.fish_count * 0.99)
            return await interaction.response.send_message(
                f"You stole just 1% of bear's fish!"
            )

        elif r >= 0.25:
            ratio = r + 0.75
            self.fish_count = round(self.fish_count * ratio)
            per = round(ratio * 100) - 100
            return await interaction.response.send_message(
                f"Uhh... something went wrong! You gave bear another {per}% of his fish!"
            )

        if r >= 0.01:
            return await interaction.response.send_message(
                "Hmm, nothing happened. *crickets*"
            )

    @app_commands.command(description="Dog bombs another user!")
    @app_commands.describe(member="The member to dog bomb!")
    @app_commands.guilds(SLASH_COMMAND_GUILDS)
    async def dogbomb(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
    ):
        """Dog bombs someone!"""
        async with self.bot.session as session:
            page = await session.get(f"https://dog.ceo/api/breeds/image/random")
        if page.status > 400:
            return await interaction.response.send_message(
                content=f"Sorry, I couldn't find a doggo to bomb with..."
            )
        text = await page.content.read()
        text = text.decode("utf-8")
        jso = json.loads(text)

        doggo = jso["message"]
        if member == interaction.user:
            await interaction.response.send_message(
                f"{member.mention} dog bombed themselves!!"
            )
        else:
            await interaction.response.send_message(
                f"{member.mention}, {interaction.user.mention} dog bombed you!!"
            )
        await interaction.channel.send(doggo)

    @app_commands.command(description="Shiba bombs another user!")
    @app_commands.describe(member="The member to shiba bomb!")
    @app_commands.guilds(SLASH_COMMAND_GUILDS)
    async def shibabomb(self, interaction: discord.Interaction, member: discord.Member):
        """Shiba bombs a user!"""
        async with self.bot.session as session:
            page = await session.get(f"https://dog.ceo/api/breed/shiba/images/random")
        if page.status > 400:
            return await interaction.response.send_message(
                content=f"Sorry, I couldn't find a shiba to bomb with..."
            )
        text = await page.content.read()
        text = text.decode("utf-8")
        jso = json.loads(text)

        doggo = jso["message"]
        if member == interaction.user:
            await interaction.response.send_message(
                f"{member.mention} shiba bombed themselves!!"
            )
        else:
            await interaction.response.send_message(
                f"{member.mention}, {interaction.user.mention} shiba bombed you!!"
            )
        await interaction.channel.send(doggo)

    @app_commands.command(description="Rolls the magic 8 ball...")
    @app_commands.guilds(SLASH_COMMAND_GUILDS)
    async def magic8ball(self, interaction: discord.Interaction):
        await interaction.response.send_message("Swishing the magic 8 ball...")
        await asyncio.sleep(1)
        await interaction.edit_original_message(content="Swishing the magic 8 ball..")
        await asyncio.sleep(1)
        await interaction.edit_original_message(content="Swishing the magic 8 ball.")
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
        await interaction.edit_original_message(content=f"**{response}**")

    @app_commands.command(description="Gets an xkcd comic!")
    @app_commands.describe(
        num="The number of the xkcd comic to get. If not provided, gets a random comic."
    )
    @app_commands.guilds(SLASH_COMMAND_GUILDS)
    async def xkcd(self, interaction: discord.Interaction, num: int = None):
        async with self.bot.session as session:
            res = await session.get("https://xkcd.com/info.0.json")
        text = await res.text()
        json_obj = json.loads(text)
        max_num = json_obj["num"]

        if num is None:
            num = random.randrange(1, max_num)
        if 1 <= num <= max_num:
            return await interaction.response.send_message(f"https://xkcd.com/{num}")
        else:
            return await interaction.response.send_message(
                "Invalid attempted number for xkcd."
            )


async def setup(bot: PiBot):
    await bot.add_cog(FunCommands(bot))
