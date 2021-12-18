import discord
import os
import traceback
import re
import time
import asyncio
import uuid
import datetime
import dateparser
import numpy as np

from discord import channel
from discord.ext import commands

from src.discord.utils import auto_report
from embed import assemble_embed
from commanderrors import CommandNotAllowedInChannel

##############
# SERVER VARIABLES
##############

from src.discord.globals import *

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
async def on_ready():
    """Called when the bot is enabled and ready to be run."""
    print(f'{bot.user} has connected!')

@bot.event
async def on_message_edit(before, after):
    # Do not trigger the message edit event for newly-created messages
    if (discord.utils.utcnow() - after.created_at).total_seconds() < 2:
        return

    # Log edit event
    print('Message from {0.author} edited to: {0.content}, from: {1.content}'.format(after, before))

    # Stop the event here for DM's (no need to censor, as author is the only one who can see them)
    if isinstance(after.channel, discord.DMChannel):
        return

    # Delete messages that contain censored words
    censor_cog = bot.get_cog("Censor")
    censor_found = censor_cog.censor_needed(after)
    if censor_found:
        await after.delete()
        await after.author.send("You recently edited a message, but it **contained a censored word**! Therefore, I unfortunately had to delete it. In the future, please do not edit innapropriate words into your messages, and they will not be deleted.")

    # Delete messages that have Discord invite links in them
    discord_invite_found = censor_cog.discord_invite_censor_needed(after)
    if discord_invite_found:
        await after.delete()
        await after.author.send("You recently edited a message, but it **contained a link to another Discord server**! Therefore, I unfortunately had to delete it. In the future, please do not edit Discord invite links into your messages and they will not be deleted.")

async def send_to_dm_log(message):
    """
    Sends a direct message object to the staff log channel.
    """
    # Get the relevant objects
    guild = bot.get_guild(SERVER_ID)
    dm_channel = discord.utils.get(guild.text_channels, name=CHANNEL_DMLOG)

    # Create an embed containing the direct message info and send it to the log channel
    message_embed = discord.Embed(
        title = ":speech_balloon: Incoming Direct Message to Pi-Bot",
        description = message.content if len(message.content) > 0 else "This message contained no content.",
        color = discord.Color.brand_green()
    )
    message_embed.add_field(name = "Author", value = message.author.mention, inline = True)
    message_embed.add_field(name = "Message ID", value = message.id, inline = True)
    message_embed.add_field(name = "Sent", value = discord.utils.format_dt(message.created_at, 'R'), inline = True)
    message_embed.add_field(name = "Attachments", value = " | ".join([f"**{a.filename}**: [Link]({a.url})" for a in message.attachments]) if len(message.attachments) > 0 else "None", inline = True)
    await dm_channel.send(embed = message_embed)

listeners = {}
async def listen_for_response(
    follow_id: int,
    timeout: int
):
    """
    Creates a global listener for a message from a user.

    :param follow_id: the user ID to create the listener for
    :param timeout: the amount of time to wait before returning None, assuming the user abandoned the operation

    :return: the found message or None
    """
    my_id = str(uuid.uuid4())
    listeners[my_id] = {
        'follow_id': follow_id,
        'timeout': timeout,
        'message': None
    }
    count = timeout
    while (count > 0):
        await asyncio.sleep(1)
        count -= 1
        if listeners[my_id]['message'] != None:
            return listeners[my_id]['message']
    return None

@bot.event
async def on_message(message):
    # Nothing needs to be done to the bot's own messages
    if message.author.id in PI_BOT_IDS:
        return

    # If user is being listened to, return their message
    for listener in listeners.items():
        if message.author.id == listener[1]['follow_id']:
            listeners[listener[0]]['message'] = message

    # Log incoming direct messages
    if type(message.channel) == discord.DMChannel and message.author not in PI_BOT_IDS:
        await send_to_dm_log(message)
        print(f"Message from {message.author} through DM's: {message.content}")
    else:
        # Print to output
        if not (message.author.id in PI_BOT_IDS and message.channel.name in [CHANNEL_EDITEDM, CHANNEL_DELETEDM, CHANNEL_DMLOG]):
            # avoid sending logs for messages in log channels
            print(f'Message from {message.author} in #{message.channel}: {message.content}')

    censor = bot.get_cog("Censor")
    if censor != None: # only case where this occurs if the cog is disabled
        await censor.on_message(message)

    # SPAM TESTING (should prob put in its own cog cuz its not essential for censor or commands)
    #  if spamming commands, we should just issue a command cooldown (2-5s makes sense)
    spam = bot.get_cog("SpamManager")
    if spam != None:
        await spam.store_and_validate(message)

