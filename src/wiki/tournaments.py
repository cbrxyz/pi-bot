import wikitextparser as wtp
import time
from tabulate import tabulate

from src.wiki.wiki import getPageText

def getInvitesPage():
    """Handles the invitational page."""
    tournamentsPage = getPageText("Invitational")
    wikitext = wtp.parse(tournamentsPage)
    return wikitext.tables

def getInviteTable():
    tables = getInvitesPage()
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
    for row in inviteTable:
        for i, cell in enumerate(row):
            if len(wtp.parse(cell).wikilinks) > 0:
                row[i] = wtp.parse(cell).wikilinks[0].title
    return tabulate(tables[0], iTHeaders, tablefmt="psql")