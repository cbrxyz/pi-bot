import asyncio
import traceback
import uuid

import discord
import src.discord.globals
from commanderrors import CommandNotAllowedInChannel
from discord import RawReactionActionEvent, ApplicationContext
from discord.ext import commands
from src.discord.globals import *
from typing import Optional, Dict, Any

##############
# SERVER VARIABLES
##############


##############
# DEV MODE CONFIG
##############

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix=(BOT_PREFIX), case_insensitive=True, intents=intents)

##############
# CHECKS
##############

from commandchecks import *

##############
# FUNCTIONS TO BE REMOVED
##############
bot.remove_command("help")

##############
# ASYNC WRAPPERS
##############

##############
# FUNCTIONS
##############


@bot.event
async def on_ready() -> None:
    """
    Called when the bot is enabled and ready to be run. Prints a message to the console
    alerting the developer that the bot is functional.
    """
    print(f"{bot.user} has connected!")


@bot.event
async def on_message_edit(before: discord.Message, after: discord.Message) -> None:
    """
    Event handler for messsage editing. For all edited messages that were not just created,
    the message is logged to stdout. Direct messages and messages from bots are not checked.

    Checks for a variety of things, including:
        * Whether the message needs to be censored.
        * Whether Discord invite links need to be removed from the message.

    Args:
        before (discord.Message): The message before it was edited.
        after (discord.Message): The message after it was edited.
    """
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
    if after.author.id in PI_BOT_IDS or after.author == bot:
        return

    # Delete messages that contain censored words
    censor_cog = bot.get_cog("Censor")
    censor_found = censor_cog.censor_needed(after.content)
    if censor_found:
        await after.delete()
        await after.author.send(
            "You recently edited a message, but it **contained a censored word**! Therefore, I unfortunately had to delete it. In the future, please do not edit innapropriate words into your messages, and they will not be deleted."
        )

    # Delete messages that have Discord invite links in them
    discord_invite_found = censor_cog.discord_invite_censor_needed(after.content)
    if discord_invite_found:
        await after.delete()
        await after.author.send(
            "You recently edited a message, but it **contained a link to another Discord server**! Therefore, I unfortunately had to delete it. In the future, please do not edit Discord invite links into your messages and they will not be deleted."
        )


