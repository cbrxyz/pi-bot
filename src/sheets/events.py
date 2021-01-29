from src.sheets.sheets import get_worksheet

async def get_events():
    """Creates Pi-Bot's event list."""
    discord_sheet = await get_worksheet()
    event_sheet = await discord_sheet.worksheet("Event Info")
    info = await event_sheet.batch_get(["B2:C100"])
    info = info[0]
    del info[0]
    event_names = []
    event_abbreviations = []
    for row in info:
        event_names.append(row[0])
        if len(row) > 1:
            event_abbreviations.append(row[1].split(","))
        else:
            event_abbreviations.append('')
    res = []
    for i, v in enumerate(event_names):
        res.append({'eventName': v,'event_abbreviations': event_abbreviations[i]})
    return res