@bot.event
async def on_member_join(member):
    role = discord.utils.get(member.guild.roles, name=ROLE_UC)
    join_channel = discord.utils.get(member.guild.text_channels, name=CHANNEL_WELCOME)
    await member.add_roles(role)
    name = member.name
    for word in src.discord.globals.CENSOR['words']:
        if len(re.findall(fr"\b({word})\b", name, re.I)):
            await auto_report(bot, "Innapropriate Username Detected", "red", f"A new member ({str(member)}) has joined the server, and I have detected that their username is innapropriate.")
    await join_channel.send(f"{member.mention}, welcome to the Scioly.org Discord Server! " +
    "You can add roles here, using the commands shown at the top of this channel. " +
    "If you have any questions, please just ask here, and a helper or moderator will answer you ASAP." +
    "\n\n" +
    "**Please add roles by typing the commands above into the text box, and if you have a question, please type it here. After adding roles, a moderator will give you access to the rest of the server to chat with other members!**")
    member_count = len(member.guild.members)
    lounge_channel = discord.utils.get(member.guild.text_channels, name=CHANNEL_LOUNGE)
    if member_count % 100 == 0:
        await lounge_channel.send(f"Wow! There are now `{member_count}` members in the server!")

@bot.event
async def on_member_remove(member):
    leave_channel = discord.utils.get(member.guild.text_channels, name=CHANNEL_LEAVE)
    unconfirmed_role = discord.utils.get(member.guild.roles, name=ROLE_UC)
    if unconfirmed_role in member.roles:
        unconfirmed_statement = "Unconfirmed: :white_check_mark:"
    else:
        unconfirmed_statement = "Unconfirmed: :x:"
    joined_at = f"Joined at: `{str(member.joined_at)}`"
    if member.nick != None:
        await leave_channel.send(f"**{member}** (nicknamed `{member.nick}`) has left the server (or was removed).\n{unconfirmed_statement}\n{joined_at}")
    else:
        await leave_channel.send(f"**{member}** has left the server (or was removed).\n{unconfirmed_statement}\n{joined_at}")
    welcome_channel = discord.utils.get(member.guild.text_channels, name=CHANNEL_WELCOME)
    # when user leaves, determine if they are mentioned in any messages in #welcome, delete if so
    async for message in welcome_channel.history(oldest_first=True):
        if not message.pinned:
            if member in message.mentions:
                await message.delete()

@bot.event
async def on_member_update(before, after):
    if after.nick == None: return
    for word in src.discord.globals.CENSOR['words']:
        if len(re.findall(fr"\b({word})\b", after.nick, re.I)):
            await auto_report(bot, "Innapropriate Username Detected", "red", f"A member ({str(after)}) has updated their nickname to **{after.nick}**, which the censor caught as innapropriate.")

@bot.event
async def on_user_update(before, after):
    for word in src.discord.globals.CENSOR['words']:
        if len(re.findall(fr"\b({word})\b", after.name, re.I)):
            await auto_report(bot, "Innapropriate Username Detected", "red", f"A member ({str(member)}) has updated their nickname to **{after.name}**, which the censor caught as innapropriate.")

