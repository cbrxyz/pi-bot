import discord
import os
import asyncio
import requests
import re
import json
import random
import math
import datetime
import dateparser
import time as timePackage
import wikipedia as wikip
import matplotlib.pyplot as plt
import numpy as np
from aioify import aioify
from dotenv import load_dotenv
from discord import channel
from discord.ext import commands, tasks

from src.sheets.events import getEvents
from src.sheets.tournaments import getTournamentChannels
from src.sheets.censor import getCensor
from src.sheets.sheets import sendVariables, getVariables, getTags
from src.forums.forums import openBrowser
from src.wiki.stylist import prettifyTemplates
from src.wiki.tournaments import getTournamentList
from src.wiki.wiki import implementCommand, getPageTables
from src.wiki.schools import getSchoolListing
from src.wiki.scilympiad import makeResultsTemplate, getPoints
from src.wiki.mosteditstable import runTable
from info import getAbout
from doggo import getDoggo, getShiba
from bear import getBearMessage
from embed import assembleEmbed
from commands import getList, getQuickList, getHelp
from lists import getStateList

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
DEV_TOKEN = os.getenv('DISCORD_DEV_TOKEN')
devMode = os.getenv('DEV_MODE') == "TRUE"

##############
# SERVER VARIABLES
##############

# Roles
ROLE_WM = "Wiki/Gallery Moderator"
ROLE_GM = "Global Moderator"
ROLE_AD = "Administrator"
ROLE_VIP = "VIP"
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

# Categories
CATEGORY_TOURNAMENTS = "tournaments"
CATEGORY_SO = "Science Olympiad"
CATEGORY_STATES = "states"
CATEGORY_GENERAL = "general"

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

if devMode:
    bot = commands.Bot(command_prefix=("?"), case_insensitive=True, intents=intents)
    SERVER_ID = int(os.getenv('DEV_SERVER_ID'))
else:
    bot = commands.Bot(command_prefix=("!"), case_insensitive=True, intents=intents)
    SERVER_ID = 698306997287780363

##############
# CHECKS
##############

async def isBear(ctx):
    """Checks to see if the user is bear, or pepperonipi (for debugging purposes)."""
    return ctx.message.author.id == 353730886577160203 or ctx.message.author.id == 715048392408956950

async def isStaff(ctx):
    """Checks to see if the user is a staff member."""
    member = ctx.message.author
    wmRole = discord.utils.get(member.guild.roles, name=ROLE_WM)
    gmRole = discord.utils.get(member.guild.roles, name=ROLE_GM)
    aRole = discord.utils.get(member.guild.roles, name=ROLE_AD)
    vipRole = discord.utils.get(member.guild.roles, name=ROLE_VIP)
    if wmRole in member.roles or gmRole in member.roles or aRole in member.roles or vipRole in member.roles: return True

async def isLauncher(ctx):
    """Checks to see if the user is a launch helper."""
    member = ctx.message.author
    staff = await isStaff(ctx)
    lhRole = discord.utils.get(member.guild.roles, name=ROLE_LH)
    if staff or lhRole in member.roles: return True

async def isAdmin(ctx):
    """Checks to see if the user is an administrator, or pepperonipi (for debugging purposes)."""
    member = ctx.message.author
    aRole = discord.utils.get(member.guild.roles, name=ROLE_AD)
    if aRole in member.roles or member.id == 715048392408956950: return True

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
DISCORD_INVITE_ENDINGS = ["9Z5zKtV", "C9PGV6h", "s4kBmas", "ftPTxhC", "gh3aXbq", "skGQXd4", "RnkqUbK"]

##############
# VARIABLES
##############
fishNow = 0
canPost = False
doHourlySync = False
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
    await pullPrevInfo()
    await updateTournamentList()
    refreshSheet.start()
    postSomething.start()
    cron.start()
    goStylist.start()
    storeVariables.start()
    changeBotStatus.start()

@tasks.loop(seconds=30.0)
async def refreshSheet():
    """Refreshes the censor list and stores variable backups."""
    await refreshAlgorithm()
    await prepareForSending()
    print("Attempted to refresh/store data from/to sheet.")

@tasks.loop(hours=10)
async def storeVariables():
    await prepareForSending("store")

@tasks.loop(hours=24)
async def goStylist():
    await prettifyTemplates()

@tasks.loop(minutes=1)
async def cron():
    print("Executed cron.")
    global CRON_LIST
    print(CRON_LIST)
    for c in CRON_LIST:
        date = c['date']
        if datetime.datetime.now() > date:
            # The date has passed, now do
            CRON_LIST.remove(c)
            await handleCron(c['do'])

async def handleCron(string):
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
            await member.remove_roles(role)
            print(f"Unmuted user ID: {iden}")
        elif string.find("unstealfishban") != -1:
            iden = int(string.split(" ")[1])
            STEALFISH_BAN.remove(iden)
            print(f"Un-stealfished user ID: {iden}")
        else:
            print("ERROR:")
            await autoReport("Error with a cron task", "red", f"Error: `{string}`")
    except Exception as e:
        await autoReport("Error with a cron task", "red", f"Error: `{e}`\nOriginal task: `{string}`")

@tasks.loop(hours=1)
async def changeBotStatus():
    botStatus = math.floor(random.random() * 24)
    if botStatus == 0:
        await bot.change_presence(activity=discord.Game(name="Game On"))
    elif botStatus == 1:
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="my SoM instrument"))
    elif botStatus == 2:
        await bot.change_presence(activity=discord.Game(name="with Pi-Bot Beta"))
    elif botStatus == 3:
        await bot.change_presence(activity=discord.Game(name="with my gravity vehicle"))
    elif botStatus == 4:
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="the WS trials"))
    elif botStatus == 5:
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="birds"))
    elif botStatus == 6:
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="2018 Nationals again"))
    elif botStatus == 7:
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="the sparkly stars"))
    elif botStatus == 8:
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="over the wiki"))
    elif botStatus == 9:
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="for tourney results"))
    elif botStatus == 10:
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="birb sounds"))
    elif botStatus == 11:
        await bot.change_presence(activity=discord.Game(name="with proteins"))
    elif botStatus == 12:
        await bot.change_presence(activity=discord.Game(name="with my detector"))
    elif botStatus == 13:
        await bot.change_presence(activity=discord.Game(name="Minecraft"))
    elif botStatus == 14:
        await bot.change_presence(activity=discord.Game(name="with circuits"))
    elif botStatus == 15:
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="my PPP fall"))
    elif botStatus == 16:
        await bot.change_presence(activity=discord.Game(name="a major scale"))
    elif botStatus == 17:
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="clinking medals"))
    elif botStatus == 18:
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="the world learn"))
    elif botStatus == 19:
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="SciOly grow"))
    elif botStatus == 20:
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="tutorials"))
    elif botStatus == 21:
        await bot.change_presence(activity=discord.Game(name="with wiki templates"))
    elif botStatus == 22:
        await bot.change_presence(activity=discord.Game(name="the flute"))
    elif botStatus == 23:
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="bear eat users"))
    print("Changed the bot's status.")

@tasks.loop(hours=28)
async def postSomething():
    global canPost
    """Allows Pi-Bot to post markov-generated statements to the forums."""
    if canPost:
        print("Attempting to post something.")
        await openBrowser()
    else:
        canPost = True

async def refreshAlgorithm():
    """Pulls data from the administrative sheet."""
    global CENSORED_WORDS
    global CENSORED_EMOJIS
    global EVENT_INFO
    global TAGS
    censor = await getCensor()
    CENSORED_WORDS = censor[0]
    CENSORED_EMOJIS = censor[1]
    EVENT_INFO = await getEvents()
    TAGS = await getTags()
    print("Refreshed data from sheet.")
    return True

async def prepareForSending(type="variable"):
    """Sends local variables to the administrative sheet as a backup."""
    r1 = json.dumps(REPORT_IDS)
    r2 = json.dumps(PING_INFO)
    r3 = json.dumps(TOURNEY_REPORT_IDS)
    r4 = json.dumps(COACH_REPORT_IDS)
    r5 = json.dumps(CRON_LIST, default = datetimeConverter)
    r6 = json.dumps(REQUESTED_TOURNAMENTS)
    await sendVariables([[r1], [r2], [r3], [r4], [r5], [r6]], type)
    print("Stored variables in sheet.")

def datetimeConverter(o):
    if isinstance(o, datetime.datetime):
        return o.__str__()

async def pullPrevInfo():
    data = await getVariables()
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
        c['date'] = datetime.datetime.strptime(c['date'], "%Y-%m-%d %H:%M:%S.%f")
    CRON_LIST = cron
    REQUESTED_TOURNAMENTS = data[5][0]
    print("Fetched previous variables.")

