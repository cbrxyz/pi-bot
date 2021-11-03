import discord
import random
import json
import datetime
from discord.ext import commands, tasks
from src.discord.globals import PING_INFO, REPORTS, CRON_LIST, SERVER_ID, CHANNEL_LEAVE, can_post, ROLE_MUTED, ROLE_SELFMUTE, STEALFISH_BAN, CENSORED_EMOJIS, CENSORED_WORDS, EVENT_INFO, TAGS

from src.discord.tournaments import update_tournament_list
from src.mongo.mongo import get_cron, get_pings, get_censor, get_reports, get_tags, get_events, delete
from src.wiki.stylist import prettify_templates
from src.discord.utils import auto_report

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
            await update_tournament_list(self.bot, {})
        except Exception as e:
            print("Error in starting function with updating tournament list:")
            print(e)

        self.cron.start()
        self.change_bot_status.start()
        self.update_member_count.start()

        print("Tasks cog loaded")

    def cog_unload(self):
        self.cron.cancel()
        self.change_bot_status.cancel()
        self.update_member_count.cancel()

    async def pull_prev_info(self):
        global PING_INFO
        global REPORTS
        global CENSORED_WORDS
        global CENSORED_EMOJIS
        global TAGS
        global EVENT_INFO

        REPORTS = await get_reports()
        PING_INFO = await get_pings()
        TAGS = await get_tags()
        EVENT_INFO = await get_events()

        censor = await get_censor()
        CENSORED_WORDS = censor[0]
        CENSORED_EMOJIS = censor[1]
        print("Fetched previous variables.")

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

    @tasks.loop(minutes=1)
    async def cron(self):
        print("Executed cron.")
        cron_list = await get_cron()
        for task in cron_list:
            if datetime.datetime.utcnow() > task['time']:
                # The date has passed, now do
                try:
                    if task['type'] == "UNBAN":
                        server = self.bot.get_guild(SERVER_ID)
                        member = await self.bot.fetch_user(task['user'])
                        await server.unban(member)
                        print(f"Unbanned user ID: {iden}")
                    elif task['type'] == "UNMUTE":
                        server = self.bot.get_guild(SERVER_ID)
                        member = server.get_member(task['user'])
                        role = discord.utils.get(server.roles, name=ROLE_MUTED)
                        self_role = discord.utils.get(server.roles, name=ROLE_SELFMUTE)
                        await member.remove_roles(role, self_role)
                        print(f"Unmuted user ID: {iden}")
                    elif task['type'] == "UNSTEALFISHBAN":
                        STEALFISH_BAN.remove(task['user'])
                        print(f"Un-stealfished user ID: {iden}")
                    else:
                        print("ERROR:")
                        await auto_report(self.bot, "Error with a cron task", "red", f"Error: `{string}`")
                    await delete("data", "cron", task["_id"])
                except Exception as e:
                    await auto_report(self.bot, "Error with a cron task", "red", f"Error: `{e}`\nOriginal task: `{string}`")

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

def setup(bot):
    bot.add_cog(CronTasks(bot))