async def send_to_dm_log(message: discord.Message) -> None:
    """
    Logs an incoming direct message to the dm-log channel. Creates an embed with
    the message content and sends it to the channel.
    """
    # Get the relevant objects
    guild = bot.get_guild(SERVER_ID)
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
    message_embed.add_field(name="Author", value=message.author.mention, inline=True)
    message_embed.add_field(name="Message ID", value=message.id, inline=True)
    message_embed.add_field(
        name="Sent", value=discord.utils.format_dt(message.created_at, "R"), inline=True
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


listeners: Dict[str, Dict[str, Any]] = {}


async def listen_for_response(
    follow_id: int, timeout: int
) -> Optional[discord.Message]:
    """
    Creates a global listener for a message from a user.

    Args:
        follow_id (int): The user ID to create the listener for
        timeout (int): The number of seconds to wait before returning None,
          and assuming the user abandoned the operation.

    Returns:
        Optional[discord.Message]: The found message or None.
    """
    # TODO Use native asyncio methods instead of checking each second
    my_id = str(uuid.uuid4())
    listeners[my_id] = {"follow_id": follow_id, "timeout": timeout, "message": None}
    count = timeout
    while count > 0:
        await asyncio.sleep(1)
        count -= 1
        if listeners[my_id]["message"] != None:
            return listeners[my_id]["message"]
    return None


@bot.event
async def on_message(message: discord.Message) -> None:
    """
    Event handler to handle sent messages. No action is completed for bots.

    Does multiple actions:
        * Checks to see if the bot is waiting for the user to respond to an interaction
          with text.
        * Logs incoming DMs
        * Prints noticeable messages to stdout
        * Checks if the message needs to be censored
    """
    # Nothing needs to be done to the bot's own messages
    if message.author.bot:
        return

    # If user is being listened to, return their message
    for listener in listeners.items():
        if message.author.id == listener[1]["follow_id"]:
            listeners[listener[0]]["message"] = message

    # Log incoming direct messages that aren't from bots
    if isinstance(message.channel, discord.DMChannel) and message.author != bot:
        await send_to_dm_log(message)
        print(f"Message from {message.author} through DM's: {message.content}")

    else:
        # Print to output
        if not (
            message.author.id in PI_BOT_IDS
            and isinstance(message.channel, discord.TextChannel)
            and message.channel.name
            in [CHANNEL_EDITEDM, CHANNEL_DELETEDM, CHANNEL_DMLOG]
        ):
            # avoid sending logs for messages in log channels
            print(
                f"Message from {message.author} in #{message.channel}: {message.content}"
            )

    # Check if the message contains a censored word/emoji
    is_private = any(
        [
            isinstance(message.channel, discord_class)
            for discord_class in [discord.DMChannel, discord.GroupChannel]
        ]
    )
    if message.content and not is_private:
        censor = bot.get_cog("Censor")
        await censor.on_message(message)

        # Check to see if the message contains repeated content or has too many caps
        spam = bot.get_cog("SpamManager")
        await spam.store_and_validate(message)


@bot.event
async def on_member_join(member: discord.Member) -> None:
    """
    Handles new members joining the server.

    Does multiple actions:
        * Checks the member's display name to see if an innapropriate username report
          needs to be filed.
        * Sends a welcome message to the welcome channel.
        * Sends a message to the lounge channel if the member joining causes the
          member count to be divisible by 100.
    """
    # Give new user confirmed role
    unconfirmed_role = discord.utils.get(member.guild.roles, name=ROLE_UC)
    assert isinstance(unconfirmed_role, discord.Role)
    await member.add_roles(unconfirmed_role)  # type: ignore

    # Check to see if user's name is innapropriate
    name = member.name
    censor_cog = bot.get_cog("Censor")
    if censor_cog.censor_needed(name):
        # If name contains a censored link
        reporter_cog = bot.get_cog("Reporter")
        await reporter_cog.create_innapropriate_username_report(member, member.name)

    # Send welcome message to the welcoming channel
    join_channel = discord.utils.get(member.guild.text_channels, name=CHANNEL_WELCOME)
    assert isinstance(join_channel, discord.TextChannel)
    await join_channel.send(
        f"{member.mention}, welcome to the Scioly.org Discord Server! "
        + "You can add roles here, using the commands shown at the top of this channel. "
        + "If you have any questions, please just ask here, and a helper or moderator will answer you ASAP."
        + "\n\n"
        + "**Please add roles by typing the commands above into the text box, and if you have a question, please type it here. After adding roles, a moderator will give you access to the rest of the server to chat with other members!**"
    )

    # Send fun alert message on every 100 members who join
    member_count = len(member.guild.members)
    lounge_channel = discord.utils.get(member.guild.text_channels, name=CHANNEL_LOUNGE)
    assert isinstance(lounge_channel, discord.TextChannel)
    if member_count % 100 == 0:
        await lounge_channel.send(
            f"Wow! There are now `{member_count}` members in the server!"
        )


@bot.event
async def on_member_remove(member: discord.Member) -> None:
    """
    Handles events regarding members leaving the server.

    Does multiple actions:
        * Posts a message to the channel which stores member leave logs.
        * Deletes all of the user's history in the welcome channel.

    Args:
        member (discord.Member): The member who left.
    """
    # Post a leaving info message
    leave_channel = discord.utils.get(member.guild.text_channels, name=CHANNEL_LEAVE)
    assert isinstance(leave_channel, discord.TextChannel)
    unconfirmed_role = discord.utils.get(member.guild.roles, name=ROLE_UC)

    if unconfirmed_role in member.roles:
        unconfirmed_statement = "Unconfirmed: :white_check_mark:"
    else:
        unconfirmed_statement = "Unconfirmed: :x:"

    joined_at = f"Joined at: `{str(member.joined_at)}`"

    if member.nick != None:
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
    assert isinstance(welcome_channel, discord.TextChannel)
    async for message in welcome_channel.history():
        if not message.pinned:
            if member in message.mentions or member == message.author:
                await message.delete()


@bot.event
async def on_member_update(_: discord.Member, after: discord.Member) -> None:
    """
    Handles members updating information about their profiles in the server.

    Currently, this only checks to see if the member updated their username to include
    an inappropriate term, in which case, an inappropriate username report is filed.

    Args:
        _ (discord.Member): The member before updating their profile.
        after (discord.Member): The member after updating their profile.
    """
    # Notify staff if the user updated their name to include an innapropriate name
    if after.nick == None:
        return  # No need to check if user does not have a new nickname set

    # Get the Censor cog
    censor_cog = bot.get_cog("Censor")
    censor_found = censor_cog.censor_needed(after.nick)
    if censor_found:
        # If name contains a censored link
        reporter_cog = bot.get_cog("Reporter")
        await reporter_cog.create_innapropriate_username_report(after, after.nick)


@bot.event
async def on_user_update(_: discord.User, after: discord.User) -> None:
    """
    Handles users updating information about themselves.

    Currently, this only checks the user's display name, and files an innapropriate
    username report if necessary.

    Args:
        _ (discord.Member): The member before updating their profile.
        after (discord.Member): The member after updating their profile.
    """
    # Get the Censor cog and see if user's new username is offending censor
    censor_cog = bot.get_cog("Censor")
    censor_found = censor_cog.censor_needed(after.name)
    if censor_found:
        # If name contains a censored link
        reporter_cog = bot.get_cog("Reporter")
        await reporter_cog.create_innapropriate_username_report(after, after.name)


@bot.event
async def on_raw_message_edit(payload: discord.RawMessageUpdateEvent) -> None:
    """
    Handles the raw payloads of messages being updated. This method is used
    to catch all message edit events, including those in which the bot can't see.

    Currently, this method is only responsible for logging information about the payload
    into a human-readable format.

    Args:
        payload (discord.RawMessageUpdateEvent): The message payload.
    """
    # Get the logger cog and log edited message
    logger_cog = bot.get_cog("Logger")
    await logger_cog.log_edit_message_payload(payload)


@bot.event
async def on_raw_message_delete(payload: discord.RawMessageDeleteEvent) -> None:
    """
    Handles the raw payloads of messages being deleted. This method is used to
    catch all instances of messages being deleted.

    Currently, this method is only responsible for logging the delete events into
    a human readable format.

    Args:
        payload (discord.RawMessageDeleteEvent): The raw message payload.
    """
    # Get the logger cog and log deleted message
    logger_cog = bot.get_cog("Logger")
    await logger_cog.log_delete_message_payload(payload)


@bot.event
async def on_raw_reaction_add(payload: RawReactionActionEvent) -> None:
    """
    Handles reaction add events. Currently just used to suppress offensive emojis.

    Args:
        payload (discord.RawReactionActionEvent): The raw payload.
    """
    if str(payload.emoji) in src.discord.globals.CENSOR["emojis"]:
        channel = bot.get_channel(payload.channel_id)
        assert isinstance(channel, discord.TextChannel)
        partial_message = channel.get_partial_message(payload.message_id)
        assert isinstance(partial_message, discord.PartialMessage)
        await partial_message.clear_reaction(payload.emoji)  # type: ignore


@bot.event
async def on_command_error(ctx: ApplicationContext, error) -> Optional[discord.Message]:
    """
    Global command error handler. Handles errors which weren't handled anywhere else.
    Helps to let users know why an error may have occurred.
    """
    print("Command Error:")
    print(error)

    # If a cog has a separate error handler, don't also run the global error handler
    if (
        ctx.command.has_error_handler() or ctx.cog.has_error_handler()
    ) and ctx.__slots__ == True:
        return None

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
        return await ctx.send("Er, you don't have the permissions to run this command.")
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
    return None


@bot.event
async def on_error(_):
    """
    Handles all bot-related errors. Logs the traceback to stdout so developers
    are aware of the issue.
    """
    print("Code Error:")
    print(traceback.format_exc())


# The cogs here will be executed in set order everytime
# Therefore on_message events can be rearraged to produce different outputs
bot.load_extension("src.discord.censor")
bot.load_extension("src.discord.ping")
bot.load_extension("src.discord.staffcommands")
bot.load_extension("src.discord.staff.invitationals")
bot.load_extension("src.discord.staff.censor")
bot.load_extension("src.discord.staff.tags")
bot.load_extension("src.discord.staff.events")
bot.load_extension("src.discord.embed")
bot.load_extension("src.discord.membercommands")
bot.load_extension("src.discord.devtools")
bot.load_extension("src.discord.funcommands")
bot.load_extension("src.discord.tasks")
bot.load_extension("src.discord.spam")
bot.load_extension("src.discord.reporter")
bot.load_extension("src.discord.logger")

# Use old HTTP version
discord.http.API_VERSION = 9

if dev_mode:
    bot.run(DEV_TOKEN)
else:
    bot.run(TOKEN)