@bot.command(aliases=["tc", "tourney", "tournaments"])
async def tournament(ctx, *args):
    member = ctx.message.author
    newArgs = list(args)
    ignoreTerms = ["invitational", "invy", "tournament", "regional", "invite"]
    for term in ignoreTerms:
        if term in newArgs:
            newArgs.remove(term)
            await ctx.send(f"Ignoring `{term}` because it is too broad of a term. *(If you need help with this command, please type `!help tournament`)*")
    if len(args) == 0:
        return await ctx.send("Please specify the tournaments you would like to be added/removed from!")
    for arg in newArgs:
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
                await autoReport("New Tournament Channel Requested", "orange", f"User ID {uid} requested tournament channel `#{arg}`.\n\nTo add this channel to the voting list for the first time, use `!tla {arg} {uid}`.\nIf the channel has already been requested in the list and this was a user mistake, use `!tla [actual name] {uid}`.")
                return await ctx.send(f"Made request for a `#{arg}` channel. Please note your submission may not instantly appear.")
            await ctx.send(f"Added a vote for `{arg}`. There " + ("are" if votes != 1 else "is") + f" now `{votes}` " + (f"votes" if votes != 1 else f"vote") + " for this channel.")
            await updateTournamentList()

@bot.command()
@commands.check(isStaff)
async def tla(ctx, iden, uid):
    global REQUESTED_TOURNAMENTS
    for t in REQUESTED_TOURNAMENTS:
        if t['iden'] == iden:
            t['count'] += 1
            await ctx.send(f"Added a vote for {iden} from {uid}. Now has `{t['count']}` votes.")
            return await updateTournamentList()
    REQUESTED_TOURNAMENTS.append({'iden': iden, 'count': 1, 'users': [uid]})
    await updateTournamentList()
    return await ctx.send(f"Added a vote for {iden} from {uid}. Now has `1` vote.")

@bot.command()
@commands.check(isStaff)
async def tlr(ctx, iden):
    global REQUESTED_TOURNAMENTS
    for t in REQUESTED_TOURNAMENTS:
        if t['iden'] == iden:
            REQUESTED_TOURNAMENTS.remove(t)
    await updateTournamentList()
    return await ctx.send(f"Removed `#{iden}` from the tournament list.")

async def updateTournamentList():
    tl = await getTournamentChannels()
    tl.sort(key=lambda x: x[0])
    global TOURNAMENT_INFO
    global REQUESTED_TOURNAMENTS
    TOURNAMENT_INFO = tl
    server = bot.get_guild(SERVER_ID)
    tourneyChannel = discord.utils.get(server.text_channels, name=CHANNEL_TOURNAMENTS)
    tourneyCat = discord.utils.get(server.categories, name=CATEGORY_TOURNAMENTS)
    botSpam = discord.utils.get(server.text_channels, name=CHANNEL_BOTSPAM)
    serverSupport = discord.utils.get(server.text_channels, name=CHANNEL_SUPPORT)
    gm = discord.utils.get(server.roles, name=ROLE_GM)
    a = discord.utils.get(server.roles, name=ROLE_AD)
    allTournamentsRole = discord.utils.get(server.roles, name=ROLE_AT)
    stringList = ""
    openSoonList = ""
    channelsRequestedList = ""
    now = datetime.datetime.now()
    for t in tl: # For each tournament in the sheet
        # Add the listing to the embed
        print(f"Tournament List: Handling {t[0]}")

        # Check if the channel needs to be made / deleted
        ch = discord.utils.get(server.text_channels, name=t[1])
        r = discord.utils.get(server.roles, name=t[0])
        tourneyDate = t[4]
        beforeDays = int(t[5])
        afterDays = int(t[6])
        tDDT = datetime.datetime.strptime(tourneyDate, "%Y-%m-%d")
        dayDiff = (tDDT - now).days
        print(f"Tournament List: Day diff for {t[0]} is {dayDiff} days.")
        if (dayDiff < (-1 * afterDays)) and ch != None:
            # If past tournament date, now out of range
            await autoReport("Tournament Channel & Role Needs to be Deleted", "orange", f"The {ch.mention} channel and {r.mention} role need to be deleted, as it is after the tournament date.")
        elif (dayDiff <= beforeDays) and ch == None:
            # If before tournament and in range
            newRole = await server.create_role(name=t[0])
            newCh = await server.create_text_channel(t[1], category=tourneyCat)
            await newCh.edit(topic=f"{t[2]} - Discussion around the {t[0]} occurring on {t[4]}.", sync_permissions=True)
            await newCh.set_permissions(newRole, read_messages=True)
            await newCh.set_permissions(allTournamentsRole, read_messages=True)
            await newCh.set_permissions(server.default_role, read_messages=False)
            stringList += (t[2] + " **" + t[0] + "** - `!tournament " + t[1] + "`\n")
        elif ch != None:
            stringList += (t[2] + " **" + t[0] + "** - `!tournament " + t[1] + "`\n")
        elif (dayDiff > beforeDays):
            openSoonList += (t[2] + " **" + t[0] + f"** - Opens in `{dayDiff - beforeDays}` days.\n")
    REQUESTED_TOURNAMENTS.sort(key=lambda x: (-x['count'], x['iden']))
    spacingNeeded = max([len(t['iden']) for t in REQUESTED_TOURNAMENTS])
    for t in REQUESTED_TOURNAMENTS:
        spaces = " " * (spacingNeeded - len(t['iden']))
        channelsRequestedList += f"`!tournament {t['iden']}{spaces}` · **{t['count']} votes**\n"
    embeds = []
    embeds.append(assembleEmbed(
        title=":medal: Tournament Channels Listing",
        desc=(
            "Below is a list of **tournament channels**. Some are available right now, some will be available soon, and others have been requested, but have not received 10 votes to be considered for a channel." + 
            f"\n\n* To join an available tournament channel, head to {botSpam.mention} and type `!tournament [name]`." + 
            f"\n\n* To make a new request for a tournament channel, head to {botSpam.mention} and type `!tournament [name]`, where `[name]` is the name of the tournament channel you would like to have created." +
            f"\n\n* Need help? Ping a {gm.mention} or {a.mention}, or ask in {serverSupport.mention}"
        )
    ))
    embeds.append(assembleEmbed(
        title="Currently Available Channels",
        desc=stringList if len(stringList) > 0 else "No channels are available currently."
    ))
    embeds.append(assembleEmbed(
        title="Channels Opening Soon",
        desc=openSoonList if len(openSoonList) > 0 else "No channels are opening soon currently.",
    ))
    embeds.append(assembleEmbed(
        title="Channels Requested",
        desc=("Vote with the command associated with the tournament channel.\n\n" + channelsRequestedList) if len(channelsRequestedList) > 0 else f"No channels have been requested currently. To make a request for a tournament channel, head to {botSpam.mention} and type `!tournament [name]`, with the name of the tournament."
    ))
    hist = await tourneyChannel.history(oldest_first=True).flatten()
    if len(hist) == 4:
        count = 0
        async for m in tourneyChannel.history(oldest_first=True):
            await m.edit(embed=embeds[count])
            count += 1
    else:
        pastMessages = await tourneyChannel.history(limit=100).flatten()
        await tourneyChannel.delete_messages(pastMessages)
        for e in embeds:
            await tourneyChannel.send(embed=e)

@bot.command()
@commands.check(isStaff)
async def vc(ctx):
    server = ctx.message.guild
    if ctx.message.channel.category.name == CATEGORY_TOURNAMENTS:
        testVC = discord.utils.get(server.voice_channels, name=ctx.message.channel.name)
        if testVC == None:
            # Voice channel needs to be opened
            newVC = await server.create_voice_channel(ctx.message.channel.name, category=ctx.message.channel.category)
            await newVC.edit(sync_permissions=True)
            # Make the channel invisible to normal members
            await newVC.set_permissions(server.default_role, view_channel=False)
            at = discord.utils.get(server.roles, name=ROLE_AT)
            for t in TOURNAMENT_INFO:
                if ctx.message.channel.name == t[1]:
                    tourneyRole = discord.utils.get(server.roles, name=t[0])
                    await newVC.set_permissions(tourneyRole, view_channel=True)
                    break
            await newVC.set_permissions(at, view_channel=True)
            return await ctx.send("Created a voice channel. **Please remember to follow the rules! No doxxing or cursing is allowed.**")
        else:
            # Voice channel needs to be closed
            await testVC.delete()
            return await ctx.send("Closed the voice channel.")
    elif ctx.message.channel.name == "games":
        # Support for opening a voice channel for #games
        testVC = discord.utils.get(server.voice_channels, name="games")
        if testVC == None:
            # Voice channel needs to be opened/doesn't exist already
            newVC = await server.create_voice_channel("games", category=ctx.message.channel.category)
            await newVC.edit(sync_permissions=True)
            await newVC.set_permissions(server.default_role, view_channel=False)
            gamesRole = discord.utils.get(server.roles, name=ROLE_GAMES)
            memberRole = discord.utils.get(server.roles, name=ROLE_MR)
            await newVC.set_permissions(gamesRole, view_channel=True)
            await newVC.set_permissions(memberRole, view_channel=False)
            return await ctx.send("Created a voice channel. **Please remember to follow the rules! No doxxing or cursing is allowed.**")
        else:
            # Voice channel needs to be closed
            await testVC.delete()
            return await ctx.send("Closed the voice channel.")
    else:
        return await ctx.send("Apologies... voice channels can currently be opened for tournament channels and the games channel.")

