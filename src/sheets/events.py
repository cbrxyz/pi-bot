from src.sheets.sheets import getWorksheet

async def getEvents():
    """Creates Pi-Bot's event list."""
    discordSheet = getWorksheet()
    eventSheet = discordSheet.worksheet("Event Info")
    info = eventSheet.get("B2:C36")
    del info[0]
    eventNames = []
    eventAbbreviations = []
    for row in info:
        eventNames.append(row[0])
        if len(row) > 1:
            eventAbbreviations.append(row[1].split(","))
        else:
            eventAbbreviations.append('')
    res = []
    for i, v in enumerate(eventNames):
        res.append({'eventName': v,'eventAbbreviations': eventAbbreviations[i]})
    return res