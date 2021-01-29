from src.sheets.sheets import get_worksheet

async def get_tournament_channels():
    """Gets the list of tournament channels."""
    discord_sheet = await get_worksheet()
    event_sheet = await discord_sheet.worksheet("Tournament List")
    info = await event_sheet.batch_get(["B2:H100"])
    info = info[0]
    del info[0]
    return info