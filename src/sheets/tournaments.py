from src.sheets.sheets import get_worksheet

async def get_tournament_channels():
    """Gets the list of tournament channels."""
    discordSheet = await get_worksheet()
    eventSheet = await discordSheet.worksheet("Tournament List")
    info = await eventSheet.batch_get(["B2:H100"])
    info = info[0]
    del info[0]
    return info