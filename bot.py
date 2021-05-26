import discord
import os
import traceback
import asyncio
# import requests
import re
import json
import random
# import math
import time
import datetime
import dateparser
import pytz
import time as time_module
# import wikipedia as wikip
import matplotlib.pyplot as plt
import numpy as np
# from aioify import aioify

from discord import channel
from discord.ext import commands, tasks

from src.sheets.events import get_events
# from src.sheets.tournaments import get_tournament_channels
from src.sheets.censor import get_censor
from src.sheets.sheets import send_variables, get_variables, get_tags
from src.forums.forums import open_browser
from src.wiki.stylist import prettify_templates
# from src.wiki.tournaments import get_tournament_list
from src.wiki.wiki import get_page_tables # implement_command,
from src.wiki.scilympiad import get_points
# from src.wiki.mosteditstable import run_table
# from info import get_about
# from doggo import get_doggo, get_shiba
# from bear import get_bear_message
from embed import assemble_embed
from commands import get_list, get_help # get_quick_list,
from commanderrors import CommandNotAllowedInChannel, SelfMuteCommandStaffInvoke

from tournaments import update_tournament_list

# load_dotenv()
# TOKEN = os.getenv('DISCORD_TOKEN')
# DEV_TOKEN = os.getenv('DISCORD_DEV_TOKEN')
# dev_mode = os.getenv('DEV_MODE') == "TRUE"

##############
# SERVER VARIABLES
##############

from src.discord.utils import *

from src.discord.globals import *

##############
# DEV MODE CONFIG
##############

intents = discord.Intents.default()
intents.members = True

# if dev_mode:
#     BOT_PREFIX = "?"
#     SERVER_ID = int(os.getenv('DEV_SERVER_ID'))
# else:
#     BOT_PREFIX = "!"
#     SERVER_ID = 698306997287780363

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
# aiowikip = aioify(obj=wikip)

##############
# FUNCTIONS
##############
    
@bot.event
async def on_ready():
    """Called when the bot is enabled and ready to be run."""
    print(f'{bot.user} has connected!')
    try:
        await pull_prev_info()
    except Exception as e:
        print("Error in starting function with pulling previous information:")
        print(e)

    try:
        await update_tournament_list(bot)
    except Exception as e:
        print("Error in starting function with updating tournament list:")
        print(e)

    try:
        refresh_sheet.start()
    except Exception as e:
        print("Error in starting function with updating tournament list:")
        print(e)

    post_something.start()
    cron.start()
    go_stylist.start()
    manage_welcome.start()
    store_variables.start()
    change_bot_status.start()
    update_member_count.start()
    
@tasks.loop(minutes=5)
async def update_member_count():
    """Updates the member count shown on hidden VC"""
    guild = bot.get_guild(SERVER_ID)
    channel_prefix = "Members"
    vc = discord.utils.find(lambda c: channel_prefix in c.name, guild.voice_channels)
    mem_count = guild.member_count
    joined_today = len([m for m in guild.members if m.joined_at.date() == datetime.datetime.today().date()])
    left_channel = discord.utils.get(guild.text_channels, name=CHANNEL_LEAVE)
    left_messages = await left_channel.history(limit=200).flatten()
    left_today = len([m for m in left_messages if m.created_at.date() == datetime.datetime.today().date()])
    await vc.edit(name=f"{mem_count} Members (+{joined_today}/-{left_today})")
    print("Refreshed member count.")

@tasks.loop(seconds=30.0)
async def refresh_sheet():
    """Refreshes the censor list and stores variable backups."""
    try:
        await refresh_algorithm()
    except Exception as e:
        print("Error when completing the refresh algorithm when refreshing the sheet:")
        print(e)

    try:
        await prepare_for_sending()
    except Exception as e:
        print("Error when sending variables to log sheet:")
        print(e)

    print("Attempted to refresh/store data from/to sheet.")

@tasks.loop(hours=10)
async def store_variables():
    await prepare_for_sending("store")

@tasks.loop(hours=24)
async def go_stylist():
    await prettify_templates()

