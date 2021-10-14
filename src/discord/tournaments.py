import discord
from src.discord.globals import TOURNAMENT_INFO, REQUESTED_TOURNAMENTS, SERVER_ID, CHANNEL_TOURNAMENTS, CATEGORY_TOURNAMENTS, CATEGORY_ARCHIVE, CHANNEL_BOTSPAM, CHANNEL_SUPPORT, ROLE_GM, ROLE_AD, ROLE_AT
import datetime
from src.mongo.mongo import get_invitationals 
from src.discord.utils import auto_report

class TournamentDropdown(discord.ui.Select):

    def __init__(self, custom_id, placeholder):
        super().__init__(custom_id = custom_id, placeholder = placeholder)

class TournamentView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout = None)

async def update_tournament_list(bot):
    tl = await get_invitationals()
    tl.sort(key=lambda t: t['official_name'])
    global TOURNAMENT_INFO
    global REQUESTED_TOURNAMENTS
    TOURNAMENT_INFO = tl
    server = bot.get_guild(SERVER_ID)
    tourney_channel = discord.utils.get(server.text_channels, name=CHANNEL_TOURNAMENTS)
    tournament_category = discord.utils.get(server.categories, name=CATEGORY_TOURNAMENTS)
    bot_spam_channel = discord.utils.get(server.text_channels, name=CHANNEL_BOTSPAM)
    server_support_channel = discord.utils.get(server.text_channels, name=CHANNEL_SUPPORT)
    gm = discord.utils.get(server.roles, name=ROLE_GM)
    a = discord.utils.get(server.roles, name=ROLE_AD)
    all_tournaments_role = discord.utils.get(server.roles, name=ROLE_AT)
    open_soon_list = ""
    now = datetime.datetime.now()
    for t in tl: # For each tournament in the sheet
        # Check if the channel needs to be made / deleted
        ch = discord.utils.get(server.text_channels, name=t['channel_name'])
        r = discord.utils.get(server.roles, name=t['official_name'])
        tourney_date = t['tourney_date']
        tourney_date_str = str(tourney_date.date())
        before_days = int(t['open_days'])
        after_days = int(t['closed_days'])
        day_diff = (tourney_date - now).days
        print(f"Tournament List: Handling {t['official_name']} (Day diff: {day_diff} days)")
        if (day_diff < (-1 * after_days)) and ch != None:
            # If past tournament date, now out of range
            if ch.category.name != CATEGORY_ARCHIVE:
                await auto_report("Tournament Channel & Role Needs to be Archived", "orange", f"The {ch.mention} channel and {r.mention} role need to be archived, as it is after the tournament date.")
        elif (day_diff <= before_days) and ch == None:
            # If before tournament and in range
            new_role = await server.create_role(name=t['official_name'])
            new_channel = await server.create_text_channel(t['channel_name'], category=tournament_category)
            await new_channel.edit(topic=f"{t['emoji']} - Discussion around the {t['official_name']} occurring on {tourney_date_str}.", sync_permissions=True)
            await new_channel.set_permissions(new_role, read_messages=True)
            await new_channel.set_permissions(all_tournaments_role, read_messages=True)
            await new_channel.set_permissions(server.default_role, read_messages=False)
        elif (day_diff > before_days):
            # Tournament is not yet ready to open
            open_soon_list += (t[2] + " **" + t[0] + f"** - Opens in `{day_diff - before_days}` days.\n")
    REQUESTED_TOURNAMENTS.sort(key=lambda x: (-x['count'], x['iden']))

    help_embed = discord.Embed(
        title = ":medal: Join a Tournament Channel!",
        color = discord.Color(0x2E66B6),
        description = f"""
        Below is a list of **tournament channels**. Some are available right now, some will be available soon, and others have been requested, but have not received enough support to be considered for a channel.

        To join a tournament channel, use the dropdowns below! Dropdowns are split up by ____.

        To request a new tournament channel, please use the `/request` command in {bot_spam_channel.mention}. If you need help, feel free to let a {a.mention} or {gm.mention} know!
        """
    )
    hist = await tourney_channel.history(oldest_first=True).flatten()
    if len(hist) == 0:
        # If the tournament channel is being initialized for the first time

        await tourney_channel.send(embed = help_embed)
