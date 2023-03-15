from __future__ import annotations

import datetime
import logging
import random
import traceback
from typing import TYPE_CHECKING, Any, Union

import discord
import src.discord.globals
from discord.ext import commands, tasks
from src.discord.invitationals import update_invitational_list
from src.discord.views import UnselfmuteView

if TYPE_CHECKING:
    from bot import PiBot

    from .reporter import Reporter


logger = logging.getLogger(__name__)


class CronTasks(commands.Cog):
    def __init__(self, bot: PiBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        try:
            await self.pull_prev_info()
        except Exception as e:
            logger.error(
                "Error in starting function with pulling previous information:"
            )
            traceback.print_exc()

        try:
            await update_invitational_list(self.bot, {})
        except Exception as e:
            logger.error("Error in starting function with updating tournament list:")
            traceback.print_exc()

        self.cron.start()
        self.change_bot_status.start()
        self.send_unselfmute.start()
        self.update_member_count.start()

    @tasks.loop(minutes=10)
    async def send_unselfmute(self):
        guild = self.bot.get_guild(src.discord.globals.SERVER_ID)
        unselfmute_channel = discord.utils.get(
            guild.text_channels, name=src.discord.globals.CHANNEL_UNSELFMUTE
        )
        assert isinstance(unselfmute_channel, discord.TextChannel)
        messages = [msg async for msg in unselfmute_channel.history()]
        if messages:
            await messages[0].edit(view=UnselfmuteView(self.bot))
        else:  # No message exists in the channel yet!
            embed = discord.Embed(
                description=f"""
                                  Clicking the reaction below will remove your selfmute, allowing you access back to the server. All of the remaining time on your selfmute will be removed. If you have questions, please DM a moderator.
                                  """,
                color=discord.Color.brand_red(),
            )
            await unselfmute_channel.send(embed=embed, view=UnselfmuteView(self.bot))

    def cog_unload(self):
        self.cron.cancel()
        self.change_bot_status.cancel()
        self.update_member_count.cancel()

    async def pull_prev_info(self):
        src.discord.globals.REPORTS = await self.bot.mongo_database.get_reports()
        src.discord.globals.PING_INFO = await self.bot.mongo_database.get_pings()
        src.discord.globals.TAGS = await self.bot.mongo_database.get_tags()
        src.discord.globals.EVENT_INFO = await self.bot.mongo_database.get_events()
        self.bot.settings = await self.bot.mongo_database.get_settings()
        assert isinstance(self.bot.settings, dict)

        src.discord.globals.CENSOR = await self.bot.mongo_database.get_censor()
        logger.info("Fetched previous variables.")

    async def add_to_cron(self, item_dict: dict) -> None:
        """
        Adds the given document to the CRON list.
        """
        await self.bot.mongo_database.insert("data", "cron", item_dict)

    async def delete_from_cron(self, doc_id: str) -> None:
        """
        Deletes a CRON task from the CRON list.
        """
        await self.bot.mongo_database.delete("data", "cron", doc_id)

    async def schedule_unban(
        self, user: discord.Member | discord.User, time: datetime.datetime
    ) -> None:
        """
        Schedules for a particular Discord user to be unbanned at a particular time.
        """
        item_dict = {"type": "UNBAN", "user": user.id, "time": time, "tag": str(user)}
        await self.add_to_cron(item_dict)

    async def schedule_unmute(
        self, user: discord.Member | discord.User, time: datetime.datetime
    ) -> None:
        """
        Schedules for a particular Discord user to be unmuted at a particular time.
        """
        item_dict = {"type": "UNMUTE", "user": user.id, "time": time, "tag": str(user)}
        await self.add_to_cron(item_dict)

    async def schedule_unselfmute(
        self, user: discord.Member | discord.User, time: datetime.datetime
    ) -> None:
        """
        Schedules for a particular Discord user to be un-selfmuted at a particular time.
        """
        item_dict = {
            "type": "UNSELFMUTE",
            "user": user.id,
            "time": time,
            "tag": str(user),
        }
        await self.add_to_cron(item_dict)

    async def schedule_status_remove(self, time: datetime.datetime) -> None:
        """
        Schedules Pi-Bot's status to be removed at a specific time.
        """
        item_dict = {"type": "REMOVE_STATUS", "time": time}
        await self.add_to_cron(item_dict)

    async def update_setting(self, setting_name: str, value: Any) -> None:
        """
        Updates the value of a setting.
        """
        await self.bot.mongo_database.update(
            "data",
            "settings",
            self.bot.settings["_id"],
            {"$set": {setting_name: value}},
        )

    @tasks.loop(minutes=5)
    async def update_member_count(self):
        """
        Autonomous task which updates the member count shown on a voice channel hidden to staff.
        """
        # Get the voice channel
        guild = self.bot.get_guild(src.discord.globals.SERVER_ID)
        channel_prefix = "Members"
        vc = discord.utils.find(
            lambda c: channel_prefix in c.name, guild.voice_channels
        )
        left_channel = discord.utils.get(
            guild.text_channels, name=src.discord.globals.CHANNEL_LEAVE
        )

        # Type checking
        assert isinstance(guild, discord.Guild)
        assert isinstance(vc, discord.VoiceChannel)
        assert isinstance(left_channel, discord.TextChannel)

        # Get relevant stats
        member_count = guild.member_count
        joined_today = len(
            [
                m
                for m in guild.members
                if isinstance(m.joined_at, datetime.datetime)
                and m.joined_at.date() == discord.utils.utcnow().date()
            ]
        )
        left_messages = [c async for c in left_channel.history(limit=200)]
        left_today = len(
            [
                m
                for m in left_messages
                if m.created_at.date() == discord.utils.utcnow().date()
            ]
        )

        # Edit the voice channel
        await vc.edit(name=f"{member_count} Members (+{joined_today}/-{left_today})")
        logger.debug("Refreshed member count.")

    @tasks.loop(minutes=1)
    async def cron(self) -> None:
        """
        The main CRON handler, running every minute. On every execution of the function, all CRON tasks are fetched and are evaluated to check if they are old and action needs to be taken.
        """
        logger.debug("Executing CRON...")
        # Get the relevant tasks
        cron_list = await self.bot.mongo_database.get_cron()

        for task in cron_list:
            # If the date has passed, execute task
            if discord.utils.utcnow() > task["time"]:
                try:
                    if task["type"] == "UNBAN":
                        await self.cron_handle_unban(task)
                    elif task["type"] == "UNMUTE":
                        await self.cron_handle_unmute(task)
                    elif task["type"] == "UNSELFMUTE":
                        await self.cron_handle_unselfmute(task)
                    elif task["type"] == "REMOVE_STATUS":
                        await self.cron_handle_remove_status(task)
                    else:
                        logger.error("ERROR:")
                        reporter_cog = self.bot.get_cog("Reporter")
                        await reporter_cog.create_cron_task_report(task)
                except Exception as _:
                    traceback.print_exc()
                    reporter_cog: commands.Cog | Reporter = self.bot.get_cog("Reporter")
                    await reporter_cog.create_cron_task_report(task)

    async def cron_handle_unban(self, task: dict):
        """
        Handles serving CRON tasks with the type of 'UNBAN'.
        """
        # Get the necessary resources
        server = self.bot.get_guild(src.discord.globals.SERVER_ID)
        reporter_cog: commands.Cog | Reporter = self.bot.get_cog("Reporter")

        # Type checking
        assert isinstance(server, discord.Guild)

        # Attempt to unban user
        member = await self.bot.fetch_user(task["user"])
        if member in server.members:
            # User is still in server, thus already unbanned
            await reporter_cog.create_cron_unban_auto_notice(member, is_present=True)
        else:
            # User is not in server, thus unban the
            already_unbanned = False
            try:
                await server.unban(member)
            except:
                # The unbanning failed (likely the user was already unbanned)
                already_unbanned = True
            await reporter_cog.create_cron_unban_auto_notice(
                member, is_present=False, already_unbanned=already_unbanned
            )

        # Remove cron task.
        await self.delete_from_cron(task["_id"])

    async def cron_handle_unmute(self, task: dict):
        """
        Handles serving CRON tasks with the type of 'UNMUTE'.
        """
        # Get the necessary resources
        server = self.bot.get_guild(src.discord.globals.SERVER_ID)
        reporter_cog: commands.Cog | Reporter = self.bot.get_cog("Reporter")
        muted_role = discord.utils.get(
            server.roles, name=src.discord.globals.ROLE_MUTED
        )

        # Type checking
        assert isinstance(server, discord.Guild)
        assert isinstance(muted_role, discord.Role)

        # Attempt to unmute user
        member = server.get_member(task["user"])
        if member in server.members:
            # User is still in server, thus can be unmuted
            await member.remove_roles(muted_role)
            await reporter_cog.create_cron_unmute_auto_notice(member, is_present=True)
        else:
            # User is not in server, thus no unmute can occur
            await reporter_cog.create_cron_unmute_auto_notice(member, is_present=False)

        # Remove cron task.
        await self.delete_from_cron(task["_id"])

    async def cron_handle_unselfmute(self, task: dict):
        """
        Handles serving CRON tasks with the type of 'UNSELFMUTE'.
        """
        # Get the necessary resources
        server = self.bot.get_guild(src.discord.globals.SERVER_ID)
        reporter_cog: commands.Cog | Reporter = self.bot.get_cog("Reporter")
        muted_role = discord.utils.get(
            server.roles, name=src.discord.globals.ROLE_SELFMUTE
        )

        # Type checking
        assert isinstance(server, discord.Guild)
        assert isinstance(muted_role, discord.Role)

        # Attempt to unmute user
        member = server.get_member(task["user"])
        if member in server.members:
            # User is still in server, thus can be unmuted
            await member.remove_roles(muted_role)

        # Remove cron task.
        await self.delete_from_cron(task["_id"])

    async def cron_handle_remove_status(self, task: dict):
        """
        Handles serving CRON tasks with the type of 'REMOVE_STATUS'.
        """
        # Attempt to remove status
        self.bot.settings["custom_bot_status_type"] = None  # reset local settings
        self.bot.settings["custom_bot_status_text"] = None  # reset local settings
        await self.bot.mongo_database.update(
            "data",
            "settings",
            self.bot.settings["_id"],
            {"$set": {"custom_bot_status_type": None, "custom_bot_status_text": None}},
        )  # update cloud settings
        self.change_bot_status.restart()  # update bot now

        # Remove cron task.
        await self.delete_from_cron(task["_id"])

    @tasks.loop(hours=1)
    async def change_bot_status(self):
        statuses = [
            {"type": "playing", "text": "Game On"},
            {"type": "listening", "text": "my SoM instrument"},
            {"type": "playing", "text": "with Pi-Bot Beta"},
            {"type": "playing", "text": "with my gravity vehicle"},
            {"type": "watching", "text": "the WS trials"},
            {"type": "watching", "text": "birbs"},
            {"type": "watching", "text": "2018 Nationals again"},
            {"type": "watching", "text": "the sparkly stars"},
            {"type": "watching", "text": "over the week"},
            {"type": "watching", "text": "for tourney results"},
            {"type": "listening", "text": "birb sounds"},
            {"type": "playing", "text": "with proteins"},
            {"type": "playing", "text": "with my detector"},
            {"type": "playing", "text": "Minecraft"},
            {"type": "playing", "text": "with circuits"},
            {"type": "watching", "text": "my PPP fall"},
            {"type": "playing", "text": "a major scale"},
            {"type": "listening", "text": "clinking medals"},
            {"type": "watching", "text": "the world learn"},
            {"type": "watching", "text": "SciOly grow"},
            {"type": "watching", "text": "tutorials"},
            {"type": "playing", "text": "with wiki templates"},
            {"type": "playing", "text": "the flute"},
            {"type": "watching", "text": "bear eat users"},
            {"type": "watching", "text": "xkcd"},
            {"type": "playing", "text": "with wiki templates"},
            {"type": "watching", "text": "Jmol tutorials"},
        ]
        bot_status = None
        if self.bot.settings["custom_bot_status_type"] == None:
            bot_status = random.choice(statuses)
        else:
            bot_status = {
                "type": self.bot.settings["custom_bot_status_type"],
                "text": self.bot.settings["custom_bot_status_text"],
            }

        if bot_status["type"] == "playing":
            await self.bot.change_presence(
                activity=discord.Game(name=bot_status["text"])
            )
        elif bot_status["type"] == "listening":
            await self.bot.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.listening, name=bot_status["text"]
                )
            )
        elif bot_status["type"] == "watching":
            await self.bot.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.watching, name=bot_status["text"]
                )
            )
        logger.info("Changed the bot's status.")


async def setup(bot: PiBot):
    await bot.add_cog(CronTasks(bot))
