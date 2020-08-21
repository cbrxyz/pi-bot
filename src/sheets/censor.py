from src.sheets.sheets import getWorksheet

async def getCensor():
    """Creates Pi-Bot's censor."""
    discordSheet = await getWorksheet()
    eventSheet = await discordSheet.worksheet("Censor Management")
    words = await eventSheet.batch_get(["B3:C1000"])
    words = words[0]
    words = words[0]
    CENSORED_WORDS = []
    CENSORED_EMOJIS = []
    for row in words:
        if len(row[0]) > 1:
            CENSORED_WORDS.append(row[0])
        if len(row) == 2:
            CENSORED_EMOJIS.append(row[1])
    return [CENSORED_WORDS, CENSORED_EMOJIS]