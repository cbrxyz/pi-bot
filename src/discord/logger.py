from __future__ import annotations

import traceback
from typing import TYPE_CHECKING, Union

import discord
from commanderrors import CommandNotAllowedInChannel
from discord.ext import commands
from src.discord.globals import (
    CENSOR,
    CHANNEL_DELETEDM,
    CHANNEL_DMLOG,
    CHANNEL_EDITEDM,
    CHANNEL_LEAVE,
    CHANNEL_LOUNGE,
    CHANNEL_WELCOME,
    PI_BOT_IDS,
    ROLE_UC,
    SERVER_ID,
)

if TYPE_CHECKING:
    from bot import PiBot
    from src.discord.censor import Censor
    from src.discord.reporter import Reporter


class Logger(commands.Cog):
    def __init__(self, bot: PiBot):
        self.bot = bot
        print("Initialized Logger cog.")

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        # Do not trigger the message edit event for newly-created messages
        if (discord.utils.utcnow() - after.created_at).total_seconds() < 2:
            return

        # Log edit event
        print(
            "Message from {0.author} edited to: {0.content}, from: {1.content}".format(
                after, before
            )
        )

        # Stop the event here for DM's (no need to censor, as author is the only one who can see them)
        if isinstance(after.channel, discord.DMChannel):
            return

        # Stop here for messages from Pi-Bot (no need to do anything else)
        if after.author.id in PI_BOT_IDS or after.author == self.bot.user:
            return

        # Delete messages that contain censored words
        censor_cog: Union[commands.Cog, Censor] = self.bot.get_cog("Censor")
        censor_found = censor_cog.censor_needed(after.content)
        if censor_found:
            await after.delete()
            await after.author.send(
                "You recently edited a message, but it **contained a censored word**! Therefore, I unfortunately had "
                "to delete it. In the future, please do not edit innapropriate words into your messages, and they "
                "will not be deleted. "
            )

        # Delete messages that have Discord invite links in them
        discord_invite_found = censor_cog.discord_invite_censor_needed(after.content)
        if discord_invite_found:
            await after.delete()
            await after.author.send(
                "You recently edited a message, but it **contained a link to another Discord server**! Therefore, "
                "I unfortunately had to delete it. In the future, please do not edit Discord invite links into your "
                "messages and they will not be deleted. "
            )

    async def send_to_dm_log(self, message: discord.Message):
        """
        Sends a direct message object to the staff log channel.
        """
        # Get the relevant objects
        guild: discord.Guild = self.bot.get_guild(SERVER_ID)
        dm_channel: discord.TextChannel = discord.utils.get(
            guild.text_channels, name=CHANNEL_DMLOG
        )

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
        # Give new user confirmed role
        unconfirmed_role = discord.utils.get(member.guild.roles, name=ROLE_UC)
        await member.add_roles(unconfirmed_role)

        # Check to see if user's name is innapropriate
        name = member.name
        censor_cog: Union[commands.Cog, Censor] = self.bot.get_cog("Censor")
        if censor_cog.censor_needed(name):
            # If name contains a censored link
            reporter_cog: Union[commands.Cog, Reporter] = self.bot.get_cog("Reporter")
            await reporter_cog.create_inappropriate_username_report(member, member.name)

        # Send welcome message to the welcoming channel
        join_channel = discord.utils.get(
            member.guild.text_channels, name=CHANNEL_WELCOME
        )
        await join_channel.send(
            f"{member.mention}, welcome to the Scioly.org Discord Server! "
            "You can add roles here, using the commands shown at the top of this channel. "
            "If you have any questions, please just ask here, and a helper or moderator will answer you ASAP."
            "\n\n"
            "**Please add roles by typing the commands above into the text box, and if you have a question, "
            "please type it here. After adding roles, a moderator will give you access to the rest of the server to "
            "chat with other "
            "members!** "
        )

        # Send fun alert message on every 100 members who join
        member_count = len(member.guild.members)
        lounge_channel: discord.TextChannel = discord.utils.get(
            member.guild.text_channels, name=CHANNEL_LOUNGE
        )
        if member_count % 100 == 0:
            await lounge_channel.send(
                f"Wow! There are now `{member_count}` members in the server!"
            )

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        # Post a leaving info message
        leave_channel: discord.TextChannel = discord.utils.get(
            member.guild.text_channels, name=CHANNEL_LEAVE
        )
        unconfirmed_role: discord.Role = discord.utils.get(
            member.guild.roles, name=ROLE_UC
        )

        if unconfirmed_role in member.roles:
            unconfirmed_statement = "Unconfirmed: :white_check_mark:"
        else:
            unconfirmed_statement = "Unconfirmed: :x:"

        joined_at = f"Joined at: `{str(member.joined_at)}`"

        if member.nick is not None:
            await leave_channel.send(
                f"**{member}** (nicknamed `{member.nick}`) has left the server (or was removed).\n{unconfirmed_statement}\n{joined_at}"
            )
        else:
            await leave_channel.send(
                f"**{member}** has left the server (or was removed).\n{unconfirmed_statement}\n{joined_at}"
            )

        # Delete any messages the user left in the welcoming channel
        welcome_channel = discord.utils.get(
            member.guild.text_channels, name=CHANNEL_WELCOME
        )
        async for message in welcome_channel.history():
            if not message.pinned:
                if member in message.mentions or member == message.author:
                    await message.delete()

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        # Notify staff if the user updated their name to include an innapropriate name
        if after.nick is None:
            return  # No need to check if user does not have a new nickname set

        # Get the Censor cog
        censor_cog: Union[commands.Cog, Censor] = self.bot.get_cog("Censor")
        censor_found = censor_cog.censor_needed(after.nick)
        if censor_found:
            # If name contains a censored link
            reporter_cog: Union[commands.Cog, Reporter] = self.bot.get_cog("Reporter")
            await reporter_cog.create_inappropriate_username_report(after, after.nick)

    @commands.Cog.listener()
    async def on_user_update(self, before, after):
        # Get the Censor cog and see if user's new username is offending censor
        censor_cog: Union[commands.Cog, Censor] = self.bot.get_cog("Censor")
        censor_found = censor_cog.censor_needed(after.name)
        if censor_found:
            # If name contains a censored link
            reporter_cog: Union[commands.Cog, Reporter] = self.bot.get_cog("Reporter")
            await reporter_cog.create_inappropriate_username_report(after, after.name)

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload):
        # Get the logger cog and log edited message
        await self.log_edit_message_payload(payload)

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload):
        # Get the logger cog and log deleted message
        await self.log_delete_message_payload(payload)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """
        Handles reaction add events. Currently, just used to suppress offensive emojis.
        """
        if str(payload.emoji) in CENSOR["emojis"]:
            channel = self.bot.get_channel(payload.channel_id)
            assert isinstance(channel, discord.TextChannel)

            partial_message = channel.get_partial_message(payload.message_id)
            assert isinstance(partial_message, discord.PartialMessage)

            await partial_message.clear_reaction(payload.emoji)

    @commands.Cog.listener()
    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ):
        print("Command Error:")
        print(error)

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
                "Sorry, it appears that your quotation marks are misaligned, and I can't read your query."
            )
        if isinstance(error, discord.ext.commands.ExpectedClosingQuoteError):
            return await ctx.send(
                "Oh. I was expecting you were going to close out your command with a quote somewhere, but never found it!"
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
                "Sorry, I'm having trouble reading one of the arguments you just used. Try again!"
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
        if isinstance(error, discord.ext.commands.NoPrivateMessage):
            return await ctx.send("Ope. You can't run this command in the DM's!")
        if isinstance(error, discord.ext.commands.NotOwner):
            return await ctx.send(
                "Oof. You have to be the bot's master to run that command!"
            )
        if isinstance(error, discord.ext.commands.MissingPermissions) or isinstance(
            error, discord.ext.commands.BotMissingPermissions
        ):
            return await ctx.send(
                "Er, you don't have the permissions to run this command."
            )
        if isinstance(error, discord.ext.commands.MissingRole) or isinstance(
            error, discord.ext.commands.BotMissingRole
        ):
            return await ctx.send(
                "Oh no... you don't have the required role to run this command."
            )
        if isinstance(error, discord.ext.commands.MissingAnyRole) or isinstance(
            error, discord.ext.commands.BotMissingAnyRole
        ):
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
        if isinstance(error, discord.ext.commands.CommandNotFound):
            return await ctx.send("Sorry, I couldn't find that command.")
        if isinstance(error, discord.ext.commands.CheckFailure):
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
                "Uh oh. This command has reached MAXIMUM CONCURRENCY. *lightning flash*. Try again later."
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

        # Overall errors
        if isinstance(error, discord.ext.commands.CommandError):
            return await ctx.send("Oops, there was a command error. Try again.")
        return

    @commands.Cog.listener()
    async def on_error(self, event, *args, **kwargs):
        print("Code Error:")
        print(traceback.format_exc())

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

        # Do not send a log for messages deleted out of the deleted messages channel (could cause a possible bot recursion)
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
                description="Because this message was not cached, I was unable to retrieve its content before it was deleted.",
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
