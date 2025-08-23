"""
Functionality for most member commands. These commands frequently help members manage
their state on the server, including allowing them to change their roles or subscriptions.
"""
from __future__ import annotations

import datetime
import random
import re
from typing import TYPE_CHECKING, Literal

import discord
import wikipedia as wikip
from aioify import aioify
from discord import app_commands
from discord.ext import commands

import src.discord.globals
from commandchecks import is_in_bot_spam, is_staff_from_ctx
from env import env
from src.discord.globals import (
    CATEGORY_STAFF,
    CHANNEL_INVITATIONALS,
    CHANNEL_UNSELFMUTE,
    ROLE_LH,
    ROLE_MR,
    ROLE_SELFMUTE,
    RULES,
)
from src.discord.views import YesNo
from src.mongo.models import Cron
from src.wiki.wiki import implement_command

if TYPE_CHECKING:
    from bot import PiBot

    from .reporter import Reporter


class MemberCommands(commands.Cog):
    """
    Class containing several commands meant to be executed by members to control
    their state across the server.
    """

    # pylint: disable=no-self-use

    def __init__(self, bot: PiBot):
        self.bot = bot
        self.aiowikip = aioify(obj=wikip)

    @app_commands.command(description="Looking for help? Try this!")
    @app_commands.guilds(*env.slash_command_guilds)
    @app_commands.checks.cooldown(2, 20, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.check(is_in_bot_spam)
    async def help(self, interaction: discord.Interaction):
        """
        Discord command that gives general help about the bot and server.

        Permissions:
            None: Accessible by all members.

        Args:
            interaction (discord.Interaction): The interaction sent from Discord.
        """
        server = self.bot.get_guild(env.server_id)
        invitationals_channel = discord.utils.get(
            server.text_channels,
            name=CHANNEL_INVITATIONALS,
        )

        # Type checking
        assert isinstance(invitationals_channel, discord.TextChannel)

        help_embed = discord.Embed(
            title="Looking for help?",
            color=discord.Color(0x2E66B6),
            description=f"""
            Hey there, I'm Scioly.org's resident bot, and I'm here to assist with all of your needs.

            To interact with me, use _slash commands_ by typing `/` and the name of the command into the text bar below. You can also use the dropdowns in the {invitationals_channel.mention} invitational to assign yourself roles!

            If you're looking for more help, feel free to ask other members (including our helpful staff members) for more information.
            """,
        )

        return await interaction.response.send_message(embed=help_embed)

    @app_commands.command(description="Gets the profile information for a username.")
    @app_commands.describe(
        username="The username to get information about. Defaults to your nickname/username.",
    )
    @app_commands.guilds(*env.slash_command_guilds)
    @app_commands.checks.cooldown(10, 60, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.check(is_in_bot_spam)
    async def profile(
        self,
        interaction: discord.Interaction,
        username: str | None = None,
    ):
        """
        Allows a user to get information about a Scioly.org profile.

        Permissions:
            Confirmed member: Unconfirmed members do not have access to this command.

        Args:
            interaction (discord.Interaction): The interaction sent from Discord.
            username (Optional[str]): The Scioly.org username to get profile information for.
                If None, then defaults to the user's shown name.
        """
        if username is None:
            username = interaction.user.nick or interaction.user.name

        async with self.bot.session.get(
            f"https://scioly.org/forums/memberlist.php?mode=viewprofile&un={username}",
        ) as page:
            if page.status > 400:
                return await interaction.response.send_message(
                    content=f"Sorry, I couldn't find a user by the username of `{username}`.",
                )
            text = await page.content.read()
            text = text.decode("utf-8")

        description = ""
        total_posts_matches = re.search(
            r"(?:<dt>Total posts:<\/dt>\s+<dd>)(\d+)",
            text,
            re.MULTILINE,
        )
        if total_posts_matches is None:
            return await interaction.response.send_message(
                content=f"Sorry, I couldn't find a user by the username of `{username}`.",
            )
        else:
            description += f"**Total Posts:** `{total_posts_matches.group(1)} posts`\n"

        has_thanked_matches = re.search(r"Has thanked: <a.*?>(\d+)", text, re.MULTILINE)
        description += f"**Has Thanked:** `{has_thanked_matches.group(1)} times`\n"

        been_thanked_matches = re.search(
            r"Been(?:&nbsp;)?thanked: <a.*?>(\d+)",
            text,
            re.MULTILINE,
        )
        description += f"**Been Thanked:** `{been_thanked_matches.group(1)} times`\n"

        date_regexes = [
            {"name": "Joined", "regex": r"<dt>Joined:</dt>\s+<dd>(.*?)</dd>"},
            {"name": "Last Active", "regex": r"<dt>Last active:</dt>\s+<dd>(.*?)</dd>"},
        ]
        for pattern in date_regexes:
            try:
                matches = re.search(pattern["regex"], text, re.MULTILINE)
                raw_dt_string = matches.group(1)
                raw_dt_string = raw_dt_string.replace("st", "")
                raw_dt_string = raw_dt_string.replace("nd", "")
                raw_dt_string = raw_dt_string.replace("rd", "")
                raw_dt_string = raw_dt_string.replace("th", "")

                raw_dt = datetime.datetime.strptime(
                    raw_dt_string,
                    "%B %d, %Y, %I:%M %p",
                )
                description += (
                    f"**{pattern['name']}:** {discord.utils.format_dt(raw_dt, 'R')}\n"
                )
            except Exception:
                # Occurs if the time can't be parsed/found
                pass

        for i in range(1, 7):
            stars_matches = re.search(
                rf"<img src=\"./images/ranks/stars{i}\.gif\"",
                text,
                re.MULTILINE,
            )
            if stars_matches is not None:
                description += f"\n**Stars:** {i * ':star:'}"
                break
            exalts_matches = re.search(
                rf"<img src=\"./images/ranks/exalt{i}\.gif\"",
                text,
                re.MULTILINE,
            )
            if exalts_matches is not None:
                description += (
                    f"\n**Stars:** {4 * ':star:'}\n"  # All exalts have 4 stars
                )
                description += f"**Medals:** {i * ':medal:'}"
                break

        profile_embed = discord.Embed(
            title=f"`{username}`",
            color=discord.Color(0x2E66B6),
            description=description,
        )

        avatar_matches = re.search(
            r"<img class=\"avatar\" src=\"(.*?)\"",
            text,
            re.MULTILINE,
        )
        if avatar_matches is not None:
            profile_embed.set_thumbnail(
                url="https://scioly.org/forums" + avatar_matches.group(1)[1:],
            )

        await interaction.response.send_message(embed=profile_embed)

    @app_commands.command(description="Returns the number of members in the server.")
    @app_commands.guilds(*env.slash_command_guilds)
    @app_commands.checks.cooldown(5, 60, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.check(is_in_bot_spam)
    async def count(self, interaction: discord.Interaction):
        """
        Returns the number of members in the server.

        Permissions:
            None: All members have access to this command.

        Args:
            interaction (discord.Interaction): The interaction sent by Discord.
        """
        guild = interaction.user.guild
        await interaction.response.send_message(
            content=f"Currently, there are `{len(guild.members)}` members in the server.",
        )

    @app_commands.command(description="Mutes yourself.")
    @app_commands.describe(mute_length="How long to mute yourself for.")
    @app_commands.guilds(*env.slash_command_guilds)
    @app_commands.checks.cooldown(1, 60, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.check(is_in_bot_spam)
    async def selfmute(
        self,
        interaction: discord.Interaction,
        mute_length: Literal[
            "10 minutes",
            "30 minutes",
            "1 hour",
            "2 hours",
            "4 hours",
            "8 hours",
            "1 day",
            "4 days",
            "7 days",
            "1 month",
            "1 year",
        ],
    ):
        """
        Discord command that allows a member to mute themselves.

        Permissions:
            Confirmed members: Unconfirmed members cannot access this command.

        Args:
            interaction (discord.Interaction): The interaction sent by Discord.
            mute_length (str): The amount of time the user wishes to mute themselves.
        """
        if is_staff_from_ctx(interaction, no_raise=True):
            return await interaction.response.send_message(
                "Staff members can't self mute! Sorry!",
            )

        member = interaction.user

        times = {
            "10 minutes": discord.utils.utcnow() + datetime.timedelta(minutes=10),
            "30 minutes": discord.utils.utcnow() + datetime.timedelta(minutes=30),
            "1 hour": discord.utils.utcnow() + datetime.timedelta(hours=1),
            "2 hours": discord.utils.utcnow() + datetime.timedelta(hours=2),
            "4 hours": discord.utils.utcnow() + datetime.timedelta(hours=4),
            "8 hours": discord.utils.utcnow() + datetime.timedelta(hours=8),
            "1 day": discord.utils.utcnow() + datetime.timedelta(days=1),
            "4 days": discord.utils.utcnow() + datetime.timedelta(days=4),
            "7 days": discord.utils.utcnow() + datetime.timedelta(days=7),
            "1 month": discord.utils.utcnow() + datetime.timedelta(days=30),
            "1 year": discord.utils.utcnow() + datetime.timedelta(days=365),
        }
        selected_time = times[mute_length]

        original_shown_embed = discord.Embed(
            title="Mute Confirmation",
            color=discord.Color.brand_red(),
            description=f"""
            You will be muted across the entire server. You will no longer be able to communicate in any channels you can read until {discord.utils.format_dt(selected_time)}.
            """,
        )

        view = YesNo()
        await interaction.response.send_message(
            content="Please confirm that you would like to mute yourself.",
            view=view,
            embed=original_shown_embed,
            ephemeral=True,
        )

        await view.wait()
        if view.value:
            try:
                role = discord.utils.get(member.guild.roles, name=ROLE_SELFMUTE)
                unselfmute_channel = discord.utils.get(
                    member.guild.text_channels,
                    name=CHANNEL_UNSELFMUTE,
                )
                await member.add_roles(role)
                await Cron(
                    type="UNSELFMUTE",
                    user=member.id,
                    time=times[mute_length],
                    tag=str(member),
                ).insert()
                return await interaction.edit_original_response(
                    content=f"You have been muted. You may use the button in the {unselfmute_channel.mention} channel to unmute.",
                    embed=None,
                    view=None,
                )
            except Exception:
                pass

        return await interaction.edit_original_response(
            content="The operation was cancelled, and you can still speak throughout the server.",
            embed=None,
            view=None,
        )

    @app_commands.command(
        description="Requests a new invitational channel! Note: This request will be sent to staff for approval.",
    )
    @app_commands.describe(
        invitational="The official name of the invitational you would like to add.",
    )
    @app_commands.guilds(*env.slash_command_guilds)
    @app_commands.checks.cooldown(3, 60, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.check(is_in_bot_spam)
    async def request(self, interaction: discord.Interaction, invitational: str):
        """
        Discord command allowing members to request a new invitational channel.

        Permissions:
            Confirmed members: Unconfirmed members cannot access this command.

        Args:
            interaction (discord.Interaction): The interaction sent by Discord.
            invitational (str): The specific invitational name the user is requesting
                to be added.
        """
        reporter_cog: commands.Cog | Reporter = self.bot.get_cog("Reporter")
        await reporter_cog.create_invitational_request_report(
            interaction.user,
            invitational,
        )
        await interaction.response.send_message(
            f"Thanks for the request. Staff will review your request to add an invitational channel for `{invitational}`. In the meantime, please do not make additional requests.",
        )

    @app_commands.command(description="Returns information about the bot and server.")
    @app_commands.guilds(*env.slash_command_guilds)
    @app_commands.checks.cooldown(2, 20, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.check(is_in_bot_spam)
    async def about(self, interaction: discord.Interaction):
        """
        Discord command which prints information about the bot.

        Permissions:
            None: This command can be access by all members.

        Args:
            interaction (discord.Interaction): The interaction sent by Discord.
        """
        repo = "https://github.com/scioly/pi-bot"
        wiki_link = "https://scioly.org/wiki/User:Pi-Bot"
        forums_link = (
            "https://scioly.org/forums/memberlist.php?mode=viewprofile&u=62443"
        )
        avatar_url = self.bot.user.display_avatar.url

        embed = discord.Embed(
            title=f"**Pi-Bot {self.bot.__version__}**",
            color=discord.Color(0xF86D5F),
            description="""
            Hey there! I'm Pi-Bot, and I help to manage the Scioly.org forums, wiki, and chat. You'll often see me around this Discord server to help users get roles and information about Science Olympiad.

            I'm developed by the community. If you'd like to find more about development, you can find more by visiting the links below.
            """,
        )
        embed.add_field(name="Code Repository", value=repo, inline=False)
        embed.add_field(name="Wiki Page", value=wiki_link, inline=False)
        embed.add_field(name="Forums Page", value=forums_link, inline=False)
        embed.set_footer(text=f"Version Commit: {self.bot.__commit__ or 'Unknown'}")
        embed.set_thumbnail(url=avatar_url)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(description="Returns the Discord server invite.")
    @app_commands.guilds(*env.slash_command_guilds)
    @app_commands.checks.cooldown(5, 60, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.check(is_in_bot_spam)
    async def invite(self, interaction: discord.Interaction):
        """
        Discord command which returns an invite link to the Discord server.

        Permissions:
            None: All members can access this command.

        Args:
            interaction (discord.Interaction): The interaction sent by Discord.
        """
        await interaction.response.send_message("https://discord.gg/C9PGV6h")

    @app_commands.command(
        description="Returns a link to the Scioly.org forums.",
    )
    @app_commands.describe(destination="The area of the site to link to.")
    @app_commands.guilds(*env.slash_command_guilds)
    @app_commands.checks.cooldown(5, 60, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.check(is_in_bot_spam)
    async def link(
        self,
        interaction: discord.Interaction,
        destination: Literal["forums", "exchange", "gallery", "obb", "wiki", "tests"],
    ):
        """
        Discord command which returns a specific Scioly.org link.

        Permissions:
            Confirmed members: Unconfirmed members cannot access this command.

        Args:
            interaction (discord.Interaction): The interaction sent by Discord.
            destination (str): The specific link destination on Scioly.org
        """
        destination_dict = {
            "forums": "forums",
            "wiki": "wiki",
            "tests": "tests",
            "exchange": "tests",
            "gallery": "gallery",
            "obb": "obb",
        }
        await interaction.response.send_message(
            f"<https://scioly.org/{destination_dict[destination]}>",
        )

    @app_commands.command(description="Returns a random number, inclusively.")
    @app_commands.describe(
        minimum="The minimum number to choose from. Defaults to 0.",
        maximum="The maximum number to choose from. Defaults to 10.",
    )
    @app_commands.guilds(*env.slash_command_guilds)
    @app_commands.checks.cooldown(5, 60, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.check(is_in_bot_spam)
    async def random(
        self,
        interaction: discord.Interaction,
        minimum: int = 0,
        maximum: int = 10,
    ):
        """
        Discord command which returns a random number between two numbers.

        Permissions:
            Confirmed members: Unconfirmed members cannot access this command.

        Args:
            interaction (discord.Interaction): The specific interaction sent by discord.
            minimum (int): The smallest number. Defaults to 0.
            maximum (int): The largest number. Defaults to 10.
        """
        if minimum > maximum:
            maximum, minimum = minimum, maximum

        num = random.randrange(minimum, maximum + 1)
        await interaction.response.send_message(
            f"Random number between `{minimum}` and `{maximum}`: `{num}`",
        )

    @app_commands.command(description="Returns information about a given rule.")
    @app_commands.describe(rule="The rule to cite.")
    @app_commands.guilds(*env.slash_command_guilds)
    @app_commands.checks.cooldown(5, 60, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.check(is_in_bot_spam)
    async def rule(
        self,
        interaction: discord.Interaction,
        rule: Literal[
            "Rule #1: Treat all with respect.",
            "Rule #2: No profanity/inappropriateness.",
            "Rule #3: Treat delicate subjects carefully.",
            "Rule #4: Do not spam or flood.",
            "Rule #5: Avoid excessive pinging.",
            "Rule #6: Avoid excessive caps.",
            "Rule #7: No doxxing/name-dropping.",
            "Rule #8: No witch-hunting.",
            "Rule #9: No impersonating.",
            "Rule #10: Do not use alts.",
            "Rule #11: Do not violate SOINC copyrights.",
            "Rule #12: No advertising.",
            "Rule #13: Use good judgement.",
        ],
    ):
        """
        Discord command which gets a specified rule.

        Permissions:
            Confirmed members: Unconfirmed members cannot access this command.

        Args:
            interaction (discord.Interaction): The interaction sent by Discord.
            rule (str): The rule to print.
        """
        num = re.findall(r"Rule #(\d+)", rule)
        num = int(num[0])
        rule = RULES[int(num) - 1]
        return await interaction.response.send_message(f"**Rule {num}:**\n> {rule}")

    @app_commands.command(description="Information about gaining the @Coach role.")
    @app_commands.guilds(*env.slash_command_guilds)
    @app_commands.checks.cooldown(5, 60, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.check(is_in_bot_spam)
    async def coach(self, interaction: discord.Interaction):
        """
        Discord command returning the link to the form to apply for the @Coach role.

        Permissions:
            None: All members can access this command.

        Args:
            interaction (discord.Interaction): The interaction sent by Discord.
        """
        await interaction.response.send_message(
            "If you would like to apply for the `Coach` role, please fill out the form here: "
            "<https://forms.gle/UBKpWgqCr9Hjw9sa6>.",
            ephemeral=True,
        )

    @app_commands.command(description="Information about the current server.")
    @app_commands.guilds(*env.slash_command_guilds)
    @app_commands.checks.cooldown(5, 60, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.check(is_in_bot_spam)
    async def info(self, interaction: discord.Interaction):
        """
        Discord command which gets information about the Discord server.

        Permissions:
            Confirmed members: Unconfirmed members cannot access this command.

        Args:
            interaction (discord.Interaction): The specific interaction sent by Discord.
        """
        server = interaction.guild
        name = server.name
        owner = server.owner
        creation_date = discord.utils.format_dt(server.created_at, "R")
        emoji_count = len(server.emojis)
        icon = server.icon.url
        animated_icon = server.icon.is_animated()
        iden = server.id
        banner = server.banner.url if server.banner else "None"
        desc = server.description
        mfa_level = server.mfa_level
        verification_level = server.verification_level
        content_filter = server.explicit_content_filter
        default_notifs = server.default_notifications
        features = server.features
        splash = server.splash.url if server.splash else "None"
        premium_level = server.premium_tier
        boosts = server.premium_subscription_count
        channel_count = len(server.channels)
        text_channel_count = len(server.text_channels)
        voice_channel_count = len(server.voice_channels)
        category_count = len(server.categories)
        system_channel = server.system_channel
        if isinstance(system_channel, discord.TextChannel):
            system_channel = system_channel.mention
        rules_channel = server.rules_channel
        if isinstance(rules_channel, discord.TextChannel):
            rules_channel = rules_channel.mention
        public_updates_channel = server.public_updates_channel
        if isinstance(public_updates_channel, discord.TextChannel):
            public_updates_channel = public_updates_channel.mention
        emoji_limit = server.emoji_limit
        bitrate_limit = server.bitrate_limit
        filesize_limit = round(server.filesize_limit / 1000000, 3)
        boosters = ", ".join([b.mention for b in server.premium_subscribers])
        role_count = len(server.roles)
        member_count = len(server.members)
        max_members = server.max_members
        discovery_splash_url = (
            server.discovery_splash.url if server.discovery_splash else "None"
        )
        member_percentage = round(member_count / max_members * 100, 3)
        emoji_percentage = round(emoji_count / emoji_limit * 100, 3)
        channel_percentage = round(channel_count / 500 * 100, 3)
        role_percentage = round(role_count / 250 * 100, 3)

        fields = [
            {
                "name": "Basic Information",
                "value": (
                    f"**Creation Date:** {creation_date}\n"
                    + f"**ID:** {iden}\n"
                    + f"**Animated Icon:** {animated_icon}\n"
                    + f"**Banner URL:** {banner}\n"
                    + f"**Splash URL:** {splash}\n"
                    + f"**Discovery Splash URL:** {discovery_splash_url}"
                ),
                "inline": False,
            },
            {
                "name": "Nitro Information",
                "value": (
                    f"**Nitro Level:** {premium_level} ({boosts} individual boosts)\n"
                    + f"**Boosters:** {boosters}"
                ),
                "inline": False,
            },
        ]
        if interaction.channel.category.name == CATEGORY_STAFF:
            fields.extend(
                [
                    {
                        "name": "Staff Information",
                        "value": (
                            f"**Owner:** {owner}\n"
                            + f"**MFA Level:** {mfa_level}\n"
                            + f"**Verification Level:** {verification_level}\n"
                            + f"**Content Filter:** {content_filter}\n"
                            + f"**Default Notifications:** {default_notifs}\n"
                            + f"**Features:** {features}\n"
                            + f"**Bitrate Limit:** {bitrate_limit}\n"
                            + f"**Filesize Limit:** {filesize_limit} MB"
                        ),
                        "inline": False,
                    },
                    {
                        "name": "Channels",
                        "value": (
                            f"**Public Updates Channel:** {public_updates_channel}\n"
                            + f"**System Channel:** {system_channel}\n"
                            + f"**Rules Channel:** {rules_channel}\n"
                            + f"**Text Channel Count:** {text_channel_count}\n"
                            + f"**Voice Channel Count:** {voice_channel_count}\n"
                            + f"**Category Count:** {category_count}\n"
                        ),
                        "inline": False,
                    },
                    {
                        "name": "Limits",
                        "value": (
                            f"**Channels:** *{channel_percentage}%* ({channel_count}/500 channels)\n"
                            + f"**Members:** *{member_percentage}%* ({member_count}/{max_members} members)\n"
                            + f"**Emoji:** *{emoji_percentage}%* ({emoji_count}/{emoji_limit} emojis)\n"
                            + f"**Roles:** *{role_percentage}%* ({role_count}/250 roles)"
                        ),
                        "inline": False,
                    },
                ],
            )

        embed = discord.Embed(
            title=f"Information for `{name}`",
            description=f"**Description:** {desc}",
        )
        embed.set_thumbnail(url=icon)
        for field in fields:
            embed.add_field(**field)

        await interaction.response.send_message(embed=embed)

    wiki_group = app_commands.Group(
        name="wiki",
        description="Get information from the community-sourced wiki, available at scioly.org/wiki",
        guild_ids=env.slash_command_guilds,
        default_permissions=discord.Permissions(send_messages=True),
    )

    @wiki_group.command(name="summary", description="Returns a summary of a wiki page.")
    @app_commands.describe(
        page="The name of the page to return a summary about. Correct caps must be used.",
    )
    @app_commands.checks.cooldown(5, 60, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.check(is_in_bot_spam)
    async def wikisummary(self, interaction: discord.Interaction, page: str):
        """
        Discord command which returns the summary of a wiki page.

        Permissions:
            Confirmed members: Unconfirmed members cannot access this command.

        Args:
            interaction (discord.Interaction): The specific app command interaction
                sent by Discord.
            page (str): The name of the page to request the summary of.
        """
        command = await implement_command("summary", page)
        if not command:
            await interaction.response.send_message(
                f"Unfortunately, the `{page}` page does not exist.",
            )
        else:
            await interaction.response.send_message(" ".join(command))

    @wiki_group.command(
        name="search",
        description="Searches the wiki for a particular page.",
    )
    @app_commands.describe(term="The term to search for across the wiki.")
    @app_commands.checks.cooldown(5, 60, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.check(is_in_bot_spam)
    async def wikisearch(self, interaction: discord.Interaction, term: str):
        """
        Discord command which searches the wiki for a specific page name.

        Permissions:
            Confirmed members: Unconfirmed members cannot access this command.

        Args:
            interaction (discord.Interaction): The specific app command interaction
                sent by Discord.
            term (str): The term to search with.
        """
        command = await implement_command("search", term)
        if len(command):
            await interaction.response.send_message(
                "\n".join([f"`{search}`" for search in command]),
            )
        else:
            await interaction.response.send_message(
                f"No pages matching `{term}` were found.",
            )

    @wiki_group.command(name="link", description="Links to a particular wiki page.")
    @app_commands.describe(page="The wiki page to link to. Correct caps must be used.")
    @app_commands.checks.cooldown(5, 60, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.check(is_in_bot_spam)
    async def wikilink(self, interaction: discord.Interaction, page: str):
        """
        Discord command which returns the link to a specific wiki page.

        Permissions:
            Confirmed members: Unconfirmed members cannot access this command.

        Args:
            interaction (discord.Interaction): The specific app command interaction
                sent by Discord.
            page (str): The name of the page to get the link of.
        """
        command = await implement_command("link", page)
        if not command:
            await interaction.response.send_message(
                f"The `{page}` page does not yet exist.",
            )
        else:
            await interaction.response.send_message(f"<{self.wiki_url_fix(command)}>")

    def wiki_url_fix(self, url):
        return url.replace("%3A", ":").replace(r"%2F", "/")

    @app_commands.command(
        description="Searches for information on Wikipedia, the free encyclopedia!",
    )
    @app_commands.describe(
        command="The command to execute.",
        request="The request to execute the command upon. What to search or summarize, etc.",
    )
    @app_commands.guilds(*env.slash_command_guilds)
    @app_commands.checks.cooldown(5, 60, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.check(is_in_bot_spam)
    async def wikipedia(
        self,
        interaction: discord.Interaction,
        command: Literal["search", "summary", "link"],
        request: str,
    ):
        """
        Discord command which gets specific information about a Wikipedia page.

        Permissions:
            Confirmed members: Unconfirmed members cannot access this command.

        Args:
            interaction (discord.Interaction): The app command interaction sent
                by Discord.
            command (str): The command to execute across Wikipedia.
            request (str): The request associated with the command.
        """
        if command == "search":
            return await interaction.response.send_message(
                "\n".join(
                    [
                        f"`{result}`"
                        for result in self.aiowikip.search(request, results=5)
                    ],
                ),
            )

        elif command == "summary":
            try:
                page = await self.aiowikip.page(request)
                return await interaction.response.send_message(
                    self.aiowikip.summary(request, sentences=3)
                    + f"\n\nRead more on Wikipedia here: <{page.url}>!",
                )
            except wikip.exceptions.DisambiguationError as e:
                return await interaction.response.send_message(
                    f"Sorry, the `{request}` term could refer to multiple pages, try again using one of these terms:"
                    + "\n".join([f"`{o}`" for o in e.options]),
                )
            except wikip.exceptions.PageError:
                return await interaction.response.send_message(
                    f"Sorry, but the `{request}` page doesn't exist! Try another term!",
                )

        elif command == "link":
            try:
                page = await self.aiowikip.page(request)
                return await interaction.response.send_message(
                    f"Sure, here's the link: <{page.url}>",
                )
            except wikip.exceptions.PageError:
                return await interaction.response.send_message(
                    f"Sorry, but the `{request}` page doesn't exist! Try another term!",
                )
            except wikip.exceptions.DisambiguationError:
                return await interaction.response.send_message(
                    f"Sorry, but the `{request}` page is a disambiguation page. Please try again!",
                )

    @app_commands.command(description="Gets a tag.")
    @app_commands.describe(tag_name="The name of the tag to get.")
    @app_commands.guilds(*env.slash_command_guilds)
    @app_commands.checks.cooldown(5, 60, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.check(is_in_bot_spam)
    async def tag(self, interaction: discord.Interaction, tag_name: str):
        """
        Discord command which prints out a tag name.

        Permissions:
            Confirmed members: Unconfirmed members do not have access to this command.

        Args:
            interaction (discord.Interaction): The app command interaction sent by Discord.
            tag_name (str): The specific tag name sent by Discord.
        """
        member = interaction.user

        if not len(src.discord.globals.TAGS):
            return await interaction.response.send_message(
                "Apologies, tags do not appear to be working at the moment. Please try again in one minute.",
            )

        staff = is_staff_from_ctx(interaction, no_raise=True)
        lh_role = discord.utils.get(member.guild.roles, name=ROLE_LH)
        member_role = discord.utils.get(member.guild.roles, name=ROLE_MR)

        for t in src.discord.globals.TAGS:
            if t.name == tag_name:
                if (
                    staff
                    or (t.permissions.launch_helpers and lh_role in member.roles)
                    or (t.permissions.members and member_role in member.roles)
                ):
                    return await interaction.response.send_message(content=t.output)
                else:
                    return await interaction.response.send_message(
                        content="Unfortunately, you do not have the permissions for this tag.",
                    )

        return await interaction.response.send_message("Tag not found.")

    @tag.autocomplete(name="tag_name")
    async def tag_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        """
        Serves as autocompletion for the /tag command. Returns the names of the
        tags the user can send with their allotted permissions

        Args:
            interaction (discord.Interaction): The interaction sent with the autocomplete
                request.
            current (str): The amount the user has typed.

        Returns:
            List[app_commands.Choice[str]]: The names of the tags the user can choose
            from given their permissions.
        """
        # Check if the user is a staff member to see if they can see staff tags
        is_staff = is_staff_from_ctx(interaction, no_raise=True)

        # Check if the user is a normal member to see if they can see member tags
        assert isinstance(interaction.guild, discord.Guild)
        member_role = discord.utils.get(interaction.guild.roles, name=ROLE_MR)
        assert isinstance(interaction.user, discord.Member)
        is_member = member_role in interaction.user.roles

        # Send the tags
        tags: list[str] = [
            t.name
            for t in src.discord.globals.TAGS
            if (t.permissions.staff and is_staff)
            or (t.permissions.members and is_member)
        ]
        return [
            app_commands.Choice(name=t, value=t)
            for t in tags
            if current.lower() in t.lower()
        ]


async def setup(bot: PiBot):
    await bot.add_cog(MemberCommands(bot))
