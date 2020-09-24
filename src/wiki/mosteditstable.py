# Imports
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

import pywikibot
import time
import asyncio
import wikitextparser as wtp
from pywikibot import pagegenerators
from datetime import date
from collections import Counter
from aioify import aioify

aiopwb = aioify(obj=pywikibot, name='aiopwb')

site = 0
entryCount = 500
curTableWTP = 0

# Define a class for storing user information
class User():
    def __init__(self, name, edits):
        self.name = name
        self.edits = edits

    def setRankChange(self, rankChange):
        self.rankChange = rankChange
    
    def setEditNumIncrease(self, increase):
        self.eni = increase

    def setEditPercentIncrease(self, increase):
        self.epi = increase

    def setUserNSPercent(self, percent):
        self.unsp = percent

    def setPagesMost(self, pages):
        self.pages = pages

#UNSP
# (Percent of edits going to user pages)
async def findUNSP(name):
    userObj = pywikibot.User(site, name)
    contribs = userObj.contributions(total=10000)
    editCount = userObj.editCount()
    userEdits = 0

    # Loop over all of user contributions
    for i in contribs:
        title = i[0].title()
        # If the title includes the user's userpage, and is not a subpage, then add it to the list
        if (title.find("User:" + name) != -1 and not title.find("/") != -1): userEdits += 1

    if editCount > 0:
        # Make final percentage value
        return (str(round(100*userEdits/editCount, 3)) + "%")
    else:
        # If the user does not have edits, just return an X to avoid division by zero error
        return "X"

# Find the rank change of the user since the last run
async def findRankChange(name, curPosition):
    userObj = pywikibot.User(site, name)
    for i in range(entryCount):
        if curTableWTP[i][2] == ("[[User:" + name + "|" + name + "]]"):
            return str(i - curPosition)
    return "X"

# Find the number of edits increased since last time
async def findEditIncrease(name, curEdits):
    for i in range(entryCount):
        if curTableWTP[i][2] == ("[[User:" + name + "|" + name + "]]"):
            return str(int(curEdits) - int(curTableWTP[i][3]))
    return "X"

async def findEditPercent(name, curEdits):
    for i in range(entryCount):
        if curTableWTP[i][2] == ("[[User:" + name + "|" + name + "]]"):
            return str(round(100*(int(curEdits) - int(curTableWTP[i][3]))/int(curTableWTP[i][3]), 1)) + "%"
    return "X"

#ME
async def findME(name):
    userObj = pywikibot.User(site, name)
    contribs = userObj.contributions(total=10000)
    editCount = userObj.editCount()
    userEdits = 0

    if editCount == 0:
        return "X"

    titleArray = []

    for i in contribs:
        titleArray.append(i[0].title())

    c = Counter(titleArray).most_common(5)

    sumString = ""
    for i in c:
        sumString += ("[[:" + i[0] + "]]")
        sumString += " ("
        sumString += str(i[1])
        sumString += ")"
        sumString += ", "

    print(sumString[:-2])

    if editCount > 0:
        return sumString
    else:
        return sumString

async def runTable():
    # Start Message
    print("Attempting to start program...")
    print("==============================")

    # Constants
    global site
    site = await aiopwb.Site()
    cat = aiopwb.Category(site, "Category:Event Pages")
    page = "User:Pi-Bot/Task 2/Most Edits Table"
    gen = site.allusers(total=10000)

    # Find Existing Table
    text = aiopwb.page.BasePage(site, page).text
    tables = 0
    if (await text.find("|}") == -1):
        print("!!!! NO MORE TABLE ENDINGS !!!!")
    title = page.title()
    tables += 1
    firstBracket = await text.find("{|")
    lastBracket = await text.find("|}")
    curTable = text[firstBracket:lastBracket + 2]
    global curTableWTP
    curTableWTP = wtp.Table(curTable).data()
    print(curTableWTP)
    for _ in range(1):
        curTableWTP.pop(0)

    # USER ARRAY
    users = []

    for user in gen:
        print(len(users))
        userName = user['name']
        userObj = pywikibot.User(site, userName)
        editCount = userObj.editCount()
        users.append(User(userName, editCount))
        await asyncio.sleep(0.05)

    users.sort(key=lambda x: x.edits, reverse=True)

    position = 1

    today = date.today()
    tableHeader = "'''Disclaimer:''' Edit count is not directly considered for promotions. '''Edit quality is always considered much more than edit quantity.'''\n\nThis leaderboard is not, and will not, be examined by staff to determine promotions. This leaderboard is made for fun only.\n\n{| class='wikitable sortable'\n|-\n!colspan='8'|Most Edits Table<br><small>Updated " + str(today) + "</small>\n|-\n!Rank !!Rank Change !!User !!Edits !!Edit Increase Since Last Run !!% of Contributions to Own User Page !!Pages Most Contributed To\n|-\n"
    table = tableHeader
    tableFooter = "|}"

    print(table)

    increaseTable = []
    for user in users[:entryCount]:
        unsp = await findUNSP(user.name)
        rankChange = await findRankChange(user.name, position)
        if rankChange == "X":
            template = ""
        elif (int(rankChange) > 0):
            template = "{{Increase}}"
        elif int(rankChange) == 0:
            template = "{{Steady}}"
        elif int(rankChange) < 0:
            template = "{{Decrease}}"
        editIncrease = await findEditIncrease(user.name, user.edits)
        perEditIncrease = await findEditPercent(user.name, user.edits)
        mEPages = await findME(user.name)
        table +=  ("|" + str(position) + "||data-sort-value='" + rankChange + "'| " + (template + " " + rankChange) + " ||[[User:" + str(user.name) + "|" + str(user.name) + "]] || " + str(user.edits) + " ||data-sort-value='" + editIncrease + "'| " + (editIncrease + " (" + perEditIncrease + ")") + " || " + unsp + " || " + mEPages + "\n|-\n")
        position += 1
        if editIncrease != "X":
            increaseTable.append({
                'name': str(user.name),
                'increase': int(editIncrease)
            })
        await asyncio.sleep(0.2)

    table += tableFooter
    page = pywikibot.page.BasePage(site, "User:Pi-Bot/Task 2/Most Edits Table")

    pageText = page.text
    pageText = table
    page.text = pageText
    page.save(summary="Added table with " + str(entryCount) + " users on " + str(today) + ". (See [[User:Pi-Bot/Task 2]] for more information.)", minor=False)
    print("Saved text to wiki page.")
    return sorted(increaseTable, key = lambda x : x['increase'], reverse=True)