@bot.event
async def on_raw_message_edit(payload):
    channel = bot.get_channel(payload.channel_id)
    guild = bot.get_guild(SERVER_ID) if channel.type == discord.ChannelType.private else channel.guild
    edited_channel = discord.utils.get(guild.text_channels, name=CHANNEL_EDITEDM)
    if channel.type != discord.ChannelType.private and channel.name in [CHANNEL_EDITEDM, CHANNEL_DELETEDM, CHANNEL_DMLOG]:
        return
    try:
        message = payload.cached_message
        if (datetime.datetime.now() - message.created_at).total_seconds() < 2:
            # no need to log events because message was created
            return
        message_now = await channel.fetch_message(message.id)
        channel_name = f"{message.author.mention}'s DM" if channel.type == discord.ChannelType.private else message.channel.mention
        embed = assemble_embed(
            title=":pencil: Edited Message",
            fields=[
                {
                    "name": "Author",
                    "value": message.author,
                    "inline": "True"
                },
                {
                    "name": "Channel",
                    "value": channel_name,
                    "inline": "True"
                },
                {
                    "name": "Message ID",
                    "value": message.id,
                    "inline": "True"
                },
                {
                    "name": "Created At (UTC)",
                    "value": message.created_at,
                    "inline": "True"
                },
                {
                    "name": "Edited At (UTC)",
                    "value": message_now.edited_at,
                    "inline": "True"
                },
                {
                    "name": "Attachments",
                    "value": " | ".join([f"**{a.filename}**: [Link]({a.url})" for a in message.attachments]) if len(message.attachments) > 0 else "None",
                    "inline": "False"
                },
                {
                    "name": "Past Content",
                    "value": message.content[:1024] if len(message.content) > 0 else "None",
                    "inline": "False"
                },
                {
                    "name": "New Content",
                    "value": message_now.content[:1024] if len(message_now.content) > 0 else "None",
                    "inline": "False"
                },
                {
                    "name": "Embed",
                    "value": "\n".join([str(e.to_dict()) for e in message.embeds]) if len(message.embeds) > 0 else "None",
                    "inline": "False"
                }
            ]
        )
        await edited_channel.send(embed=embed)
    except Exception as e:
        message_now = await channel.fetch_message(payload.message_id)
        embed = assemble_embed(
            title=":pencil: Edited Message",
            fields=[
                {
                    "name": "Channel",
                    "value": bot.get_channel(payload.channel_id).mention,
                    "inline": "True"
                },
                {
                    "name": "Message ID",
                    "value": payload.message_id,
                    "inline": "True"
                },
                {
                    "name": "Author",
                    "value": message_now.author,
                    "inline": "True"
                },
                {
                    "name": "Created At (UTC)",
                    "value": message_now.created_at,
                    "inline": "True"
                },
                {
                    "name": "Edited At (UTC)",
                    "value": message_now.edited_at,
                    "inline": "True"
                },
                {
                    "name": "New Content",
                    "value": message_now.content[:1024] if len(message_now.content) > 0 else "None",
                    "inline": "False"
                },
                {
                    "name": "Raw Payload",
                    "value": str(payload.data)[:1024] if len(payload.data) > 0 else "None",
                    "inline": "False"
                },
                {
                    "name": "Current Attachments",
                    "value": " | ".join([f"**{a.filename}**: [Link]({a.url})" for a in message_now.attachments]) if len(message_now.attachments) > 0 else "None",
                    "inline": "False"
                },
                {
                    "name": "Current Embed",
                    "value": "\n".join([str(e.to_dict()) for e in message_now.embeds])[:1024] if len(message_now.embeds) > 0 else "None",
                    "inline": "False"
                }
            ]
        )
        await edited_channel.send(embed=embed)

@bot.event
async def on_raw_message_delete(payload):
    channel = bot.get_channel(payload.channel_id)
    guild = bot.get_guild(SERVER_ID) if channel.type == discord.ChannelType.private else channel.guild
    if channel.type != discord.ChannelType.private and channel.name in [CHANNEL_REPORTS, CHANNEL_DELETEDM]:
        print("Ignoring deletion event because of the channel it's from.")
        return
    deleted_channel = discord.utils.get(guild.text_channels, name=CHANNEL_DELETEDM)
    try:
        message = payload.cached_message
        channel_name = f"{message.author.mention}'s DM" if channel.type == discord.ChannelType.private else message.channel.mention
        embed = assemble_embed(
            title=":fire: Deleted Message",
            fields=[
                {
                    "name": "Author",
                    "value": message.author,
                    "inline": "True"
                },
                {
                    "name": "Channel",
                    "value": channel_name,
                    "inline": "True"
                },
                {
                    "name": "Message ID",
                    "value": message.id,
                    "inline": "True"
                },
                {
                    "name": "Created At (UTC)",
                    "value": message.created_at,
                    "inline": "True"
                },
                {
                    "name": "Edited At (UTC)",
                    "value": message.edited_at,
                    "inline": "True"
                },
                {
                    "name": "Attachments",
                    "value": " | ".join([f"**{a.filename}**: [Link]({a.url})" for a in message.attachments]) if len(message.attachments) > 0 else "None",
                    "inline": "False"
                },
                {
                    "name": "Content",
                    "value": str(message.content)[:1024] if len(message.content) > 0 else "None",
                    "inline": "False"
                },
                {
                    "name": "Embed",
                    "value": "\n".join([str(e.to_dict()) for e in message.embeds])[:1024] if len(message.embeds) > 0 else "None",
                    "inline": "False"
                }
            ]
        )
        await deleted_channel.send(embed=embed)
    except Exception as e:
        print(e)
        embed = assemble_embed(
            title=":fire: Deleted Message",
            fields=[
                {
                    "name": "Channel",
                    "value": bot.get_channel(payload.channel_id).mention,
                    "inline": "True"
                },
                {
                    "name": "Message ID",
                    "value": payload.message_id,
                    "inline": "True"
                }
            ]
        )
        await deleted_channel.send(embed=embed)

