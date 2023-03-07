"""
Logs actions that happened on the Scioly.org Discord server to specific information
buckets, such as a Discord channel or database log.
"""
from __future__ import annotations

import logging
import traceback
from typing import TYPE_CHECKING

import discord
from commanderrors import CommandNotAllowedInChannel
from discord.ext import commands
from src.discord.globals import (
    CHANNEL_DELETEDM,
    CHANNEL_DMLOG,
    CHANNEL_EDITEDM,
    CHANNEL_LEAVE,
    CHANNEL_LOUNGE,
    CHANNEL_WELCOME,
    ROLE_UC,
    SERVER_ID,
)

if TYPE_CHECKING:
    from bot import PiBot


logger = logging.getLogger(__name__)


class Logger(commands.Cog):
    """
    Cog which stores all logging functionality.
    """

    # pylint: disable=no-self-use

    def __init__(self, bot: PiBot):
        self.bot = bot

    async def send_to_dm_log(self, message: discord.Message):
        """
        Sends a direct message object to the staff log channel. Used to store
        messages sent directly to the bot by a user.
        """
        # Get the relevant objects
        guild = self.bot.get_guild(SERVER_ID)
        assert isinstance(guild, discord.Guild)

        dm_channel = discord.utils.get(guild.text_channels, name=CHANNEL_DMLOG)
        assert isinstance(dm_channel, discord.TextChannel)

        # Create an embed containing the direct message info and send it to the log channel
        message_embed = discord.Embed(
            title=":speech_balloon: Incoming Direct Message to Pi-Bot",
            description=message.content
            if len(message.content) > 0
            else "This message contained no content.",
            color=discord.Color.brand_green(),
        )
        message_embed.add_field(
            name="Author", value=message.author.mention, inline=True
        )
        message_embed.add_field(name="Message ID", value=message.id, inline=True)
        message_embed.add_field(
            name="Sent",
            value=discord.utils.format_dt(message.created_at, "R"),
            inline=True,
        )
        message_embed.add_field(
            name="Attachments",
            value=" | ".join(
                [f"**{a.filename}**: [Link]({a.url})" for a in message.attachments]
            )
            if len(message.attachments) > 0
            else "None",
            inline=True,
        )
        await dm_channel.send(embed=message_embed)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """
        Executes when a member joins. Completes the following actions:
            * Sends a welcome message to the #welcome channel.
            * Sends a message to #lounge if the number of members ends with two zeros.

        Args:
            member (discord.Member): The member who just joined the server.
        """
        join_channel = discord.utils.get(
            member.guild.text_channels, name=CHANNEL_WELCOME
        )
        assert isinstance(join_channel, discord.TextChannel)
        await join_channel.send(
            f"{member.mention}, welcome to the Scioly.org Discord Server! "
            "You can add roles here, using the commands shown at the top of "
            "this channel. If you have any questions, please just ask here, "
            "and a helper or moderator will answer you ASAP."
            "\n\n"
            "**Please add roles by typing the commands above into the text box,"
            " and if you have a question, please type it here. After adding "
            "roles, a moderator will give you access to the rest of the server to "
            "chat with other members!**"
        )

        # Send fun alert message on every 100 members who join
        member_count = len(member.guild.members)
        lounge_channel = discord.utils.get(
            member.guild.text_channels, name=CHANNEL_LOUNGE
        )
        assert isinstance(lounge_channel, discord.TextChannel)

        if member_count % 100 == 0:
            await lounge_channel.send(
                f"Wow! There are now `{member_count}` members in the server!"
            )

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """
        When a member leaves the server, log that the member left, along with information
        about their membership when they left.

        Args:
            member (discord.Member): The member who left the server.
        """
        # Post a leaving info message
        leave_channel = discord.utils.get(
            member.guild.text_channels, name=CHANNEL_LEAVE
        )
        unconfirmed_role = discord.utils.get(member.guild.roles, name=ROLE_UC)
        assert isinstance(leave_channel, discord.TextChannel)
        assert isinstance(unconfirmed_role, discord.Role)

        if unconfirmed_role in member.roles:
            unconfirmed_statement = ":white_check_mark:"
            embed = discord.Embed(color=discord.Color.yellow())
        else:
            unconfirmed_statement = ":x:"
            embed = discord.Embed(color=discord.Color.brand_red())

        embed.title = "Member Leave"

        joined_at = (
            f"{discord.utils.format_dt(member.joined_at, style='f')} "
            f"({discord.utils.format_dt(member.joined_at, style='R')})"
        )
        embed.description = (
            f"**{member}** (nicknamed `{member.nick}`) has left the server (or was removed)."
            if member.nick
            else f"**{member}** has left the server (or was removed)."
        )

        embed.add_field(name="Joined At", value=joined_at)
        embed.add_field(name="Unconfirmed", value=unconfirmed_statement)
        await leave_channel.send(embed=embed)

        # Delete any messages the user left in the welcoming channel
        welcome_channel = discord.utils.get(
            member.guild.text_channels, name=CHANNEL_WELCOME
        )
        assert isinstance(welcome_channel, discord.TextChannel)
        async for message in welcome_channel.history():
            if not message.pinned:
                if member in message.mentions or member == message.author:
                    await message.delete()

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload: discord.RawMessageUpdateEvent):
        """
        When any message is edited, get the payload and create a log with it.

        Args:
            payload (RawMessageUpdateEvent): The payload of the editing.
        """
        # Get the logger cog and log edited message
        await self.log_edit_message_payload(payload)

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent):
        """
        When some message is deleted across the server, grab the event payload
        and create a log from it.

        Args:
            payload (RawMessageDeleteEvent): The payload to log.
        """
        # Get the logger cog and log deleted message
        await self.log_delete_message_payload(payload)

    @commands.Cog.listener()
    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ):
        # If a cog has a separate error handler, don't also run the global error handler
        if (
            ctx.command.has_error_handler() or ctx.cog.has_error_handler()
        ) and True == ctx.__slots__:
            return

        # Argument parsing errors
        if isinstance(error, discord.ext.commands.UnexpectedQuoteError) or isinstance(
            error, discord.ext.commands.InvalidEndOfQuotedStringError
        ):
            return await ctx.send(
                "Sorry, it appears that your quotation marks are misaligned, "
                "and I can't read your query."
            )
        if isinstance(error, discord.ext.commands.ExpectedClosingQuoteError):
            return await ctx.send(
                "Oh. I was expecting you were going to close out your command "
                "with a quote somewhere, but never found it!"
            )

        # User input errors
        if isinstance(error, discord.ext.commands.MissingRequiredArgument):
            return await ctx.send(
                "Oops, you are missing a required argument in the command."
            )
        if isinstance(error, discord.ext.commands.ArgumentParsingError):
            return await ctx.send("Sorry, I had trouble parsing one of your arguments.")
        if isinstance(error, discord.ext.commands.TooManyArguments):
            return await ctx.send("Woahhh!! Too many arguments for this command!")
        if isinstance(error, discord.ext.commands.BadArgument) or isinstance(
            error, discord.ext.commands.BadUnionArgument
        ):
            return await ctx.send(
                "Sorry, I'm having trouble reading one of the arguments you just "
                "used. Try again!"
            )

        # Check failure errors
        if isinstance(error, discord.ext.commands.CheckAnyFailure):
            return await ctx.send(
                "It looks like you aren't able to run this command, sorry."
            )
        if isinstance(error, discord.ext.commands.PrivateMessageOnly):
            return await ctx.send(
                "Pssttt. You're going to have to DM me to run this command!"
            )
        if isinstance(
            error,
            (
                discord.ext.commands.NoPrivateMessage,
                discord.app_commands.NoPrivateMessage,
            ),
        ):
            return await ctx.send("Ope. You can't run this command in the DM's!")
        if isinstance(error, discord.ext.commands.NotOwner):
            return await ctx.send(
                "Oof. You have to be the bot's master to run that command!"
            )
        if isinstance(
            error,
            (
                discord.ext.commands.MissingPermissions,
                discord.ext.commands.BotMissingPermissions,
                discord.app_commands.MissingPermissions,
                discord.app_commands.BotMissingPermissions,
            ),
        ):
            return await ctx.send(
                "Er, you don't have the permissions to run this command."
            )
        if isinstance(
            error, discord.ext.commands.MissingRole, discord.app_commands.MissingRole
        ) or isinstance(error, discord.ext.commands.BotMissingRole):
            return await ctx.send(
                "Oh no... you don't have the required role to run this command."
            )
        if isinstance(error, discord.ext.commands.NSFWChannelRequired):
            return await ctx.send(
                "Uh... this channel can only be run in a NSFW channel... sorry to disappoint."
            )

        # Command errors
        if isinstance(error, CommandNotAllowedInChannel):
            return await ctx.send(
                f"You are not allowed to use this command in {error.channel.mention}."
            )
        if isinstance(error, discord.ext.commands.ConversionError):
            return await ctx.send("Oops, there was a bot error here, sorry about that.")
        if isinstance(error, discord.ext.commands.UserInputError):
            return await ctx.send(
                "Hmmm... I'm having trouble reading what you're trying to tell me."
            )
        if isinstance(
            error,
            (
                discord.ext.commands.CommandNotFound,
                discord.app_commands.CommandNotFound,
            ),
        ):
            return await ctx.send("Sorry, I couldn't find that command.")
        if isinstance(
            error,
            (discord.ext.commands.CheckFailure, discord.app_commands.CheckFailure),
        ):
            return await ctx.send("Sorry, but I don't think you can run that command.")
        if isinstance(error, discord.ext.commands.DisabledCommand):
            return await ctx.send("Sorry, but this command is disabled.")
        if isinstance(error, discord.ext.commands.CommandInvokeError):
            return await ctx.send(
                "Sorry, but an error incurred when the command was invoked."
            )
        if isinstance(error, discord.ext.commands.CommandOnCooldown):
            return await ctx.send("Slow down buster! This command's on cooldown.")
        if isinstance(error, discord.ext.commands.MaxConcurrencyReached):
            return await ctx.send(
                "Uh oh. This command has reached MAXIMUM CONCURRENCY. "
                "*lightning flash*. Try again later."
            )

        # Extension errors (not doing specifics)
        if isinstance(error, discord.ext.commands.ExtensionError):
            return await ctx.send(
                "Oh no. There's an extension error. Please ping a developer about this one."
            )

        # Client exception errors (not doing specifics)
        if isinstance(error, discord.ext.commands.CommandRegistrationError):
            return await ctx.send(
                "Oh boy. Command registration error. Please ping a developer about this."
            )

        if isinstance(error, discord.app_commands.CheckFailure):
            return await ctx.send(
                "Unfortunately, you are not able to use this command. Try running the command in `#bot-spam`."
            )

        # Overall errors
        if isinstance(error, discord.ext.commands.CommandError):
            return await ctx.send("Oops, there was a command error. Try again.")
        return

    @commands.Cog.listener()
    async def on_error(self, _):
        logger.error(traceback.format_exc())

    async def log_edit_message_payload(self, payload):
        """
        Logs a payload for the 'Edit Message' event.
        """
        # Get the required resources for logging
        channel = self.bot.get_channel(payload.channel_id)
        guild = (
            self.bot.get_guild(SERVER_ID)
            if channel.type == discord.ChannelType.private
            else channel.guild
        )
        edited_channel: discord.TextChannel = discord.utils.get(
            guild.text_channels, name=CHANNEL_EDITEDM
        )

        # Ignore payloads for events in logging channels (which would cause recursion)
        if channel.type != discord.ChannelType.private and channel.name in [
            CHANNEL_EDITEDM,
            CHANNEL_DELETEDM,
            CHANNEL_DMLOG,
        ]:
            return

        # Attempt to log from the cached message if found, else just report on what is available
        try:
            message = payload.cached_message
            if (discord.utils.utcnow() - message.created_at).total_seconds() < 2:
                # No need to log edit event for a message that was just created
                return

            message_now = await channel.fetch_message(message.id)
            channel_name = (
                f"{message.author.mention}'s DM"
                if channel.type == discord.ChannelType.private
                else message.channel.mention
            )

            embed = discord.Embed(
                title=":pencil: Edited Message", color=discord.Color.yellow()
            )
            fields = [
                {"name": "Author", "value": message.author, "inline": True},
                {"name": "Channel", "value": channel_name, "inline": True},
                {
                    "name": "Message ID",
                    "value": f"{payload.message_id} ([jump!]({message_now.jump_url}))",
                    "inline": True,
                },
                {
                    "name": "Created At",
                    "value": discord.utils.format_dt(message.created_at, "R"),
                    "inline": True,
                },
                {
                    "name": "Edited At",
                    "value": discord.utils.format_dt(message_now.edited_at, "R"),
                    "inline": True,
                },
                {
                    "name": "Attachments",
                    "value": " | ".join(
                        [
                            f"**{a.filename}**: [Link]({a.url})"
                            for a in message.attachments
                        ]
                    )
                    if len(message.attachments) > 0
                    else "None",
                    "inline": "False",
                },
                {
                    "name": "Past Content",
                    "value": message.content[:1024]
                    if len(message.content) > 0
                    else "None",
                    "inline": "False",
                },
                {
                    "name": "New Content",
                    "value": message_now.content[:1024]
                    if len(message_now.content) > 0
                    else "None",
                    "inline": "False",
                },
                {
                    "name": "Embed",
                    "value": "\n".join([str(e.to_dict()) for e in message.embeds])
                    if len(message.embeds) > 0
                    else "None",
                    "inline": "False",
                },
            ]
            for field in fields:
                embed.add_field(
                    name=field["name"], value=field["value"], inline=field["inline"]
                )

            await edited_channel.send(embed=embed)

        except Exception as _:  # No cached message is available
            message_now = await channel.fetch_message(payload.message_id)
            embed = discord.Embed(
                title=":pencil: Edited Message", color=discord.Color.orange()
            )

            fields = [
                {
                    "name": "Channel",
                    "value": self.bot.get_channel(payload.channel_id).mention,
                    "inline": True,
                },
                {
                    "name": "Message ID",
                    "value": f"{payload.message_id} ([jump!]({message_now.jump_url}))",
                    "inline": True,
                },
                {"name": "Author", "value": message_now.author, "inline": True},
                {
                    "name": "Created At",
                    "value": discord.utils.format_dt(message_now.created_at, "R"),
                    "inline": True,
                },
                {
                    "name": "Edited At",
                    "value": discord.utils.format_dt(message_now.edited_at, "R"),
                    "inline": True,
                },
                {
                    "name": "New Content",
                    "value": message_now.content[:1024]
                    if len(message_now.content) > 0
                    else "None",
                    "inline": "False",
                },
                {
                    "name": "Current Attachments",
                    "value": " | ".join(
                        [
                            f"**{a.filename}**: [Link]({a.url})"
                            for a in message_now.attachments
                        ]
                    )
                    if len(message_now.attachments) > 0
                    else "None",
                    "inline": "False",
                },
                {
                    "name": "Current Embed",
                    "value": "\n".join([str(e.to_dict()) for e in message_now.embeds])[
                        :1024
                    ]
                    if len(message_now.embeds) > 0
                    else "None",
                    "inline": "False",
                },
            ]
            for field in fields:
                embed.add_field(
                    name=field["name"], value=field["value"], inline=field["inline"]
                )

            await edited_channel.send(embed=embed)

    async def log_delete_message_payload(self, payload):
        """
        Logs a message payload that came from a 'Delete Message' payload.
        """
        # Get the required resources
        channel = self.bot.get_channel(payload.channel_id)
        guild = (
            self.bot.get_guild(SERVER_ID)
            if channel.type == discord.ChannelType.private
            else channel.guild
        )
        deleted_channel: discord.TextChannel = discord.utils.get(
            guild.text_channels, name=CHANNEL_DELETEDM
        )

        # Do not send a log for messages deleted out of the deleted messages
        # channel (could cause a possible bot recursion)
        if channel.type != discord.ChannelType.private and channel.name in [
            CHANNEL_DELETEDM
        ]:
            return

        try:
            message = payload.cached_message
            channel_name = (
                f"{message.author.mention}'s DM"
                if channel.type == discord.ChannelType.private
                else message.channel.mention
            )
            embed = discord.Embed(
                title=":fire: Deleted Message", color=discord.Color.brand_red()
            )
            fields = [
                {"name": "Author", "value": message.author, "inline": True},
                {"name": "Channel", "value": channel_name, "inline": True},
                {
                    "name": "Message ID",
                    "value": f"`{payload.message_id}`",
                    "inline": True,
                },
                {
                    "name": "Created At",
                    "value": discord.utils.format_dt(message.created_at, "R"),
                    "inline": True,
                },
                {
                    "name": "Deleted At",
                    "value": discord.utils.format_dt(discord.utils.utcnow(), "R"),
                    "inline": True,
                },
                {
                    "name": "Attachments",
                    "value": " | ".join(
                        [
                            f"**{a.filename}**: [Link]({a.url})"
                            for a in message.attachments
                        ]
                    )
                    if len(message.attachments) > 0
                    else "None",
                    "inline": "False",
                },
                {
                    "name": "Content",
                    "value": str(message.content)[:1024]
                    if len(message.content) > 0
                    else "None",
                    "inline": "False",
                },
                {
                    "name": "Embed",
                    "value": "\n".join([str(e.to_dict()) for e in message.embeds])[
                        :1024
                    ]
                    if len(message.embeds) > 0
                    else "None",
                    "inline": "False",
                },
            ]
            for field in fields:
                embed.add_field(
                    name=field["name"], value=field["value"], inline=field["inline"]
                )

            await deleted_channel.send(embed=embed)

        except Exception as _:

            embed = discord.Embed(
                title=":fire: Deleted Message",
                description=(
                    "Because this message was not cached, I was unable to "
                    "retrieve its content before it was deleted. _Note, this may "
                    "mean that the message was ephemeral, aka, only visible to one "
                    "user. Ephemeral messages are not cached, as most users will "
                    "never see them._"
                ),
                color=discord.Color.dark_red(),
            )
            fields = [
                {
                    "name": "Channel",
                    "value": self.bot.get_channel(payload.channel_id).mention,
                    "inline": True,
                },
                {
                    "name": "Message ID",
                    "value": f"`{payload.message_id}`",
                    "inline": True,
                },
            ]
            for field in fields:
                embed.add_field(
                    name=field["name"], value=field["value"], inline=field["inline"]
                )

            await deleted_channel.send(embed=embed)


async def setup(bot: PiBot):
    await bot.add_cog(Logger(bot))
