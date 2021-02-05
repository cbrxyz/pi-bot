from src.sheets.sheets import get_raw_censor

async def get_censor():
    """Creates Pi-Bot's censor."""
    words = await get_raw_censor()
    words = words[0]
    CENSORED_WORDS = []
    CENSORED_EMOJIS = []
    for row in words:
        if len(row[0]) > 1:
            CENSORED_WORDS.append(row[0])
        if len(row) == 2:
            CENSORED_EMOJIS.append(row[1])
    return [CENSORED_WORDS, CENSORED_EMOJIS]