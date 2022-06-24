import discord
import os
import traceback
import asyncio
import requests
import re
import json
import random
import math
import time
import datetime
import dateparser
import pytz
import time as time_module
import wikipedia as wikip
import matplotlib.pyplot as plt
import numpy as np
from aioify import aioify
from dotenv import load_dotenv
from discord import channel
from discord.ext import commands, tasks

from src.sheets.events import get_events
from src.sheets.tournaments import get_tournament_channels
from src.sheets.censor import get_censor
from src.sheets.sheets import send_variables, get_variables, get_tags
from src.forums.forums import open_browser
from src.wiki.stylist import prettify_templates
from src.wiki.tournaments import get_tournament_list
from src.wiki.wiki import implement_command, get_page_tables
from src.wiki.schools import get_school_listing
from src.wiki.scilympiad import make_results_template, get_points
from src.wiki.mosteditstable import run_table
from info import get_about
from doggo import get_doggo, get_shiba
from bear import get_bear_message
from embed import assemble_embed
from commands import get_list, get_quick_list, get_help
from lists import get_state_list
import xkcd as xkcd_module # not to interfere with xkcd method
from commanderrors import CommandNotAllowedInChannel
from commanderrors import NoDMsAllowed

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
DEV_TOKEN = os.getenv('DISCORD_DEV_TOKEN')
dev_mode = os.getenv('DEV_MODE') == "TRUE"

##############
# SERVER VARIABLES
##############

# Roles
ROLE_WM = "Wiki/Gallery Moderator"
ROLE_GM = "Global Moderator"
ROLE_AD = "Administrator"
ROLE_VIP = "VIP"
ROLE_STAFF = "Staff"
ROLE_BT = "Bots"
ROLE_LH = "Launch Helper"
ROLE_AT = "All Tournaments"
ROLE_GAMES = "Games"
ROLE_MR = "Member"
ROLE_UC = "Unconfirmed"
ROLE_DIV_A = "Division A"
ROLE_DIV_B = "Division B"
ROLE_DIV_C = "Division C"
ROLE_EM = "Exalted Member"
ROLE_ALUMNI = "Alumni"
ROLE_MUTED = "Muted"
ROLE_PRONOUN_HE = "He / Him / His"
ROLE_PRONOUN_SHE = "She / Her / Hers"
ROLE_PRONOUN_THEY = "They / Them / Theirs"
ROLE_SELFMUTE = "Self Muted"
ROLE_QUARANTINE = "Quarantine"
ROLE_ALL_STATES = "All States"

# Channels
CHANNEL_TOURNAMENTS = "tournaments"
CHANNEL_BOTSPAM = "bot-spam"
CHANNEL_SUPPORT = "site-support"
CHANNEL_GAMES = "games"
CHANNEL_DMLOG = "dm-log"
CHANNEL_WELCOME = "welcome"
CHANNEL_LOUNGE = "lounge"
CHANNEL_LEAVE = "member-leave"
CHANNEL_DELETEDM = "deleted-messages"
CHANNEL_EDITEDM = "edited-messages"
CHANNEL_REPORTS = "reports"
CHANNEL_JOIN = "join-logs"
CHANNEL_UNSELFMUTE = "un-self-mute"

# Categories
CATEGORY_TOURNAMENTS = "tournaments"
CATEGORY_SO = "Science Olympiad"
CATEGORY_STATES = "states"
CATEGORY_GENERAL = "general"
CATEGORY_ARCHIVE = "archives"
CATEGORY_STAFF = "staff"

# Emoji reference
EMOJI_FAST_REVERSE = "\U000023EA"
EMOJI_LEFT_ARROW = "\U00002B05"
EMOJI_RIGHT_ARROW = "\U000027A1"
EMOJI_FAST_FORWARD = "\U000023E9"
EMOJI_UNSELFMUTE = "click_to_unmute"
EMOJI_FULL_UNSELFMUTE = "<:click_to_unmute:799389279385026610>"

# Rules
RULES = [
    "Treat *all* users with respect.",
    "No profanity or inappropriate language, content, or links.",
    "Treat delicate subjects delicately. When discussing religion, politics, instruments, or other similar topics, please remain objective and avoid voicing strong opinions.",
    "Do not spam or flood (an excessive number of messages sent within a short timespan).",
    "Avoid intentional repeating pinging of other users (saying another user’s name).",
    "Avoid excessive use of caps, which constitutes yelling and is disruptive.",
    "Never name-drop (using a real name without permission) or dox another user.",
    "No witch-hunting (requests of kicks or bans for other users).",
    "While you are not required to use your Scioly.org username as your nickname for this Server, please avoid assuming the username of or otherwise impersonating another active user.",
    "Do not use multiple accounts within this Server, unless specifically permitted. A separate tournament account may be operated alongside a personal account.",
    "Do not violate Science Olympiad Inc. copyrights. In accordance with the Scioly.org Resource Policy, all sharing of tests on Scioly.org must occur in the designated Test Exchanges. Do not solicit test trades on this Server.",
    "Do not advertise other servers or paid services with which you have an affiliation.",
    "Use good judgment when deciding what content to leave in and take out. As a general rule of thumb: 'When in doubt, leave it out.'"
]

##############
# DEV MODE CONFIG
##############

intents = discord.Intents.default()
intents.members = True

if dev_mode:
    BOT_PREFIX = "?"
    SERVER_ID = int(os.getenv('DEV_SERVER_ID'))
else:
    BOT_PREFIX = "!"
    SERVER_ID = 698306997287780363

bot = commands.Bot(command_prefix=(BOT_PREFIX), case_insensitive=True, intents=intents)

##############
# CHECKS
##############

async def is_bear(ctx):
    """Checks to see if the user is bear, or pepperonipi (for debugging purposes)."""
    return ctx.message.author.id == 353730886577160203 or ctx.message.author.id == 715048392408956950

async def is_staff(ctx):
    """Checks to see if the user is a staff member."""
    member = ctx.message.author
    vipRole = discord.utils.get(member.guild.roles, name=ROLE_VIP)
    staffRole = discord.utils.get(member.guild.roles, name=ROLE_STAFF)
    return vipRole in member.roles or staffRole in member.roles

async def is_launcher(ctx):
    """Checks to see if the user is a launch helper."""
    member = ctx.message.author
    staff = await is_staff(ctx)
    lhRole = discord.utils.get(member.guild.roles, name=ROLE_LH)
    if staff or lhRole in member.roles: return True

async def is_launcher_no_ctx(member):
    server = bot.get_guild(SERVER_ID)
    wmRole = discord.utils.get(server.roles, name=ROLE_WM)
    gm_role = discord.utils.get(server.roles, name=ROLE_GM)
    aRole = discord.utils.get(server.roles, name=ROLE_AD)
    vipRole = discord.utils.get(server.roles, name=ROLE_VIP)
    lhRole = discord.utils.get(server.roles, name=ROLE_LH)
    roles = [wmRole, gm_role, aRole, vipRole, lhRole]
    member = server.get_member(member)
    for role in roles:
        if role in member.roles: return True
    return False

async def is_admin(ctx):
    """Checks to see if the user is an administrator, or pepperonipi (for debugging purposes)."""
    member = ctx.message.author
    aRole = discord.utils.get(member.guild.roles, name=ROLE_AD)
    if aRole in member.roles or member.id == 715048392408956950: return True

def not_blacklisted_channel(blacklist):
    """Given a string array blacklist, check if command was not invoked in specified blacklist channels."""
    async def predicate(ctx):
        channel = ctx.message.channel
        server = bot.get_guild(SERVER_ID)
        for c in blacklist:
            if channel == discord.utils.get(server.text_channels, name=c):
                raise CommandNotAllowedInChannel(channel, "Command was invoked in a blacklisted channel.")
        return True
    
    return commands.check(predicate)
    
def is_whitelisted_channel(whitelist):
    """Given a string array whitelist, check if command was invoked in specified whitelisted channels."""
    async def predicate(ctx):
        channel = ctx.message.channel
        server = bot.get_guild(SERVER_ID)
        for c in whitelist:
            if channel == discord.utils.get(server.text_channels, name=c):
                return True
        raise CommandNotAllowedInChannel(channel, "Command was invoked in a non-whitelisted channel.")
    
    return commands.check(predicate)

def checkDM():
    """Checks if the user has DM permissions. If the send responds 403, then they have DMs disabled."""
    async def predicate(ctx):
        user = ctx.message.author
        try:
            await user.send("")
        except discord.Forbidden:
            raise NoDMsAllowed(user, f"{user} has DMs set to off.")
        except discord.HTTPException:
            pass
        return True
    
    return commands.check(predicate)

##############
# CONSTANTS
##############
PI_BOT_IDS = [
    723767075427844106,
    743254543952904197,
    637519324072116247
]
RULES_CHANNEL_ID = 737087680269123606
WELCOME_CHANNEL_ID = 743253216921387088
DISCORD_INVITE_ENDINGS = ["9Z5zKtV", "C9PGV6h", "s4kBmas", "ftPTxhC", "gh3aXbq", "skGQXd4", "RnkqUbK", "scioly"]

##############
# VARIABLES
##############
fish_now = 0
can_post = False
do_hourly_sync = False
CENSORED_WORDS = []
CENSORED_EMOJIS = []
EVENT_INFO = 0
REPORT_IDS = []
PING_INFO = []
TOURNEY_REPORT_IDS = []
COACH_REPORT_IDS = []
SHELLS_OPEN = []
CRON_LIST = []
RECENT_MESSAGES = []
STEALFISH_BAN = []
TOURNAMENT_INFO = []
REQUESTED_TOURNAMENTS = []
TAGS = []
STOPNUKE = False

##############
# FUNCTIONS TO BE REMOVED
##############
bot.remove_command("help")

##############
# ASYNC WRAPPERS
##############
aiowikip = aioify(obj=wikip)

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
        await update_tournament_list()
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
            await auto_report("Error with a cron task", "red", f"Error: `{string}`")
    except Exception as e:
        await auto_report("Error with a cron task", "red", f"Error: `{e}`\nOriginal task: `{string}`")

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
    botStatus = statuses[math.floor(random.random() * len(statuses))]
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

