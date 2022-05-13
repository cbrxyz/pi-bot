from __future__ import annotations

import datetime
import re
from typing import TYPE_CHECKING, Union

import discord
import src.discord.globals
from discord import app_commands
from discord.ext import commands
from src.discord.globals import CHANNEL_BOTSPAM, SLASH_COMMAND_GUILDS

if TYPE_CHECKING:
    from bot import PiBot


class PingManager(commands.GroupCog, name="ping"):
    recent_messages = {}

    def __init__(self, bot: PiBot):
        self.bot = bot
        self.recent_messages = {}
        print("Initialized Ping cog.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Do not ping for messages in a private channel
        if message.channel.type == discord.ChannelType.private:
            return

        # Do not ping for messages from a bot
        if message.author.bot:
            return

        # Do not ping for messages from webhooks
        if message.author.discriminator == "0000":
            return

        # Do not ping if the message is coming from the botspam channel
        botspam_channel = discord.utils.get(
            message.guild.text_channels, name=CHANNEL_BOTSPAM
        )
        if message.channel == botspam_channel:
            return

        # Store the message to generate recent message history
        if message.channel.id not in self.recent_messages:
            self.recent_messages[message.channel.id] = [message]
        else:
            self.recent_messages[message.channel.id].append(message)
            if len(self.recent_messages[message.channel.id]) > 5:
                self.recent_messages[message.channel.id] = self.recent_messages[
                    message.channel.id
                ][
                    1:
                ]  # Cut off the message from the longest time ago if there are too many messages stored

        # Send a ping alert to the relevant users
        for user in src.discord.globals.PING_INFO:

            # Do not ping the author of the message
            if user["user_id"] == message.author.id:
                continue

            pings = [rf"\b({ping})\b" for ping in user["word_pings"]]
            pings.extend(user["regex_pings"])

            # Do not ping any users mentioned in the message
            user_is_mentioned = user["user_id"] in [m.id for m in message.mentions]
            if user_is_mentioned:
                continue

            # Do not ping if the user cannot see the channel or has DND enabled
            user_can_see_channel = user["user_id"] in [
                m.id for m in message.channel.members
            ]
            user_in_dnd = "dnd" in user and user["dnd"]
            if not user_can_see_channel or user_in_dnd:
                continue

            # Count the number of pings in the message
            ping_count = 0
            for ping in pings:
                if len(re.findall(ping, message.content, re.I)):
                    ping_count += 1

            if ping_count:
                user_obj = self.bot.get_user(user["user_id"])
                await self.send_ping_pm(user_obj, message, ping_count)

    def format_text(
        self, text: str, length: int, user: Union[discord.Member, discord.User]
    ) -> str:
        """
        Highlights ping expressions in the message and shorten long messages with an ellipsis.
        """
        user_ping_obj = [
            user_obj
            for user_obj in src.discord.globals.PING_INFO
            if user_obj["user_id"] == user.id
        ][0]
        assert isinstance(user_ping_obj, dict)

        pings = [rf"\b({ping})\b" for ping in user_ping_obj["word_pings"]]
        pings.extend(user_ping_obj["regex_pings"])

        for expression in pings:
            try:
                text = re.sub(rf"{expression}", r"**\1**", text, flags=re.I)
            except Exception as e:
                print(f"Could not bold ping due to unfavored RegEx. Error: {e}")

        # Prevent the text from being too long
        if len(text) > length:
            return text[: length - 3] + "..."
        else:
            return text

    def expire_recent_messages(self) -> None:
        """
        Remove all recent messages older than a specified amount of time.

        Currently, this is called whenever a ping PM is sent.
        """
        for _, messages in self.recent_messages.items():
            for message in messages[:]:
                if (discord.utils.utcnow() - message.created_at) > datetime.timedelta(
                    hours=3
                ):
                    messages.remove(message)

    async def send_ping_pm(
        self, user: discord.User, message: discord.Message, ping_count: int
    ) -> None:
        """
        Sends a direct message to the user about a message containing a relevant ping expression.
        """
        # Expire recent messages
        self.expire_recent_messages()

        # Create the alert embed
        description = ""
        if ping_count == 1:
            description = "**One of your pings was mentioned by a user in the Scioly.org Discord server!**"
        elif ping_count > 1:
            description = "**Several of your pings were mentioned by a user in the Scioly.org Discord server!**"

        description = (
            description
            + "\n\n"
            + "\n".join(
                [
                    f"{message.author.mention}: {self.format_text(message.content, 100, user)}"
                    for message in self.recent_messages[message.channel.id]
                ]
            )
        )
        description = (
            description
            + "\n\n"
            + f"Come check out the conversation! [Click here]({message.jump_url}) to be teleported to the message!"
        )
        embed = discord.Embed(
            title=":bellhop: Ping Alert!",
            color=discord.Color.brand_red(),
            description=description,
        )
        embed.set_thumbnail(url=message.author.display_avatar.url)

        embed.set_footer(
            text=f"If you don't want this ping anymore, use /ping remove in the Scioly.org Discord server!"
        )

        # Send the user an alert message
        await user.send(embed=embed)

    @app_commands.command(description="Toggles 'Do Not Disturb' mode.")
    @app_commands.guilds(SLASH_COMMAND_GUILDS)
    async def dnd(self, interaction: discord.Interaction):
        user = [
            u
            for u in src.discord.globals.PING_INFO
            if u["user_id"] == interaction.user.id
        ]

        if len(user):
            user = user[0]
            if "dnd" not in user:
                user["dnd"] = True
                return await interaction.response.send_message(
                    "Enabled DND mode for pings."
                )
            elif user["dnd"]:
                user["dnd"] = False
                return await interaction.response.send_message(
                    "Disabled DND mode for pings."
                )
            else:
                user["dnd"] = True
                return await interaction.response.send_message(
                    "Enabled DND mode for pings."
                )
        else:
            return await interaction.response.send_message(
                "You can't enter DND mode without any pings!"
            )

    @app_commands.command(
        name="add", description="Adds a new ping to notify you about."
    )
    @app_commands.describe(word="The new word to add a ping for.")
    @app_commands.guilds(SLASH_COMMAND_GUILDS)
    async def pingadd(self, interaction: discord.Interaction, word: str):
        # Check to see if author in ping info already
        member = interaction.user
        if any(
            [True for u in src.discord.globals.PING_INFO if u["user_id"] == member.id]
        ):
            # User already has an object in the PING_INFO dictionary
            user = next(
                (u for u in src.discord.globals.PING_INFO if u["user_id"] == member.id),
                None,
            )
            pings = user["word_pings"] + user["regex_pings"]
            try:
                re.findall(word, "test phrase")
            except:
                return await interaction.response.send_message(
                    f"Ignoring adding the `{word}` ping because it uses illegal characters."
                )
            if f"({word})" in pings or f"\\b({word})\\b" in pings or word in pings:
                return await interaction.response.send_message(
                    f"Ignoring adding the `{word}` ping because you already have a ping currently set as that."
                )
            else:
                print(f"adding word: {re.escape(word)}")
                relevant_doc = [
                    doc
                    for doc in src.discord.globals.PING_INFO
                    if doc["user_id"] == member.id
                ][0]
                relevant_doc["word_pings"].append(word)
                await self.bot.mongo_database.update(
                    "data", "pings", user["_id"], {"$push": {"word_pings": word}}
                )
        else:
            # User does not already have an object in the PING_INFO dictionary
            new_user_dict = {
                "user_id": member.id,
                "word_pings": [word],
                "regex_pings": [],
                "dnd": False,
            }
            src.discord.globals.PING_INFO.append(new_user_dict)
            await self.bot.mongo_database.insert("data", "pings", new_user_dict)
        return await interaction.response.send_message(
            f"Great! You will now receive an alert for messages that contain the `{word}` word.\n\nPlease be "
            f'responsible with the pinging feature. Using pings senselessly (such as pinging for "the" or "a") may '
            f"result in you being temporarily disallowed from using or receiving pings. "
        )

    @app_commands.command(
        name="test", description="Tests your pings on an example message."
    )
    @app_commands.guilds(SLASH_COMMAND_GUILDS)
    @app_commands.describe(test="The phrase to test your pings against.")
    async def pingtest(self, interaction: discord.Interaction, test: str):
        member = interaction.user
        user = next(
            (u for u in src.discord.globals.PING_INFO if u["user_id"] == member.id),
            None,
        )
        assert isinstance(user, dict)

        word_pings = [
            {"new": rf"\b({ping})\b", "original": ping} for ping in user["word_pings"]
        ]
        user_pings = word_pings + user["regex_pings"]
        matched = False
        response = ""

        for ping in user_pings:
            if isinstance(ping, dict):
                if len(re.findall(ping["new"], test, re.I)) > 0:
                    response += f"Your ping `{ping['original']}` matches `{test}`.\n"
                    matched = True
            else:
                if len(re.findall(ping, test, re.I)) > 0:
                    response += f"Your ping `{ping}` matches `{test}`.\n"
                    matched = True

        if not matched:
            return await interaction.response.send_message(
                f"`{test}` matched `0` pings."
            )
        else:
            return await interaction.response.send_message(response)

    @app_commands.command(
        name="list", description="Lists all of your registered pings."
    )
    @app_commands.guilds(SLASH_COMMAND_GUILDS)
    async def pinglist(self, interaction: discord.Interaction):
        member = interaction.user
        user = next(
            (u for u in src.discord.globals.PING_INFO if u["user_id"] == member.id),
            None,
        )

        # User has no pings
        if user is None or len(user["word_pings"] + user["regex_pings"]) == 0:
            return await interaction.response.send_message(
                "You have no registered pings."
            )

        else:
            response = ""
            if len(user["regex_pings"]) > 0:
                response += "Your RegEx pings are: " + ", ".join(
                    [f"`{regex}`" for regex in user["regex_pings"]]
                )
            if len(user["word_pings"]) > 0:
                response += "Your pings are: " + ", ".join(
                    [f"`{word}`" for word in user["word_pings"]]
                )
            if not len(response):
                response = "You have no registered pings."
            await interaction.response.send_message(response)

    @app_commands.command(
        name="remove", description="Removes a ping from your list of registered pings."
    )
    @app_commands.describe(
        word="The word to remove a ping for. Or use 'all' to remove all pings."
    )
    @app_commands.guilds(SLASH_COMMAND_GUILDS)
    async def pingremove(self, interaction: discord.Interaction, word: str):
        # Get the user's info
        member = interaction.user
        user = next(
            (u for u in src.discord.globals.PING_INFO if u["user_id"] == member.id),
            None,
        )

        # The user has no pings
        if user is None or len(user["word_pings"] + user["regex_pings"]) == 0:
            return await interaction.response.send_message(
                "You have no registered pings."
            )

        # Remove all of user's pings
        if word == "all":
            user["word_pings"] = []
            user["regex_pings"] = []
            await self.bot.mongo_database.update(
                "data",
                "pings",
                user["_id"],
                {"$pull": {"word_pings": {}, "regex_pings": {}}},
            )
            return await interaction.response.send_message(
                "I removed all of your pings."
            )

        # Attempt to remove a word ping
        if word in user["word_pings"]:
            user["word_pings"].remove(word)
            await self.bot.mongo_database.update(
                "data", "pings", user["_id"], {"$pull": {"word_pings": word}}
            )
            return await interaction.response.send_message(
                f"I removed the `{word}` ping you were referencing."
            )

        # Attempt to remove a regex ping
        elif word in user["regex_pings"]:
            user["regex_pings"].remove(word)
            await self.bot.mongo_database.update(
                "data", "pings", user["_id"], {"$pull": {"regex_pings": word}}
            )
            return await interaction.response.send_message(
                f"I removed the `{word}` RegEx ping you were referencing."
            )

        # Attempt to remove a word ping with extra formatting
        elif f"\\b({word})\\b" in user["word_pings"]:
            user["word_pings"].remove(f"\\e({word})\\b")
            await self.bot.mongo_database.update(
                "data",
                "pings",
                user["_id"],
                {"$pull": {"word_pings": f"\\e({word})\\b"}},
            )
            return await interaction.response.send_message(
                f"I removed the `{word}` ping you were referencing."
            )

        # Attempt to remove a word ping with alternate extra formatting
        elif f"({word})" in user["word_pings"]:
            user["word_pings"].remove(f"({word})")
            await self.bot.mongo_database.update(
                "data", "pings", user["_id"], {"$pull": {"word_pings": f"({word})"}}
            )
            return await interaction.response.send_message(
                f"I removed the `{word}` RegEx ping you were referencing."
            )

        else:
            return await interaction.response.send_message(
                f"I can't find the **`{word}`** ping you are referencing, sorry. Try another ping, or see all of your "
                f"pings with `/ping list`. "
            )


async def setup(bot: PiBot):
    await bot.add_cog(PingManager(bot))
