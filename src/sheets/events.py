from src.sheets.sheets import get_worksheet

async def get_events():
    """Creates Pi-Bot's event list."""
    discordSheet = await get_worksheet()
    eventSheet = await discordSheet.worksheet("Event Info")
    info = await eventSheet.batch_get(["B2:C100"])
    info = info[0]
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