@bot.command(aliases=["tc", "tourney", "tournaments"])
async def tournament(ctx, *args):
    member = ctx.message.author
    new_args = list(args)
    ignore_terms = ["invitational", "invy", "tournament", "regional", "invite"]
    for term in ignore_terms:
        if term in new_args:
            new_args.remove(term)
            await ctx.send(f"Ignoring `{term}` because it is too broad of a term. *(If you need help with this command, please type `!help tournament`)*")
    if len(args) == 0:
        return await ctx.send("Please specify the tournaments you would like to be added/removed from!")
    for arg in new_args:
        # Stop users from possibly adding the channel hash in front of arg
        arg = arg.replace("#", "")
        arg = arg.lower()
        found = False
        if arg == "all":
            role = discord.utils.get(member.guild.roles, name=ROLE_AT)
            if role in member.roles:
                await ctx.send(f"Removed your `All Tournaments` role.")
                await member.remove_roles(role)
            else:
                await ctx.send(f"Added your `All Tournaments` role.")
                await member.add_roles(role)
            continue
        for t in TOURNAMENT_INFO:
            if arg == t[1]:
                found = True
                role = discord.utils.get(member.guild.roles, name=t[0])
                if role == None:
                    return await ctx.send(f"Apologies! The `{t[0]}` channel is currently not available.")
                if role in member.roles:
                    await ctx.send(f"Removed you from the `{t[0]}` channel.")
                    await member.remove_roles(role)
                else:
                    await ctx.send(f"Added you to the `{t[0]}` channel.")
                    await member.add_roles(role)
                break
        if not found:
            uid = member.id
            found2 = False
            votes = 1
            for t in REQUESTED_TOURNAMENTS:
                if arg == t['iden']:
                    found2 = True
                    if uid in t['users']:
                        return await ctx.send("Sorry, but you can only vote once for a specific tournament!")
                    t['count'] += 1
                    t['users'].append(uid)
                    votes = t['count']
                    break
            if not found2:
                await auto_report("New Tournament Channel Requested", "orange", f"User ID {uid} requested tournament channel `#{arg}`.\n\nTo add this channel to the voting list for the first time, use `!tla {arg} {uid}`.\nIf the channel has already been requested in the list and this was a user mistake, use `!tla [actual name] {uid}`.")
                return await ctx.send(f"Made request for a `#{arg}` channel. Please note your submission may not instantly appear.")
            await ctx.send(f"Added a vote for `{arg}`. There " + ("are" if votes != 1 else "is") + f" now `{votes}` " + (f"votes" if votes != 1 else f"vote") + " for this channel.")
            await update_tournament_list()

@bot.command()
@commands.check(is_staff)
async def tla(ctx, iden, uid):
    global REQUESTED_TOURNAMENTS
    for t in REQUESTED_TOURNAMENTS:
        if t['iden'] == iden:
            t['count'] += 1
            await ctx.send(f"Added a vote for {iden} from {uid}. Now has `{t['count']}` votes.")
            return await update_tournament_list()
    REQUESTED_TOURNAMENTS.append({'iden': iden, 'count': 1, 'users': [uid]})
    await update_tournament_list()
    return await ctx.send(f"Added a vote for {iden} from {uid}. Now has `1` vote.")

@bot.command()
@commands.check(is_staff)
async def tlr(ctx, iden):
    global REQUESTED_TOURNAMENTS
    for t in REQUESTED_TOURNAMENTS:
        if t['iden'] == iden:
            REQUESTED_TOURNAMENTS.remove(t)
    await update_tournament_list()
    return await ctx.send(f"Removed `#{iden}` from the tournament list.")

async def update_tournament_list():
    tl = await get_tournament_channels()
    tl.sort(key=lambda x: x[0])
    global TOURNAMENT_INFO
    global REQUESTED_TOURNAMENTS
    TOURNAMENT_INFO = tl
    server = bot.get_guild(SERVER_ID)
    tourney_channel = discord.utils.get(server.text_channels, name=CHANNEL_TOURNAMENTS)
    tournament_category = discord.utils.get(server.categories, name=CATEGORY_TOURNAMENTS)
    bot_spam_channel = discord.utils.get(server.text_channels, name=CHANNEL_BOTSPAM)
    server_support_channel = discord.utils.get(server.text_channels, name=CHANNEL_SUPPORT)
    gm = discord.utils.get(server.roles, name=ROLE_GM)
    a = discord.utils.get(server.roles, name=ROLE_AD)
    all_tournaments_role = discord.utils.get(server.roles, name=ROLE_AT)
    string_lists = []
    string_lists.append("")
    open_soon_list = ""
    channels_requested_list = ""
    now = datetime.datetime.now()
    for t in tl: # For each tournament in the sheet
        # Check if the channel needs to be made / deleted
        ch = discord.utils.get(server.text_channels, name=t[1])
        r = discord.utils.get(server.roles, name=t[0])
        tourney_date = t[4]
        before_days = int(t[5])
        after_days = int(t[6])
        tourney_date_datetime = datetime.datetime.strptime(tourney_date, "%Y-%m-%d")
        day_diff = (tourney_date_datetime - now).days
        print(f"Tournament List: Handling {t[0]} (Day diff: {day_diff} days)")
        if (day_diff < (-1 * after_days)) and ch != None:
            # If past tournament date, now out of range
            if ch.category.name != CATEGORY_ARCHIVE:
                await auto_report("Tournament Channel & Role Needs to be Archived", "orange", f"The {ch.mention} channel and {r.mention} role need to be archived, as it is after the tournament date.")
        elif (day_diff <= before_days) and ch == None:
            # If before tournament and in range
            new_role = await server.create_role(name=t[0])
            new_channel = await server.create_text_channel(t[1], category=tournament_category)
            await new_channel.edit(topic=f"{t[2]} - Discussion around the {t[0]} occurring on {t[4]}.", sync_permissions=True)
            await new_channel.set_permissions(new_role, read_messages=True)
            await new_channel.set_permissions(all_tournaments_role, read_messages=True)
            await new_channel.set_permissions(server.default_role, read_messages=False)
            string_to_add = (t[2] + " **" + t[0] + "** - `!tournament " + t[1] + "`\n")
            while len(string_lists[-1] + string_to_add) > 2048:
                string_lists.append("")
            string_lists[-1] += string_to_add
        elif ch != None:
            string_to_add = (t[2] + " **" + t[0] + "** - `!tournament " + t[1] + "`\n")
            while len(string_lists[-1] + string_to_add) > 2048:
                string_lists.append("")
            string_lists[-1] += string_to_add
        elif (day_diff > before_days):
            open_soon_list += (t[2] + " **" + t[0] + f"** - Opens in `{day_diff - before_days}` days.\n")
    REQUESTED_TOURNAMENTS.sort(key=lambda x: (-x['count'], x['iden']))
    spacing_needed = max([len(t['iden']) for t in REQUESTED_TOURNAMENTS]) if len(REQUESTED_TOURNAMENTS) > 0 else 0
    for t in REQUESTED_TOURNAMENTS:
        spaces = " " * (spacing_needed - len(t['iden']))
        channels_requested_list += f"`!tournament {t['iden']}{spaces}` · **{t['count']} votes**\n"
    embeds = []
    embeds.append(assemble_embed(
        title=":medal: Tournament Channels Listing",
        desc=(
            "Below is a list of **tournament channels**. Some are available right now, some will be available soon, and others have been requested, but have not received 10 votes to be considered for a channel." +
            f"\n\n* To join an available tournament channel, head to {bot_spam_channel.mention} and type `!tournament [name]`." +
            f"\n\n* To make a new request for a tournament channel, head to {bot_spam_channel.mention} and type `!tournament [name]`, where `[name]` is the name of the tournament channel you would like to have created." +
            f"\n\n* Need help? Ping a {gm.mention} or {a.mention}, or ask in {server_support_channel.mention}"
        )
    ))
    for i, s in enumerate(string_lists):
        embeds.append(assemble_embed(
            title=f"Currently Available Channels (Page {i + 1}/{len(string_lists)})",
            desc=s if len(s) > 0 else "No channels are available currently."
        ))
    embeds.append(assemble_embed(
        title="Channels Opening Soon",
        desc=open_soon_list if len(open_soon_list) > 0 else "No channels are opening soon currently.",
    ))
    embeds.append(assemble_embed(
        title="Channels Requested",
        desc=("Vote with the command associated with the tournament channel.\n\n" + channels_requested_list) if len(channels_requested_list) > 0 else f"No channels have been requested currently. To make a request for a tournament channel, head to {bot_spam_channel.mention} and type `!tournament [name]`, with the name of the tournament."
    ))
    hist = await tourney_channel.history(oldest_first=True).flatten()
    if len(hist) != 0:
        # When the tourney channel already has embeds
        if len(embeds) < len(hist):
            messages = await tourney_channel.history(oldest_first=True).flatten()
            for m in messages[len(embeds):]:
                await m.delete()
        count = 0
        async for m in tourney_channel.history(oldest_first=True):
            await m.edit(embed=embeds[count])
            count += 1
        if len(embeds) > len(hist):
            for e in embeds[len(hist):]:
                await tourney_channel.send(embed=e)
    else:
        # If the tournament channel is being initialized for the first time
        past_messages = await tourney_channel.history(limit=100).flatten()
        await tourney_channel.delete_messages(past_messages)
        for e in embeds:
            await tourney_channel.send(embed=e)

@bot.command()
@commands.check(is_staff)
async def vc(ctx):
    server = ctx.message.guild
    if ctx.message.channel.category.name == CATEGORY_TOURNAMENTS:
        test_vc = discord.utils.get(server.voice_channels, name=ctx.message.channel.name)
        if test_vc == None:
            # Voice channel needs to be opened
            new_vc = await server.create_voice_channel(ctx.message.channel.name, category=ctx.message.channel.category)
            await new_vc.edit(sync_permissions=True)
            # Make the channel invisible to normal members
            await new_vc.set_permissions(server.default_role, view_channel=False)
            at = discord.utils.get(server.roles, name=ROLE_AT)
            for t in TOURNAMENT_INFO:
                if ctx.message.channel.name == t[1]:
                    tourney_role = discord.utils.get(server.roles, name=t[0])
                    await new_vc.set_permissions(tourney_role, view_channel=True)
                    break
            await new_vc.set_permissions(at, view_channel=True)
            return await ctx.send("Created a voice channel. **Please remember to follow the rules! No doxxing or cursing is allowed.**")
        else:
            # Voice channel needs to be closed
            await test_vc.delete()
            return await ctx.send("Closed the voice channel.")
    elif ctx.message.channel.category.name == CATEGORY_STATES:
        test_vc = discord.utils.get(server.voice_channels, name=ctx.message.channel.name)
        if test_vc == None:
            # Voice channel does not currently exist
            if len(ctx.message.channel.category.channels) == 50:
                # Too many voice channels in the state category
                # Let's move one state to the next category
                new_cat = filter(lambda x: x.name == "states", server.categories)
                new_cat = list(new_cat)
                if len(new_cat) < 2: 
                    return await ctx.send("Could not find alternate states channel to move overflowed channels to.")
                else:
                    # Success, we found the other category
                    current_cat = ctx.message.channel.category
                    await current_cat.channels[-1].edit(category = new_cat[1], position = 0)
            new_vc = await server.create_voice_channel(ctx.message.channel.name, category=ctx.message.channel.category)
            await new_vc.edit(sync_permissions=True)
            await new_vc.set_permissions(server.default_role, view_channel=False)
            muted_role = discord.utils.get(server.roles, name=ROLE_MUTED)
            all_states_role = discord.utils.get(server.roles, name=ROLE_ALL_STATES)
            self_muted_role = discord.utils.get(server.roles, name=ROLE_SELFMUTE)
            quarantine_role = discord.utils.get(server.roles, name=ROLE_QUARANTINE)
            state_role_name = await lookup_role(ctx.message.channel.name.replace("-", " "))
            state_role = discord.utils.get(server.roles, name = state_role_name)
            await new_vc.set_permissions(muted_role, connect=False)
            await new_vc.set_permissions(self_muted_role, connect=False)
            await new_vc.set_permissions(quarantine_role, connect=False)
            await new_vc.set_permissions(state_role, view_channel = True, connect=True)
            await new_vc.set_permissions(all_states_role, view_channel = True, connect=True)
            current_pos = ctx.message.channel.position
            return await ctx.send("Created a voice channel. **Please remember to follow the rules! No doxxing or cursing is allowed.**")
        else:
            await test_vc.delete()
            if len(ctx.message.channel.category.channels) == 49:
                # If we had to move a channel out of category to make room, move it back
                # Let's move one state to the next category
                new_cat = filter(lambda x: x.name == "states", server.categories)
                new_cat = list(new_cat)
                if len(new_cat) < 2: 
                    return await ctx.send("Could not find alternate states channel to move overflowed channels to.")
                else:
                    # Success, we found the other category
                    current_cat = ctx.message.channel.category
                    await new_cat[1].channels[0].edit(category = current_cat, position = 1000)
            return await ctx.send("Closed the voice channel.")
    elif ctx.message.channel.name == "games":
        # Support for opening a voice channel for #games
        test_vc = discord.utils.get(server.voice_channels, name="games")
        if test_vc == None:
            # Voice channel needs to be opened/doesn't exist already
            new_vc = await server.create_voice_channel("games", category=ctx.message.channel.category)
            await new_vc.edit(sync_permissions=True)
            await new_vc.set_permissions(server.default_role, view_channel=False)
            games_role = discord.utils.get(server.roles, name=ROLE_GAMES)
            member_role = discord.utils.get(server.roles, name=ROLE_MR)
            await new_vc.set_permissions(games_role, view_channel=True)
            await new_vc.set_permissions(member_role, view_channel=False)
            return await ctx.send("Created a voice channel. **Please remember to follow the rules! No doxxing or cursing is allowed.**")
        else:
            # Voice channel needs to be closed
            await test_vc.delete()
            return await ctx.send("Closed the voice channel.")
    else:
        return await ctx.send("Apologies... voice channels can currently be opened for tournament channels and the games channel.")

