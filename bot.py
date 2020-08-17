import discord
import os
import asyncio
import requests
import re
import json
import random
import math
from dotenv import load_dotenv
from discord import channel
from discord.ext import commands, tasks

from src.sheets.events import getEvents
from src.sheets.censor import getCensor
from src.sheets.sheets import sendVariables, getVariables
from src.forums.forums import openBrowser
from info import getAbout
from doggo import getDoggo, getShiba
from bear import getBearMessage
from embed import assembleEmbed
from commands import getList, getHelp
from src.wiki.tournaments import getInviteTable

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
DEV_TOKEN = os.getenv('DISCORD_DEV_TOKEN')
devMode = os.getenv('DEV_MODE') == "TRUE"

if devMode:
    bot = commands.Bot(command_prefix=("bp", "?"))
else:
    bot = commands.Bot(command_prefix=("pb ", "!"))

##############
# CHECKS
##############

async def isBear(ctx):
    """Checks to see if the user is bear, or pepperonipi (for debugging purposes)."""
    return ctx.message.author.id == 353730886577160203 or ctx.message.author.id == 715048392408956950

async def isStaff(ctx):
    """Checks to see if the user is a staff member."""
    member = ctx.message.author
    wmRole = discord.utils.get(member.guild.roles, name="Wiki Moderator")
    gmRole = discord.utils.get(member.guild.roles, name="Global Moderator")
    aRole = discord.utils.get(member.guild.roles, name="Administrator")
    vipRole = discord.utils.get(member.guild.roles, name="VIP")
    if wmRole in member.roles or gmRole in member.roles or aRole in member.roles or vipRole in member.roles: return True

async def isAdmin(ctx):
    """Checks to see if the user is an administrator, or pepperonipi (for debugging purposes)."""
    member = ctx.message.author
    aRole = discord.utils.get(member.guild.roles, name="Administrator")
    if aRole in member.roles or member.id == 715048392408956950: return True

##############
# CONSTANTS
##############
PI_BOT_ID = 723767075427844106
PI_BOT_BETA_ID = 743254543952904197

##############
# VARIABLES
##############
fishNow = 0
canPost = False
CENSORED_WORDS = []
CENSORED_EMOJIS = []
EVENT_INFO = 0
REPORT_IDS = []
PING_INFO = []
TOURNEY_REPORT_IDS = []
COACH_REPORT_IDS = []

##############
# FUNCTIONS TO BE REMOVED
##############
bot.remove_command("help")

##############
# FUNCTIONS
##############

@bot.event
async def on_ready():
    """Called when the bot is enabled and ready to be run."""
    print(f'{bot.user} has connected!')
    await pullPrevInfo()
    refreshSheet.start()
    postSomething.start()
    changeBotStatus.start()

@tasks.loop(seconds=30.0)
async def refreshSheet():
    """Refreshes the censor list and stores variable backups."""
    await refreshAlgorithm()
    await prepareForSending()
    print("Attempted to refresh/store data from/to sheet.")

@tasks.loop(hours=1)
async def changeBotStatus():
    botStatus = math.floor(random.random() * 10)
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
    censor = getCensor()
    CENSORED_WORDS = censor[0]
    CENSORED_EMOJIS = censor[1]
    EVENT_INFO = await getEvents()
    print("Refreshed data from sheet.")
    return True

async def prepareForSending():
    """Sends local variables to the administrative sheet as a backup."""
    r1 = json.dumps(REPORT_IDS)
    r2 = json.dumps(PING_INFO)
    r3 = json.dumps(TOURNEY_REPORT_IDS)
    r4 = json.dumps(COACH_REPORT_IDS)
    await sendVariables([[r1], [r2], [r3], [r4]])
    print("Stored variables in sheet.")

async def pullPrevInfo():
    data = await getVariables()
    global PING_INFO
    global REPORT_IDS
    global TOURNEY_REPORT_IDS
    global COACH_REPORT_IDS
    REPORT_IDS = data[0][0]
    PING_INFO = data[1][0]
    TOURNEY_REPORT_IDS = data[2][0]
    COACH_REPORT_IDS = data[3][0]
    print("Fetched previous variables.")

