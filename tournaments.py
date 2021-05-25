import discord
from src.discord.globals import TOURNAMENT_INFO, REQUESTED_TOURNAMENTS, SERVER_ID, CHANNEL_TOURNAMENTS, CATEGORY_TOURNAMENTS, CATEGORY_ARCHIVE, CHANNEL_BOTSPAM, CHANNEL_SUPPORT, ROLE_GM, ROLE_AD, ROLE_AT
import datetime
from src.sheets.tournaments import get_tournament_channels
from src.discord.utils import auto_report

async def update_tournament_list(bot):
    tl = await get_tournament_channels()
    tl.sort(key=lambda x: x[0])
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
    string_lists = []
    string_lists.append("")
    open_soon_list = ""
    channels_requested_list = ""
    now = datetime.datetime.now()
    for t in tl: # For each tournament in the sheet
        # Check if the channel needs to be made / deleted
        ch = discord.utils.get(server.text_channels, name=t[1])
        r = discord.utils.get(server.roles, name=t[0])
        tourney_date = t[4]
        before_days = int(t[5])
        after_days = int(t[6])
        tourney_date_datetime = datetime.datetime.strptime(tourney_date, "%Y-%m-%d")
        day_diff = (tourney_date_datetime - now).days
        print(f"Tournament List: Handling {t[0]} (Day diff: {day_diff} days)")
        if (day_diff < (-1 * after_days)) and ch != None:
            # If past tournament date, now out of range
            if ch.category.name != CATEGORY_ARCHIVE:
                await auto_report("Tournament Channel & Role Needs to be Archived", "orange", f"The {ch.mention} channel and {r.mention} role need to be archived, as it is after the tournament date.")
        elif (day_diff <= before_days) and ch == None:
            # If before tournament and in range
            new_role = await server.create_role(name=t[0])
            new_channel = await server.create_text_channel(t[1], category=tournament_category)
            await new_channel.edit(topic=f"{t[2]} - Discussion around the {t[0]} occurring on {t[4]}.", sync_permissions=True)
            await new_channel.set_permissions(new_role, read_messages=True)
            await new_channel.set_permissions(all_tournaments_role, read_messages=True)
            await new_channel.set_permissions(server.default_role, read_messages=False)
            string_to_add = (t[2] + " **" + t[0] + "** - `!tournament " + t[1] + "`\n")
            while len(string_lists[-1] + string_to_add) > 2048:
                string_lists.append("")
            string_lists[-1] += string_to_add
        elif ch != None:
            string_to_add = (t[2] + " **" + t[0] + "** - `!tournament " + t[1] + "`\n")
            while len(string_lists[-1] + string_to_add) > 2048:
                string_lists.append("")
            string_lists[-1] += string_to_add
        elif (day_diff > before_days):
            open_soon_list += (t[2] + " **" + t[0] + f"** - Opens in `{day_diff - before_days}` days.\n")
    REQUESTED_TOURNAMENTS.sort(key=lambda x: (-x['count'], x['iden']))
    spacing_needed = max([len(t['iden']) for t in REQUESTED_TOURNAMENTS]) if len(REQUESTED_TOURNAMENTS) > 0 else 0
    for t in REQUESTED_TOURNAMENTS:
        spaces = " " * (spacing_needed - len(t['iden']))
        channels_requested_list += f"`!tournament {t['iden']}{spaces}` · **{t['count']} votes**\n"
    embeds = []
    embeds.append(assemble_embed(
        title=":medal: Tournament Channels Listing",
        desc=(
            "Below is a list of **tournament channels**. Some are available right now, some will be available soon, and others have been requested, but have not received 10 votes to be considered for a channel." +
            f"\n\n* To join an available tournament channel, head to {bot_spam_channel.mention} and type `!tournament [name]`." +
            f"\n\n* To make a new request for a tournament channel, head to {bot_spam_channel.mention} and type `!tournament [name]`, where `[name]` is the name of the tournament channel you would like to have created." +
            f"\n\n* Need help? Ping a {gm.mention} or {a.mention}, or ask in {server_support_channel.mention}"
        )
    ))
    for i, s in enumerate(string_lists):
        embeds.append(assemble_embed(
            title=f"Currently Available Channels (Page {i + 1}/{len(string_lists)})",
            desc=s if len(s) > 0 else "No channels are available currently."
        ))
    embeds.append(assemble_embed(
        title="Channels Opening Soon",
        desc=open_soon_list if len(open_soon_list) > 0 else "No channels are opening soon currently.",
    ))
    embeds.append(assemble_embed(
        title="Channels Requested",
        desc=("Vote with the command associated with the tournament channel.\n\n" + channels_requested_list) if len(channels_requested_list) > 0 else f"No channels have been requested currently. To make a request for a tournament channel, head to {bot_spam_channel.mention} and type `!tournament [name]`, with the name of the tournament."
    ))
    hist = await tourney_channel.history(oldest_first=True).flatten()
    if len(hist) != 0:
        # When the tourney channel already has embeds
        if len(embeds) < len(hist):
            messages = await tourney_channel.history(oldest_first=True).flatten()
            for m in messages[len(embeds):]:
                await m.delete()
        count = 0
        async for m in tourney_channel.history(oldest_first=True):
            await m.edit(embed=embeds[count])
            count += 1
        if len(embeds) > len(hist):
            for e in embeds[len(hist):]:
                await tourney_channel.send(embed=e)
    else:
        # If the tournament channel is being initialized for the first time
        past_messages = await tourney_channel.history(limit=100).flatten()
        await tourney_channel.delete_messages(past_messages)
        for e in embeds:
            await tourney_channel.send(embed=e)