@bot.command()
@commands.check(is_staff)
async def getVariable(ctx, var):
    """Fetches a local variable."""
    if ctx.message.channel.name != "staff":
        await ctx.send("You can only fetch variables from the staff channel.")
    else:
        await ctx.send("Attempting to find variable.")
        try:
            variable = globals()[var]
            await ctx.send(f"Variable value: `{variable}`")
        except:
            await ctx.send(f"Can't find that variable!")

@bot.command(aliases=["eats", "beareats"])
@commands.check(is_bear)
async def eat(ctx, user):
    """Allows bear to eat users >:D"""
    message = await get_bear_message(user)
    await ctx.message.delete()
    await ctx.send(message)

@bot.command()
@commands.check(is_staff)
async def refresh(ctx):
    """Refreshes data from the sheet."""
    await update_tournament_list()
    res = await refresh_algorithm()
    if res == True:
        await ctx.send("Successfully refreshed data from sheet.")
    else:
        await ctx.send(":warning: Unsuccessfully refreshed data from sheet.")

@bot.command(aliases=["gci", "cid", "channelid"])
async def getchannelid(ctx):
    """Gets the channel ID of the current channel."""
    await ctx.send("Hey <@" + str(ctx.message.author.id) + ">! The channel ID is `" + str(ctx.message.channel.id) + "`. :)")

@bot.command(aliases=["gei", "eid"])
async def getemojiid(ctx, emoji: discord.Emoji):
    """Gets the ID of the given emoji."""
    return await ctx.send(f"{emoji} - `{emoji}`")

@bot.command(aliases=["rid"])
async def getroleid(ctx, name):
    role = discord.utils.get(ctx.message.author.guild.roles, name=name)
    return await ctx.send(f"`{role.mention}`")

@bot.command(aliases=["gui", "ui", "userid"])
async def getuserid(ctx, user=None):
    """Gets the user ID of the caller or another user."""
    if user == None:
        await ctx.send(f"Your user ID is `{ctx.message.author.id}`.")
    elif user[:3] != "<@!":
        member = ctx.message.guild.get_member_named(user)
        await ctx.send(f"The user ID of {user} is: `{member.id}`")
    else:
        user = user.replace("<@!", "").replace(">", "")
        await ctx.send(f"The user ID of <@{user}> is `{user}`.")

@bot.command(aliases=["ufi"])
@commands.check(is_staff)
async def userfromid(ctx, iden:int):
    """Mentions a user with the given ID."""
    user = bot.get_user(iden)
    await ctx.send(user.mention)

@bot.command(aliases=["hi"])
async def hello(ctx):
    """Simply says hello. Used for testing the bot."""
    await ctx.send("Well, hello there.")

@bot.command(aliases=["what"])
async def about(ctx):
    """Prints information about the bot."""
    await ctx.send(get_about())

@bot.command(aliases=["server", "link", "invitelink"])
async def invite(ctx):
    await ctx.send("https://discord.gg/scioly")

@bot.command()
async def forums(ctx):
    await ctx.send("<https://scioly.org/forums>")

@bot.command()
async def obb(ctx):
    await ctx.send("<https://scioly.org/obb>")

@bot.command(aliases=["tests", "testexchange"])
async def exchange(ctx):
    await ctx.send("<https://scioly.org/tests>")

@bot.command()
async def gallery(ctx):
    await ctx.send("<https://scioly.org/gallery>")

@bot.command(aliases=["random"])
async def rand(ctx, a=1, b=10):
    r = random.randrange(a, b + 1)
    await ctx.send(f"Random number between `{a}` and `{b}`: `{r}`")

@bot.command()
@not_blacklisted_channel(blacklist=[CHANNEL_WELCOME])
async def magic8ball(ctx):
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
    response = sayings[math.floor(random.random()*len(sayings))]
    await ctx.message.reply(f"**{response}**")

@bot.command()
@not_blacklisted_channel(blacklist=[CHANNEL_WELCOME])
async def xkcd(ctx, num = None):
    max_num = await xkcd_module.get_max()
    if num == None:
        rand = random.randrange(1, int(max_num))
        return await xkcd(ctx, str(rand))
    if num.isdigit() and 1 <= int(num) <= int(max_num):
        return await ctx.send(f"https://xkcd.com/{num}")
    else:
        return await ctx.send("Invalid attempted number for xkcd.")

@bot.command()
async def rule(ctx, num):
    """Gets a specified rule."""
    if not num.isdigit() or int(num) < 1 or int(num) > 13:
        # If the rule number is not actually a number
        return await ctx.send("Please use a valid rule number, from 1 through 13. (Ex: `!rule 7`)")
    rule = RULES[int(num) - 1]
    return await ctx.send(f"**Rule {num}:**\n> {rule}")

@bot.command()
async def coach(ctx):
    """Gives an account the coach role."""
    await ctx.send("If you would like to apply for the `Coach` role, please fill out the form here: <https://forms.gle/UBKpWgqCr9Hjw9sa6>.")

@bot.command(aliases=["slow", "sm"])
@commands.check(is_staff)
async def slowmode(ctx, arg:int=None):
    if arg == None:
        if ctx.channel.slowmode_delay == 0:
            await ctx.channel.edit(slowmode_delay=10)
            await ctx.send("Enabled a 10 second slowmode.")
        else:
            await ctx.channel.edit(slowmode_delay=0)
            await ctx.send("Removed slowmode.")
    else:
        await ctx.channel.edit(slowmode_delay=arg)
        if arg != 0:
            await ctx.send(f"Enabled a {arg} second slowmode.")
        else:
            await ctx.send(f"Removed slowmode.")

@bot.command(aliases=["state"])
async def states(ctx, *args):
    """Assigns someone with specific states."""
    new_args = [str(arg).lower() for arg in args]

    # Fix commas as possible separator
    if len(new_args) == 1:
        new_args = new_args[0].split(",")
    new_args = [re.sub("[;,]", "", arg) for arg in new_args]

    member = ctx.message.author
    states = await get_state_list()
    states = [s[:s.rfind(" (")] for s in states]
    triple_word_states = [s for s in states if len(s.split(" ")) > 2]
    double_word_states = [s for s in states if len(s.split(" ")) > 1]
    removed_roles = []
    added_roles = []
    for term in ["california", "ca", "cali"]:
        if term in [arg.lower() for arg in args]:
            return await ctx.send("Which California, North or South? Try `!state norcal` or `!state socal`.")
    if len(new_args) < 1:
        return await ctx.send("Sorry, but you need to specify a state (or multiple states) to add/remove.")
    elif len(new_args) > 10:
        return await ctx.send("Sorry, you are attempting to add/remove too many states at once.")
    for string in ["South", "North"]:
        california_list = [f"California ({string})", f"California-{string}", f"California {string}", f"{string}ern California", f"{string} California", f"{string} Cali", f"Cali {string}", f"{string} CA", f"CA {string}"]
        if string == "North":
            california_list.append("NorCal")
        else:
            california_list.append("SoCal")
        for listing in california_list:
            words = listing.split(" ")
            all_here = sum(1 for word in words if word.lower() in new_args)
            if all_here == len(words):
                role = discord.utils.get(member.guild.roles, name=f"California ({string})")
                if role in member.roles:
                    await member.remove_roles(role)
                    removed_roles.append(f"California ({string})")
                else:
                    await member.add_roles(role)
                    added_roles.append(f"California ({string})")
                for word in words:
                    new_args.remove(word.lower())
    for triple in triple_word_states:
        words = triple.split(" ")
        all_here = 0
        all_here = sum(1 for word in words if word.lower() in new_args)
        if all_here == 3:
            # Word is in args
            role = discord.utils.get(member.guild.roles, name=triple)
            if role in member.roles:
                await member.remove_roles(role)
                removed_roles.append(triple)
            else:
                await member.add_roles(role)
                added_roles.append(triple)
            for word in words:
                new_args.remove(word.lower())
    for double in double_word_states:
        words = double.split(" ")
        all_here = 0
        all_here = sum(1 for word in words if word.lower() in new_args)
        if all_here == 2:
            # Word is in args
            role = discord.utils.get(member.guild.roles, name=double)
            if role in member.roles:
                await member.remove_roles(role)
                removed_roles.append(double)
            else:
                await member.add_roles(role)
                added_roles.append(double)
            for word in words:
                new_args.remove(word.lower())
    for arg in new_args:
        role_name = await lookup_role(arg)
        if role_name == False:
            return await ctx.send(f"Sorry, the {arg} state could not be found. Try again.")
        role = discord.utils.get(member.guild.roles, name=role_name)
        if role in member.roles:
            await member.remove_roles(role)
            removed_roles.append(role_name)
        else:
            await member.add_roles(role)
            added_roles.append(role_name)
    if len(added_roles) > 0 and len(removed_roles) == 0:
        state_res = "Added states " + (' '.join([f'`{arg}`' for arg in added_roles])) + "."
    elif len(removed_roles) > 0 and len(added_roles) == 0:
        state_res = "Removed states " + (' '.join([f'`{arg}`' for arg in removed_roles])) + "."
    else:
        state_res = "Added states " + (' '.join([f'`{arg}`' for arg in added_roles])) + ", and removed states " + (' '.join([f'`{arg}`' for arg in removed_roles])) + "."
    await ctx.send(state_res)