@bot.command()
@commands.check(isAdmin)
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

@commands.check(isStaff)
@bot.command()
async def refresh(ctx):
    """Refreshes data from the sheet."""
    res = await refreshAlgorithm()
    if res == True:
        await ctx.send("Successfully refreshed data from sheet.")
    else:
        await ctx.send(":warning: Unsuccessfully refreshed data from sheet.")

@bot.command(aliases=["gci", "cid", "channelid"])
async def getchannelid(ctx):
    """Gets the channel ID of the current channel."""
    await ctx.send("Hey <@" + str(ctx.message.author.id) + ">! The channel ID is `" + str(ctx.message.channel.id) + "`. :)")

@bot.command(aliases=["ui"])
async def getuserid(ctx, user=None):
    """Gets the user ID of the caller or another user."""
    if user == None:
        await ctx.send(f"Your user ID is `{ctx.message.author.id}`.")
    else:
        user = user.replace("<@!", "").replace(">", "")
        await ctx.send(f"The user ID of <@{user}> is `{user}`.")

@bot.command()
async def hello(ctx):
    """Simply says hello. Used for testing the bot."""
    await ctx.send("Well, hello there.")

@bot.command(aliases=["what"])
async def about(ctx):
    """Prints information about the bot."""
    await ctx.send(getAbout())

@bot.command()
async def invites(ctx):
    """Fetches the invite table."""
    await ctx.send("Fetching invites...")
    message = getInviteTable()
    await ctx.send(f"```\n{message}```")

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

@bot.command()
async def tourney(ctx):
    """Gives an account the Tournament role."""
    await ctx.send("Giving you the Tournament role...")
    member = ctx.message.author
    role = discord.utils.get(member.guild.roles, name="Tournament")
    if role in member.roles:
        await ctx.send("Oops... you already have the Tournament role. If it needs to be removed, please open a report using `!report \"message...\"`.")
    else:
        await member.add_roles(role)
        await autoReport("Member Applied for Tournament Role", "DarkCyan", f"{ctx.message.author.name} applied for the Tournament role. Please verify that they are a tournament.")
        await ctx.send("Successfully gave you the Tournament role, and sent a verification message to staff.")

@bot.command(aliases=["state"])
async def states(ctx, *args):
    """Assigns someone with specific states."""
    member = ctx.message.author
    removedRoles = []
    addedRoles = []
    if len(args) < 1:
        return await ctx.send("Sorry, but you need to specify a state (or multiple states) to add/remove.")
    elif len(args) > 5:
        return await ctx.send("Sorry, you are attempting to add/remove too many states at once.")
    for arg in args:
        if arg == "California" or arg == "Cali" or arg == "CA":
            return await ctx.send("Which California, North or South??")
    for arg in args:
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
    GAMES_CHANNEL = 740046587006419014
    jbcObj = bot.get_channel(GAMES_CHANNEL)
    member = ctx.message.author
    role = discord.utils.get(member.guild.roles, name="Games")
    if role in member.roles:
        await member.remove_roles(role)
        await ctx.send("Removed you from the games club... feel free to come back anytime!")
        await jbcObj.send(f"{member.mention} left the party.")
    else:
        await member.add_roles(role)
        await ctx.send(f"You are now in the channel. Come and have fun in <#{GAMES_CHANNEL}>! :tada:")
        await jbcObj.send(f"Please welcome {member.mention} to the party!!")

