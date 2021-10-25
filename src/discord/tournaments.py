import discord
from src.discord.globals import TOURNAMENT_INFO, SERVER_ID, CHANNEL_TOURNAMENTS, CATEGORY_TOURNAMENTS, CATEGORY_ARCHIVE, CHANNEL_BOTSPAM, CHANNEL_SUPPORT, ROLE_GM, ROLE_AD, ROLE_AT
import datetime
from src.mongo.mongo import get_invitationals, update_many
from src.discord.utils import auto_report

class Tournament:

    def __init__(
            self,
            objects
        ):
        self._properties = objects
        self.doc_id = objects.get('_id')
        self.official_name = objects.get('official_name')
        self.channel_name = objects.get('channel_name')
        self.emoji = objects.get('emoji')
        self.aliases = objects.get('aliases')
        self.tourney_date = objects.get('tourney_date')
        self.open_days = objects.get('open_days')
        self.closed_days = objects.get('closed_days')
        self.voters = objects.get('voters')
        self.status = objects.get('status')

class TournamentDropdown(discord.ui.Select):

    def __init__(self, month_tournaments, bot, voting = False):

        final_options = []
        for tourney in month_tournaments:
            final_options.append(
                discord.SelectOption(
                    label = tourney.official_name,
                    description = f"Occurs on {str(tourney.tourney_date.date())}.",
                    emoji = tourney.emoji
                )
            )
        
        super().__init__(
            options = final_options,
            min_values = 1,
            max_values = len(final_options),
            placeholder = "Choose a tournament..."
        )

        self.bot = bot
        self.voting = voting
        self.tournaments = month_tournaments

    async def callback(self, interaction: discord.Interaction):
        member = interaction.user
        server = member.guild
        if not self.voting:
            # If this dropdown isn't being used for voting
            for value in self.values:
                print(value, 1)
                role = discord.utils.get(server.roles, name=value)
                if role in member.roles:
                    await member.remove_roles(role)
                else:
                    await member.add_roles(role)
        else:
            # This dropdown is being used for voting
            need_to_update = []
            already_voted_for = []
            for value in self.values:
                print(value)
                tournament = discord.utils.get(self.tournaments, official_name = value)
                if member.id in tournament.voters:
                    # This user has already voted for this tournament.
                    already_voted_for.append(tournament)
                else:
                    # This user has not already voted for this tournament.
                    tournament.voters.append(member.id)
                    need_to_update.append(tournament)
            if len(need_to_update) > 0:
                # Some docs need to be updated
                docs_to_update = [t._properties for t in need_to_update]
                await update_many("data", "invitationals", docs_to_update, {"$push": {"voters": member.id}})
            result_string = ""
            for tourney in need_to_update:
                result_string += f"`{tourney.official_name}` - I added your vote! This tourney now has {len(tourney.voters)} votes!\n"
            for tourney in already_voted_for:
                result_string += f"`{tourney.official_name}` - You already voted for this channel! This channel has {len(tourney.voters)} votes!\n"
            result_string = result_string[:-1] # Delete last newline character
            await interaction.response.send_message(result_string, ephemeral = True)

class TournamentDropdownView(discord.ui.View):

    def __init__(self, month_tournaments, bot, voting = False):
        super().__init__(timeout = None)
        self.voting = voting
        self.add_item(TournamentDropdown(month_tournaments, bot, voting = self.voting))

async def update_tournament_list(bot):
    tournaments = await get_invitationals()
    tournaments = [Tournament(t) for t in tournaments]
    tournaments.sort(key=lambda t: t.official_name)
    global TOURNAMENT_INFO
    TOURNAMENT_INFO = tournaments
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
    for t in tournaments: # For each tournament in the sheet
        # Check if the channel needs to be made / deleted
        ch = discord.utils.get(server.text_channels, name=t.channel_name)
        r = discord.utils.get(server.roles, name=t.official_name)
        tourney_date_str = str(t.tourney_date.date())
        before_days = int(t.open_days)
        after_days = int(t.closed_days)
        day_diff = (t.tourney_date - now).days
        print(f"Tournament List: Handling {t.official_name} (Day diff: {day_diff} days)")
        if (day_diff < (-1 * after_days)) and ch != None:
            # If past tournament date, now out of range
            if ch.category.name != CATEGORY_ARCHIVE:
                await auto_report("Tournament Channel & Role Needs to be Archived", "orange", f"The {ch.mention} channel and {r.mention} role need to be archived, as it is after the tournament date.")
        elif (day_diff <= before_days) and ch == None:
            # If before tournament and in range
            new_role = await server.create_role(name=t.official_name)
            new_channel = await server.create_text_channel(t.channel_name, category=tournament_category)
            await new_channel.edit(topic=f"{t.emoji} - Discussion around the {t.official_name} occurring on {tourney_date_str}.", sync_permissions=True)
            await new_channel.set_permissions(new_role, read_messages=True)
            await new_channel.set_permissions(all_tournaments_role, read_messages=True)
            await new_channel.set_permissions(server.default_role, read_messages=False)
        elif (day_diff > before_days):
            # Tournament is not yet ready to open
            # open_soon_list += (t[2] + " **" + t[0] + f"** - Opens in `{day_diff - before_days}` days.\n")
            pass

    help_embed = discord.Embed(
        title = ":first_place: Join a Tournament Channel!",
        color = discord.Color(0x2E66B6),
        description = f"""
        Below is a list of **tournament channels**. Some are available right now, some will be available soon, and others have been requested, but have not received enough support to be considered for a channel.

        To join a tournament channel, use the dropdowns below! Dropdowns are split up by date!

        To request a new tournament channel, please use the `/request` command in {bot_spam_channel.mention}. If you need help, feel free to let a {a.mention} or {gm.mention} know!
        """
    )
    await tourney_channel.purge() # Delete all messages to make way for new messages/views
    await tourney_channel.send(embed = help_embed)

    months = [
        {'name': 'October', 'number': 10, 'year': 2021},
        {'name': 'November', 'number': 11, 'year': 2021},
        {'name': 'December', 'number': 12, 'year': 2021},
        {'name': 'January', 'number': 1, 'year': 2022},
        {'name': 'February', 'number': 2, 'year': 2022}
    ]
    for month in months:
        month_tournaments = [t for t in tournaments if t.tourney_date.month == month['number'] and t.tourney_date.year == month['year'] and t.status == "open"]
        if len(month_tournaments) > 0:
            await tourney_channel.send(f"Join a channel for a tournament in **{month['name']} {month['year']}**:", view = TournamentDropdownView(month_tournaments, bot))
        else:
            # No tournaments in the given month :(
            await tourney_channel.send(f"Sorry, there are no channels opened for tournaments in **{month['name']} {month['year']}**.")

    voting_tournaments = [t for t in tournaments if t.status == "voting"]
    voting_embed = discord.Embed(
        title = ":second_place: Vote for a Tournament Channel!",
        color = discord.Color(0x2E66B6),
        description = "Below are tournament channels that are in the **voting phase**. These tournaments have been requested by users but have not received enough support to become official channels.\n\nIf you vote for these tournament channels to become official, you will automatically be added to these channels upon their creation."
    )
    await tourney_channel.send(embed = voting_embed)
    await tourney_channel.send("Please choose from the requested tournaments below:", view = TournamentDropdownView(voting_tournaments, bot, voting = True))