@bot.command()
async def games(ctx):
    """Removes or adds someone to the games channel."""
    games_channel = discord.utils.get(ctx.message.author.guild.text_channels, name=CHANNEL_GAMES)
    member = ctx.message.author
    role = discord.utils.get(member.guild.roles, name=ROLE_GAMES)
    if role in member.roles:
        await member.remove_roles(role)
        await ctx.send("Removed you from the games club... feel free to come back anytime!")
        await games_channel.send(f"{member.mention} left the party.")
    else:
        await member.add_roles(role)
        await ctx.send(f"You are now in the channel. Come and have fun in {games_channel.mention}! :tada:")
        await games_channel.send(f"Please welcome {member.mention} to the party!!")

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

@bot.command()
@commands.check(is_staff)
async def lock(ctx):
    """Locks a channel to Member access."""
    member = ctx.message.author
    channel = ctx.message.channel

    if (channel.category.name in ["beta", "staff", "Pi-Bot"]):
        return await ctx.send("This command is not suitable for this channel because of its category.")

    member_role = discord.utils.get(member.guild.roles, name=ROLE_MR)
    if (channel.category.name == CATEGORY_STATES):
        await ctx.channel.set_permissions(member_role, add_reactions=False, send_messages=False)
    else:
        await ctx.channel.set_permissions(member_role, add_reactions=False, send_messages=False, read_messages=True)

    wiki_role = discord.utils.get(member.guild.roles, name=ROLE_WM)
    gm_role = discord.utils.get(member.guild.roles, name=ROLE_GM)
    admin_role = discord.utils.get(member.guild.roles, name=ROLE_AD)
    bot_role = discord.utils.get(member.guild.roles, name=ROLE_BT)
    await ctx.channel.set_permissions(wiki_role, add_reactions=True, send_messages=True, read_messages=True)
    await ctx.channel.set_permissions(gm_role, add_reactions=True, send_messages=True, read_messages=True)
    await ctx.channel.set_permissions(admin_role, add_reactions=True, send_messages=True, read_messages=True)
    await ctx.channel.set_permissions(bot_role, add_reactions=True, send_messages=True, read_messages=True)
    await ctx.send("Locked the channel to Member access.")

@bot.command()
@commands.check(is_staff)
async def unlock(ctx):
    """Unlocks a channel to Member access."""
    member = ctx.message.author
    channel = ctx.message.channel

    if (channel.category.name in ["beta", "staff", "Pi-Bot"]):
        return await ctx.send("This command is not suitable for this channel because of its category.")

    if (channel.category.name == CATEGORY_SO or channel.category.name == CATEGORY_GENERAL):
        await ctx.send("Synced permissions with channel category.")
        return await channel.edit(sync_permissions=True)

    member_role = discord.utils.get(member.guild.roles, name=ROLE_MR)
    if (channel.category.name != CATEGORY_STATES):
        await ctx.channel.set_permissions(member_role, add_reactions=True, send_messages=True, read_messages=True)
    else:
        await ctx.channel.set_permissions(member_role, add_reactions=True, send_messages=True)

    wiki_role = discord.utils.get(member.guild.roles, name=ROLE_WM)
    gm_role = discord.utils.get(member.guild.roles, name=ROLE_GM)
    aRole = discord.utils.get(member.guild.roles, name=ROLE_AD)
    bRole = discord.utils.get(member.guild.roles, name=ROLE_BT)
    await ctx.channel.set_permissions(wiki_role, add_reactions=True, send_messages=True, read_messages=True)
    await ctx.channel.set_permissions(gm_role, add_reactions=True, send_messages=True, read_messages=True)
    await ctx.channel.set_permissions(aRole, add_reactions=True, send_messages=True, read_messages=True)
    await ctx.channel.set_permissions(bRole, add_reactions=True, send_messages=True, read_messages=True)
    await ctx.send("Unlocked the channel to Member access. Please check if permissions need to be synced.")

@bot.command()
async def info(ctx):
    """Gets information about the Discord server."""
    server = ctx.message.guild
    name = server.name
    owner = server.owner
    creation_date = server.created_at
    emoji_count = len(server.emojis)
    icon = server.icon_url_as(format=None, static_format='jpeg')
    animated_icon = server.is_icon_animated()
    iden = server.id
    banner = server.banner_url
    desc = server.description
    mfa_level = server.mfa_level
    verification_level = server.verification_level
    content_filter = server.explicit_content_filter
    default_notifs = server.default_notifications
    features = server.features
    splash = server.splash_url
    premium_level = server.premium_tier
    boosts = server.premium_subscription_count
    channel_count = len(server.channels)
    text_channel_count = len(server.text_channels)
    voice_channel_count = len(server.voice_channels)
    category_count = len(server.categories)
    system_channel = server.system_channel
    if type(system_channel) == discord.TextChannel: system_channel = system_channel.mention
    rules_channel = server.rules_channel
    if type(rules_channel) == discord.TextChannel: rules_channel = rules_channel.mention
    public_updates_channel = server.public_updates_channel
    if type(public_updates_channel) == discord.TextChannel: public_updates_channel = public_updates_channel.mention
    emoji_limit = server.emoji_limit
    bitrate_limit = server.bitrate_limit
    filesize_limit = round(server.filesize_limit/1000000, 3)
    boosters = server.premium_subscribers
    for i, b in enumerate(boosters):
        # convert user objects to mentions
        boosters[i] = b.mention
    boosters = ", ".join(boosters)
    print(boosters)
    role_count = len(server.roles)
    member_count = len(server.members)
    max_members = server.max_members
    discovery_splash_url = server.discovery_splash_url
    member_percentage = round(member_count/max_members * 100, 3)
    emoji_percentage = round(emoji_count/emoji_limit * 100, 3)
    channel_percentage = round(channel_count/500 * 100, 3)
    role_percenatege = round(role_count/250 * 100, 3)

    staff_member = await is_staff(ctx)
    fields = [
            {
                "name": "Basic Information",
                "value": (
                    f"**Creation Date:** {creation_date}\n" +
                    f"**ID:** {iden}\n" +
                    f"**Animated Icon:** {animated_icon}\n" +
                    f"**Banner URL:** {banner}\n" +
                    f"**Splash URL:** {splash}\n" +
                    f"**Discovery Splash URL:** {discovery_splash_url}"
                ),
                "inline": False
            },
            {
                "name": "Nitro Information",
                "value": (
                    f"**Nitro Level:** {premium_level} ({boosts} individual boosts)\n" +
                    f"**Boosters:** {boosters}"
                ),
                "inline": False
            }
        ]
    if staff_member and ctx.channel.category.name == CATEGORY_STAFF:
        fields.extend(
            [{
                "name": "Staff Information",
                "value": (
                    f"**Owner:** {owner}\n" +
                    f"**MFA Level:** {mfa_level}\n" +
                    f"**Verification Level:** {verification_level}\n" +
                    f"**Content Filter:** {content_filter}\n" +
                    f"**Default Notifications:** {default_notifs}\n" +
                    f"**Features:** {features}\n" +
                    f"**Bitrate Limit:** {bitrate_limit}\n" +
                    f"**Filesize Limit:** {filesize_limit} MB"
                ),
                "inline": False
            },
            {
                "name": "Channels",
                "value": (
                    f"**Public Updates Channel:** {public_updates_channel}\n" +
                    f"**System Channel:** {system_channel}\n" +
                    f"**Rules Channel:** {rules_channel}\n" +
                    f"**Text Channel Count:** {text_channel_count}\n" +
                    f"**Voice Channel Count:** {voice_channel_count}\n" +
                    f"**Category Count:** {category_count}\n"
                ),
                "inline": False
            },
            {
                "name": "Limits",
                "value": (
                    f"**Channels:** *{channel_percentage}%* ({channel_count}/500 channels)\n" +
                    f"**Members:** *{member_percentage}%* ({member_count}/{max_members} members)\n" +
                    f"**Emoji:** *{emoji_percentage}%* ({emoji_count}/{emoji_limit} emojis)\n" +
                    f"**Roles:** *{role_percenatege}%* ({role_count}/250 roles)"
                ),
                "inline": False
            }
        ])
    embed = assemble_embed(
        title=f"Information for `{name}`",
        desc=f"**Description:** {desc}",
        thumbnailUrl=icon,
        fields=fields
    )
    await ctx.send(embed=embed)

@bot.command(aliases=["r"])
async def report(ctx, *args):
    """Creates a report that is sent to staff members."""
    server = bot.get_guild(SERVER_ID)
    reports_channel = discord.utils.get(server.text_channels, name=CHANNEL_REPORTS)
    message = args[0]
    if len(args) > 1:
        message = ' '.join(args)
    poster = str(ctx.message.author)
    embed = assemble_embed(
        title=f"Report Received (using `!report`)",
        webcolor="red",
        authorName = poster,
        authorIcon = ctx.message.author.avatar_url_as(format="jpg"),
        fields = [{
            "name": "Message",
            "value": message,
            "inline": False
        }]
    )
    message = await reports_channel.send(embed=embed)
    REPORT_IDS.append(message.id)
    await message.add_reaction("\U00002705")
    await message.add_reaction("\U0000274C")
    await ctx.send("Thanks, report created.")

# Meant for Pi-Bot only
async def auto_report(reason, color, message):
    """Allows Pi-Bot to generate a report by himself."""
    server = bot.get_guild(SERVER_ID)
    reports_channel = discord.utils.get(server.text_channels, name=CHANNEL_REPORTS)
    embed = assemble_embed(
        title=f"{reason} (message from Pi-Bot)",
        webcolor=color,
        fields = [{
            "name": "Message",
            "value": message,
            "inline": False
        }]
    )
    message = await reports_channel.send(embed=embed)
    REPORT_IDS.append(message.id)
    await message.add_reaction("\U00002705")
    await message.add_reaction("\U0000274C")

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

@bot.command()
async def resultstemplate(ctx, url):
    if url.find("scilympiad.com") == -1:
        return await ctx.send("The URL must be a Scilympiad results link.")
    await ctx.send("**Warning:** Because Scilympiad is constantly evolving, this command may break. Please preview the template on the wiki before saving! If this command breaks, please DM pepperonipi or open an issue on GitHub. Thanks!")
    res = await make_results_template(url)
    with open("resultstemplate.txt", "w+") as t:
        t.write(res)
    file = discord.File("resultstemplate.txt", filename="resultstemplate.txt")
    await ctx.send(file=file)

