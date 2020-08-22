import wikitextparser as wtp
import time
from tabulate import tabulate
from aioify import aioify

from src.wiki.wiki import getPageText

aiowtp = aioify(obj=wtp, name='aiowtp')

async def getInvitesPage():
    """Handles the invitational page."""
    tournamentsPage = await getPageText("Invitational")
    tournamentsPage = str(tournamentsPage)
    wikitext = wtp.parse(tournamentsPage)
    return wikitext.tables

async def getInviteTable():
    tables = await getInvitesPage()
    tables = [table.data() for table in tables]
    inviteTable = tables[0]
    iTHeaders = inviteTable.pop(0)
    print("made it to here")
    for row in inviteTable:
        del row[4]
        del row[4]
        del row[4]
        del row[4]
        del row[4]
        del row[4]
    print("made it to here 2")
    for row in inviteTable:
        for i, cell in enumerate(row):
            if len(aiowtp.parse(cell).wikilinks) > 0:
                row[i] = aiowtp.parse(cell).wikilinks[0].title
    return tabulate(tables[0], iTHeaders, tablefmt="psql")