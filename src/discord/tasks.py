import discord
import random
import json
import datetime
from discord.ext import commands, tasks
from src.discord.globals import PING_INFO, REPORT_IDS, TOURNEY_REPORT_IDS, COACH_REPORT_IDS, CRON_LIST, REQUESTED_TOURNAMENTS, SERVER_ID, CHANNEL_LEAVE, can_post, ROLE_MUTED, ROLE_SELFMUTE, STEALFISH_BAN
from src.sheets.sheets import send_variables, get_variables

from tournaments import update_tournament_list
from src.forums.forums import open_browser
from src.wiki.stylist import prettify_templates
from src.discord.utils import auto_report, refresh_algorithm, datetime_converter

class CronTasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_ready(self):
        try:
            await self.pull_prev_info()
        except Exception as e:
            print("Error in starting function with pulling previous information:")
            print(e)
    
        try:
            await update_tournament_list(bot)
        except Exception as e:
            print("Error in starting function with updating tournament list:")
            print(e)
    
        try:
            self.refresh_sheet.start()
        except Exception as e:
            print("Error in starting function with updating tournament list:")
            print(e)
    
        self.post_something.start()
        self.cron.start()
        self.go_stylist.start()
        self.manage_welcome.start()
        self.store_variables.start()
        self.change_bot_status.start()
        self.update_member_count.start()
        
        print("Tasks cog loaded")
    
    def cog_unload(self):
        self.refresh_sheet.cancel()
        self.post_something.cancel()
        self.cron.cancel()
        self.go_stylist.cancel()
        self.manage_welcome.cancel()
        self.store_variables.cancel()
        self.change_bot_status.cancel()
        self.update_member_count.cancel()
    
    async def pull_prev_info(self):
        data = await get_variables()
        global PING_INFO
        global REPORT_IDS
        global TOURNEY_REPORT_IDS
        global COACH_REPORT_IDS
        global CRON_LIST
        global REQUESTED_TOURNAMENTS
        REPORT_IDS = data[0][0]
        PING_INFO = data[1][0]
        TOURNEY_REPORT_IDS = data[2][0]
        COACH_REPORT_IDS = data[3][0]
        cron = data[4][0]
        for c in cron:
            try:
                c['date'] = datetime.datetime.strptime(c['date'], "%Y-%m-%d %H:%M:%S.%f")
            except Exception as e:
                print("ERROR WITH CRON TASK: ", e)
        CRON_LIST = cron
        REQUESTED_TOURNAMENTS = data[5][0]
        print("Fetched previous variables.")
    
    async def prepare_for_sending(self, type="variable"):
        """Sends local variables to the administrative sheet as a backup."""
        r1 = json.dumps(REPORT_IDS)
        r2 = json.dumps(PING_INFO)
        r3 = json.dumps(TOURNEY_REPORT_IDS)
        r4 = json.dumps(COACH_REPORT_IDS)
        r5 = json.dumps(CRON_LIST, default = datetime_converter)
        r6 = json.dumps(REQUESTED_TOURNAMENTS)
        await send_variables([[r1], [r2], [r3], [r4], [r5], [r6]], type)
        print("Stored variables in sheet.")
        
    async def handle_cron(self, string):
        try:
            if string.find("unban") != -1:
                iden = int(string.split(" ")[1])
                server = self.bot.get_guild(SERVER_ID)
                member = await self.bot.fetch_user(int(iden))
                await server.unban(member)
                print(f"Unbanned user ID: {iden}")
            elif string.find("unmute") != -1:
                iden = int(string.split(" ")[1])
                server = self.bot.get_guild(SERVER_ID)
                member = server.get_member(int(iden))
                role = discord.utils.get(server.roles, name=ROLE_MUTED)
                self_role = discord.utils.get(server.roles, name=ROLE_SELFMUTE)
                await member.remove_roles(role, self_role)
                print(f"Unmuted user ID: {iden}")
            elif string.find("unstealfishban") != -1:
                iden = int(string.split(" ")[1])
                STEALFISH_BAN.remove(iden)
                print(f"Un-stealfished user ID: {iden}")
            else:
                print("ERROR:")
                await auto_report(self.bot, "Error with a cron task", "red", f"Error: `{string}`")
        except Exception as e:
            await auto_report(self.bot, "Error with a cron task", "red", f"Error: `{e}`\nOriginal task: `{string}`")
        
    @tasks.loop(minutes=5)
    async def update_member_count(self):
        """Updates the member count shown on hidden VC"""
        guild = self.bot.get_guild(SERVER_ID)
        channel_prefix = "Members"
        vc = discord.utils.find(lambda c: channel_prefix in c.name, guild.voice_channels)
        mem_count = guild.member_count
        joined_today = len([m for m in guild.members if m.joined_at.date() == datetime.datetime.today().date()])
        left_channel = discord.utils.get(guild.text_channels, name=CHANNEL_LEAVE)
        left_messages = await left_channel.history(limit=200).flatten()
        left_today = len([m for m in left_messages if m.created_at.date() == datetime.datetime.today().date()])
        await vc.edit(name=f"{mem_count} Members (+{joined_today}/-{left_today})")
        print("Refreshed member count.")
        
    @tasks.loop(seconds=30.0)
    async def refresh_sheet(self):
        """Refreshes the censor list and stores variable backups."""
        try:
            await refresh_algorithm()
        except Exception as e:
            print("Error when completing the refresh algorithm when refreshing the sheet:")
            print(e)
    
        try:
            await self.prepare_for_sending()
        except Exception as e:
            print("Error when sending variables to log sheet:")
            print(e)
    
        print("Attempted to refresh/store data from/to sheet.")
    
    @tasks.loop(hours=10)
    async def store_variables(self):
        await self.prepare_for_sending("store")
    
    @tasks.loop(hours=24)
    async def go_stylist(self):
        await prettify_templates()
        
    @tasks.loop(minutes=10)
    async def manage_welcome(self):
        server = self.bot.get_guild(SERVER_ID)
        now = datetime.datetime.now()
        # Channel message deleting is currently disabled
        # if now.hour < ((0 - TZ_OFFSET) % 24) or now.hour > ((11 - TZ_OFFSET) % 24):
        #     print(f"Cleaning #{CHANNEL_WELCOME}.")
        #     # if between 12AM EST and 11AM EST do not do the following:
        #     channel = discord.utils.get(server.text_channels, name=CHANNEL_WELCOME)
        #     async for message in channel.history(limit=None):
        #         # if message is over 3 hours old
        #         author = message.author
        #         user_no_delete = await is_launcher_no_ctx(message.author)
        #         num_of_roles = len(author.roles)
        #         if num_of_roles > 4 and (now - author.joined_at).seconds // 60 > 1 and not user_no_delete:
        #             await _confirm([author])
        #         if (now - message.created_at).seconds // 3600 > 3 and not message.pinned:
        #             # delete it
        #             await message.delete()
        # else:
        #     print(f"Skipping #{CHANNEL_WELCOME} clean because it is outside suitable time ranges.")
    
    @tasks.loop(minutes=1)
    async def cron(self):
        print("Executed cron.")
        global CRON_LIST
        for c in CRON_LIST:
            date = c['date']
            if datetime.datetime.now() > date:
                # The date has passed, now do
                CRON_LIST.remove(c)
                await self.handle_cron(c['do'])
    
    @tasks.loop(hours=1)
    async def change_bot_status(self):
        statuses = [
            {"type": "playing", "message": "Game On"},
            {"type": "listening", "message": "my SoM instrument"},
            {"type": "playing", "message": "with Pi-Bot Beta"},
            {"type": "playing", "message": "with my gravity vehicle"},
            {"type": "watching", "message": "the WS trials"},
            {"type": "watching", "message": "birbs"},
            {"type": "watching", "message": "2018 Nationals again"},
            {"type": "watching", "message": "the sparkly stars"},
            {"type": "watching", "message": "over the week"},
            {"type": "watching", "message": "for tourney results"},
            {"type": "listening", "message": "birb sounds"},
            {"type": "playing", "message": "with proteins"},
            {"type": "playing", "message": "with my detector"},
            {"type": "playing", "message": "Minecraft"},
            {"type": "playing", "message": "with circuits"},
            {"type": "watching", "message": "my PPP fall"},
            {"type": "playing", "message": "a major scale"},
            {"type": "listening", "message": "clinking medals"},
            {"type": "watching", "message": "the world learn"},
            {"type": "watching", "message": "SciOly grow"},
            {"type": "watching", "message": "tutorials"},
            {"type": "playing", "message": "with wiki templates"},
            {"type": "playing", "message": "the flute"},
            {"type": "watching", "message": "bear eat users"},
            {"type": "watching", "message": "xkcd"},
            {"type": "playing", "message": "with wiki templates"},
            {"type": "watching", "message": "Jmol tutorials"},
        ]
        botStatus = random.choice(statuses)
        if botStatus["type"] == "playing":
            await self.bot.change_presence(activity=discord.Game(name=botStatus["message"]))
        elif botStatus["type"] == "listening":
            await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=botStatus["message"]))
        elif botStatus["type"] == "watching":
            await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=botStatus["message"]))
        print("Changed the bot's status.")
    
    @tasks.loop(hours=28)
    async def post_something(self):
        global can_post
        """Allows Pi-Bot to post markov-generated statements to the forums."""
        if can_post:
            print("Attempting to post something.")
            await open_browser()
        else:
            can_post = True
            
def setup(bot):
    bot.add_cog(CronTasks(bot))