@bot.command()
async def report(ctx, *args):
    """Creates a report that is sent to staff members."""
    if len(args) > 1:
        return await ctx.send("Please report one message wrapped in double quotes. (`!report \"Message!\"`)")
    message = args[0]
    poster = str(ctx.message.author)
    reportsChannel = bot.get_channel(739596418762801213)
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
    reportsChannel = bot.get_channel(739596418762801213)
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
async def ping(ctx, command="", *args):
    """Controls Pi-Bot's ping interface."""
    if command == "":
        return await ctx.send("Uh, I need a command you want to run.")
    member = ctx.message.author.id
    if len(args) > 8:
        return await ctx.send("You are giving me too many pings at once! Please separate your requests over multiple commands.")
    if command.lower() in ["add", "new", "delete", "remove", "test", "try"] and len(args) < 1:
        return await ctx.send(f"In order to {command} a ping, you must supply a regular expression or word.")
    if command.lower() in ["add", "new"]:
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
                if arg in pings:
                    await ctx.send(f"Ignoring adding the `{arg}` ping because you already have a ping currently set as that.")
                    ignoredList.append(arg)
                else:
                    pings.append(fr"{arg}")
        else:
            # nope
            PING_INFO.append({
                "id": member,
                "pings": [fr"{arg}" for arg in args]
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
                await ctx.send("Found the ping you are referencing... attemping to remove.")
            else:
                return await ctx.send(f"I can't find my phone or the **`{arg}`** ping you are referencing, sorry. Try another ping, or see all of your pings with `!ping list`.")
        return await ctx.send("I removed all pings you requested.")
    elif command.lower() in ["list", "all"]:
        user = next((u for u in PING_INFO if u['id'] == member), None)
        if user == None or len(user['pings']) == 0:
            return await ctx.send("You have no registered pings.")
        else:
            return await ctx.send("Your pings are: " + ", ".join([f"`{regex}`" for regex in user['pings']]))
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

@bot.command()
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

async def pingPM(userID, pinger, pingExp, jumpUrl):
    """Allows Pi-Bot to PM a user about a ping."""
    userToSend = bot.get_user(userID)
    embed = assembleEmbed(
        title=":bellhop: Ping Alert!",
        desc=f"Looks like `{pinger}` pinged a ping expression of yours.",
        fields=[
            {"name": "Expression Matched", "value": pingExp, "inline": True},
            {"name": "Jump To Message", "value": f"[woosh!]({jumpUrl})", "inline": True}
        ]
    )
    await userToSend.send(embed=embed)

@bot.command()
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
async def list(ctx):
    """Lists all of the commands a user may access."""
    ls = await getList(ctx)
    await ctx.send(embed=ls)

async def censor(message):
    """Constructs Pi-Bot's censor."""
    channel = message.channel
    author = message.author.name
    ava = message.author.avatar_url
    wh = await channel.create_webhook(name="Censor (Automated)")
    content = message.content
    for word in CENSORED_WORDS:
        content = re.sub(fr'\b({word})\b', "<censored>", content, flags=re.IGNORECASE)
    for word in CENSORED_EMOJIS:
        content = re.sub(fr"{word}", "<censored>", content, flags=re.I)
    await wh.send(content, username=(author + " (auto-censor)"), avatar_url=ava)
    await wh.delete()

@bot.command()
@commands.check(isStaff)
async def kick(ctx, user:discord.Member, reason:str=False):
    """Kicks a user for the specified reason."""
    if reason == False:
        return await ctx.send("Please specify a reason why you want to kick this user!")
    await user.kick(reason=reason)
    await ctx.send("The user was kicked.")

@bot.command()
@commands.check(isStaff)
async def prepembed(ctx, channel:discord.TextChannel, *, jsonInput):
    """Helps to create an embed to be sent to a channel."""
    jso = json.loads(jsonInput)
    title = jso['title'] if 'title' in jso else ""
    desc = jso['description'] if 'description' in jso else ""
    titleUrl = jso['titleUrl'] if 'titleUrl' in jso else ""
    hexcolor = jso['hexColor'] if 'hexColor' in jso else ""
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
        footerUrl=footerUrl
    )
    await channel.send(embed=embed)

@bot.command(aliases=["event"])
async def events(ctx, *args):
    """Adds or removes event roles from a user."""
    if len(args) < 1:
        return await ctx.send("You need to specify at least one event to add/remove!")
    elif len(args) > 5:
        return await ctx.send("Woah, that's a lot for me to handle at once. Please separate your requests over multiple commands.")
    member = ctx.message.author
    eventInfo = EVENT_INFO
    eventNames = []
    for arg in args:
        foundEvent = False
        for event in eventInfo:
            aliases = event['eventAbbreviations']
            if arg in aliases or arg == event['eventName']:
                eventNames.append(event['eventName'])
                foundEvent = True
                break
        if foundEvent == False:
            return await ctx.send(f"Sorry, I couldn't find the `{arg}` event.")
    removedRoles = []
    addedRoles = []
    for event in eventNames:
        role = discord.utils.get(member.guild.roles, name=event)
        if role in member.roles: 
            await member.remove_roles(role)
            removedRoles.append(event)
        else:
            await member.add_roles(role)
            addedRoles.append(event)
    if len(addedRoles) > 0 and len(removedRoles) == 0:
        eventRes = "Added events " + (' '.join([f'`{arg}`' for arg in addedRoles])) + "."
    elif len(removedRoles) > 0 and len(addedRoles) == 0:
        eventRes = "Removed events " + (' '.join([f'`{arg}`' for arg in removedRoles])) + "."
    else:
        eventRes = "Added events " + (' '.join([f'`{arg}`' for arg in addedRoles])) + ", and removed events " + (' '.join([f'`{arg}`' for arg in removedRoles])) + "."
    await ctx.send(eventRes)

async def getWords():
    """Gets the censor list"""
    global CENSORED_WORDS
    CENSORED_WORDS = getCensor()

@bot.command(aliases=["man"])
async def help(ctx, command="help"):
    """Allows a user to request help for a command."""
    hlp = await getHelp(ctx, command)
    await ctx.send(embed=hlp)

@bot.command()
async def fish(ctx):
    """Gives a fish to bear."""
    global fishNow
    fishNow += 1
    await ctx.send(f"You feed bear one fish. Bear now has {fishNow} fish!")

@bot.command()
async def nofish(ctx):
    """Removes all of bear's fish."""
    global fishNow
    fishNow = 0
    await ctx.send(f"Alright, no fish for bear!!")

@bot.command()
async def diva(ctx):
    """Gives a user the Division A role."""
    res = await assignDiv(ctx, "Division A")
    if res == True:
        await ctx.send("Assigned the Division A role, removed all other division roles.")
    else:
        await ctx.send("Huh, doesn't look like I can do that for some reason. *scratches head*")

@bot.command()
async def divb(ctx):
    """Gives a user the Division B role."""
    res = await assignDiv(ctx, "Division B")
    if res == True:
        await ctx.send("Assigned the Division B role, removed all other division roles.")
    else:
        await ctx.send("Huh, doesn't look like I can do that for some reason. *scratches head*")

@bot.command()
async def divc(ctx):
    """Gives a user the Division C role."""
    res = await assignDiv(ctx, "Division C")
    if res == True:
        await ctx.send("Assigned the Division C role, removed all other division roles.")
    else:
        await ctx.send("Huh, doesn't look like I can do that for some reason. *scratches head*")

@bot.command()
async def divd(ctx):
    """Gives a user the Division D role."""
    res = await assignDiv(ctx, "Division D")
    if res == True:
        await ctx.send("Assigned the Division D role, removed all other division roles.")
    else:
        await ctx.send("Huh, doesn't look like I can do that for some reason. *scratches head*")

async def assignDiv(ctx, div):
    """Assigns a user a div"""
    member = ctx.message.author
    role = discord.utils.get(member.guild.roles, name=div)
    divArole = discord.utils.get(member.guild.roles, name="Division A")
    divBrole = discord.utils.get(member.guild.roles, name="Division B")
    divCrole = discord.utils.get(member.guild.roles, name="Division C")
    divDrole = discord.utils.get(member.guild.roles, name="Division D")
    await member.remove_roles(divArole, divBrole, divCrole, divDrole)
    await member.add_roles(role)
    return True

@bot.command()
async def wiki(ctx, *args):
    multiple = False
    ignoreCase = False
    for arg in args:
        if arg[:1] == "-":
            multiple = arg.lower() == "-multiple"
            ignoreCase = arg.lower() == "-ignorecase"
    if len(args) > 5 and multiple:
        return await ctx.send("Slow down there buster. Please 5 or less wiki pages at a time.")
    if multiple:
        for arg in args:
            if arg[:1] != "-":
                arg = arg.replace(" ", "_")
                if not ignoreCase:
                    arg = arg.title()
                await ctx.send(f"<https://scioly.org/wiki/index.php/{arg}>")
    else:
        if not ignoreCase:
            args = [arg.title() for arg in args]
        stringSum = "_".join([arg for arg in args if arg[:1] != "-"])
        await ctx.send(f"<https://scioly.org/wiki/index.php/{stringSum}>")

@bot.command()
async def profile(ctx, name:str=False):
    if name == False:
        name = ctx.message.author.name
    if name.find("<@") != -1:
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
@commands.check(isStaff)
async def exalt(ctx, user):
    """Exalts a user."""
    member = ctx.message.author
    role = discord.utils.get(member.guild.roles, name="Exalted Member")
    iden = await harvestID(user)
    userObj = member.guild.get_member(int(iden))
    await userObj.add_roles(role)
    await ctx.send(f"Successfully exalted. Congratulations {user}! :tada: :tada:")

@bot.command()
@commands.check(isStaff)
async def mute(ctx, user):
    """Mutes a user."""
    member = ctx.message.author
    role = discord.utils.get(member.guild.roles, name="Muted")
    iden = await harvestID(user)
    userObj = member.guild.get_member(int(iden))
    await userObj.add_roles(role)
    await ctx.send(f"Successfully muted {user}.")

@bot.command()
@commands.check(isStaff)
async def unmute(ctx, user):
    """Unmutes a user."""
    member = ctx.message.author
    role = discord.utils.get(member.guild.roles, name="Muted")
    iden = await harvestID(user)
    userObj = member.guild.get_member(int(iden))
    await userObj.remove_roles(role)
    await ctx.send(f"Successfully unmuted {user}.")

@bot.command()
@commands.check(isStaff)
async def ban(ctx, member:discord.User=None, reason =None):
    """Bans a user."""
    if member == None or member == ctx.message.author:
        await ctx.channel.send("You cannot ban yourself! >:(")
        return
    if reason == None:
        reason = "No reason given."
    message = f"You have been banned from the Scioly.org Discord server for {reason}."
    await member.send(message)
    await ctx.guild.ban(member, reason=reason)
    await ctx.channel.send(f"{member} is banned!")

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
async def pronouns(ctx, arg):
    """Assigns or removes pronoun roles from a user."""
    member = ctx.message.author
    heRole = discord.utils.get(member.guild.roles, name="He / Him / His")
    sheRole = discord.utils.get(member.guild.roles, name="She / Her / Hers")
    theyRole = discord.utils.get(member.guild.roles, name="They / Them / Theirs")
    await member.remove_roles(heRole, sheRole, theyRole)
    if arg.lower() in ["he", "him", "his", "he / him / his"]:
        await member.add_roles(heRole)
        await ctx.send("Alrighty, your pronouns are set.")
    elif arg.lower() in ["she", "her", "hers", "she / her / hers"]:
        await member.add_roles(sheRole)
        await ctx.send("Alrighty, your pronouns are set.")
    elif arg.lower() in ["they", "them", "their", "they / them / their"]:
        await member.add_roles(theyRole)
        await ctx.send("Alrighty, your pronouns are set.")
    elif arg.lower() in ["remove", "clear", "delete", "nuke"]:
        await ctx.send("Alrighty, your pronouns have been removed.")
    else:
        await ctx.send("Sorry, I don't recognize those pronouns. The pronoun roles we currently have are:\n" +
        "- He / Him / His\n" +
        "- She / Her / Hers\n" +
        "- They / Them / Theirs\n" + 
        "Feel free to request alternate pronouns, by opening a report, or reaching out a staff member.")

@bot.command()
@commands.check(isStaff)
async def confirm(ctx, member:discord.Member):
    """Allows a staff member to confirm a user."""
    beforeMessage = None
    i = 0
    async for message in ctx.message.channel.history(oldest_first=True):
        # Delete any messages sent by Pi-Bot where message before is by member
        if i > 0:
            if message.author.id == PI_BOT_ID and beforeMessage.author == member and len(message.embeds) == 0:
                await message.delete()
            
            # Delete any messages by user
            if message.author == member and len(message.embeds) == 0:
                await message.delete()

        beforeMessage = message
        i += 1
    role1 = discord.utils.get(member.guild.roles, name="Unconfirmed")
    role2 = discord.utils.get(member.guild.roles, name="Member")
    await member.remove_roles(role1)
    await member.add_roles(role2)
    message = await ctx.send(f"Alrighty, confirmed {member.mention}. Welcome to the server! :tada:")
    await asyncio.sleep(5)
    await ctx.message.delete()
    await message.delete()

@bot.command()
@commands.check(isStaff)
async def nuke(ctx, count):
    """Nukes (deletes) a specified amount of messages."""
    if int(count) > 100:
        return await ctx.send("Chill. No more than deleting 100 messages at a time.")
    await ctx.send("INCOMING TRANSMISSION.")
    await ctx.send("PREPARE FOR IMPACT.")
    await ctx.send(f"NUKING {count} MESSAGES IN 3...")
    await asyncio.sleep(1)
    await ctx.send(f"NUKING {count} MESSAGES IN 2...")
    await asyncio.sleep(1)
    await ctx.send(f"NUKING {count} MESSAGES IN 1...")
    await asyncio.sleep(1)
    channel = ctx.message.channel
    try:
        logs = await channel.history(limit=(int(count) + 6)).flatten()
        await channel.delete_messages(logs)
    except:
        # This will run if the messages are over 14 days old, and cannot be bulk deleted
        async for m in channel.history(limit=(int(count) + 6)):
            await m.delete()
    await ctx.send("https://media.giphy.com/media/XUFPGrX5Zis6Y/giphy.gif")
    await asyncio.sleep(5)
    async for m in channel.history(limit=1):
        await m.delete()

@bot.event
async def on_message(message):
    print('Message from {0.author}: {0.content}'.format(message))
    if message.author.id == PI_BOT_ID or message.author.id == PI_BOT_BETA_ID: return
    content = message.content
    pingable = True
    if message.content[:1] == "!" or message.content[:1] == "?" or message.content[:2] == "pb" or message.content[:2] == "bp":
        pingable = False
    if message.channel.id == 724125653212987454:
        # If the message is coming from #bot-spam
        pingable = False
    if pingable:
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
        for user in PING_INFO:
            if user['id'] == message.author.id:
                continue
            pings = user['pings']
            for ping in pings:
                if len(re.findall(ping, content, re.I)) > 0 and message.author.discriminator != "0000":
                    if user['id'] in [m.id for m in message.channel.members] and ('dnd' not in user or user['dnd'] != True):
                        # Check that the user can actually see the message
                        await pingPM(user['id'], str(message.author), ping, message.jump_url)
    await bot.process_commands(message)

@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id != 723767075427844106:
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
    role = discord.utils.get(member.guild.roles, name="Unconfirmed")
    await member.add_roles(role)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, discord.ext.commands.CommandNotFound):
        await ctx.send("Sorry, I couldn't find that command.")
    if isinstance(error, discord.ext.commands.MissingPermissions):
        await cxt.send("Sorry, you do not have the permissons to do that.")
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