@bot.event
async def on_command_error(ctx, error):
    print("Command Error:")
    print(error)

    # If a cog has a separate error handler, don't also run the global error handler
    if (ctx.command.has_error_handler() or ctx.cog.has_error_handler()) and ctx.__slots__ == True:
        return

    # Argument parsing errors
    if isinstance(error, discord.ext.commands.UnexpectedQuoteError) or isinstance(error, discord.ext.commands.InvalidEndOfQuotedStringError):
        return await ctx.send("Sorry, it appears that your quotation marks are misaligned, and I can't read your query.")
    if isinstance(error, discord.ext.commands.ExpectedClosingQuoteError):
        return await ctx.send("Oh. I was expecting you were going to close out your command with a quote somewhere, but never found it!")

    # User input errors
    if isinstance(error, discord.ext.commands.MissingRequiredArgument):
        return await ctx.send("Oops, you are missing a required argument in the command.")
    if isinstance(error, discord.ext.commands.ArgumentParsingError):
        return await ctx.send("Sorry, I had trouble parsing one of your arguments.")
    if isinstance(error, discord.ext.commands.TooManyArguments):
        return await ctx.send("Woahhh!! Too many arguments for this command!")
    if isinstance(error, discord.ext.commands.BadArgument) or isinstance(error, discord.ext.commands.BadUnionArgument):
        return await ctx.send("Sorry, I'm having trouble reading one of the arguments you just used. Try again!")

    # Check failure errors
    if isinstance(error, discord.ext.commands.CheckAnyFailure):
        return await ctx.send("It looks like you aren't able to run this command, sorry.")
    if isinstance(error, discord.ext.commands.PrivateMessageOnly):
        return await ctx.send("Pssttt. You're going to have to DM me to run this command!")
    if isinstance(error, discord.ext.commands.NoPrivateMessage):
        return await ctx.send("Ope. You can't run this command in the DM's!")
    if isinstance(error, discord.ext.commands.NotOwner):
        return await ctx.send("Oof. You have to be the bot's master to run that command!")
    if isinstance(error, discord.ext.commands.MissingPermissions) or isinstance(error, discord.ext.commands.BotMissingPermissions):
        return await ctx.send("Er, you don't have the permissions to run this command.")
    if isinstance(error, discord.ext.commands.MissingRole) or isinstance(error, discord.ext.commands.BotMissingRole):
        return await ctx.send("Oh no... you don't have the required role to run this command.")
    if isinstance(error, discord.ext.commands.MissingAnyRole) or isinstance(error, discord.ext.commands.BotMissingAnyRole):
        return await ctx.send("Oh no... you don't have the required role to run this command.")
    if isinstance(error, discord.ext.commands.NSFWChannelRequired):
        return await ctx.send("Uh... this channel can only be run in a NSFW channel... sorry to disappoint.")

    # Command errors
    if isinstance(error, CommandNotAllowedInChannel):
        return await ctx.send(f"You are not allowed to use this command in {error.channel.mention}.")
    if isinstance(error, discord.ext.commands.ConversionError):
        return await ctx.send("Oops, there was a bot error here, sorry about that.")
    if isinstance(error, discord.ext.commands.UserInputError):
        return await ctx.send("Hmmm... I'm having trouble reading what you're trying to tell me.")
    if isinstance(error, discord.ext.commands.CommandNotFound):
        return await ctx.send("Sorry, I couldn't find that command.")
    if isinstance(error, discord.ext.commands.CheckFailure):
        return await ctx.send("Sorry, but I don't think you can run that command.")
    if isinstance(error, discord.ext.commands.DisabledCommand):
        return await ctx.send("Sorry, but this command is disabled.")
    if isinstance(error, discord.ext.commands.CommandInvokeError):
        return await ctx.send("Sorry, but an error incurred when the command was invoked.")
    if isinstance(error, discord.ext.commands.CommandOnCooldown):
        return await ctx.send("Slow down buster! This command's on cooldown.")
    if isinstance(error, discord.ext.commands.MaxConcurrencyReached):
        return await ctx.send("Uh oh. This command has reached MAXIMUM CONCURRENCY. *lightning flash*. Try again later.")

    # Extension errors (not doing specifics)
    if isinstance(error, discord.ext.commands.ExtensionError):
        return await ctx.send("Oh no. There's an extension error. Please ping a developer about this one.")

    # Client exception errors (not doing specifics)
    if isinstance(error, discord.ext.commands.CommandRegistrationError):
        return await ctx.send("Oh boy. Command registration error. Please ping a developer about this.")

    # Overall errors
    if isinstance(error, discord.ext.commands.CommandError):
        return await ctx.send("Oops, there was a command error. Try again.")
    return

@bot.event
async def on_error(event, *args, **kwargs):
    print("Code Error:")
    print(traceback.format_exc())

# The cogs here will be executed in set order everytime
# Therefore on_message events can be rearraged to produce different outputs
bot.load_extension("src.discord.censor")
bot.load_extension("src.discord.ping")
bot.load_extension("src.discord.staffcommands")
bot.load_extension("src.discord.embed")
bot.load_extension("src.discord.membercommands")
bot.load_extension("src.discord.devtools")
bot.load_extension("src.discord.funcommands")
bot.load_extension("src.discord.tasks")
bot.load_extension("src.discord.spam")

if dev_mode:
    bot.run(DEV_TOKEN)
else:
    bot.run(TOKEN)