@bot.command()
@commands.check(isStaff)
async def getVariable(ctx, var):
    """Fetches a local variable."""
    if ctx.message.channel.id != 724125340733145140:
        await ctx.send("You can only fetch variables from the staff channel.")
    else:
        await ctx.send("Attempting to find variable.")
        try:
            variable = globals()[var]
            await ctx.send(f"Variable value: `{variable}`")
        except:
            await ctx.send(f"Can't find that variable!")

@bot.command(aliases=["eats", "beareats"])
@commands.check(isBear)
async def eat(ctx, user):
    """Allows bear to eat users >:D"""
    message = await getBearMessage(user)
    await ctx.send(message)

@bot.command()
@commands.check(isStaff)
async def refresh(ctx):
    """Refreshes data from the sheet."""
    await updateTournamentList()
    res = await refreshAlgorithm()
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

@bot.command(aliases=["ui"])
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

@bot.command(aliases=["hi"])
async def hello(ctx):
    """Simply says hello. Used for testing the bot."""
    await ctx.send("Well, hello there.")

@bot.command(aliases=["what"])
async def about(ctx):
    """Prints information about the bot."""
    await ctx.send(getAbout())

@bot.command(aliases=["server", "link", "invitelink"])
async def invite(ctx):
    await ctx.send("https://discord.gg/C9PGV6h")

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
    await ctx.send("Giving you the Coach role...")
    member = ctx.message.author
    role = discord.utils.get(member.guild.roles, name="Coach")
    if role in member.roles:
        await ctx.send("Oops... you already have the Coach role. If it needs to be removed, please open a report using `!report \"message...\"`.")
    else:
        await member.add_roles(role)
        await autoReport("Member Applied for Coach Role", "DarkCyan", f"{ctx.message.author.name} applied for the Coach role. Please verify that they are a coach.")
        await ctx.send("Successfully gave you the Coach role, and sent a verification message to staff.")

@bot.command(aliases=["slow", "sm"])
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
    newArgs = [str(arg).lower() for arg in args]

    # Fix commas as possible separator
    if len(newArgs) == 1:
        newArgs = newArgs[0].split(",")
    newArgs = [re.sub("[;,]", "", arg) for arg in newArgs]

    member = ctx.message.author
    states = await getStateList()
    states = [s[:s.rfind(" (")] for s in states]
    tripleWordStates = [s for s in states if len(s.split(" ")) > 2]
    doubleWordStates = [s for s in states if len(s.split(" ")) > 1]
    removedRoles = []
    addedRoles = []
    for term in ["california", "ca", "cali"]:
        if term in [arg.lower() for arg in args]:
            return await ctx.send("Which California, North or South? Try `!state norcal` or `!state socal`.")
    if len(newArgs) < 1:
        return await ctx.send("Sorry, but you need to specify a state (or multiple states) to add/remove.")
    elif len(newArgs) > 10:
        return await ctx.send("Sorry, you are attempting to add/remove too many states at once.")
    for string in ["South", "North"]:
        californiaList = [f"California ({string})", f"California-{string}", f"California {string}", f"{string}ern California", f"{string} California", f"{string} Cali", f"Cali {string}", f"{string} CA", f"CA {string}"]
        if string == "North":
            californiaList.append("NorCal")
        else:
            californiaList.append("SoCal")
        for listing in californiaList:
            words = listing.split(" ")
            allHere = sum(1 for word in words if word.lower() in newArgs)
            if allHere == len(words):
                role = discord.utils.get(member.guild.roles, name=f"California ({string})")
                if role in member.roles:
                    await member.remove_roles(role)
                    removedRoles.append(f"California ({string})")
                else:
                    await member.add_roles(role)
                    addedRoles.append(f"California ({string})")
                for word in words:
                    newArgs.remove(word.lower())
    for triple in tripleWordStates:
        words = triple.split(" ")
        allHere = 0
        allHere = sum(1 for word in words if word.lower() in newArgs)
        if allHere == 3:
            # Word is in args
            role = discord.utils.get(member.guild.roles, name=triple)
            if role in member.roles:
                await member.remove_roles(role)
                removedRoles.append(triple)
            else:
                await member.add_roles(role)
                addedRoles.append(triple)
            for word in words:
                newArgs.remove(word.lower())
    for double in doubleWordStates:
        words = double.split(" ")
        allHere = 0
        allHere = sum(1 for word in words if word.lower() in newArgs)
        if allHere == 2:
            # Word is in args
            role = discord.utils.get(member.guild.roles, name=double)
            if role in member.roles:
                await member.remove_roles(role)
                removedRoles.append(double)
            else:
                await member.add_roles(role)
                addedRoles.append(double)
            for word in words:
                newArgs.remove(word.lower())
    for arg in newArgs:
        roleName = await lookupRole(arg)
        if roleName == False:
            return await ctx.send(f"Sorry, the {arg} state could not be found. Try again.")
        role = discord.utils.get(member.guild.roles, name=roleName)
        if role in member.roles:
            await member.remove_roles(role)
            removedRoles.append(roleName)
        else:
            await member.add_roles(role)
            addedRoles.append(roleName)
    if len(addedRoles) > 0 and len(removedRoles) == 0:
        stateRes = "Added states " + (' '.join([f'`{arg}`' for arg in addedRoles])) + "."
    elif len(removedRoles) > 0 and len(addedRoles) == 0:
        stateRes = "Removed states " + (' '.join([f'`{arg}`' for arg in removedRoles])) + "."
    else:
        stateRes = "Added states " + (' '.join([f'`{arg}`' for arg in addedRoles])) + ", and removed states " + (' '.join([f'`{arg}`' for arg in removedRoles])) + "."
    await ctx.send(stateRes)

@bot.command()
async def games(ctx):
    """Removes or adds someone to the games channel."""
    jbcObj = discord.utils.get(ctx.message.author.guild.text_channels, name=CHANNEL_GAMES)
    member = ctx.message.author
    role = discord.utils.get(member.guild.roles, name=ROLE_GAMES)
    if role in member.roles:
        await member.remove_roles(role)
        await ctx.send("Removed you from the games club... feel free to come back anytime!")
        await jbcObj.send(f"{member.mention} left the party.")
    else:
        await member.add_roles(role)
        await ctx.send(f"You are now in the channel. Come and have fun in {jbcObj.mention}! :tada:")
        await jbcObj.send(f"Please welcome {member.mention} to the party!!")

@bot.command(aliases=["tags", "t"])
async def tag(ctx, name):
    member = ctx.message.author
    if len(TAGS) == 0:
        return await ctx.send("Apologies, tags do not appear to be working at the moment. Please try again in one minute.")
    staff = await isStaff(ctx)
    lh_role = discord.utils.get(member.guild.roles, name=ROLE_LH)
    member_role = discord.utils.get(member.guild.roles, name=ROLE_MR)
    for t in TAGS:
        if t['name'] == name:
            if staff or (t['launch_helpers'] and lh_role in member.roles) or (t['members'] and member_role in member.roles):
                return await ctx.send(t['text'])
            else:
                return await ctx.send("Unfortunately, you do not have the permissions for this tag.")
    return await ctx.send("Tag not found.")

@bot.command()
@commands.check(isStaff)
async def lock(ctx):
    """Locks a channel to Member access."""
    member = ctx.message.author
    channel = ctx.message.channel

    if (channel.category.name in ["beta", "staff", "Pi-Bot"]):
        return await ctx.send("This command is not suitable for this channel because of its category.")

    memberRole = discord.utils.get(member.guild.roles, name=ROLE_MR)
    if (channel.category.name == CATEGORY_STATES):
        await ctx.channel.set_permissions(memberRole, add_reactions=False, send_messages=False)
    else:
        await ctx.channel.set_permissions(memberRole, add_reactions=False, send_messages=False, read_messages=True)

    wikiRole = discord.utils.get(member.guild.roles, name=ROLE_WM)
    gmRole = discord.utils.get(member.guild.roles, name=ROLE_GM)
    aRole = discord.utils.get(member.guild.roles, name=ROLE_AD)
    bRole = discord.utils.get(member.guild.roles, name=ROLE_BT)
    await ctx.channel.set_permissions(wikiRole, add_reactions=True, send_messages=True, read_messages=True)
    await ctx.channel.set_permissions(gmRole, add_reactions=True, send_messages=True, read_messages=True)
    await ctx.channel.set_permissions(aRole, add_reactions=True, send_messages=True, read_messages=True)
    await ctx.channel.set_permissions(bRole, add_reactions=True, send_messages=True, read_messages=True)
    await ctx.send("Locked the channel to Member access.")

