from src.sheets.sheets import getWorksheet

def getCensor():
    """Creates Pi-Bot's censor."""
    discordSheet = getWorksheet()
    eventSheet = discordSheet.worksheet("Censor Management")
    words = eventSheet.get("B3:B1000")
    words = [row[0] for row in words]
    return words