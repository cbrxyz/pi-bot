import discord
import random
import json
import datetime
from discord.ext import commands, tasks
import src.discord.globals

from src.discord.tournaments import update_tournament_list
from src.mongo.mongo import get_cron, get_pings, get_censor, get_settings, get_reports, get_tags, get_events, insert, delete
from src.wiki.stylist import prettify_templates

class CronTasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("Initialized Tasks cog.")

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

    def cog_unload(self):
        self.cron.cancel()
        self.change_bot_status.cancel()
        self.update_member_count.cancel()

    async def pull_prev_info(self):
        src.discord.globals.REPORTS = await get_reports()
        src.discord.globals.PING_INFO = await get_pings()
        src.discord.globals.TAGS = await get_tags()
        src.discord.globals.EVENT_INFO = await get_events()
        src.discord.globals.SETTINGS = await get_settings()

        src.discord.globals.CENSOR = await get_censor()
        print("Fetched previous variables.")

    async def add_to_cron(self, item_dict: dict) -> None:
        """
        Adds the given document to the CRON list.
        """
        await insert('data', 'cron', item_dict)

    async def delete_from_cron(self, doc_id: str) -> None:
        """
        Deletes a CRON task from the CRON list.
        """
        await delete('data', 'cron', doc_id)

    async def schedule_unban(self, user: discord.User, time: datetime.datetime) -> None:
        """
        Schedules for a particular Discord user to be unbanned at a particular time.
        """
        item_dict = {
            'type': "UNBAN",
            'user': user.id,
            'time': time,
            'tag': str(user)
        }
        await self.add_to_cron(item_dict)

    async def schedule_unmute(self, user: discord.User, time: datetime.datetime) -> None:
        """
        Schedules for a particular Discord user to be unmuted at a particular time.
        """
        item_dict = {
            'type': "UNMUTE",
            'user': user.id,
            'time': time,
            'tag': str(user)
        }
        await self.add_to_cron(item_dict)

    async def schedule_unselfmute(self, user: discord.User, time: datetime.datetime) -> None:
        """
        Schedules for a particular Discord user to be un-selfmuted at a particular time.
        """
        item_dict = {
            'type': "UNSELFMUTE",
            'user': user.id,
            'time': time,
            'tag': str(user)
        }
        await self.add_to_cron(item_dict)

    @tasks.loop(minutes=5)
    async def update_member_count(self):
        """
        Autonomous task which updates the member count shown on a voice channel hidden to staff.
        """
        # Get the voice channel
        guild = self.bot.get_guild(src.discord.globals.SERVER_ID)
        channel_prefix = "Members"
        vc = discord.utils.find(lambda c: channel_prefix in c.name, guild.voice_channels)
        left_channel = discord.utils.get(guild.text_channels, name=src.discord.globals.CHANNEL_LEAVE)

        # Type checking
        assert isinstance(guild, discord.Guild)
        assert isinstance(vc, discord.VoiceChannel)
        assert isinstance(left_channel, discord.TextChannel)

        # Get relevant stats
        member_count = guild.member_count
        joined_today = len([m for m in guild.members if isinstance(m.joined_at, datetime.datetime) and m.joined_at.date() == discord.utils.utcnow().date()])
        left_messages = await left_channel.history(limit=200).flatten()
        left_today = len([m for m in left_messages if m.created_at.date() == discord.utils.utcnow().date()])

        # Edit the voice channel
        await vc.edit(name=f"{member_count} Members (+{joined_today}/-{left_today})")
        print("Refreshed member count.")

    @tasks.loop(minutes=1)
    async def cron(self) -> None:
        """
        The main CRON handler, running every minute. On every execution of the function, all CRON tasks are fetched and are evaluated to check if they are old and action needs to be taken.
        """
        # Get the relevant tasks
        cron_list = await get_cron()

        for task in cron_list:
            # If the date has passed, execute task
            if discord.utils.utcnow() > task['time']:
                try:
                    if task['type'] == "UNBAN":
                        await self.cron_handle_unban(task)
                    elif task['type'] == "UNMUTE":
                        await self.cron_handle_unmute(task)
                    elif task['type'] == "UNSTEALFISHBAN":
                        src.discord.globals.STEALFISH_BAN.remove(task['user'])
                        print(f"Un-stealfished user ID: {iden}")
                    else:
                        print("ERROR:")
                        reporter_cog = self.bot.get_cog('Reporter')
                        await reporter_cog.create_cron_task_report(task)
                    await delete("data", "cron", task["_id"])
                except Exception as _:
                    reporter_cog = self.bot.get_cog('Reporter')
                    await reporter_cog.create_cron_task_report(task)

    async def cron_handle_unban(self, task: dict):
        """
        Handles serving CRON tasks with the type of 'UNBAN'.
        """
        # Get the necessary resources
        server = self.bot.get_guild(src.discord.globals.SERVER_ID)
        reporter_cog = self.bot.get_cog("Reporter")

        # Type checking
        assert isinstance(server, discord.Guild)

        # Attempt to unban user
        member = await self.bot.fetch_user(task['user'])
        if member in server.members:
            # User is still in server, thus already unbanned
            await reporter_cog.create_cron_unban_auto_notice(member, is_present = True)
        else:
            # User is not in server, thus unban the
            already_unbanned = False
            try:
                await server.unban(member)
            except:
                # The unbanning failed (likely the user was already unbanned)
                already_unbanned = True
            await reporter_cog.create_cron_unban_auto_notice(member, is_present = False, already_unbanned = already_unbanned)

        # Remove cron task.
        await self.delete_from_cron(task['_id'])

    async def cron_handle_unmute(self, task: dict):
        """
        Handles serving CRON tasks with the type of 'UNMUTE'.
        """
        # Get the necessary resources
        server = self.bot.get_guild(src.discord.globals.SERVER_ID)
        reporter_cog = self.bot.get_cog("Reporter")
        muted_role = discord.utils.get(server.roles, name = src.discord.globals.ROLE_MUTED)

        # Type checking
        assert isinstance(server, discord.Guild)
        assert isinstance(muted_role, discord.Role)

        # Attempt to unmute user
        member = server.get_member(task['user'])
        if member in server.members:
            # User is still in server, thus can be unmuted
            await member.remove_roles(muted_role)
            await reporter_cog.create_cron_unmute_auto_notice(member, is_present = True)
        else:
            # User is not in server, thus no unmute can occur
            await reporter_cog.create_cron_unmute_auto_notice(member, is_present = False)

        # Remove cron task.
        await self.delete_from_cron(task['_id'])

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
        if src.discord.globals.SETTINGS['custom_bot_status_type'] == None:
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