@tasks.loop(minutes=10)
async def manage_welcome():
    server = bot.get_guild(SERVER_ID)
    now = datetime.datetime.now()
    # Channel message deleting is currently disabled
    # if now.hour < ((0 - TZ_OFFSET) % 24) or now.hour > ((11 - TZ_OFFSET) % 24):
    #     print(f"Cleaning #{CHANNEL_WELCOME}.")
    #     # if between 12AM EST and 11AM EST do not do the following:
    #     channel = discord.utils.get(server.text_channels, name=CHANNEL_WELCOME)
    #     async for message in channel.history(limit=None):
    #         # if message is over 3 hours old
    #         author = message.author
    #         user_no_delete = await is_launcher_no_ctx(message.author)
    #         num_of_roles = len(author.roles)
    #         if num_of_roles > 4 and (now - author.joined_at).seconds // 60 > 1 and not user_no_delete:
    #             await _confirm([author])
    #         if (now - message.created_at).seconds // 3600 > 3 and not message.pinned:
    #             # delete it
    #             await message.delete()
    # else:
    #     print(f"Skipping #{CHANNEL_WELCOME} clean because it is outside suitable time ranges.")

@tasks.loop(minutes=1)
async def cron():
    print("Executed cron.")
    global CRON_LIST
    for c in CRON_LIST:
        date = c['date']
        if datetime.datetime.now() > date:
            # The date has passed, now do
            CRON_LIST.remove(c)
            await handle_cron(c['do'])

async def handle_cron(string):
    try:
        if string.find("unban") != -1:
            iden = int(string.split(" ")[1])
            server = bot.get_guild(SERVER_ID)
            member = await bot.fetch_user(int(iden))
            await server.unban(member)
            print(f"Unbanned user ID: {iden}")
        elif string.find("unmute") != -1:
            iden = int(string.split(" ")[1])
            server = bot.get_guild(SERVER_ID)
            member = server.get_member(int(iden))
            role = discord.utils.get(server.roles, name=ROLE_MUTED)
            self_role = discord.utils.get(server.roles, name=ROLE_SELFMUTE)
            await member.remove_roles(role, self_role)
            print(f"Unmuted user ID: {iden}")
        elif string.find("unstealfishban") != -1:
            iden = int(string.split(" ")[1])
            STEALFISH_BAN.remove(iden)
            print(f"Un-stealfished user ID: {iden}")
        else:
            print("ERROR:")
            await auto_report(bot, "Error with a cron task", "red", f"Error: `{string}`")
    except Exception as e:
        await auto_report(bot, "Error with a cron task", "red", f"Error: `{e}`\nOriginal task: `{string}`")

@tasks.loop(hours=1)
async def change_bot_status():
    statuses = [
        {"type": "playing", "message": "Game On"},
        {"type": "listening", "message": "my SoM instrument"},
        {"type": "playing", "message": "with Pi-Bot Beta"},
        {"type": "playing", "message": "with my gravity vehicle"},
        {"type": "watching", "message": "the WS trials"},
        {"type": "watching", "message": "birbs"},
        {"type": "watching", "message": "2018 Nationals again"},
        {"type": "watching", "message": "the sparkly stars"},
        {"type": "watching", "message": "over the week"},
        {"type": "watching", "message": "for tourney results"},
        {"type": "listening", "message": "birb sounds"},
        {"type": "playing", "message": "with proteins"},
        {"type": "playing", "message": "with my detector"},
        {"type": "playing", "message": "Minecraft"},
        {"type": "playing", "message": "with circuits"},
        {"type": "watching", "message": "my PPP fall"},
        {"type": "playing", "message": "a major scale"},
        {"type": "listening", "message": "clinking medals"},
        {"type": "watching", "message": "the world learn"},
        {"type": "watching", "message": "SciOly grow"},
        {"type": "watching", "message": "tutorials"},
        {"type": "playing", "message": "with wiki templates"},
        {"type": "playing", "message": "the flute"},
        {"type": "watching", "message": "bear eat users"},
        {"type": "watching", "message": "xkcd"},
        {"type": "playing", "message": "with wiki templates"},
        {"type": "watching", "message": "Jmol tutorials"},
    ]
    botStatus = random.choice(statuses)
    if botStatus["type"] == "playing":
        await bot.change_presence(activity=discord.Game(name=botStatus["message"]))
    elif botStatus["type"] == "listening":
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=botStatus["message"]))
    elif botStatus["type"] == "watching":
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=botStatus["message"]))
    print("Changed the bot's status.")

@tasks.loop(hours=28)
async def post_something():
    global can_post
    """Allows Pi-Bot to post markov-generated statements to the forums."""
    if can_post:
        print("Attempting to post something.")
        await open_browser()
    else:
        can_post = True