@bot.command()
@checkDM()
async def ping(ctx, command=None, *args):
    """Controls Pi-Bot's ping interface."""
    if command is None:
        return await ctx.send("Uh, I need a command you want to run.")
    member = ctx.message.author.id
    if len(args) > 8:
        return await ctx.send("You are giving me too many pings at once! Please separate your requests over multiple commands.")
    if command.lower() in ["add", "new", "addregex", "newregex", "addregexp", "newregexp", "delete", "remove", "test", "try"] and len(args) < 1:
        return await ctx.send(f"In order to {command} a ping, you must supply a regular expression or word.")
    if command.lower() in ["add", "new", "addregex", "newregex", "addregexp", "newregexp"]:
        # Check to see if author in ping info already
        ignored_list = []
        if any([True for u in PING_INFO if u['id'] == member]):
            #yes
            user = next((u for u in PING_INFO if u['id'] == member), None)
            pings = user['pings']
            for arg in args:
                try:
                    re.findall(arg, "test phrase")
                except:
                    await ctx.send(f"Ignoring adding the `{arg}` ping because it uses illegal characters.")
                    ignored_list.append(arg)
                    continue
                if f"({arg})" in pings or f"\\b({arg})\\b" in pings or arg in pings:
                    await ctx.send(f"Ignoring adding the `{arg}` ping because you already have a ping currently set as that.")
                    ignored_list.append(arg)
                else:
                    if command.lower() in ["add", "new"]:
                        print(f"adding word: {re.escape(arg)}")
                        pings.append(fr"\b({re.escape(arg)})\b")
                    else:
                        print(f"adding regexp: {arg}")
                        pings.append(fr"({arg})")
        else:
            # nope
            if command.lower() in ["add", "new"]:
                PING_INFO.append({
                    "id": member,
                    "pings": [fr"\b({re.escape(arg)})\b" for arg in args]
                })
            else:
                PING_INFO.append({
                    "id": member,
                    "pings": [fr"({arg})" for arg in args]
                })
        return await ctx.send(f"Alrighty... I've got you all set up for the following pings: " + (" ".join([f"`{arg}`" for arg in args if arg not in ignored_list])))
    elif command.lower() in ["delete", "remove"]:
        user = next((u for u in PING_INFO if u['id'] == member), None)
        if user == None or len(user['pings']) == 0:
            return await ctx.send("You have no registered pings.")
        for arg in args:
            if arg == "all":
                user['pings'] = []
                return await ctx.send("I removed all of your pings.")
            if arg in user['pings']:
                user['pings'].remove(arg)
                await ctx.send(f"I removed the `{arg}` RegExp ping you were referencing.")
            elif f"\\b({arg})\\b" in user['pings']:
                user['pings'].remove(f"\\b({arg})\\b")
                await ctx.send(f"I removed the `{arg}` word ping you were referencing.")
            elif f"({arg})" in user['pings']:
                user['pings'].remove(f"({arg})")
                await ctx.send(f"I removed the `{arg}` RegExp ping you were referencing.")
            else:
                return await ctx.send(f"I can't find my phone or the **`{arg}`** ping you are referencing, sorry. Try another ping, or see all of your pings with `!ping list`.")
        return await ctx.send("I removed all pings you requested.")
    elif command.lower() in ["list", "all"]:
        user = next((u for u in PING_INFO if u['id'] == member), None)
        if user == None or len(user['pings']) == 0:
            return await ctx.send("You have no registered pings.")
        else:
            pings = user['pings']
            regex_pings = []
            word_pings = []
            for ping in pings:
                if ping[:2] == "\\b":
                    word_pings.append(ping)
                else:
                    regex_pings.append(ping)
            if len(regex_pings) > 0:
                await ctx.send("Your RegEx pings are: " + ", ".join([f"`{regex}`" for regex in regex_pings]))
            if len(word_pings) > 0:
                await ctx.send("Your word pings are: " + ", ".join([f"`{word[3:-3]}`" for word in word_pings]))
    elif command.lower() in ["test", "try"]:
        user = next((u for u in PING_INFO if u['id'] == member), None)
        user_pings = user['pings']
        matched = False
        for arg in args:
            for ping in user_pings:
                if len(re.findall(ping, arg, re.I)) > 0:
                    await ctx.send(f"Your ping `{ping}` matches `{arg}`.")
                    matched = True
        if not matched:
            await ctx.send("Your test matched no pings of yours.")
    else:
        return await ctx.send("Sorry, I can't find that command.")

@bot.command(aliases=["donotdisturb"])
async def dnd(ctx):
    member = ctx.message.author.id
    if any([True for u in PING_INFO if u['id'] == member]):
        user = next((u for u in PING_INFO if u['id'] == member), None)
        if 'dnd' not in user:
            user['dnd'] = True
            return await ctx.send("Enabled DND mode for pings.")
        elif user['dnd'] == True:
            user['dnd'] = False
            return await ctx.send("Disabled DND mode for pings.")
        else:
            user['dnd'] = True
            return await ctx.send("Enabled DND mode for pings.")
    else:
        return await ctx.send("You can't enter DND mode without any pings!")

async def ping_pm(user_id, pinger, ping_exp, channel, content, jump_url):
    """Allows Pi-Bot to PM a user about a ping."""
    user_to_send = bot.get_user(user_id)
    try:
        content = re.sub(rf'{ping_exp}', r'**\1**', content, flags=re.I)
    except Exception as e:
        print(f"Could not bold ping due to unfavored RegEx. Error: {e}")
    ping_exp = ping_exp.replace(r"\b(", "").replace(r")\b", "")
    warning = f"\n\nIf you don't want this ping anymore, in `#bot-spam` on the server, send `!ping remove {ping_exp}`"
    embed = assemble_embed(
        title=":bellhop: Ping Alert!",
        desc=(f"Looks like `{pinger}` pinged a ping expression of yours in the Scioly.org Discord Server!" + warning),
        fields=[
            {"name": "Expression Matched", "value": f" `{ping_exp}`", "inline": "True"},
            {"name": "Jump To Message", "value": f"[Click here!]({jump_url})", "inline": "True"},
            {"name": "Channel", "value": f"`#{channel}`", "inline": "True"},
            {"name": "Content", "value": content, "inline": "False"}
        ],
        hexcolor="#2E66B6"
    )
    await user_to_send.send(embed=embed)

@bot.command(aliases=["doggobomb"])
@not_blacklisted_channel(blacklist=[CHANNEL_WELCOME])
async def dogbomb(ctx, member:str=False):
    """Dog bombs someone!"""
    if member == False:
        return await ctx.send("Tell me who you want to dog bomb!! :dog:")
    doggo = await get_doggo()
    await ctx.send(doggo)
    await ctx.send(f"{member}, <@{ctx.message.author.id}> dog bombed you!!")

@bot.command()
@not_blacklisted_channel(blacklist=[CHANNEL_WELCOME])
async def shibabomb(ctx, member:str=False):
    """Shiba bombs a user!"""
    if member == False:
        return await ctx.send("Tell me who you want to shiba bomb!! :dog:")
    doggo = await get_shiba()
    await ctx.send(doggo)
    await ctx.send(f"{member}, <@{ctx.message.author.id}> shiba bombed you!!")

@bot.command()
async def me(ctx, *args):
    """Replaces the good ol' /me"""
    await ctx.message.delete()
    if len(args) < 1:
        return await ctx.send(f"*{ctx.message.author.mention} " + "is cool!*")
    else:
        await ctx.send(f"*{ctx.message.author.mention} " + " ".join(arg for arg in args) + "*")

@bot.command(aliases=["list"])
async def list_command(ctx, cmd:str=False):
    """Lists all of the commands a user may access."""
    if cmd == False: # for quick list of commands
        ls = await get_quick_list(ctx)
        await ctx.send(embed=ls)
    if cmd == "all" or cmd == "commands":
        ls = await get_list(ctx.message.author, 1)
        sent_list = await ctx.send(embed=ls)
        await sent_list.add_reaction(EMOJI_FAST_REVERSE)
        await sent_list.add_reaction(EMOJI_LEFT_ARROW)
        await sent_list.add_reaction(EMOJI_RIGHT_ARROW)
        await sent_list.add_reaction(EMOJI_FAST_FORWARD)
    elif cmd == "states":
        states_list = await get_state_list()
        list = assemble_embed(
            title="List of all states",
            desc="\n".join([f"`{state}`" for state in states_list])
        )
        await ctx.send(embed=list)
    elif cmd == "events":
        events_list = [r['eventName'] for r in EVENT_INFO]
        list = assemble_embed(
            title="List of all events",
            desc="\n".join([f"`{name}`" for name in events_list])
        )
        await ctx.send(embed=list)

@bot.command()
async def school(ctx, title, state):
    lists = await get_school_listing(title, state)
    fields = []
    if len(lists) > 20:
        return await ctx.send(f"Woah! Your query returned `{len(lists)}` schools, which is too much to send at once. Try narrowing your query!")
    for l in lists:
        fields.append({'name': l['name'], 'value': f"```{l['wikicode']}```", 'inline': "False"})
    embed = assemble_embed(
        title="School Data",
        desc=f"Your query for `{title}` in `{state}` returned `{len(lists)}` results. Thanks for contribtuing to the wiki!",
        fields=fields,
        hexcolor="#2E66B6"
    )
    await ctx.send(embed=embed)

async def censor(message):
    """Constructs Pi-Bot's censor."""
    channel = message.channel
    ava = message.author.avatar_url
    wh = await channel.create_webhook(name="Censor (Automated)")
    content = message.content
    for word in CENSORED_WORDS:
        content = re.sub(fr'\b({word})\b', "<censored>", content, flags=re.IGNORECASE)
    for word in CENSORED_EMOJIS:
        content = re.sub(fr"{word}", "<censored>", content, flags=re.I)
    author = message.author.nick
    if author == None:
        author = message.author.name
    # Make sure pinging through @everyone, @here, or any role can not happen
    mention_perms = discord.AllowedMentions(everyone=False, users=True, roles=False)
    await wh.send(content, username=(author + " (auto-censor)"), avatar_url=ava, allowed_mentions=mention_perms)
    await wh.delete()

@bot.command()
@commands.check(is_staff)
async def kick(ctx, user:discord.Member, reason:str=False):
    """Kicks a user for the specified reason."""
    if reason == False:
        return await ctx.send("Please specify a reason why you want to kick this user!")
    if user.id in PI_BOT_IDS:
        return await ctx.send("Hey! You can't kick me!!")
    await user.kick(reason=reason)
    await ctx.send("The user was kicked.")

