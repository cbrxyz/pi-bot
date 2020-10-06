from src.sheets.sheets import getWorksheet

async def getTournamentChannels():
    """Gets the list of tournament channels."""
    discordSheet = await getWorksheet()
    eventSheet = await discordSheet.worksheet("Tournament List")
    info = await eventSheet.batch_get(["B2:H100"])
    info = info[0]
    del info[0]
    return info