async def refresh_algorithm():
    """Pulls data from the administrative sheet."""
    try:
        global CENSORED_WORDS
        global CENSORED_EMOJIS
        censor = await get_censor()
        CENSORED_WORDS = censor[0]
        CENSORED_EMOJIS = censor[1]
    except Exception as e:
        print("Could not refresh censor in refresh_algorithm:")
        print(e)

    try:
        global EVENT_INFO
        EVENT_INFO = await get_events()
    except Exception as e:
        print("Could not refresh event list in refresh_algorithm:")
        print(e)

    try:
        global TAGS
        TAGS = await get_tags()
    except Exception as e:
        print("Could not refresh tags in refresh_algorithm:")
        print(e)
    
    print("Refreshed data from sheet.")
    return True

async def prepare_for_sending(type="variable"):
    """Sends local variables to the administrative sheet as a backup."""
    r1 = json.dumps(REPORT_IDS)
    r2 = json.dumps(PING_INFO)
    r3 = json.dumps(TOURNEY_REPORT_IDS)
    r4 = json.dumps(COACH_REPORT_IDS)
    r5 = json.dumps(CRON_LIST, default = datetime_converter)
    r6 = json.dumps(REQUESTED_TOURNAMENTS)
    await send_variables([[r1], [r2], [r3], [r4], [r5], [r6]], type)
    print("Stored variables in sheet.")

def datetime_converter(o):
    if isinstance(o, datetime.datetime):
        return o.__str__()

async def pull_prev_info():
    data = await get_variables()
    global PING_INFO
    global REPORT_IDS
    global TOURNEY_REPORT_IDS
    global COACH_REPORT_IDS
    global CRON_LIST
    global REQUESTED_TOURNAMENTS
    REPORT_IDS = data[0][0]
    PING_INFO = data[1][0]
    TOURNEY_REPORT_IDS = data[2][0]
    COACH_REPORT_IDS = data[3][0]
    cron = data[4][0]
    for c in cron:
        try:
            c['date'] = datetime.datetime.strptime(c['date'], "%Y-%m-%d %H:%M:%S.%f")
        except Exception as e:
            print("ERROR WITH CRON TASK: ", e)
    CRON_LIST = cron
    REQUESTED_TOURNAMENTS = data[5][0]
    print("Fetched previous variables.")

# @bot.command(aliases=["tc", "tourney", "tournaments"])
# async def tournament(ctx, *args):
#     member = ctx.message.author
#     new_args = list(args)
#     ignore_terms = ["invitational", "invy", "tournament", "regional", "invite"]
#     for term in ignore_terms:
#         if term in new_args:
#             new_args.remove(term)
#             await ctx.send(f"Ignoring `{term}` because it is too broad of a term. *(If you need help with this command, please type `!help tournament`)*")
#     if len(args) == 0:
#         return await ctx.send("Please specify the tournaments you would like to be added/removed from!")
#     for arg in new_args:
#         # Stop users from possibly adding the channel hash in front of arg
#         arg = arg.replace("#", "")
#         arg = arg.lower()
#         found = False
#         if arg == "all":
#             role = discord.utils.get(member.guild.roles, name=ROLE_AT)
#             if role in member.roles:
#                 await ctx.send(f"Removed your `All Tournaments` role.")
#                 await member.remove_roles(role)
#             else:
#                 await ctx.send(f"Added your `All Tournaments` role.")
#                 await member.add_roles(role)
#             continue
#         for t in TOURNAMENT_INFO:
#             if arg == t[1]:
#                 found = True
#                 role = discord.utils.get(member.guild.roles, name=t[0])
#                 if role == None:
#                     return await ctx.send(f"Apologies! The `{t[0]}` channel is currently not available.")
#                 if role in member.roles:
#                     await ctx.send(f"Removed you from the `{t[0]}` channel.")
#                     await member.remove_roles(role)
#                 else:
#                     await ctx.send(f"Added you to the `{t[0]}` channel.")
#                     await member.add_roles(role)
#                 break
#         if not found:
#             uid = member.id
#             found2 = False
#             votes = 1
#             for t in REQUESTED_TOURNAMENTS:
#                 if arg == t['iden']:
#                     found2 = True
#                     if uid in t['users']:
#                         return await ctx.send("Sorry, but you can only vote once for a specific tournament!")
#                     t['count'] += 1
#                     t['users'].append(uid)
#                     votes = t['count']
#                     break
#             if not found2:
#                 await auto_report(bot, "New Tournament Channel Requested", "orange", f"User ID {uid} requested tournament channel `#{arg}`.\n\nTo add this channel to the voting list for the first time, use `!tla {arg} {uid}`.\nIf the channel has already been requested in the list and this was a user mistake, use `!tla [actual name] {uid}`.")
#                 return await ctx.send(f"Made request for a `#{arg}` channel. Please note your submission may not instantly appear.")
#             await ctx.send(f"Added a vote for `{arg}`. There " + ("are" if votes != 1 else "is") + f" now `{votes}` " + (f"votes" if votes != 1 else f"vote") + " for this channel.")
#             await update_tournament_list()