@bot.command()
@commands.check(is_staff)
async def met(ctx):
    """Runs Pi-Bot's Most Edits Table"""
    msg1 = await ctx.send("Attemping to run the Most Edits Table.")
    res = await run_table()
    print(res)
    names = [v['name'] for v in res]
    data = [v['increase'] for v in res]
    names = names[:10]
    data = data[:10]

    fig = plt.figure()
    plt.bar(names, data, color="#2E66B6")
    plt.xlabel("Usernames")
    plt.xticks(rotation=90)
    plt.ylabel("Edits past week")
    plt.title("Top wiki editors for the past week!")
    plt.tight_layout()
    plt.savefig("met.png")
    plt.close()
    await msg1.delete()
    msg2 = await ctx.send("Generating graph...")
    await asyncio.sleep(3)
    await msg2.delete()

    file = discord.File("met.png", filename="met.png")
    embed = assemble_embed(
        title="**Top wiki editors for the past week!**",
        desc=("Check out the past week's top wiki editors! Thank you all for your contributions to the wiki! :heart:\n\n" +
        f"`1st` - **{names[0]}** ({data[0]} edits)\n" +
        f"`2nd` - **{names[1]}** ({data[1]} edits)\n" +
        f"`3rd` - **{names[2]}** ({data[2]} edits)\n" +
        f"`4th` - **{names[3]}** ({data[3]} edits)\n" +
        f"`5th` - **{names[4]}** ({data[4]} edits)"),
        imageUrl="attachment://met.png",
    )
    await ctx.send(file=file, embed=embed)

@bot.command()
@commands.check(is_staff)
async def prepembed(ctx, channel:discord.TextChannel, *, jsonInput):
    """Helps to create an embed to be sent to a channel."""
    jso = json.loads(jsonInput)
    title = jso['title'] if 'title' in jso else ""
    desc = jso['description'] if 'description' in jso else ""
    titleUrl = jso['titleUrl'] if 'titleUrl' in jso else ""
    hexcolor = jso['hexColor'] if 'hexColor' in jso else "#2E66B6"
    webcolor = jso['webColor'] if 'webColor' in jso else ""
    thumbnailUrl = jso['thumbnailUrl'] if 'thumbnailUrl' in jso else ""
    authorName = jso['authorName'] if 'authorName' in jso else ""
    authorUrl = jso['authorUrl'] if 'authorUrl' in jso else ""
    authorIcon = jso['authorIcon'] if 'authorIcon' in jso else ""
    if 'author' in jso:
        authorName = ctx.message.author.name
        authorIcon = ctx.message.author.avatar_url_as(format="jpg")
    fields = jso['fields'] if 'fields' in jso else ""
    footerText = jso['footerText'] if 'footerText' in jso else ""
    footerUrl = jso['footerUrl'] if 'footerUrl' in jso else ""
    imageUrl = jso['imageUrl'] if 'imageUrl' in jso else ""
    embed = assemble_embed(
        title=title,
        desc=desc,
        titleUrl=titleUrl,
        hexcolor=hexcolor,
        webcolor=webcolor,
        thumbnailUrl=thumbnailUrl,
        authorName=authorName,
        authorUrl=authorUrl,
        authorIcon=authorIcon,
        fields=fields,
        footerText=footerText,
        footerUrl=footerUrl,
        imageUrl=imageUrl
    )
    await channel.send(embed=embed)

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

@bot.command(aliases=["feedbear"])
@not_blacklisted_channel(blacklist=[CHANNEL_WELCOME])
async def fish(ctx):
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

@bot.command(aliases=["badbear"])
@not_blacklisted_channel(blacklist=[CHANNEL_WELCOME])
async def stealfish(ctx):
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

@bot.command(aliases=["slap", "trouts", "slaps", "troutslaps"])
@not_blacklisted_channel(blacklist=[CHANNEL_WELCOME])
async def trout(ctx, member:str=False):
    if await sanitize_mention(member) == False:
        return await ctx.send("Woah... looks like you're trying to be a little sneaky with what you're telling me to do. Not so fast!")
    if member == False:
        await ctx.send(f"{ctx.message.author.mention} trout slaps themselves!")
    else:
        await ctx.send(f"{ctx.message.author.mention} slaps {member} with a giant trout!")
    await ctx.send("http://gph.is/1URFXN9")

@bot.command(aliases=["givecookie"])
@not_blacklisted_channel(blacklist=[CHANNEL_WELCOME])
async def cookie(ctx, member:str=False):
    if await sanitize_mention(member) == False:
        return await ctx.send("Woah... looks like you're trying to be a little sneaky with what you're telling me to do. You can't ping roles or everyone.")
    if member == False:
        await ctx.send(f"{ctx.message.author.mention} gives themselves a cookie.")
    else:
        await ctx.send(f"{ctx.message.author.mention} gives {member} a cookie!")
    await ctx.send("http://gph.is/1UOaITh")

@bot.command()
@not_blacklisted_channel(blacklist=[CHANNEL_WELCOME])
async def treat(ctx):
    await ctx.send("You give bernard one treat!")
    await ctx.send("http://gph.is/11nJAH5")

@bot.command(aliases=["givehershey", "hershey"])
@not_blacklisted_channel(blacklist=[CHANNEL_WELCOME])
async def hersheybar(ctx, member:str=False):
    if await sanitize_mention(member) == False:
        return await ctx.send("Woah... looks like you're trying to be a little sneaky with what you're telling me to do. You can't ping roles or everyone.")
    if member == False:
        await ctx.send(f"{ctx.message.author.mention} gives themselves a Hershey bar.")
    else:
        await ctx.send(f"{ctx.message.author.mention} gives {member} a Hershey bar!")
    await ctx.send("http://gph.is/2rt64CX")

@bot.command(aliases=["giveicecream"])
@not_blacklisted_channel(blacklist=[CHANNEL_WELCOME])
async def icecream(ctx, member:str=False):
    if await sanitize_mention(member) == False:
        return await ctx.send("Woah... looks like you're trying to be a little sneaky with what you're telling me to do. You can't ping roles or everyone.")
    if member == False:
        await ctx.send(f"{ctx.message.author.mention} gives themselves some ice cream.")
    else:
        await ctx.send(f"{ctx.message.author.mention} gives {member} ice cream!")
    await ctx.send("http://gph.is/YZLMMs")

async def sanitize_mention(member):
    if member == False: return True
    if member == "@everyone" or member == "@here": return False
    if member[:3] == "<@&": return False
    return True

@bot.command(aliases=["div"])
async def division(ctx, div):
    if div.lower() == "a":
        res = await assign_div(ctx, "Division A")
        await ctx.send("Assigned you the Division A role, and removed all other division/alumni roles.")
    elif div.lower() == "b":
        res = await assign_div(ctx, "Division B")
        await ctx.send("Assigned you the Division B role, and removed all other division/alumni roles.")
    elif div.lower() == "c":
        res = await assign_div(ctx, "Division C")
        await ctx.send("Assigned you the Division C role, and removed all other division/alumni roles.")
    elif div.lower() == "d":
        await ctx.send("This server does not have a Division D role. Instead, use the `!alumni` command!")
    elif div.lower() in ["remove", "clear", "none", "x"]:
        member = ctx.message.author
        div_a_role = discord.utils.get(member.guild.roles, name=ROLE_DIV_A)
        div_b_role = discord.utils.get(member.guild.roles, name=ROLE_DIV_B)
        div_c_role = discord.utils.get(member.guild.roles, name=ROLE_DIV_C)
        await member.remove_roles(div_a_role, div_b_role, div_c_role)
        await ctx.send("Removed all of your division/alumni roles.")
    else:
        return await ctx.send("Sorry, I don't seem to see that division. Try `!division c` to assign the Division C role, or `!division d` to assign the Division D role.")

async def assign_div(ctx, div):
    """Assigns a user a div"""
    member = ctx.message.author
    role = discord.utils.get(member.guild.roles, name=div)
    div_a_role = discord.utils.get(member.guild.roles, name=ROLE_DIV_A)
    div_b_role = discord.utils.get(member.guild.roles, name=ROLE_DIV_B)
    div_c_role = discord.utils.get(member.guild.roles, name=ROLE_DIV_C)
    alumni_role = discord.utils.get(member.guild.roles, name=ROLE_ALUMNI)
    await member.remove_roles(div_a_role, div_b_role, div_c_role, alumni_role)
    await member.add_roles(role)
    return True

@bot.command()
async def alumni(ctx):
    """Removes or adds the alumni role from a user."""
    member = ctx.message.author
    div_a_role = discord.utils.get(member.guild.roles, name=ROLE_DIV_A)
    div_b_role = discord.utils.get(member.guild.roles, name=ROLE_DIV_B)
    div_c_role = discord.utils.get(member.guild.roles, name=ROLE_DIV_C)
    await member.remove_roles(div_a_role, div_b_role, div_c_role)
    role = discord.utils.get(member.guild.roles, name=ROLE_ALUMNI)
    if role in member.roles:
        await member.remove_roles(role)
        await ctx.send("Removed your alumni status.")
    else:
        await member.add_roles(role)
        await ctx.send(f"Added the alumni role, and removed all other division roles.")

@bot.command()
async def wiki(ctx, command:str=False, *args):
    # Check to make sure not too much at once
    if not command:
        return await ctx.send("<https://scioly.org/wiki>")
    if len(args) > 7:
        return await ctx.send("Slow down there buster. Please keep the command to 12 or less arguments at once.")
    multiple = False
    for arg in args:
        if arg[:1] == "-":
            multiple = arg.lower() == "-multiple"
    if command in ["summary"]:
        if multiple:
            for arg in [arg for arg in args if arg[:1] != "-"]:
                text = await implement_command("summary", arg)
                if text == False:
                    await ctx.send(f"The `{arg}` page does not exist!")
                else:
                    await ctx.send(" ".join(text))
        else:
            string_sum = " ".join([arg for arg in args if arg[:1] != "-"])
            text = await implement_command("summary", string_sum)
            if text == False:
                await ctx.send(f"The `{arg}` page does not exist!")
            else:
                await ctx.send(" ".join(text))
    elif command in ["search"]:
        if multiple:
            return await ctx.send("Ope! No multiple searches at once yet!")
        searches = await implement_command("search", " ".join([arg for arg in args]))
        await ctx.send("\n".join([f"`{s}`" for s in searches]))
    else:
        # Assume link
        if multiple:
            new_args = [command] + list(args)
            for arg in [arg for arg in new_args if arg[:1] != "-"]:
                url = await implement_command("link", arg)
                if url == False:
                    await ctx.send(f"The `{arg}` page does not exist!")
                await ctx.send(f"<{wiki_url_fix(url)}>")
        else:
            string_sum = " ".join([arg for arg in args if arg[:1] != "-"])
            if len(args) > 0 and command.rstrip() != "link":
                string_sum = f"{command} {string_sum}"
            elif command.rstrip() != "link":
                string_sum = command
            url = await implement_command("link", string_sum)
            if url == False:
                await ctx.send(f"The `{string_sum}` page does not exist!")
            else:
                await ctx.send(f"<{wiki_url_fix(url)}>")

def wiki_url_fix(url):
    return url.replace("%3A", ":").replace(r"%2F","/")

