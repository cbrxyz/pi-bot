# Imports
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

import asyncio
import time
from collections import Counter
from datetime import date

import pywikibot
import wikitextparser as wtp
from aioify import aioify
from pywikibot import pagegenerators

aiopwb = aioify(obj=pywikibot, name="aiopwb")

site = 0
entry_count = 500
cur_table_wtp = 0

# Define a class for storing user information
class User:
    def __init__(self, name, edits):
        self.name = name
        self.edits = edits

    def set_rank_change(self, rank_change):
        self.rank_change = rank_change

    def set_edit_num_increase(self, increase):
        self.eni = increase

    def set_edit_percent_increase(self, increase):
        self.epi = increase

    def set_user_ns_perfect(self, percent):
        self.unsp = percent

    def set_pages_most(self, pages):
        self.pages = pages


# UNSP
# (Percent of edits going to user pages)
async def find_unsp(name):
    user_obj = pywikibot.User(site, name)
    contribs = user_obj.contributions(total=10000)
    edit_count = user_obj.editCount()
    userEdits = 0

    # Loop over all of user contributions
    for i in contribs:
        title = i[0].title()
        # If the title includes the user's userpage, and is not a subpage, then add it to the list
        if title.find("User:" + name) != -1 and not title.find("/") != -1:
            userEdits += 1

    if edit_count > 0:
        # Make final percentage value
        return str(round(100 * userEdits / edit_count, 3)) + "%"
    else:
        # If the user does not have edits, just return an X to avoid division by zero error
        return "X"


# Find the rank change of the user since the last run
async def find_rank_change(name, cur_position):
    user_obj = pywikibot.User(site, name)
    for i in range(entry_count):
        if cur_table_wtp[i][2] == ("[[User:" + name + "|" + name + "]]"):
            return str(i - cur_position)
    return "X"


# Find the number of edits increased since last time
async def find_edit_increase(name, cur_edits):
    for i in range(entry_count):
        if cur_table_wtp[i][2] == ("[[User:" + name + "|" + name + "]]"):
            return str(int(cur_edits) - int(cur_table_wtp[i][3]))
    return "X"


async def find_edit_percent(name, cur_edits):
    for i in range(entry_count):
        if cur_table_wtp[i][2] == ("[[User:" + name + "|" + name + "]]"):
            return (
                str(
                    round(
                        100
                        * (int(cur_edits) - int(cur_table_wtp[i][3]))
                        / int(cur_table_wtp[i][3]),
                        1,
                    )
                )
                + "%"
            )
    return "X"


# ME
async def find_most_edited(name):
    user_obj = pywikibot.User(site, name)
    contribs = user_obj.contributions(total=10000)
    edit_count = user_obj.editCount()
    user_edits = 0

    if edit_count == 0:
        return "X"

    title_array = []

    for i in contribs:
        title_array.append(i[0].title())

    c = Counter(title_array).most_common(5)

    sum_string = ""
    for i in c:
        sum_string += "[[:" + i[0] + "]]"
        sum_string += " ("
        sum_string += str(i[1])
        sum_string += ")"
        sum_string += ", "

    print(sum_string[:-2])

    if edit_count > 0:
        return sum_string
    else:
        return sum_string


async def run_table():
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
    if await text.find("|}") == -1:
        print("!!!! NO MORE TABLE ENDINGS !!!!")
    title = page.title()
    tables += 1
    first_bracket = await text.find("{|")
    last_bracket = await text.find("|}")
    cur_table = text[first_bracket : last_bracket + 2]
    global cur_table_wtp
    cur_table_wtp = wtp.Table(cur_table).data()
    print(cur_table_wtp)
    for _ in range(1):
        cur_table_wtp.pop(0)

    # USER ARRAY
    users = []

    for user in gen:
        print(len(users))
        user_name = user["name"]
        user_obj = pywikibot.User(site, user_name)
        edit_count = user_obj.editCount()
        users.append(User(user_name, edit_count))
        await asyncio.sleep(0.05)

    users.sort(key=lambda x: x.edits, reverse=True)

    position = 1

    today = date.today()
    table_header = (
        "'''Disclaimer:''' Edit count is not directly considered for promotions. '''Edit quality is always considered much more than edit quantity.'''\n\nThis leaderboard is not, and will not, be examined by staff to determine promotions. This leaderboard is made for fun only.\n\n{| class='wikitable sortable'\n|-\n!colspan='8'|Most Edits Table<br><small>Updated "
        + str(today)
        + "</small>\n|-\n!Rank !!Rank Change !!User !!Edits !!Edit Increase Since Last Run !!% of Contributions to Own User Page !!Pages Most Contributed To\n|-\n"
    )
    table = table_header
    table_footer = "|}"

    print(table)

    increase_table = []
    for user in users[:entry_count]:
        unsp = await find_unsp(user.name)
        rank_change = await find_rank_change(user.name, position)
        if rank_change == "X":
            template = ""
        elif int(rank_change) > 0:
            template = "{{Increase}}"
        elif int(rank_change) == 0:
            template = "{{Steady}}"
        elif int(rank_change) < 0:
            template = "{{Decrease}}"
        edit_increase = await find_edit_increase(user.name, user.edits)
        per_edit_increase = await find_edit_percent(user.name, user.edits)
        most_edited_pages = await find_most_edited(user.name)
        table += (
            "|"
            + str(position)
            + "||data-sort-value='"
            + rank_change
            + "'| "
            + (template + " " + rank_change)
            + " ||[[User:"
            + str(user.name)
            + "|"
            + str(user.name)
            + "]] || "
            + str(user.edits)
            + " ||data-sort-value='"
            + edit_increase
            + "'| "
            + (edit_increase + " (" + per_edit_increase + ")")
            + " || "
            + unsp
            + " || "
            + most_edited_pages
            + "\n|-\n"
        )
        position += 1
        if edit_increase != "X":
            increase_table.append(
                {"name": str(user.name), "increase": int(edit_increase)}
            )
        await asyncio.sleep(0.2)

    table += table_footer
    page = pywikibot.page.BasePage(site, "User:Pi-Bot/Task 2/Most Edits Table")

    page_text = page.text
    page_text = table
    page.text = page_text
    page.save(
        summary="Added table with "
        + str(entry_count)
        + " users on "
        + str(today)
        + ". (See [[User:Pi-Bot/Task 2]] for more information.)",
        minor=False,
    )
    print("Saved text to wiki page.")
    return sorted(increase_table, key=lambda x: x["increase"], reverse=True)