@bot.command()
async def enable_mem(ctx):
    bot.add_cog(MemberCommands(bot))
    
@bot.command()
async def disable_mem(ctx):
    print("removing cog")
    bot.remove_cog('MemberCommands')
    print("removed")
    print(bot.cogs)

# cant fully test this command due to lack of access
@bot.command()
@commands.check(is_staff)
async def tla(ctx, iden, uid):
    global REQUESTED_TOURNAMENTS
    for t in REQUESTED_TOURNAMENTS:
        if t['iden'] == iden:
            t['count'] += 1
            await ctx.send(f"Added a vote for {iden} from {uid}. Now has `{t['count']}` votes.")
            return await update_tournament_list(ctx.bot)
    REQUESTED_TOURNAMENTS.append({'iden': iden, 'count': 1, 'users': [uid]})
    await update_tournament_list(ctx.bot)
    return await ctx.send(f"Added a vote for {iden} from {uid}. Now has `1` vote.")

@bot.command()
@commands.check(is_staff)
async def tlr(ctx, iden):
    global REQUESTED_TOURNAMENTS
    for t in REQUESTED_TOURNAMENTS:
        if t['iden'] == iden:
            REQUESTED_TOURNAMENTS.remove(t)
    await update_tournament_list(ctx.bot)
    return await ctx.send(f"Removed `#{iden}` from the tournament list.")

@bot.command()
@commands.check(is_staff)
async def refresh(ctx):
    """Refreshes data from the sheet."""
    await update_tournament_list(ctx.bot)
    res = await refresh_algorithm()
    if res == True:
        await ctx.send("Successfully refreshed data from sheet.")
    else:
        await ctx.send(":warning: Unsuccessfully refreshed data from sheet.")

@bot.command(aliases=["tags", "t"])
async def tag(ctx, name):
    member = ctx.message.author
    if len(TAGS) == 0:
        return await ctx.send("Apologies, tags do not appear to be working at the moment. Please try again in one minute.")
    staff = await is_staff(ctx)
    lh_role = discord.utils.get(member.guild.roles, name=ROLE_LH)
    member_role = discord.utils.get(member.guild.roles, name=ROLE_MR)
    for t in TAGS:
        if t['name'] == name:
            if staff or (t['launch_helpers'] and lh_role in member.roles) or (t['members'] and member_role in member.roles):
                await ctx.message.delete()
                return await ctx.send(t['text'])
            else:
                return await ctx.send("Unfortunately, you do not have the permissions for this tag.")
    return await ctx.send("Tag not found.")

# # Meant for Pi-Bot only
# async def auto_report(reason, color, message):
#     """Allows Pi-Bot to generate a report by himself."""
#     server = bot.get_guild(SERVER_ID)
#     reports_channel = discord.utils.get(server.text_channels, name=CHANNEL_REPORTS)
#     embed = assemble_embed(
#         title=f"{reason} (message from Pi-Bot)",
#         webcolor=color,
#         fields = [{
#             "name": "Message",
#             "value": message,
#             "inline": False
#         }]
#     )
#     message = await reports_channel.send(embed=embed)
#     REPORT_IDS.append(message.id)
#     await message.add_reaction("\U00002705")
#     await message.add_reaction("\U0000274C")