@bot.command(aliases=["wp"])
async def wikipedia(ctx, request:str=False, *args):
    term = " ".join(args)
    if request == False:
        return await ctx.send("You must specifiy a command and keyword, such as `!wikipedia search \"Science Olympiad\"`")
    if request == "search":
        return await ctx.send("\n".join([f"`{result}`" for result in aiowikip.search(term, results=5)]))
    elif request == "summary":
        try:
            term = term.title()
            page = await aiowikip.page(term)
            return await ctx.send(aiowikip.summary(term, sentences=3) + f"\n\nRead more on Wikipedia here: <{page.url}>!")
        except wikip.exceptions.DisambiguationError as e:
            return await ctx.send(f"Sorry, the `{term}` term could refer to multiple pages, try again using one of these terms:" + "\n".join([f"`{o}`" for o in e.options]))
        except wikip.exceptions.PageError as e:
            return await ctx.send(f"Sorry, but the `{term}` page doesn't exist! Try another term!")
    else:
        try:
            term = f"{request} {term}".strip()
            term = term.title()
            page = await aiowikip.page(term)
            return await ctx.send(f"Sure, here's the link: <{page.url}>")
        except wikip.exceptions.PageError as e:
            return await ctx.send(f"Sorry, but the `{term}` page doesn't exist! Try another term!")
        except wikip.exceptions.DisambiguationError as e:
            return await ctx.send(f"Sorry, but the `{term}` page is a disambiguation page. Please try again!")

@bot.command()
async def profile(ctx, name:str=False):
    if name == False:
        member = ctx.message.author
        name = member.nick
        if name == None:
            name = member.name
    elif name.find("<@") != -1:
        iden = await harvest_id(name)
        member = ctx.message.author.guild.get_member(int(iden))
        name = member.nick
        if name == None:
            name = member.name
    embed = assemble_embed(
        title=f"Scioly.org Information for {name}",
        desc=(f"[`Forums`](https://scioly.org/forums/memberlist.php?mode=viewprofile&un={name}) | [`Wiki`](https://scioly.org/wiki/index.php?title=User:{name})"),
        hexcolor="#2E66B6"
    )
    await ctx.send(embed=embed)

@bot.command()
async def latex(ctx, *args):
    new_args = " ".join(args)
    print(new_args)
    new_args = new_args.replace(" ", r"&space;")
    print(new_args)
    await ctx.send(r"https://latex.codecogs.com/png.latex?\dpi{150}{\color{Gray}" + new_args + "}")

@bot.command(aliases=["membercount"])
async def count(ctx):
    guild = ctx.message.author.guild
    await ctx.send(f"Currently, there are `{len(guild.members)}` members in the server.")

@bot.command()
@commands.check(is_staff)
async def exalt(ctx, user):
    """Exalts a user."""
    member = ctx.message.author
    role = discord.utils.get(member.guild.roles, name=ROLE_EM)
    iden = await harvest_id(user)
    user_obj = member.guild.get_member(int(iden))
    await user_obj.add_roles(role)
    await ctx.send(f"Successfully exalted. Congratulations {user}! :tada: :tada:")

@bot.command()
@commands.check(is_staff)
async def unexalt(ctx, user):
    """Unexalts a user."""
    member = ctx.message.author
    role = discord.utils.get(member.guild.roles, name=ROLE_EM)
    iden = await harvest_id(user)
    user_obj = member.guild.get_member(int(iden))
    await user_obj.remove_roles(role)
    await ctx.send(f"Successfully unexalted.")

@bot.command()
@commands.check(is_staff)
async def mute(ctx, user:discord.Member, *args):
    """
    Mutes a user.

    :param user: User to be muted.
    :type user: discord.Member
    :param *args: The time to mute the user for.
    :type *args: str
    """
    time = " ".join(args)
    await _mute(ctx, user, time, self=False)

@bot.command()
async def selfmute(ctx, *args):
    """
    Self mutes the user that invokes the command.

    :param *args: The time to mute the user for.
    :type *args: str
    """
    user = ctx.message.author
    if await is_staff(ctx):
        return await ctx.send("Staff members can't self mute.")
    time = " ".join(args)
    await _mute(ctx, user, time, self=True)

async def _mute(ctx, user:discord.Member, time: str, self: bool):
    """
    Helper function for muting commands.

    :param user: User to be muted.
    :type user: discord.Member
    :param time: The time to mute the user for.
    :type time: str
    """
    if user.id in PI_BOT_IDS:
        return await ctx.send("Hey! You can't mute me!!")
    if time == None:
        return await ctx.send("You need to specify a length that this used will be muted. Examples are: `1 day`, `2 months, 1 day`, or `indef` (aka, forever).")
    role = None
    if self:
        role = discord.utils.get(user.guild.roles, name=ROLE_SELFMUTE)
    else:
        role = discord.utils.get(user.guild.roles, name=ROLE_MUTED)
    parsed = "indef"
    if time != "indef":
        parsed = dateparser.parse(time, settings={"PREFER_DATES_FROM": "future"})
        if parsed == None:
            return await ctx.send("Sorry, but I don't understand that length of time.")
        CRON_LIST.append({"date": parsed, "do": f"unmute {user.id}"})
    await user.add_roles(role)
    eastern = pytz.timezone("US/Eastern")
    await ctx.send(f"Successfully muted {user.mention} until `{str(eastern.localize(parsed))} EST`.")

@bot.command()
@commands.check(is_staff)
async def unmute(ctx, user):
    """Unmutes a user."""
    member = ctx.message.author
    role = discord.utils.get(member.guild.roles, name=ROLE_MUTED)
    iden = await harvest_id(user)
    user_obj = member.guild.get_member(int(iden))
    await user_obj.remove_roles(role)
    await ctx.send(f"Successfully unmuted {user}.")

@bot.command()
@commands.check(is_staff)
async def ban(ctx, member:discord.User=None, reason=None, *args):
    """Bans a user."""
    time = " ".join(args)
    if member == None or member == ctx.message.author:
        return await ctx.channel.send("You cannot ban yourself! >:(")
    if reason == None:
        return await ctx.send("You need to give a reason for you banning this user.")
    if time == None:
        return await ctx.send("You need to specify a length that this used will be banned. Examples are: `1 day`, `2 months, 1 day`, or `indef` (aka, forever).")
    if member.id in PI_BOT_IDS:
        return await ctx.send("Hey! You can't ban me!!")
    message = f"You have been banned from the Scioly.org Discord server for {reason}."
    parsed = "indef"
    if time != "indef":
        parsed = dateparser.parse(time, settings={"PREFER_DATES_FROM": "future"})
        if parsed == None:
            return await ctx.send(f"Sorry, but I don't understand the length of time: `{time}`.")
        CRON_LIST.append({"date": parsed, "do": f"unban {member.id}"})
    await member.send(message)
    await ctx.guild.ban(member, reason=reason)
    eastern = pytz.timezone("US/Eastern")
    await ctx.channel.send(f"**{member}** is banned until `{str(eastern.localize(parsed))} EST`.")

@bot.command()
@commands.check(is_staff)
async def unban(ctx, member:discord.User=None):
    """Unbans a user."""
    if member == None:
        await ctx.channel.send("Please give either a user ID or mention a user.")
        return
    await ctx.guild.unban(member)
    await ctx.channel.send(f"Inverse ban hammer applied, user unbanned. Please remember that I cannot force them to re-join the server, they must join themselves.")

@bot.command()
@commands.check(is_staff)
async def archive(ctx):
    tournament = [t for t in TOURNAMENT_INFO if t[1] == ctx.channel.name]
    bot_spam = discord.utils.get(ctx.guild.text_channels, name = CHANNEL_BOTSPAM)
    archive_cat = discord.utils.get(ctx.guild.categories, name = CATEGORY_ARCHIVE)
    tournament_name, tournament_formal = None, None
    if len(tournament) > 0:
        tournament_name = tournament[0][1]
        tournament_formal = tournament[0][0]
    tournament_role = discord.utils.get(ctx.guild.roles, name = tournament_formal)
    all_tourney_role = discord.utils.get(ctx.guild.roles, name = ROLE_AT)
    embed = assemble_embed(
        title = 'This channel is now archived.',
        desc = (f'Thank you all for your discussion around the {tournament_formal}. Now that we are well past the tournament date, we are going to close this channel to help keep tournament discussions relevant and on-topic.\n\n' + 
        f'If you have more questions/comments related to this tournament, you are welcome to bring them up in {ctx.channel.mention}. This channel is now read-only.\n\n' +
        f'If you would like to no longer view this channel, you are welcome to type `!tournament {tournament_name}` into {bot_spam}, and the channel will disappear for you. Members with the `All Tournaments` role will continue to see the channel.'),
        webcolor='red'
    )
    await ctx.channel.set_permissions(tournament_role, send_messages = False, view_channel = True)
    await ctx.channel.set_permissions(all_tourney_role, send_messages = False, view_channel = True)
    await ctx.channel.edit(category = archive_cat, position = 1000)
    await ctx.channel.send(embed = embed)
    await ctx.message.delete()

@bot.command()
async def pronouns(ctx, *args):
    """Assigns or removes pronoun roles from a user."""
    member = ctx.message.author
    if len(args) < 1:
        await ctx.send(f"{member.mention}, please specify a pronoun to add/remove. Current options include `!pronouns he`, `!pronouns she`, and `!pronouns they`.")
    he_role = discord.utils.get(member.guild.roles, name=ROLE_PRONOUN_HE)
    she_role = discord.utils.get(member.guild.roles, name=ROLE_PRONOUN_SHE)
    they_role = discord.utils.get(member.guild.roles, name=ROLE_PRONOUN_THEY)
    for arg in args:
        if arg.lower() in ["he", "him", "his", "he / him / his"]:
            if he_role in member.roles:
                await ctx.send("Oh, looks like you already have the He / Him / His role. Removing it.")
                await member.remove_roles(he_role)
            else:
                await member.add_roles(he_role)
                await ctx.send("Added the He / Him / His role.")
        elif arg.lower() in ["she", "her", "hers", "she / her / hers"]:
            if she_role in member.roles:
                await ctx.send("Oh, looks like you already have the She / Her / Hers role. Removing it.")
                await member.remove_roles(she_role)
            else:
                await member.add_roles(she_role)
                await ctx.send("Added the She / Her / Hers role.")
        elif arg.lower() in ["they", "them", "their", "they / them / their"]:
            if they_role in member.roles:
                await ctx.send("Oh, looks like you already have the They / Them / Theirs role. Removing it.")
                await member.remove_roles(they_role)
            else:
                await member.add_roles(they_role)
                await ctx.send("Added the They / Them / Theirs role.")
        elif arg.lower() in ["remove", "clear", "delete", "nuke"]:
            await member.remove_roles(he_role, she_role, they_role)
            return await ctx.send("Alrighty, your pronouns have been removed.")
        elif arg.lower() in ["help", "what"]:
            return await ctx.send("For help with pronouns, please use `!help pronouns`.")
        else:
            return await ctx.send(f"Sorry, I don't recognize the `{arg}` pronoun. The pronoun roles we currently have are:\n" +
            "> `!pronouns he  ` (which gives you *He / Him / His*)\n" +
            "> `!pronouns she ` (which gives you *She / Her / Hers*)\n" +
            "> `!pronouns they` (which gives you *They / Them / Theirs*)\n" +
            "To remove pronouns, use `!pronouns remove`.\n" +
            "Feel free to request alternate pronouns, by opening a report, or reaching out a staff member.")

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