@bot.command()
@commands.check(isStaff)
async def unlock(ctx):
    """Unlocks a channel to Member access."""
    member = ctx.message.author
    channel = ctx.message.channel

    if (channel.category.name in ["beta", "staff", "Pi-Bot"]):
        return await ctx.send("This command is not suitable for this channel because of its category.")

    if (channel.category.name == CATEGORY_SO or channel.category.name == CATEGORY_GENERAL):
        await ctx.send("Synced permissions with channel category.")
        return await channel.edit(sync_permissions=True)

    memberRole = discord.utils.get(member.guild.roles, name=ROLE_MR)
    if (channel.category.name != CATEGORY_STATES):
        await ctx.channel.set_permissions(memberRole, add_reactions=True, send_messages=True, read_messages=True)
    else:
        await ctx.channel.set_permissions(memberRole, add_reactions=True, send_messages=True)

    wikiRole = discord.utils.get(member.guild.roles, name=ROLE_WM)
    gmRole = discord.utils.get(member.guild.roles, name=ROLE_GM)
    aRole = discord.utils.get(member.guild.roles, name=ROLE_AD)
    bRole = discord.utils.get(member.guild.roles, name=ROLE_BT)
    await ctx.channel.set_permissions(wikiRole, add_reactions=True, send_messages=True, read_messages=True)
    await ctx.channel.set_permissions(gmRole, add_reactions=True, send_messages=True, read_messages=True)
    await ctx.channel.set_permissions(aRole, add_reactions=True, send_messages=True, read_messages=True)
    await ctx.channel.set_permissions(bRole, add_reactions=True, send_messages=True, read_messages=True)
    await ctx.send("Unlocked the channel to Member access. Please check if permissions need to be synced.")