@bot.command()
async def graphpage(ctx, title, temp_format, table_index, div, place_col=0):
    temp = temp_format.lower() in ["y", "yes", "true"]
    await ctx.send(
        "*Inputs read:*\n" +
        f"Page title: `{title}`\n" +
        f"Template: `{temp}`\n" +
        f"Table index (staring at 0): `{table_index}`\n" +
        f"Division: `{div}`\n" +
        (f"Column with point values: `{place_col}`" if not temp else "")
    )
    points = []
    table_index = int(table_index)
    place_col = int(place_col)
    if temp:
        template = await get_page_tables(title, True)
        template = [t for t in template if t.normal_name() == "State results box"]
        template = template[table_index]
        ordinal = lambda n: "%d%s" % (n,"tsnrhtdd"[(n//10%10!=1)*(n%10<4)*n%10::4]) # Thanks https://codegolf.stackexchange.com/questions/4707/outputting-ordinal-numbers-1st-2nd-3rd#answer-4712
        for i in range(100):
            if template.has_arg(ordinal(i) + "_points"):
                points.append(template.get_arg(ordinal(i) + "_points").value.replace("\n", ""))
    else:
        tables = await get_page_tables(title, False)
        tables = tables[table_index]
        data = tables.data()
        points = [r[place_col] for r in data]
        del points[0]
    points = [int(p) for p in points]
    await _graph(points, title + " - Division " + div, title + "Div" + div + ".svg")
    with open(title + "Div" + div + ".svg") as f:
        pic = discord.File(f)
        await ctx.send(file=pic)
    return await ctx.send("Attempted to graph.")

@bot.command()
async def graphscilympiad(ctx, url, title):
    points = await get_points(url)
    await _graph(points, title, "graph1.svg")
    with open("graph1.svg") as f:
        pic = discord.File(f)
        await ctx.send(file=pic)
    return await ctx.send("Attempted to graph.")

async def _graph(points, graph_title, title):
    plt.plot(range(1, len(points) + 1), points, marker='o', color='#2E66B6')
    z = np.polyfit(range(1, len(points) + 1), points, 1)
    p = np.poly1d(z)
    plt.plot(range(1, len(points) + 1), p(range(1, len(points) + 1)), "--", color='#CCCCCC')
    plt.xlabel("Place")
    plt.ylabel("Points")
    plt.title(graph_title)
    plt.savefig(title)
    plt.close()
    await asyncio.sleep(2)

@bot.command(aliases=["event"])
async def events(ctx, *args):
    """Adds or removes event roles from a user."""
    if len(args) < 1:
        return await ctx.send("You need to specify at least one event to add/remove!")
    elif len(args) > 10:
        return await ctx.send("Woah, that's a lot for me to handle at once. Please separate your requests over multiple commands.")
    member = ctx.message.author
    new_args = [str(arg).lower() for arg in args]

    # Fix commas as possible separator
    if len(new_args) == 1:
        new_args = new_args[0].split(",")
    new_args = [re.sub("[;,]", "", arg) for arg in new_args]

    event_info = EVENT_INFO
    event_names = []
    removed_roles = []
    added_roles = []
    could_not_handle = []
    multi_word_events = []

    if type(EVENT_INFO) == int:
        # When the bot starts up, EVENT_INFO is initialized to 0 before receiving the data from the sheet a few seconds later. This lets the user know this.
        return await ctx.send("Apologies... refreshing data currently. Try again in a few seconds.")

    for i in range(7, 1, -1):
        # Supports adding 7-word to 2-word long events
        multi_word_events += [e['eventName'] for e in event_info if len(e['eventName'].split(" ")) == i]
        for event in multi_word_events:
            words = event.split(" ")
            all_here = 0
            all_here = sum(1 for word in words if word.lower() in new_args)
            if all_here == i:
                # Word is in args
                role = discord.utils.get(member.guild.roles, name=event)
                if role in member.roles:
                    await member.remove_roles(role)
                    removed_roles.append(event)
                else:
                    await member.add_roles(role)
                    added_roles.append(event)
                for word in words:
                    new_args.remove(word.lower())
    for arg in new_args:
        found_event = False
        for event in event_info:
            aliases = [abbr.lower() for abbr in event['event_abbreviations']]
            if arg.lower() in aliases or arg.lower() == event['eventName'].lower():
                event_names.append(event['eventName'])
                found_event = True
                break
        if not found_event:
            could_not_handle.append(arg)
    for event in event_names:
        role = discord.utils.get(member.guild.roles, name=event)
        if role in member.roles:
            await member.remove_roles(role)
            removed_roles.append(event)
        else:
            await member.add_roles(role)
            added_roles.append(event)
    if len(added_roles) > 0 and len(removed_roles) == 0:
        event_res = "Added events " + (' '.join([f'`{arg}`' for arg in added_roles])) + ((", and could not handle: " + " ".join([f"`{arg}`" for arg in could_not_handle])) if len(could_not_handle) else "") + "."
    elif len(removed_roles) > 0 and len(added_roles) == 0:
        event_res = "Removed events " + (' '.join([f'`{arg}`' for arg in removed_roles])) + ((", and could not handle: " + " ".join([f"`{arg}`" for arg in could_not_handle])) if len(could_not_handle) else "") + "."
    else:
        event_res = "Added events " + (' '.join([f'`{arg}`' for arg in added_roles])) + ", " + ("and " if not len(could_not_handle) else "") + "removed events " + (' '.join([f'`{arg}`' for arg in removed_roles])) + ((", and could not handle: " + " ".join([f"`{arg}`" for arg in could_not_handle])) if len(could_not_handle) else "") + "."
    await ctx.send(event_res)

async def get_words():
    """Gets the censor list"""
    global CENSORED_WORDS
    CENSORED_WORDS = get_censor()

@bot.command(aliases=["man"])
async def help(ctx, command:str=None):
    """Allows a user to request help for a command."""
    if command == None:
        embed = assemble_embed(
            title="Looking for help?",
            desc=("Hey there, I'm a resident bot of Scioly.org!\n\n" +
            "On Discord, you can send me commands using `!` before the command name, and I will process it to help you! " +
            "For example, `!states`, `!events`, and `!fish` are all valid commands that can be used!\n\n" +
            "If you want to see some commands that you can use on me, just type `!list`! " +
            "If you need more help, please feel free to reach out to a staff member!")
        )
        return await ctx.send(embed=embed)
    hlp = await get_help(ctx, command)
    await ctx.send(embed=hlp)

@bot.command()
@commands.check(is_launcher)
async def confirm(ctx, *args: discord.Member):
    """Allows a staff member to confirm a user."""
    await _confirm(args)

async def _confirm(members):
    server = bot.get_guild(SERVER_ID)
    channel = discord.utils.get(server.text_channels, name=CHANNEL_WELCOME)
    for member in members:
        role1 = discord.utils.get(member.guild.roles, name=ROLE_UC)
        role2 = discord.utils.get(member.guild.roles, name=ROLE_MR)
        await member.remove_roles(role1)
        await member.add_roles(role2)
        message = await channel.send(f"Alrighty, confirmed {member.mention}. Welcome to the server! :tada:")
        await asyncio.sleep(3)
        await message.delete()
        before_message = None
        f = 0
        async for message in channel.history(oldest_first=True):
            # Delete any messages sent by Pi-Bot where message before is by member
            if f > 0:
                if message.author.id in PI_BOT_IDS and before_message.author == member and len(message.embeds) == 0:
                    await message.delete()

                # Delete any messages by user
                if message.author == member and len(message.embeds) == 0:
                    await message.delete()

                if member in message.mentions:
                    await message.delete()

            before_message = message
            f += 1

@bot.command()
async def nuke(ctx, count):
    """Nukes (deletes) a specified amount of messages."""
    global STOPNUKE
    launcher = await is_launcher(ctx)
    staff = await is_staff(ctx)
    if not (staff or (launcher and ctx.message.channel.name == "welcome")):
        return await ctx.send("APOLOGIES. INSUFFICIENT RANK FOR NUKE.")
    if STOPNUKE:
        return await ctx.send("TRANSMISSION FAILED. ALL NUKES ARE CURRENTLY PAUSED. TRY AGAIN LATER.")
    if int(count) > 100:
        return await ctx.send("Chill. No more than deleting 100 messages at a time.")
    channel = ctx.message.channel
    if int(count) < 0:
        history = await channel.history(limit=105).flatten()
        message_count = len(history)
        print(message_count)
        if message_count > 100:
            count = 100
        else:
            count = message_count + int(count) - 1
        if count <= 0:
            return await ctx.send("Sorry, you can not delete a negative amount of messages. This is likely because you are asking to save more messages than there are in the channel.")
    await ctx.send("=====\nINCOMING TRANSMISSION.\n=====")
    await ctx.send("PREPARE FOR IMPACT.")
    for i in range(10, 0, -1):
        await ctx.send(f"NUKING {count} MESSAGES IN {i}... TYPE `!stopnuke` AT ANY TIME TO STOP ALL TRANSMISSION.")
        await asyncio.sleep(1)
        if STOPNUKE:
            return await ctx.send("A COMMANDER HAS PAUSED ALL NUKES FOR 20 SECONDS. NUKE CANCELLED.")
    if not STOPNUKE:
        async for m in channel.history(limit=(int(count) + 13)):
            if not m.pinned and not STOPNUKE:
                await m.delete()
        msg = await ctx.send("https://media.giphy.com/media/XUFPGrX5Zis6Y/giphy.gif")
        await asyncio.sleep(5)
        await msg.delete()

@bot.command()
async def stopnuke(ctx):
    global STOPNUKE
    launcher = await is_launcher(ctx)
    staff = await is_staff(ctx)
    if not (staff or (launcher and ctx.message.channel.name == CHANNEL_WELCOME)):
        return await ctx.send("APOLOGIES. INSUFFICIENT RANK FOR STOPPING NUKE.")
    STOPNUKE = True
    await ctx.send("TRANSMISSION RECEIVED. STOPPED ALL CURRENT NUKES.")
    await asyncio.sleep(15)
    for i in range(5, 0, -1):
        await ctx.send(f"NUKING WILL BE ALLOWED IN {i}. BE WARNED COMMANDER.")
        await asyncio.sleep(1)
    STOPNUKE = False

@bot.event
async def on_message_edit(before, after):
    if (datetime.datetime.now() - after.created_at).total_seconds() < 2: 
        # no need to log edit events for messages just created
        return
    print('Message from {0.author} edited to: {0.content}, from: {1.content}'.format(after, before))
    for word in CENSORED_WORDS:
        if len(re.findall(fr"\b({word})\b", after.content, re.I)):
            print(f"Censoring message by {after.author} because of the word: `{word}`")
            await after.delete()
    for word in CENSORED_EMOJIS:
        if len(re.findall(fr"{word}", after.content)):
            print(f"Censoring message by {after.author} because of the emoji: `{word}`")
            await after.delete()
    if not any(ending for ending in DISCORD_INVITE_ENDINGS if ending in after.content) and (len(re.findall("discord.gg", after.content, re.I)) > 0 or len(re.findall("discord.com/invite", after.content, re.I)) > 0):
        print(f"Censoring message by {after.author} because of the it mentioned a Discord invite link.")
        await after.delete()

async def send_to_dm_log(message):
    server = bot.get_guild(SERVER_ID)
    dmChannel = discord.utils.get(server.text_channels, name=CHANNEL_DMLOG)
    embed = assemble_embed(
        title=":speech_balloon: New DM",
        fields=[
            {
                    "name": "Author",
                    "value": message.author,
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
                    "name": "Attachments",
                    "value": " | ".join([f"**{a.filename}**: [Link]({a.url})" for a in message.attachments]) if len(message.attachments) > 0 else "None",
                    "inline": "False"
                },
                {
                    "name": "Content",
                    "value": message.content if len(message.content) > 0 else "None",
                    "inline": "False"
                },
                {
                    "name": "Embed",
                    "value": "\n".join([str(e.to_dict()) for e in message.embeds]) if len(message.embeds) > 0 else "None",
                    "inline": "False"
                }
            ]
    )
    await dmChannel.send(embed=embed)

@bot.event
async def on_message(message):
    if message.author.id in PI_BOT_IDS: return
    
    # Log DMs (might put this into cog idk this just needs to run b4 the censor)
    if type(message.channel) == discord.DMChannel:
        await send_to_dm_log(message)
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
    global RECENT_MESSAGES
    caps = False
    u = sum(1 for c in message.content if c.isupper())
    l = sum(1 for c in message.content if c.islower())
    if u > (l + 3): caps = True
    RECENT_MESSAGES = [{"author": message.author.id,"content": message.content.lower(), "caps": caps}] + RECENT_MESSAGES[:20]
    # Spam checker
    if RECENT_MESSAGES.count({"author": message.author.id, "content": message.content.lower()}) >= 6:
        muted_role = discord.utils.get(message.author.guild.roles, name=ROLE_MUTED)
        parsed = dateparser.parse("1 hour", settings={"PREFER_DATES_FROM": "future"})
        CRON_LIST.append({"date": parsed, "do": f"unmute {message.author.id}"})
        await message.author.add_roles(muted_role)
        await message.channel.send(f"Successfully muted {message.author.mention} for 1 hour.")
        await auto_report(bot, "User was auto-muted (spam)", "red", f"A user ({str(message.author)}) was auto muted in {message.channel.mention} because of repeated spamming.")
    elif RECENT_MESSAGES.count({"author": message.author.id, "content": message.content.lower()}) >= 3:
        await message.channel.send(f"{message.author.mention}, please watch the spam. You will be muted if you do not stop.")
    # Caps checker
    elif sum(1 for m in RECENT_MESSAGES if m['author'] == message.author.id and m['caps']) > 8 and caps:
        muted_role = discord.utils.get(message.author.guild.roles, name=ROLE_MUTED)
        parsed = dateparser.parse("1 hour", settings={"PREFER_DATES_FROM": "future"})
        CRON_LIST.append({"date": parsed, "do": f"unmute {message.author.id}"})
        await message.author.add_roles(muted_role)
        await message.channel.send(f"Successfully muted {message.author.mention} for 1 hour.")
        await auto_report(bot, "User was auto-muted (caps)", "red", f"A user ({str(message.author)}) was auto muted in {message.channel.mention} because of repeated caps.")
    elif sum(1 for m in RECENT_MESSAGES if m['author'] == message.author.id and m['caps']) > 3 and caps:
        await message.channel.send(f"{message.author.mention}, please watch the caps, or else I will lay down the mute hammer!")
    
    if re.match(r'\s*[!"#$%&\'()*+,\-./:;<=>?@[\]^_`{|}~]', message.content.lstrip()[1:]) == None: # A bit messy, but gets it done
        await bot.process_commands(message)

@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id not in PI_BOT_IDS:
        guild = bot.get_guild(payload.guild_id)
        reports_channel = discord.utils.get(guild.text_channels, name=CHANNEL_REPORTS)
        if payload.emoji.name == EMOJI_UNSELFMUTE:
            guild = bot.get_guild(payload.guild_id)
            self_muted_role = discord.utils.get(guild.roles, name=ROLE_SELFMUTE)
            un_self_mute_channel = discord.utils.get(guild.text_channels, name=CHANNEL_UNSELFMUTE)
            member = payload.member
            message = await un_self_mute_channel.fetch_message(payload.message_id)
            if self_muted_role in member.roles:
                await member.remove_roles(self_muted_role)
            await message.clear_reactions()
            await message.add_reaction(EMOJI_FULL_UNSELFMUTE)
            for obj in CRON_LIST[:]:
                if obj['do'] == f'unmute {payload.user_id}':
                    CRON_LIST.remove(obj)
        if payload.message_id in REPORT_IDS:
            messageObj = await reports_channel.fetch_message(payload.message_id)
            if payload.emoji.name == "\U0000274C": # :x:
                print("Report cleared with no action.")
                await messageObj.delete()
            if payload.emoji.name == "\U00002705": # :white_check_mark:
                print("Report handled.")
                await messageObj.delete()
            return

@bot.event
async def on_reaction_add(reaction, user):
    msg = reaction.message
    if len(msg.embeds) > 0:
        if msg.embeds[0].title.startswith("List of Commands") and user.id not in PI_BOT_IDS:
            currentPage = int(re.findall(r'(\d+)(?=\/)', msg.embeds[0].title)[0])
            print(currentPage)
            ls = False
            if reaction.emoji == EMOJI_FAST_REVERSE:
                ls = await get_list(user, 1)
            elif reaction.emoji == EMOJI_LEFT_ARROW:
                ls = await get_list(user, currentPage - 1)
            elif reaction.emoji == EMOJI_RIGHT_ARROW:
                ls = await get_list(user, currentPage + 1)
            elif reaction.emoji == EMOJI_FAST_FORWARD:
                ls = await get_list(user, 100)
            if ls != False:
                await reaction.message.edit(embed=ls)
            await reaction.remove(user)

@bot.event
async def on_member_join(member):
    role = discord.utils.get(member.guild.roles, name=ROLE_UC)
    join_channel = discord.utils.get(member.guild.text_channels, name=CHANNEL_WELCOME)
    await member.add_roles(role)
    name = member.name
    for word in CENSORED_WORDS:
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
    for word in CENSORED_WORDS:
        if len(re.findall(fr"\b({word})\b", after.nick, re.I)):
            await auto_report(bot, "Innapropriate Username Detected", "red", f"A member ({str(after)}) has updated their nickname to **{after.nick}**, which the censor caught as innapropriate.")

@bot.event
async def on_user_update(before, after):
    for word in CENSORED_WORDS:
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
    if hasattr(ctx.command, 'on_error'):
        return
    
    # cog = ctx.cog
    # if cog:
    #     if cog._get_overridden_method(cog.cog_command_error) is not None:
    #         return
    # This causes errors when commands in an overridden error handler raise a common exception.
    
    # this is such a garbage way of doing it
    ignored = (SelfMuteCommandStaffInvoke,)
    if isinstance(error, ignored):
        return
    
    # print("Command Error:")
    # print(error)
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
bot.load_extension("src.discord.membercommands")
bot.load_extension("src.discord.devtools")
bot.load_extension("src.discord.funcommands")

if dev_mode:
    bot.run(DEV_TOKEN)
else:
    bot.run(TOKEN)