@bot.command()
@commands.check(is_staff)
async def clrreact(ctx, msg: discord.Message, *args: discord.Member):
    """
    Clears all reactions from a given message.

    :param msg: the message containing the reactions
    :type msg: discord.Message
    :param *args: list of users to clear reactions of
    :type *args: List[discord.Member], optional
    """
    users = args
    if (not users):
        await msg.clear_reactions()
        await ctx.send("Cleared all reactions on message.")
    else:
        for u in users:
            for r in msg.reactions:
                await r.remove(u)
        await ctx.send(f"Cleared reactions on message from {len(users)} user(s).")

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
    # Log DMs
    if type(message.channel) == discord.DMChannel:
        await send_to_dm_log(message)
    else:
        # Print to output
        if not (message.author.id in PI_BOT_IDS and message.channel.name in [CHANNEL_EDITEDM, CHANNEL_DELETEDM, CHANNEL_DMLOG]):
            # avoid sending logs for messages in log channels
            print(f'Message from {message.author} in #{message.channel}: {message.content}')

    # Prevent command usage in channels outside of #bot-spam
    author = message.author
    if type(message.channel) != discord.DMChannel and message.content.startswith(BOT_PREFIX) and author.roles[-1] == discord.utils.get(author.guild.roles, name=ROLE_MR):
        if message.channel.name != CHANNEL_BOTSPAM:
            allowedCommands = ["about", "dogbomb", "exchange", "gallery", "invite", "me", "magic8ball", "latex", "obb", "profile", "r", "report", "rule", "shibabomb", "tag", "wiki", "wikipedia", "wp"]
            allowed = False
            for c in allowedCommands:
                if message.content.find(BOT_PREFIX + c) != -1: allowed = True
            if not allowed:
                botspam_channel = discord.utils.get(message.guild.text_channels, name=CHANNEL_BOTSPAM)
                clarify_message = await message.channel.send(f"{author.mention}, please use bot commands only in {botspam_channel.mention}. If you have more questions, you can ping a global moderator.")
                await asyncio.sleep(10)
                await clarify_message.delete()
                return await message.delete()

    if message.author.id in PI_BOT_IDS: return
    content = message.content
    for word in CENSORED_WORDS:
        if len(re.findall(fr"\b({word})\b", content, re.I)):
            print(f"Censoring message by {message.author} because of the word: `{word}`")
            await message.delete()
            await censor(message)
    for word in CENSORED_EMOJIS:
        if len(re.findall(fr"{word}", content)):
            print(f"Censoring message by {message.author} because of the emoji: `{word}`")
            await message.delete()
            await censor(message)
    if not any(ending for ending in DISCORD_INVITE_ENDINGS if ending in message.content) and (len(re.findall("discord.gg", content, re.I)) > 0 or len(re.findall("discord.com/invite", content, re.I)) > 0):
        print(f"Censoring message by {message.author} because of the it mentioned a Discord invite link.")
        await message.delete()
        ssChannel = discord.utils.get(message.author.guild.text_channels, name=CHANNEL_SUPPORT)
        await message.channel.send(f"*Links to external Discord servers can not be sent in accordance with rule 12. If you have questions, please ask in {ssChannel.mention}.*")
    pingable = True
    if message.content[:1] == "!" or message.content[:1] == "?" or message.content[:2] == "pb" or message.content[:2] == "bp":
        pingable = False
    if message.channel.id == 724125653212987454:
        # If the message is coming from #bot-spam
        pingable = False
    if pingable:
        for user in PING_INFO:
            if user['id'] == message.author.id:
                continue
            pings = user['pings']
            for ping in pings:
                if len(re.findall(ping, content, re.I)) > 0 and message.author.discriminator != "0000":
                    # Do not send a ping if the user is mentioned
                    user_is_mentioned = user['id'] in [m.id for m in message.mentions]
                    if user['id'] in [m.id for m in message.channel.members] and ('dnd' not in user or user['dnd'] != True) and not user_is_mentioned:
                        # Check that the user can actually see the message
                        name = message.author.nick
                        if name == None:
                            name = message.author.name
                        await ping_pm(user['id'], name, ping, message.channel.name, message.content, message.jump_url)
    # SPAM TESTING
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
        await auto_report("User was auto-muted (spam)", "red", f"A user ({str(message.author)}) was auto muted in {message.channel.mention} because of repeated spamming.")
    elif RECENT_MESSAGES.count({"author": message.author.id, "content": message.content.lower()}) >= 3:
        await message.channel.send(f"{message.author.mention}, please watch the spam. You will be muted if you do not stop.")
    # Caps checker
    elif sum(1 for m in RECENT_MESSAGES if m['author'] == message.author.id and m['caps']) > 8 and caps:
        muted_role = discord.utils.get(message.author.guild.roles, name=ROLE_MUTED)
        parsed = dateparser.parse("1 hour", settings={"PREFER_DATES_FROM": "future"})
        CRON_LIST.append({"date": parsed, "do": f"unmute {message.author.id}"})
        await message.author.add_roles(muted_role)
        await message.channel.send(f"Successfully muted {message.author.mention} for 1 hour.")
        await auto_report("User was auto-muted (caps)", "red", f"A user ({str(message.author)}) was auto muted in {message.channel.mention} because of repeated caps.")
    elif sum(1 for m in RECENT_MESSAGES if m['author'] == message.author.id and m['caps']) > 3 and caps:
        await message.channel.send(f"{message.author.mention}, please watch the caps, or else I will lay down the mute hammer!")

    # Do not treat messages with only exclamations as command
    if message.content.count(BOT_PREFIX) != len(message.content):
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
            await auto_report("Innapropriate Username Detected", "red", f"A new member ({str(member)}) has joined the server, and I have detected that their username is innapropriate.")
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
            await auto_report("Innapropriate Username Detected", "red", f"A member ({str(after)}) has updated their nickname to **{after.nick}**, which the censor caught as innapropriate.")

@bot.event
async def on_user_update(before, after):
    for word in CENSORED_WORDS:
        if len(re.findall(fr"\b({word})\b", after.name, re.I)):
            await auto_report("Innapropriate Username Detected", "red", f"A member ({str(member)}) has updated their nickname to **{after.name}**, which the censor caught as innapropriate.")

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
    if isinstance(error, NoDMsAllowed):
        return await ctx.send("Pings require direct messages to be sent to you. You need to turn on \"Allow direct messages from server members.\"")
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

async def lookup_role(name):
    name = name.title()
    if name == "Al" or name == "Alabama": return "Alabama"
    elif name == "All" or name == "All States": return "All States"
    elif name == "Ak" or name == "Alaska": return "Alaska"
    elif name == "Ar" or name == "Arkansas": return "Arkansas"
    elif name == "Az" or name == "Arizona": return "Arizona"
    elif name == "Cas" or name == "Ca-S" or name == "California (South)" or name == "Socal" or name == "California South" or name == "california-north": return "California (South)"
    elif name == "Can" or name == "Ca-N" or name == "California (North)" or name == "Nocal" or name == "California North" or name == "california-south": return "California (North)"
    if name == "Co" or name == "Colorado": return "Colorado"
    elif name == "Ct" or name == "Connecticut": return "Connecticut"
    elif name == "Dc" or name == "District Of Columbia" or name == "district-of-columbia": return "District of Columbia"
    elif name == "De" or name == "Delaware": return "Delaware"
    elif name == "Fl" or name == "Florida": return "Florida"
    elif name == "Ga" or name == "Georgia": return "Georgia"
    elif name == "Hi" or name == "Hawaii": return "Hawaii"
    elif name == "Id" or name == "Idaho": return "Idaho"
    elif name == "Il" or name == "Illinois": return "Illinois"
    elif name == "In" or name == "Indiana": return "Indiana"
    elif name == "Ia" or name == "Iowa": return "Iowa"
    elif name == "Ks" or name == "Kansas": return "Kansas"
    elif name == "Ky" or name == "Kentucky": return "Kentucky"
    elif name == "La" or name == "Louisiana": return "Louisiana"
    elif name == "Me" or name == "Maine": return "Maine"
    elif name == "Md" or name == "Maryland": return "Maryland"
    elif name == "Ma" or name == "Massachusetts": return "Massachusetts"
    elif name == "Mi" or name == "Michigan": return "Michigan"
    elif name == "Mn" or name == "Minnesota": return "Minnesota"
    elif name == "Ms" or name == "Mississippi": return "Mississippi"
    elif name == "Mo" or name == "Missouri": return "Missouri"
    elif name == "Mt" or name == "Montana": return "Montana"
    elif name == "Ne" or name == "Nebraska": return "Nebraska"
    elif name == "Nv" or name == "Nevada": return "Nevada"
    elif name == "Nh" or name == "New Hampshire": return "New Hampshire"
    elif name == "Nj" or name == "New Jersey": return "New Jersey"
    elif name == "Nm" or name == "New Mexico": return "New Mexico"
    elif name == "Ny" or name == "New York": return "New York"
    elif name == "Nc" or name == "North Carolina": return "North Carolina"
    elif name == "Nd" or name == "North Dakota": return "North Dakota"
    elif name == "Oh" or name == "Ohio": return "Ohio"
    elif name == "Ok" or name == "Oklahoma": return "Oklahoma"
    elif name == "Or" or name == "Oregon": return "Oregon"
    elif name == "Pa" or name == "Pennsylvania": return "Pennsylvania"
    elif name == "Ri" or name == "Rhode Island": return "Rhode Island"
    elif name == "Sc" or name == "South Carolina": return "South Carolina"
    elif name == "Sd" or name == "South Dakota": return "South Dakota"
    elif name == "Tn" or name == "Tennessee": return "Tennessee"
    elif name == "Tx" or name == "Texas": return "Texas"
    elif name == "Ut" or name == "Utah": return "Utah"
    elif name == "Vt" or name == "Vermont": return "Vermont"
    elif name == "Va" or name == "Virginia": return "Virginia"
    elif name == "Wa" or name == "Washington": return "Washington"
    elif name == "Wv" or name == "West Virginia": return "West Virginia"
    elif name == "Wi" or name == "Wisconsin": return "Wisconsin"
    elif name == "Wy" or name == "Wyoming": return "Wyoming"
    return False

async def harvest_id(user):
    return user.replace("<@!", "").replace(">", "")

if dev_mode:
    bot.run(DEV_TOKEN)
else:
    bot.run(TOKEN)