@bot.command(aliases=["r"])
async def report(ctx, *args):
    """Creates a report that is sent to staff members."""
    if len(args) > 1:
        return await ctx.send("Please report one message wrapped in double quotes. (`!report \"Message!\"`)")
    message = args[0]
    poster = str(ctx.message.author)
    reportsChannel = discord.utils.get(ctx.message.author.guild.text_channels, name="reports")
    embed = assembleEmbed(
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
    message = await reportsChannel.send(embed=embed)
    REPORT_IDS.append(message.id)
    await message.add_reaction("\U00002705")
    await message.add_reaction("\U0000274C")
    await ctx.send("Thanks, report created.")

# Meant for Pi-Bot only
async def autoReport(reason, color, message):
    """Allows Pi-Bot to generate a report by himself."""
    server = bot.get_guild(SERVER_ID)
    reportsChannel = discord.utils.get(server.text_channels, name="reports")
    embed = assembleEmbed(
        title=f"{reason} (message from Pi-Bot)",
        webcolor=color,
        fields = [{
            "name": "Message",
            "value": message,
            "inline": False
        }]
    )
    message = await reportsChannel.send(embed=embed)
    REPORT_IDS.append(message.id)
    await message.add_reaction("\U00002705")
    await message.add_reaction("\U0000274C")

@bot.command()
async def graphpage(ctx, title, tempFormat, tableIndex, div, placeCol=0):
    temp = tempFormat.lower() in ["y", "yes", "true"]
    await ctx.send(
        "*Inputs read:*\n" +
        f"Page title: `{title}`\n" +
        f"Template: `{temp}`\n" +
        f"Table index (staring at 0): `{tableIndex}`\n" +
        f"Division: `{div}`\n" +
        (f"Column with point values: `{placeCol}`" if not temp else "")
    )
    points = []
    tableIndex = int(tableIndex)
    placeCol = int(placeCol)
    if temp:
        template = await getPageTables(title, True)
        template = [t for t in template if t.normal_name() == "State results box"]
        template = template[tableIndex]
        ordinal = lambda n: "%d%s" % (n,"tsnrhtdd"[(n//10%10!=1)*(n%10<4)*n%10::4]) # Thanks https://codegolf.stackexchange.com/questions/4707/outputting-ordinal-numbers-1st-2nd-3rd#answer-4712
        for i in range(100):
            if template.has_arg(ordinal(i) + "_points"):
                points.append(template.get_arg(ordinal(i) + "_points").value.replace("\n", ""))
    else:
        tables = await getPageTables(title, False)
        tables = tables[tableIndex]
        data = tables.data()
        points = [r[placeCol] for r in data]
        del points[0]
    points = [int(p) for p in points]
    await _graph(points, title + " - Division " + div, title + "Div" + div + ".svg")
    with open(title + "Div" + div + ".svg") as f:
        pic = discord.File(f)
        await ctx.send(file=pic)
    return await ctx.send("Attempted to graph.")

@bot.command()
async def graphscilympiad(ctx, url, title):
    points = await getPoints(url)
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
    res = await makeResultsTemplate(url)
    with open("resultstemplate.txt", "w+") as t:
        t.write(res)
    file = discord.File("resultstemplate.txt", filename="resultstemplate.txt")
    await ctx.send(file=file)

@bot.command()
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
        ignoredList = []
        if any([True for u in PING_INFO if u['id'] == member]):
            #yes
            user = next((u for u in PING_INFO if u['id'] == member), None)
            pings = user['pings']
            for arg in args:
                try:
                    re.findall(arg, "test phrase")
                except:
                    await ctx.send(f"Ignoring adding the `{arg}` ping because it uses illegal characters.")
                    ignoredList.append(arg)
                    continue
                if f"({arg})" in pings or f"\\b({arg})\\b" in pings or arg in pings:
                    await ctx.send(f"Ignoring adding the `{arg}` ping because you already have a ping currently set as that.")
                    ignoredList.append(arg)
                else:
                    if command.lower() in ["add", "new"]:
                        print("adding word")
                        pings.append(fr"\b({arg})\b")
                    else:
                        print("adding regexp")
                        pings.append(fr"({arg})")
        else:
            # nope
            if command.lower() in ["add", "new"]:
                PING_INFO.append({
                    "id": member,
                    "pings": [fr"\b({arg})\b" for arg in args]
                })
            else:
                PING_INFO.append({
                    "id": member,
                    "pings": [fr"({arg})" for arg in args]
                })
        return await ctx.send(f"Alrighty... I've got you all set up for the following pings: " + (" ".join([f"`{arg}`" for arg in args if arg not in ignoredList])))
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
            regexPings = []
            wordPings = []
            for ping in pings:
                if ping[:2] == "\\b":
                    wordPings.append(ping)
                else:
                    regexPings.append(ping)
            if len(regexPings) > 0:
                await ctx.send("Your RegEx pings are: " + ", ".join([f"`{regex}`" for regex in regexPings]))
            if len(wordPings) > 0:
                await ctx.send("Your word pings are: " + ", ".join([f"`{word[3:-3]}`" for word in wordPings]))
    elif command.lower() in ["test", "try"]:
        user = next((u for u in PING_INFO if u['id'] == member), None)
        usersPings = user['pings']
        matched = False
        for arg in args:
            for ping in usersPings:
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

async def pingPM(userID, pinger, pingExp, channel, content, jumpUrl):
    """Allows Pi-Bot to PM a user about a ping."""
    userToSend = bot.get_user(userID)
    try:
        content = re.sub(rf'{pingExp}', r'**\1**', content, flags=re.I)
    except Exception as e:
        print(f"Could not bold ping due to unfavored RegEx. Error: {e}")
    pingExp = pingExp.replace(r"\b(", "").replace(r")\b", "")
    warning = f"\n\nIf you don't want this ping anymore, in `#bot-spam` on the server, send `!ping remove {pingExp}`"
    embed = assembleEmbed(
        title=":bellhop: Ping Alert!",
        desc=(f"Looks like `{pinger}` pinged a ping expression of yours in the Scioly.org Discord Server!" + warning),
        fields=[
            {"name": "Expression Matched", "value": f" `{pingExp}`", "inline": "True"},
            {"name": "Jump To Message", "value": f"[Click here!]({jumpUrl})", "inline": "True"},
            {"name": "Channel", "value": f"`#{channel}`", "inline": "True"},
            {"name": "Content", "value": content, "inline": "False"}
        ],
        hexcolor="#2E66B6"
    )
    await userToSend.send(embed=embed)

@bot.command(aliases=["doggobomb"])
async def dogbomb(ctx, member:str=False):
    """Dog bombs someone!"""
    if member == False:
        return await ctx.send("Tell me who you want to shiba bomb!! :dog:")
    doggo = await getDoggo()
    await ctx.send(doggo)
    await ctx.send(f"{member}, <@{ctx.message.author.id}> dog bombed you!!")

@bot.command()
async def shibabomb(ctx, member:str=False):
    """Shiba bombs a user!"""
    if member == False:
        return await ctx.send("Tell me who you want to shiba bomb!! :dog:")
    doggo = await getShiba()
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
        ls = await getQuickList(ctx)
        await ctx.send(embed=ls)
    if cmd == "all" or cmd == "commands":
        ls = await getList(ctx)
        await ctx.send(embed=ls)
    elif cmd == "states":
        statesList = await getStateList()
        list = assembleEmbed(
            title="List of all states",
            desc="\n".join([f"`{state}`" for state in statesList])
        )
        await ctx.send(embed=list)
    elif cmd == "events":
        eventsList = [r['eventName'] for r in EVENT_INFO]
        list = assembleEmbed(
            title="List of all events",
            desc="\n".join([f"`{name}`" for name in eventsList])
        )
        await ctx.send(embed=list)

@bot.command()
async def school(ctx, title, state):
    lists = await getSchoolListing(title, state)
    fields = []
    if len(lists) > 20:
        return await ctx.send(f"Woah! Your query returned `{len(lists)}` schools, which is too much to send at once. Try narrowing your query!")
    for l in lists:
        fields.append({'name': l['name'], 'value': f"```{l['wikicode']}```", 'inline': "False"})
    embed = assembleEmbed(
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
    # Make sure pinging through @everyone and @here can not happen
    content = re.sub(r'(?<!<)@', '\1\u200b', content)
    await wh.send(content, username=(author + " (auto-censor)"), avatar_url=ava)
    await wh.delete()

@bot.command()
@commands.check(isStaff)
async def kick(ctx, user:discord.Member, reason:str=False):
    """Kicks a user for the specified reason."""
    if reason == False:
        return await ctx.send("Please specify a reason why you want to kick this user!")
    if user.id in PI_BOT_IDS:
        return await ctx.send("Hey! You can't kick me!!")
    await user.kick(reason=reason)
    await ctx.send("The user was kicked.")

@bot.command()
@commands.check(isStaff)
async def met(ctx):
    """Runs Pi-Bot's Most Edits Table"""
    msg1 = await ctx.send("Attemping to run the Most Edits Table.")
    res = await runTable()
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
    await msg1.delete()
    msg2 = await ctx.send("Generating graph...")
    await asyncio.sleep(3)
    await msg2.delete()

    file = discord.File("met.png", filename="met.png")
    embed = assembleEmbed(
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
@commands.check(isStaff)
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
    embed = assembleEmbed(
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
    newArgs = [str(arg).lower() for arg in args]

    # Fix commas as possible separator
    if len(newArgs) == 1:
        newArgs = newArgs[0].split(",")
    newArgs = [re.sub("[;,]", "", arg) for arg in newArgs]

    eventInfo = EVENT_INFO
    eventNames = []
    removedRoles = []
    addedRoles = []
    couldNotHandle = []
    multiWordEvents = []

    if type(EVENT_INFO) == int:
        # When the bot starts up, EVENT_INFO is initialized to 0 before receiving the data from the sheet a few seconds later. This lets the user know this.
        return await ctx.send("Apologies... refreshing data currently. Try again in a few seconds.")

    for i in range(7, 1, -1):
        # Supports adding 7-word to 2-word long events
        multiWordEvents += [e['eventName'] for e in eventInfo if len(e['eventName'].split(" ")) == i]
        for event in multiWordEvents:
            words = event.split(" ")
            allHere = 0
            allHere = sum(1 for word in words if word.lower() in newArgs)
            if allHere == i:
                # Word is in args
                role = discord.utils.get(member.guild.roles, name=event)
                if role in member.roles:
                    await member.remove_roles(role)
                    removedRoles.append(event)
                else:
                    await member.add_roles(role)
                    addedRoles.append(event)
                for word in words:
                    newArgs.remove(word.lower())
    for arg in newArgs:
        foundEvent = False
        for event in eventInfo:
            aliases = [abbr.lower() for abbr in event['eventAbbreviations']]
            if arg.lower() in aliases or arg.lower() == event['eventName'].lower():
                eventNames.append(event['eventName'])
                foundEvent = True
                break
        if not foundEvent:
            couldNotHandle.append(arg)
    for event in eventNames:
        role = discord.utils.get(member.guild.roles, name=event)
        if role in member.roles:
            await member.remove_roles(role)
            removedRoles.append(event)
        else:
            await member.add_roles(role)
            addedRoles.append(event)
    if len(addedRoles) > 0 and len(removedRoles) == 0:
        eventRes = "Added events " + (' '.join([f'`{arg}`' for arg in addedRoles])) + ((", and could not handle: " + " ".join([f"`{arg}`" for arg in couldNotHandle])) if len(couldNotHandle) else "") + "."
    elif len(removedRoles) > 0 and len(addedRoles) == 0:
        eventRes = "Removed events " + (' '.join([f'`{arg}`' for arg in removedRoles])) + ((", and could not handle: " + " ".join([f"`{arg}`" for arg in couldNotHandle])) if len(couldNotHandle) else "") + "."
    else:
        eventRes = "Added events " + (' '.join([f'`{arg}`' for arg in addedRoles])) + ", " + ("and " if not len(couldNotHandle) else "") + "removed events " + (' '.join([f'`{arg}`' for arg in removedRoles])) + ((", and could not handle: " + " ".join([f"`{arg}`" for arg in couldNotHandle])) if len(couldNotHandle) else "") + "."
    await ctx.send(eventRes)

async def getWords():
    """Gets the censor list"""
    global CENSORED_WORDS
    CENSORED_WORDS = getCensor()

@bot.command(aliases=["man"])
async def help(ctx, command:str=None):
    """Allows a user to request help for a command."""
    if command == None:
        embed = assembleEmbed(
            title="Looking for help?",
            desc=("Hey there, I'm a resident bot of Scioly.org!\n\n" + 
            "On Discord, you can send me commands using `!` before the command name, and I will process it to help you! " + 
            "For example, `!states`, `!events`, and `!fish` are all valid commands that can be used!\n\n" + 
            "If you want to see some commands that you can use on me, just type `!list`! " + 
            "If you need more help, please feel free to reach out to a staff member!")
        )
        return await ctx.send(embed=embed)
    hlp = await getHelp(ctx, command)
    await ctx.send(embed=hlp)

@bot.command(aliases=["feedbear"])
async def fish(ctx):
    """Gives a fish to bear."""
    global fishNow
    r = random.random()
    if r > 0.99:
        fishNow = pow(fishNow, 2)
        return await ctx.send(f":tada:\n:tada:\n:tada:\nWow, you hit the jackbox! Bear's fish was squared! Bear now has {fishNow} fish! \n:tada:\n:tada:\n:tada:")
    if r > 0.9:
        fishNow += 10
        return await ctx.send(f"Wow, you gave bear a super fish! Added 10 fish! Bear now has {fishNow} fish!")
    if r > 0.1:
        fishNow += 1
        return await ctx.send(f"You feed bear one fish. Bear now has {fishNow} fish!")
    if r > 0.02:
        fishNow += 0
        return await ctx.send(f"You can't find any fish... and thus can't feed bear. Bear still has {fishNow} fish.")
    else:
        fishNow = round(pow(fishNow, 0.5))
        return await ctx.send(f":sob:\n:sob:\n:sob:\nAww, bear's fish was accidentally square root'ed. Bear now has {fishNow} fish. \n:sob:\n:sob:\n:sob:")

@bot.command()
async def nofish(ctx):
    """DEPRECATED - Removes all of bear's fish."""
    await ctx.send("`!nofish` no longer exists! Please use `!stealfish` instead.")

@bot.command(aliases=["badbear"])
async def stealfish(ctx):
    global fishNow
    member = ctx.message.author
    r = random.random()
    if member.id in STEALFISH_BAN:
        return await ctx.send("Hey! You've been banned from stealing fish for now.")
    if r >= 0.75:
        ratio = r - 0.5
        fishNow = round(fishNow * (1 - ratio))
        per = round(ratio * 100)
        return await ctx.send(f"You stole {per}% of bear's fish!")
    if r >= 0.416:
        parsed = dateparser.parse("1 hour", settings={"PREFER_DATES_FROM": "future"})
        STEALFISH_BAN.append(member.id)
        CRON_LIST.append({"date": parsed, "do": f"unstealfishban {member.id}"})
        return await ctx.send(f"Sorry {member.mention}, but it looks like you're going to banned from using this command for 1 hour!")
    if r >= 0.25:
        parsed = dateparser.parse("1 day", settings={"PREFER_DATES_FROM": "future"})
        STEALFISH_BAN.append(member.id)
        CRON_LIST.append({"date": parsed, "do": f"unstealfishban {member.id}"})
        return await ctx.send(f"Sorry {member.mention}, but it looks like you're going to banned from using this command for 1 day!")
    if r >= 0.01:
        return await ctx.send("Hmm, nothing happened. *crickets*")
    else:
        STEALFISH_BAN.append(member.id)
        return await ctx.send("You are banned from using `!stealfish` until the next version of Pi-Bot is released.")

@bot.command(aliases=["slap", "trouts", "slaps", "troutslaps"])
async def trout(ctx, member:str=False):
    if await sanitizeMention(member) == False:
        return await ctx.send("Woah... looks like you're trying to be a little sneaky with what you're telling me to do. Not so fast!")
    if member == False:
        await ctx.send(f"{ctx.message.author.mention} trout slaps themselves!")
    else:
        await ctx.send(f"{ctx.message.author.mention} slaps {member} with a giant trout!")
    await ctx.send("http://gph.is/1URFXN9")

@bot.command(aliases=["givecookie"])
async def cookie(ctx, member:str=False):
    if await sanitizeMention(member) == False:
        return await ctx.send("Woah... looks like you're trying to be a little sneaky with what you're telling me to do. You can't ping roles or everyone.")
    if member == False:
        await ctx.send(f"{ctx.message.author.mention} gives themselves a cookie.")
    else:
        await ctx.send(f"{ctx.message.author.mention} gives {member} a cookie!")
    await ctx.send("http://gph.is/1UOaITh")

@bot.command()
async def treat(ctx):
    await ctx.send("You give bernard one treat!")
    await ctx.send("http://gph.is/11nJAH5")

@bot.command(aliases=["givehershey", "hershey"])
async def hersheybar(ctx, member:str=False):
    if await sanitizeMention(member) == False:
        return await ctx.send("Woah... looks like you're trying to be a little sneaky with what you're telling me to do. You can't ping roles or everyone.")
    if member == False:
        await ctx.send(f"{ctx.message.author.mention} gives themselves a Hershey bar.")
    else:
        await ctx.send(f"{ctx.message.author.mention} gives {member} a Hershey bar!")
    await ctx.send("http://gph.is/2rt64CX")

@bot.command(aliases=["giveicecream"])
async def icecream(ctx, member:str=False):
    if await sanitizeMention(member) == False:
        return await ctx.send("Woah... looks like you're trying to be a little sneaky with what you're telling me to do. You can't ping roles or everyone.")
    if member == False:
        await ctx.send(f"{ctx.message.author.mention} gives themselves some ice cream.")
    else:
        await ctx.send(f"{ctx.message.author.mention} gives {member} ice cream!")
    await ctx.send("http://gph.is/YZLMMs")

async def sanitizeMention(member):
    if member == False: return True
    if member == "@everyone" or member == "@here": return False
    if member[:3] == "<@&": return False
    return True

@bot.command(aliases=["div"])
async def division(ctx, div):
    if div.lower() == "a":
        res = await assignDiv(ctx, "Division A")
        await ctx.send("Assigned you the Division A role, and removed all other divison/alumni roles.")
    elif div.lower() == "b":
        res = await assignDiv(ctx, "Division B")
        await ctx.send("Assigned you the Division B role, and removed all other divison/alumni roles.")
    elif div.lower() == "c":
        res = await assignDiv(ctx, "Division C")
        await ctx.send("Assigned you the Division C role, and removed all other divison/alumni roles.")
    elif div.lower() == "d":
        await ctx.send("This server does not have a Division D role. Instead, use the `!alumni` command!")
    elif div.lower() in ["remove", "clear", "none", "x"]:
        member = ctx.message.author
        divArole = discord.utils.get(member.guild.roles, name=ROLE_DIV_A)
        divBrole = discord.utils.get(member.guild.roles, name=ROLE_DIV_B)
        divCrole = discord.utils.get(member.guild.roles, name=ROLE_DIV_C)
        await member.remove_roles(divArole, divBrole, divCrole)
        await ctx.send("Removed all of your division/alumni roles.")
    else:
        return await ctx.send("Sorry, I don't seem to see that division. Try `!division c` to assign the Division C role, or `!division d` to assign the Division D role.")

async def assignDiv(ctx, div):
    """Assigns a user a div"""
    member = ctx.message.author
    role = discord.utils.get(member.guild.roles, name=div)
    divArole = discord.utils.get(member.guild.roles, name=ROLE_DIV_A)
    divBrole = discord.utils.get(member.guild.roles, name=ROLE_DIV_B)
    divCrole = discord.utils.get(member.guild.roles, name=ROLE_DIV_C)
    alumnirole = discord.utils.get(member.guild.roles, name=ROLE_ALUMNI)
    await member.remove_roles(divArole, divBrole, divCrole, alumnirole)
    await member.add_roles(role)
    return True

@bot.command()
async def alumni(ctx):
    """Removes or adds the alumni role from a user."""
    member = ctx.message.author
    divArole = discord.utils.get(member.guild.roles, name=ROLE_DIV_A)
    divBrole = discord.utils.get(member.guild.roles, name=ROLE_DIV_B)
    divCrole = discord.utils.get(member.guild.roles, name=ROLE_DIV_C)
    await member.remove_roles(divArole, divBrole, divCrole)
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
                text = await implementCommand("summary", arg)
                if text == False:
                    await ctx.send(f"The `{arg}` page does not exist!")
                else:
                    await ctx.send(" ".join(text))
        else:
            stringSum = " ".join([arg for arg in args if arg[:1] != "-"])
            text = await implementCommand("summary", stringSum)
            if text == False:
                await ctx.send(f"The `{arg}` page does not exist!")
            else:
                await ctx.send(" ".join(text))
    elif command in ["search"]:
        if multiple:
            return await ctx.send("Ope! No multiple searches at once yet!")
        searches = await implementCommand("search", " ".join([arg for arg in args]))
        await ctx.send("\n".join([f"`{s}`" for s in searches]))
    else:
        # Assume link
        if multiple:
            newArgs = [command] + list(args)
            for arg in [arg for arg in newArgs if arg[:1] != "-"]:
                url = await implementCommand("link", arg)
                if url == False:
                    await ctx.send(f"The `{arg}` page does not exist!")
                await ctx.send(f"<{wikiUrlFix(url)}>")
        else:
            stringSum = " ".join([arg for arg in args if arg[:1] != "-"])
            if len(args) > 0 and command.rstrip() != "link":
                stringSum = f"{command} {stringSum}"
            elif command.rstrip() != "link":
                stringSum = command
            url = await implementCommand("link", stringSum)
            if url == False:
                await ctx.send(f"The `{stringSum}` page does not exist!")
            else:
                await ctx.send(f"<{wikiUrlFix(url)}>")

def wikiUrlFix(url):
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
        iden = await harvestID(name)
        member = ctx.message.author.guild.get_member(int(iden))
        name = member.nick
        if name == None:
            name = member.name
    embed = assembleEmbed(
        title=f"Scioly.org Information for {name}",
        desc=(f"[`Forums`](https://scioly.org/forums/memberlist.php?mode=viewprofile&un={name}) | [`Wiki`](https://scioly.org/wiki/index.php?title=User:{name})"),
        hexcolor="#2E66B6"
    )
    await ctx.send(embed=embed)

@bot.command()
async def latex(ctx, *args):
    newArgs = " ".join(args)
    print(newArgs)
    newArgs = newArgs.replace(" ", r"&space;")
    print(newArgs)
    await ctx.send(r"https://latex.codecogs.com/png.latex?\dpi{150}{\color{Gray}" + newArgs + "}")

@bot.command(aliases=["membercount"])
async def count(ctx):
    guild = ctx.message.author.guild
    await ctx.send(f"Currently, there are `{len(guild.members)}` members in the server.")

@bot.command()
@commands.check(isStaff)
async def exalt(ctx, user):
    """Exalts a user."""
    member = ctx.message.author
    role = discord.utils.get(member.guild.roles, name=ROLE_EM)
    iden = await harvestID(user)
    userObj = member.guild.get_member(int(iden))
    await userObj.add_roles(role)
    await ctx.send(f"Successfully exalted. Congratulations {user}! :tada: :tada:")

@bot.command()
@commands.check(isStaff)
async def unexalt(ctx, user):
    """Unexalts a user."""
    member = ctx.message.author
    role = discord.utils.get(member.guild.roles, name=ROLE_EM)
    iden = await harvestID(user)
    userObj = member.guild.get_member(int(iden))
    await userObj.remove_roles(role)
    await ctx.send(f"Successfully unexalted.")

@bot.command()
@commands.check(isStaff)
async def mute(ctx, user:discord.Member, *args):
    """
    Mutes a user.

    :param user: User to be muted.
    :type user: discord.Member
    :param *args: The time to mute the user for.
    :type *args: str
    """
    time = " ".join(args)
    await _mute(ctx, user, time)

@bot.command()
async def selfmute(ctx, *args):
    """
    Self mutes the user that invokes the command.

    :param *args: The time to mute the user for.
    :type *args: str
    """
    user = ctx.message.author
    if await isStaff(ctx):
        return await ctx.send("Staff members can't self mute.")
    time = " ".join(args)
    await _mute(ctx, user, time)

async def _mute(ctx, user:discord.Member, time: str):
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
    role = discord.utils.get(user.guild.roles, name=ROLE_MUTED)
    parsed = "indef"
    if time != "indef":
        parsed = dateparser.parse(time, settings={"PREFER_DATES_FROM": "future", "TIMEZONE": "US/Eastern"})
        if parsed == None:
            return await ctx.send("Sorry, but I don't understand that length of time.")
        CRON_LIST.append({"date": parsed, "do": f"unmute {user.id}"})
    await user.add_roles(role)
    await ctx.send(f"Successfully muted {user.mention} until `{str(parsed)} EST`.")

@bot.command()
@commands.check(isStaff)
async def unmute(ctx, user):
    """Unmutes a user."""
    member = ctx.message.author
    role = discord.utils.get(member.guild.roles, name=ROLE_MUTED)
    iden = await harvestID(user)
    userObj = member.guild.get_member(int(iden))
    await userObj.remove_roles(role)
    await ctx.send(f"Successfully unmuted {user}.")

@bot.command()
@commands.check(isStaff)
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
        parsed = dateparser.parse(time, settings={"PREFER_DATES_FROM": "future", "TIMEZONE": "US/Eastern"})
        if parsed == None:
            return await ctx.send(f"Sorry, but I don't understand the length of time: `{time}`.")
        CRON_LIST.append({"date": parsed, "do": f"unban {member.id}"})
    await member.send(message)
    await ctx.guild.ban(member, reason=reason)
    await ctx.channel.send(f"**{member}** is banned until `{str(parsed)} EST`.")

@bot.command()
@commands.check(isStaff)
async def unban(ctx, id:int=0):
    """Unbans a user."""
    if id == 0:
        await ctx.channel.send("Please give a user ID.")
        return
    invite = await ctx.channel.create_invite(max_age = 86400)
    member = await bot.fetch_user(id)
    await ctx.guild.unban(member)
    await ctx.channel.send(f"Inverse ban hammer applied, user unbanned. Please remember that I cannot force them to re-join the server, they must join themselves.")

@bot.command()
async def pronouns(ctx, *args):
    """Assigns or removes pronoun roles from a user."""
    member = ctx.message.author
    if len(args) < 1:
        await ctx.send(f"{member.mention}, please specify a pronoun to add/remove. Current options include `!pronouns he`, `!pronouns she`, and `!pronouns they`.")
    heRole = discord.utils.get(member.guild.roles, name=ROLE_PRONOUN_HE)
    sheRole = discord.utils.get(member.guild.roles, name=ROLE_PRONOUN_SHE)
    theyRole = discord.utils.get(member.guild.roles, name=ROLE_PRONOUN_THEY)
    for arg in args:
        if arg.lower() in ["he", "him", "his", "he / him / his"]:
            if heRole in member.roles:
                await ctx.send("Oh, looks like you already have the He / Him / His role. Removing it.")
                await member.remove_roles(heRole)
            else:
                await member.add_roles(heRole)
                await ctx.send("Added the He / Him / His role.")
        elif arg.lower() in ["she", "her", "hers", "she / her / hers"]:
            if sheRole in member.roles:
                await ctx.send("Oh, looks like you already have the She / Her / Hers role. Removing it.")
                await member.remove_roles(sheRole)
            else:
                await member.add_roles(sheRole)
                await ctx.send("Added the She / Her / Hers role.")
        elif arg.lower() in ["they", "them", "their", "they / them / their"]:
            if theyRole in member.roles:
                await ctx.send("Oh, looks like you already have the They / Them / Theirs role. Removing it.")
                await member.remove_roles(theyRole)
            else:
                await member.add_roles(theyRole)
                await ctx.send("Added the They / Them / Theirs role.")
        elif arg.lower() in ["remove", "clear", "delete", "nuke"]:
            await member.remove_roles(heRole, sheRole, theyRole)
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
@commands.check(isLauncher)
async def confirm(ctx, *args: discord.Member):
    """Allows a staff member to confirm a user."""
    for i, member in enumerate(args):
        beforeMessage = None
        f = 0
        async for message in ctx.message.channel.history(oldest_first=True):
            # Delete any messages sent by Pi-Bot where message before is by member
            if f > 0:
                if message.author.id in PI_BOT_IDS and beforeMessage.author == member and len(message.embeds) == 0:
                    await message.delete()

                # Delete any messages by user
                if message.author == member and len(message.embeds) == 0:
                    await message.delete()

            beforeMessage = message
            f += 1
        role1 = discord.utils.get(member.guild.roles, name=ROLE_UC)
        role2 = discord.utils.get(member.guild.roles, name=ROLE_MR)
        await member.remove_roles(role1)
        await member.add_roles(role2)
        message = await ctx.send(f"Alrighty, confirmed {member.mention}. Welcome to the server! :tada:")
        await asyncio.sleep(3)
        if not i:
            await ctx.message.delete()
        await message.delete()

@bot.command()
async def nuke(ctx, count):
    """Nukes (deletes) a specified amount of messages."""
    global STOPNUKE
    launcher = await isLauncher(ctx)
    staff = await isStaff(ctx)
    if not (staff or (launcher and ctx.message.channel.name == "welcome")):
        return await ctx.send("APOLOGIES. INSUFFICIENT RANK FOR NUKE.")
    if STOPNUKE:
        return await ctx.send("TRANSMISSION FAILED. ALL NUKES ARE CURRENTLY PAUSED. TRY AGAIN LATER.")
    if int(count) > 100:
        return await ctx.send("Chill. No more than deleting 100 messages at a time.")
    await ctx.send("=====\nINCOMING TRANSMISSION.\n=====")
    await ctx.send("PREPARE FOR IMPACT.")
    for i in range(10, 0, -1):
        await ctx.send(f"NUKING {count} MESSAGES IN {i}... TYPE `!stopnuke` AT ANY TIME TO STOP ALL TRANSMISSION.")
        await asyncio.sleep(1)
        if STOPNUKE:
            return await ctx.send("A COMMANDER HAS PAUSED ALL NUKES FOR 20 SECONDS. NUKE CANCELLED.")
    if not STOPNUKE:
        channel = ctx.message.channel
        async for m in channel.history(limit=(int(count) + 13)):
            if not m.pinned and not STOPNUKE:
                await m.delete()
        msg = await ctx.send("https://media.giphy.com/media/XUFPGrX5Zis6Y/giphy.gif")
        await asyncio.sleep(5)
        await msg.delete()

@bot.command()
async def stopnuke(ctx):
    global STOPNUKE
    launcher = await isLauncher(ctx)
    staff = await isStaff(ctx)
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
@commands.check(isStaff)
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

async def sendToDMLog(message):
    server = bot.get_guild(SERVER_ID)
    dmChannel = discord.utils.get(server.text_channels, name=CHANNEL_DMLOG)
    embed = assembleEmbed(
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
        await sendToDMLog(message)

    print('Message from {0.author}: {0.content}'.format(message))
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
        await message.channel.send("<censored>")
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
                    userIsMentioned = user['id'] in [m.id for m in message.mentions]
                    if user['id'] in [m.id for m in message.channel.members] and ('dnd' not in user or user['dnd'] != True) and not userIsMentioned:
                        # Check that the user can actually see the message
                        name = message.author.nick
                        if name == None:
                            name = message.author.name
                        await pingPM(user['id'], name, ping, message.channel.name, message.content, message.jump_url)
    # SPAM TESTING
    global RECENT_MESSAGES
    caps = False
    u = sum(1 for c in message.content if c.isupper())
    l = sum(1 for c in message.content if c.islower())
    if u > (l + 3): caps = True
    RECENT_MESSAGES = [{"author": message.author.id,"content": message.content.lower(), "caps": caps}] + RECENT_MESSAGES[:20]
    # Spam checker
    if RECENT_MESSAGES.count({"author": message.author.id, "content": message.content.lower()}) >= 6:
        mutedRole = discord.utils.get(message.author.guild.roles, name=ROLE_MUTED)
        parsed = dateparser.parse("1 hour", settings={"PREFER_DATES_FROM": "future"})
        CRON_LIST.append({"date": parsed, "do": f"unmute {message.author.id}"})
        await message.author.add_roles(mutedRole)
        await message.channel.send(f"Successfully muted {message.author.mention} for 1 hour.")
        await autoReport("User was auto-muted (spam)", "red", f"A user ({str(message.author)}) was auto muted in {message.channel.mention} because of repeated spamming.")
    elif RECENT_MESSAGES.count({"author": message.author.id, "content": message.content.lower()}) >= 3:
        await message.channel.send(f"{message.author.mention}, please watch the spam. You will be muted if you do not stop.")
    # Caps checker
    elif sum(1 for m in RECENT_MESSAGES if m['author'] == message.author.id and m['caps']) > 8 and caps:
        mutedRole = discord.utils.get(message.author.guild.roles, name=ROLE_MUTED)
        parsed = dateparser.parse("1 hour", settings={"PREFER_DATES_FROM": "future"})
        CRON_LIST.append({"date": parsed, "do": f"unmute {message.author.id}"})
        await message.author.add_roles(mutedRole)
        await message.channel.send(f"Successfully muted {message.author.mention} for 1 hour.")
        await autoReport("User was auto-muted (caps)", "red", f"A user ({str(message.author)}) was auto muted in {message.channel.mention} because of repeated caps.")
    elif sum(1 for m in RECENT_MESSAGES if m['author'] == message.author.id and m['caps']) > 3 and caps:
        await message.channel.send(f"{message.author.mention}, please watch the caps, or else I will lay down the mute hammer!")
    await bot.process_commands(message)

@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id not in PI_BOT_IDS:
        reportsChannel = bot.get_channel(739596418762801213)
        if payload.message_id in REPORT_IDS:
            messageObj = await reportsChannel.fetch_message(payload.message_id)
            if payload.emoji.name == "\U0000274C":
                print("Report cleared with no action.")
                await messageObj.delete()
            if payload.emoji.name == "\U00002705":
                print("Report handled.")
                await messageObj.delete()

@bot.event
async def on_member_join(member):
    role = discord.utils.get(member.guild.roles, name=ROLE_UC)
    joinChannel = discord.utils.get(member.guild.text_channels, name=CHANNEL_WELCOME)
    await member.add_roles(role)
    name = member.name
    for word in CENSORED_WORDS:
        if len(re.findall(fr"\b({word})\b", name, re.I)):
            await autoReport("Innapropriate Username Detected", "red", f"A new member ({str(member)}) has joined the server, and I have detected that their username is innapropriate.")
    await joinChannel.send(f"{member.mention}, welcome to the Scioly.org Discord Server! " +
    "You can add roles here, using the commands shown at the top of this channel. " +
    "If you have any questions, please just ask here, and a helper or moderator will answer you ASAP." +
    "\n\n" +
    "**Please add roles by typing the commands above into the text box, and if you have a question, please type it here. After adding roles, a moderator will give you access to the rest of the server to chat with other members!**")
    memberCount = len(member.guild.members)
    loungeChannel = discord.utils.get(member.guild.text_channels, name=CHANNEL_LOUNGE)
    if memberCount % 100 == 0:
        await loungeChannel.send(f"Wow! There are now `{memberCount}` members in the server!")

@bot.event
async def on_member_remove(member):
    leaveChannel = discord.utils.get(member.guild.text_channels, name=CHANNEL_LEAVE)
    unconfirmedRole = discord.utils.get(member.guild.roles, name=ROLE_UC)
    if unconfirmedRole in member.roles:
        unconfirmedStatement = "Unconfirmed: :white_check_mark:"
    else:
        unconfirmedStatement = "Unconfirmed: :x:"
    joinedAt = f"Joined at: `{str(member.joined_at)}`"
    if member.nick != None:
        await leaveChannel.send(f"**{member}** (nicknamed `{member.nick}`) has left the server (or was removed).\n{unconfirmedStatement}\n{joinedAt}")
    else:
        await leaveChannel.send(f"**{member}** has left the server (or was removed).\n{unconfirmedStatement}\n{joinedAt}")

@bot.event
async def on_member_update(before, after):
    if after.nick == None: return
    for word in CENSORED_WORDS:
        if len(re.findall(fr"\b({word})\b", after.nick, re.I)):
            await autoReport("Innapropriate Username Detected", "red", f"A member ({str(after)}) has updated their nickname to **{after.nick}**, which the censor caught as innapropriate.")

@bot.event
async def on_user_update(before, after):
    for word in CENSORED_WORDS:
        if len(re.findall(fr"\b({word})\b", after.name, re.I)):
            await autoReport("Innapropriate Username Detected", "red", f"A member ({str(member)}) has updated their nickname to **{after.name}**, which the censor caught as innapropriate.")

@bot.event
async def on_raw_message_edit(payload):
    channel = bot.get_channel(payload.channel_id)
    editedChannel = discord.utils.get(channel.guild.text_channels, name=CHANNEL_EDITEDM)
    if channel.name in [CHANNEL_EDITEDM, CHANNEL_DELETEDM]:
        return
    try:
        message = payload.cached_message
        msgNow = await channel.fetch_message(message.id)
        embed = assembleEmbed(
            title=":pencil: Edited Message",
            fields=[
                {
                    "name": "Author",
                    "value": message.author,
                    "inline": "True"
                },
                {
                    "name": "Channel",
                    "value": message.channel.mention,
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
                    "value": msgNow.edited_at,
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
                    "value": msgNow.content[:1024] if len(msgNow.content) > 0 else "None",
                    "inline": "False"
                },
                {
                    "name": "Embed",
                    "value": "\n".join([str(e.to_dict()) for e in message.embeds]) if len(message.embeds) > 0 else "None",
                    "inline": "False"
                }
            ]
        )
        await editedChannel.send(embed=embed)
    except Exception as e:
        msgNow = await channel.fetch_message(payload.message_id)
        embed = assembleEmbed(
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
                    "value": msgNow.author,
                    "inline": "True"
                },
                {
                    "name": "Created At (UTC)",
                    "value": msgNow.created_at,
                    "inline": "True"
                },
                {
                    "name": "Edited At (UTC)",
                    "value": msgNow.edited_at,
                    "inline": "True"
                },
                {
                    "name": "New Content",
                    "value": msgNow.content[:1024] if len(msgNow.content) > 0 else "None",
                    "inline": "False"
                },
                {
                    "name": "Raw Payload",
                    "value": str(payload.data)[:1024] if len(payload.data) > 0 else "None",
                    "inline": "False"
                },
                {
                    "name": "Current Attachments",
                    "value": " | ".join([f"**{a.filename}**: [Link]({a.url})" for a in msgNow.attachments]) if len(msgNow.attachments) > 0 else "None",
                    "inline": "False"
                },
                {
                    "name": "Current Embed",
                    "value": "\n".join([str(e.to_dict()) for e in msgNow.embeds])[:1024] if len(msgNow.embeds) > 0 else "None",
                    "inline": "False"
                }
            ]
        )
        await editedChannel.send(embed=embed)

@bot.event
async def on_raw_message_delete(payload):
    if bot.get_channel(payload.channel_id).name in [CHANNEL_REPORTS, CHANNEL_DELETEDM]:
        print("Ignoring deletion event because of the channel it's from.")
        return
    channel = bot.get_channel(payload.channel_id)
    deletedChannel = discord.utils.get(channel.guild.text_channels, name=CHANNEL_DELETEDM)
    try:
        message = payload.cached_message
        embed = assembleEmbed(
            title=":fire: Deleted Message",
            fields=[
                {
                    "name": "Author",
                    "value": message.author,
                    "inline": "True"
                },
                {
                    "name": "Channel",
                    "value": message.channel.mention,
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
        await deletedChannel.send(embed=embed)
    except Exception as e:
        print(e)
        embed = assembleEmbed(
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
        await deletedChannel.send(embed=embed)

@bot.event
async def on_command_error(ctx, error):
    print("ERROR:")
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

async def lookupRole(name):
    name = name.title()
    if name == "Al" or name == "Alabama": return "Alabama"
    elif name == "All" or name == "All States": return "All States"
    elif name == "Ak" or name == "Alaska": return "Alaska"
    elif name == "Ar" or name == "Arkansas": return "Arkansas"
    elif name == "Az" or name == "Arizona": return "Arizona"
    elif name == "Cas" or name == "Ca-S" or name == "California (South)" or name == "Socal" or name == "California South": return "California (South)"
    elif name == "Can" or name == "Ca-N" or name == "California (North)" or name == "Nocal" or name == "California North": return "California (North)"
    if name == "Co" or name == "Colorado": return "Colorado"
    elif name == "Ct" or name == "Connecticut": return "Connecticut"
    elif name == "Dc" or name == "District Of Columbia": return "District of Columbia"
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

async def harvestID(user):
    return user.replace("<@!", "").replace(">", "")

if devMode:
    bot.run(DEV_TOKEN)
else:
    bot.run(TOKEN)