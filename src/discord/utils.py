

async def harvest_id(user):
    return user.replace("<@!", "").replace(">", "")