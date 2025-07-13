from __future__ import annotations

import datetime
import logging
import random
import traceback
from typing import TYPE_CHECKING

import discord
from beanie.odm.operators.update.general import Set
from discord.ext import commands, tasks

import src.discord.globals
from env import env
from src.discord.invitationals import update_invitational_list
from src.discord.views import UnselfmuteView
from src.mongo.models import Censor, Cron, Event, Ping, Settings, Tag

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
        except Exception:
            logger.error(
                "Error in starting function with pulling previous information:",
            )
            traceback.print_exc()

        try:
            await update_invitational_list(self.bot, {})
        except Exception:
            logger.error("Error in starting function with updating tournament list:")
            traceback.print_exc()

        self.cron.start()
        self.change_bot_status.start()
        self.send_unselfmute.start()
        self.update_member_count.start()

    @tasks.loop(minutes=10)
    async def send_unselfmute(self):
        guild = self.bot.get_guild(env.server_id)
        unselfmute_channel = discord.utils.get(
            guild.text_channels,
            name=src.discord.globals.CHANNEL_UNSELFMUTE,
        )
        assert isinstance(unselfmute_channel, discord.TextChannel)
        messages = [msg async for msg in unselfmute_channel.history()]
        if messages:
            await messages[0].edit(view=UnselfmuteView(self.bot))
        else:  # No message exists in the channel yet!
            embed = discord.Embed(
                description="""
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
        src.discord.globals.PING_INFO = await Ping.find_all().to_list()
        src.discord.globals.TAGS = await Tag.find_all().to_list()
        src.discord.globals.EVENT_INFO = await Event.find_all().to_list()
        settings = await Settings.find_one({})

        if not settings:
            logger.warn(
                "Settings were not found in database. Going to prompt user for info to construct a minimal config ...",
            )
            # TODO: Add env options to override these settings
            while True:
                try:
                    season_str = input("Please enter the year for the current season: ")
                    season = int(season_str)
                    break
                except ValueError:
                    print(f"{season_str} is not a valid year!")
                    pass
            settings = Settings(
                custom_bot_status_type=None,
                custom_bot_status_text=None,
                invitational_season=season,
            )
            await settings.save()

        self.bot.settings = settings

        src.discord.globals.CENSOR = await Censor.find_one({})

        if not src.discord.globals.CENSOR:
            src.discord.globals.CENSOR = Censor(words=[], emojis=[])
            await src.discord.globals.CENSOR.save()
        logger.info("Fetched previous variables.")

    async def schedule_unban(
        self,
        user: discord.Member | discord.User,
        time: datetime.datetime,
    ) -> None:
        """
        Schedules for a particular Discord user to be unbanned at a particular time.
        """
        await Cron(type="UNBAN", user=user.id, time=time, tag=str(user)).insert()

    async def schedule_unmute(
        self,
        user: discord.Member | discord.User,
        time: datetime.datetime,
    ) -> None:
        """
        Schedules for a particular Discord user to be unmuted at a particular time.
        """
        await Cron(type="UNMUTE", user=user.id, time=time, tag=str(user)).insert()

    async def schedule_unselfmute(
        self,
        user: discord.Member | discord.User,
        time: datetime.datetime,
    ) -> None:
        """
        Schedules for a particular Discord user to be un-selfmuted at a particular time.
        """
        await Cron(type="UNSELFMUTE", user=user.id, time=time, tag=str(user)).insert()

    async def schedule_status_remove(self, time: datetime.datetime) -> None:
        """
        Schedules Pi-Bot's status to be removed at a specific time.
        """
        await Cron(
            type="REMOVE_STATUS",
            time=time,
            user=0,
            tag="",
        ).insert()  # FIXME: Make user and time fields somehow depend on `type`

    @tasks.loop(minutes=5)
    async def update_member_count(self):
        """
        Autonomous task which updates the member count shown on a voice channel hidden to staff.
        """
        # Get the voice channel
        guild = self.bot.get_guild(env.server_id)
        channel_prefix = "Members"
        vc = discord.utils.find(
            lambda c: channel_prefix in c.name,
            guild.voice_channels,
        )
        left_channel = discord.utils.get(
            guild.text_channels,
            name=src.discord.globals.CHANNEL_LEAVE,
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
            ],
        )
        left_messages = [c async for c in left_channel.history(limit=200)]
        left_today = len(
            [
                m
                for m in left_messages
                if m.created_at.date() == discord.utils.utcnow().date()
            ],
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
        cron_list = await Cron.find_all().to_list()

        for task in cron_list:
            # If the date has passed, execute task
            if discord.utils.utcnow() > task.time:
                try:
                    if task.cron_type == "UNBAN":
                        await self.cron_handle_unban(task)
                    elif task.cron_type == "UNMUTE":
                        await self.cron_handle_unmute(task)
                    elif task.cron_type == "UNSELFMUTE":
                        await self.cron_handle_unselfmute(task)
                    elif task.cron_type == "REMOVE_STATUS":
                        await self.cron_handle_remove_status(task)
                    else:
                        logger.error("ERROR:")
                        reporter_cog = self.bot.get_cog("Reporter")
                        await reporter_cog.create_cron_task_report(task)
                except Exception:
                    traceback.print_exc()
                    reporter_cog: commands.Cog | Reporter = self.bot.get_cog("Reporter")
                    await reporter_cog.create_cron_task_report(task)

    async def cron_handle_unban(self, task: Cron):
        """
        Handles serving CRON tasks with the type of 'UNBAN'.
        """
        # Get the necessary resources
        server = self.bot.get_guild(env.server_id)
        reporter_cog: commands.Cog | Reporter = self.bot.get_cog("Reporter")

        # Type checking
        assert isinstance(server, discord.Guild)

        # Attempt to unban user
        member = await self.bot.fetch_user(task.user)
        if member in server.members:
            # User is still in server, thus already unbanned
            await reporter_cog.create_cron_unban_auto_notice(member, is_present=True)
        else:
            # User is not in server, thus unban the
            already_unbanned = False
            try:
                await server.unban(member)
            except Exception:
                # The unbanning failed (likely the user was already unbanned)
                already_unbanned = True
            await reporter_cog.create_cron_unban_auto_notice(
                member,
                is_present=False,
                already_unbanned=already_unbanned,
            )

        # Remove cron task.
        await task.delete()

    async def cron_handle_unmute(self, task: Cron):
        """
        Handles serving CRON tasks with the type of 'UNMUTE'.
        """
        # Get the necessary resources
        server = self.bot.get_guild(env.server_id)
        reporter_cog: commands.Cog | Reporter = self.bot.get_cog("Reporter")
        muted_role = discord.utils.get(
            server.roles,
            name=src.discord.globals.ROLE_MUTED,
        )

        # Type checking
        assert isinstance(server, discord.Guild)
        assert isinstance(muted_role, discord.Role)

        # Attempt to unmute user
        member = server.get_member(task.user)
        if member in server.members:
            # User is still in server, thus can be unmuted
            await member.remove_roles(muted_role)
            await reporter_cog.create_cron_unmute_auto_notice(member, is_present=True)
        else:
            # User is not in server, thus no unmute can occur
            await reporter_cog.create_cron_unmute_auto_notice(member, is_present=False)

        # Remove cron task.
        await task.delete()

    async def cron_handle_unselfmute(self, task: Cron):
        """
        Handles serving CRON tasks with the type of 'UNSELFMUTE'.
        """
        # Get the necessary resources
        server = self.bot.get_guild(env.server_id)
        self.bot.get_cog("Reporter")
        muted_role = discord.utils.get(
            server.roles,
            name=src.discord.globals.ROLE_SELFMUTE,
        )

        # Type checking
        assert isinstance(server, discord.Guild)
        assert isinstance(muted_role, discord.Role)

        # Attempt to unmute user
        member = server.get_member(task.user)
        if member in server.members:
            # User is still in server, thus can be unmuted
            await member.remove_roles(muted_role)

        # Remove cron task.
        await task.delete()

    async def cron_handle_remove_status(self, task: Cron):
        """
        Handles serving CRON tasks with the type of 'REMOVE_STATUS'.
        """
        # FIXME: Subject to premature removal of status if two /status commands are run with different expirations
        # Attempt to remove status
        await self.bot.settings.update(
            Set(
                {
                    Settings.custom_bot_status_type: None,
                    Settings.custom_bot_status_text: None,
                },
            ),
        )
        self.change_bot_status.restart()  # update bot now

        # Remove cron task.
        await task.delete()

    @tasks.loop(hours=1)
    async def change_bot_status(self):
        member_count = self.bot.get_guild(env.server_id).member_count or 0
        activities = [
            discord.Activity(type=discord.ActivityType.playing, name="Game On"),
            discord.Activity(type=discord.ActivityType.watching, name="bear eat users"),
            discord.Activity(type=discord.ActivityType.listening, name="lofi"),
            discord.Activity(
                type=discord.ActivityType.watching,
                name="my balsa plane fly",
            ),
            discord.Activity(
                type=discord.ActivityType.listening,
                name="#announcements",
            ),
            discord.Activity(
                type=discord.ActivityType.watching,
                name="Assassinator's next move",
            ),
            discord.Activity(
                type=discord.ActivityType.watching,
                name="the Recent Changes page",
            ),
            discord.Activity(
                type=discord.ActivityType.watching,
                name=f"over {member_count} members",
            ),
            discord.Activity(type=discord.ActivityType.playing, name="Tetris"),
            discord.Activity(type=discord.ActivityType.playing, name="Minecraft"),
            discord.Activity(type=discord.ActivityType.listening, name="birb calls"),
            discord.Activity(
                type=discord.ActivityType.watching,
                name="the sky for stars",
            ),
            discord.Activity(
                type=discord.ActivityType.watching,
                name="anatomical explanations",
            ),
            discord.Activity(
                type=discord.ActivityType.watching,
                name="ES training videos",
            ),
            discord.Activity(type=discord.ActivityType.watching, name="birbs"),
            discord.Activity(type=discord.ActivityType.playing, name="with circuits"),
            discord.Activity(
                type=discord.ActivityType.listening,
                name="clinking medals",
            ),
            discord.Activity(type=discord.ActivityType.listening, name="Taylor Swift"),
            discord.Activity(
                type=discord.ActivityType.playing,
                name="with wiki templates",
            ),
            discord.Activity(
                type=discord.ActivityType.listening,
                name="my SoM instrument",
            ),
            discord.Activity(
                type=discord.ActivityType.watching,
                name="my succulents grow",
            ),
            discord.Activity(
                type=discord.ActivityType.listening,
                name="voices in the wind",
            ),
            discord.Activity(
                type=discord.ActivityType.listening,
                name="voices in my head",
            ),
            discord.Activity(
                type=discord.ActivityType.listening,
                name="your suggestions",
            ),
            discord.Activity(
                type=discord.ActivityType.watching,
                name="cute cat videos",
            ),
            discord.Activity(
                type=discord.ActivityType.watching,
                name="physics lectures",
            ),
            discord.Activity(
                type=discord.ActivityType.watching,
                name="out for new staff",
            ),
            discord.Activity(type=discord.ActivityType.playing, name="with my bridge"),
            discord.Activity(
                type=discord.ActivityType.watching,
                name="Earth get hotter",
            ),
            discord.Activity(
                type=discord.ActivityType.playing,
                name="with my WiFi antenna",
            ),
            discord.Activity(
                type=discord.ActivityType.watching,
                name="for new forum posts",
            ),
            discord.Activity(type=discord.ActivityType.listening, name="the teachings"),
            discord.Activity(type=discord.ActivityType.listening, name="alumni advice"),
            discord.Activity(type=discord.ActivityType.watching, name="for bad words"),
            discord.Activity(
                type=discord.ActivityType.watching,
                name="for tourney results",
            ),
        ]
        activity = None
        if self.bot.settings.custom_bot_status_type is None:
            activity = random.choice(activities)
        else:
            try:
                activity_type = getattr(
                    discord.ActivityType,
                    self.bot.settings.custom_bot_status_type,
                )
                activity = discord.Activity(
                    type=activity_type,
                    text=self.bot.settings.custom_bot_status_text,
                )
            except Exception:
                activity = discord.Activity(
                    type=discord.ActivityType.watching,
                    text="Error with custom s.",
                )

        await self.bot.change_presence(activity=activity)
        logger.info("Changed the bot's status.")


async def setup(bot: PiBot):
    await bot.add_cog(CronTasks(bot))
