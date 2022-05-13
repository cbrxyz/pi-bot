from __future__ import annotations

import datetime
import re
from typing import TYPE_CHECKING, Literal, Union

import commandchecks
import discord
import src.discord.globals
from discord import app_commands
from discord.ext import commands
from src.discord.globals import (
    CATEGORY_ARCHIVE,
    CATEGORY_TOURNAMENTS,
    EMOJI_GUILDS,
    EMOJI_LOADING,
    ROLE_STAFF,
    ROLE_VIP,
    SERVER_ID,
    SLASH_COMMAND_GUILDS,
)
from src.discord.tournaments import update_tournament_list
from src.discord.views import YesNo

if TYPE_CHECKING:
    from bot import PiBot
    from src.discord.tasks import CronTasks


class StaffInvitational(commands.Cog):
    def __init__(self, bot: PiBot):
        self.bot = bot
        print("Initialized Invitationals cog.")

    invitational_status_group = app_commands.Group(
        name="invitational",
        description="Updates the bot's invitational system.",
        guild_ids=[SLASH_COMMAND_GUILDS],
        default_permissions=discord.Permissions(manage_channels=True),
    )

    @invitational_status_group.command(
        name="add",
        description="Staff command. Adds a new invitational for voting.",
    )
    @app_commands.checks.has_any_role(ROLE_STAFF, ROLE_VIP)
    @app_commands.describe(
        official_name="The official name of the tournament, such as MIT Invitational.",
        channel_name="The name of the Discord channel that will be created, such as 'mit'",
        tourney_date="The date of the tournament, formatted as YYYY-mm-dd, such as 2022-01-06.",
        status="Determines if the new tournament channel will be sent to voting or added immediately.",
    )
    async def invitational_add(
        self,
        interaction: discord.Interaction,
        official_name: str,
        channel_name: str,
        tourney_date: str,
        status: Literal["voting", "add_immediately"],
    ):
        # Check for staff permissions
        commandchecks.is_staff_from_ctx(interaction)

        # Create tournament doc
        new_tourney_doc = {
            "official_name": official_name,
            "channel_name": channel_name,
            "tourney_date": datetime.datetime.strptime(tourney_date, "%Y-%m-%d"),
            "aliases": [],
            "open_days": 10,
            "closed_days": 30,
            "voters": [],
            "status": "open" if status == "add_immediately" else "voting",
        }

        # Send default message
        await interaction.response.send_message(f"{EMOJI_LOADING} Loading...")

        # Attempt to get tournament emoji
        emoji = None
        while emoji is None:
            # Send info message
            await interaction.edit_original_message(
                content=f"{EMOJI_LOADING}\nPlease send the emoji to use for the tournament. If you would like to use "
                f"a custom image, **send a message containing a file that is less than 256KB in size.**\n\nIf "
                f"you would like to use a standard emoji, please send a message with only the standard emoji. "
            )

            # Get user response
            emoji_message: discord.Message = await self.bot.listen_for_response(
                follow_id=interaction.user.id,
                timeout=120,
            )

            # If emoji message has file, use this as emoji, otherwise, use default emoji provided
            if not emoji_message:
                return await interaction.edit_original_message(
                    content="No emoji was provided after 2 minutes, so the operation was cancelled."
                )

            if len(emoji_message.attachments):
                # If attachments provided

                emoji_attachment = emoji_message.attachments[0]
                await emoji_message.delete()

                # Check for attachment size
                if emoji_attachment.size > 256000:
                    size_message = await interaction.channel.send(
                        "Please use an emoji that is less than 256KB."
                    )
                    await size_message.delete(delay=15)
                    continue

                # Check for attachment type
                if emoji_attachment.content_type not in [
                    "image/gif",
                    "image/jpeg",
                    "image/png",
                ]:
                    type_message = await interaction.channel.send(
                        "Please use a file that is a GIF, JPEG, or PNG."
                    )
                    await type_message.delete(delay=15)
                    continue

                # Check for emoji creation in guilds
                created_emoji = False
                for i, guild_id in enumerate(EMOJI_GUILDS):
                    guild = self.bot.get_guild(guild_id)
                    assert isinstance(guild, discord.Guild)

                    # Attempt to add emoji to guild
                    if len(guild.emojis) < guild.emoji_limit:
                        # The guild can fit more custom emojis
                        emoji = await guild.create_custom_emoji(
                            name=f"tournament_{channel_name}",
                            image=await emoji_attachment.read(),
                            reason=f"Created by {interaction.user}.",
                        )
                        created_emoji = True
                        emoji_creation_message = await interaction.channel.send(
                            f"Created {emoji} (`{str(emoji)}`) emoji in guild `{guild_id}`. (Guild {i + 1}/{len(EMOJI_GUILDS)})"
                        )
                        await emoji_creation_message.delete(delay=10)
                        break

                if not created_emoji:
                    await interaction.edit_original_message(
                        content=f"Sorry {interaction.user}! The emoji guilds are currently full; a bot administrator "
                        f"will need to add more emoji guilds. "
                    )
                    return

            # If just standard emoji, use that
            if len(emoji_message.content) > 0:
                emoji = emoji_message.content

        # Tournament creation embed description
        description = f"""
            **Official Name:** {official_name}
            **Channel Name:** `#{channel_name}`
            **Tournament Date:** {discord.utils.format_dt(new_tourney_doc['tourney_date'], 'D')}
            **Closes After:** {new_tourney_doc['closed_days']} days (the tournament channel is expected to close on {discord.utils.format_dt(new_tourney_doc['tourney_date'] + datetime.timedelta(days=new_tourney_doc['closed_days']), 'D')})
            **Tournament Emoji:** {emoji}
            """

        # Update tournament with status
        if status == "add_immediately":
            description += (
                "\n**This tournament channel will be opened immediately.** This means that it will require "
                "no votes by users to open. This option should generally only be used for tournaments that "
                "have a very strong attendance or desire to be added to the server. "
            )
        else:
            description += (
                "\n**This tournament channel will require a certain number of votes to be opened.** This "
                "means that the tournament channel will not immediately be created - rather, users will "
                "need to vote on the channel being created before the action is done. "
            )

        # Final Embed class
        confirm_embed = discord.Embed(
            title=f"Add New Invitational",
            color=discord.Color(0x2E66B6),
            description=description,
        )

        # Use Yes/No view for final confirmation
        view = YesNo()
        await interaction.edit_original_message(
            content=f"Please confirm that you would like to add the following tournament:",
            embed=confirm_embed,
            view=view,
        )
        await view.wait()
        if view.value:
            # Staff member responded with "Yes"
            new_tourney_doc["emoji"] = str(emoji)
            await self.bot.mongo_database.insert(
                "data", "invitationals", new_tourney_doc
            )
            await interaction.edit_original_message(
                content="The invitational was added successfully! The tournament list will now be refreshed.",
                embed=None,
                view=None,
            )
            await update_tournament_list(self.bot, {})
        else:
            await interaction.edit_original_message(
                content="The operation was cancelled.", embed=None, view=None
            )

    @invitational_status_group.command(
        name="approve",
        description="Staff command. Approves a invitational to be fully opened.",
    )
    @app_commands.checks.has_any_role(ROLE_STAFF, ROLE_VIP)
    @app_commands.describe(
        short_name="The short name of the invitational, such as 'mit'."
    )
    async def invitational_approve(
        self, interaction: discord.Interaction, short_name: str
    ):
        # Check for staff permissions
        commandchecks.is_staff_from_ctx(interaction)

        # Sending message about operation started
        await interaction.response.send_message(
            f"{EMOJI_LOADING} Attempting to approve..."
        )

        invitationals = await self.bot.mongo_database.get_invitationals()
        found_invitationals = [
            i for i in invitationals if i["channel_name"] == short_name
        ]

        # If invitational is not found
        if len(found_invitationals) < 1:
            await interaction.edit_original_message(
                content=f"Sorry, I couldn't find an invitational with the short name of `{short_name}`."
            )

        # If an invitational is found
        elif len(found_invitationals) == 1:

            # Check to see if invitational is already open
            if found_invitationals[0]["status"] == "open":
                await interaction.edit_original_message(
                    content=f"The `{short_name}` invitational is already open."
                )

            # If not, update invitational to be open
            await update(
                "data",
                "invitationals",
                found_invitationals[0]["_id"],
                {"$set": {"status": "open"}},
            )
            await interaction.edit_original_message(
                content=f"The status of the `{short_name}` invitational was updated."
            )

            # Update tournament list
            await update_tournament_list(self.bot, {})

        else:
            await interaction.edit_original_message(
                content="I found more than one invitational with a matching name. Contact an administrator - "
                "something is wrong. "
            )

    @invitational_status_group.command(
        name="edit",
        description="Staff command. Edits data about an invitational channel.",
    )
    @app_commands.checks.has_any_role(ROLE_STAFF, ROLE_VIP)
    @app_commands.describe(
        short_name="The short name of the invitational you would like to edit, such as 'mit'.",
        feature_to_edit="The feature you would like to edit about the invitational.",
    )
    async def invitational_edit(
        self,
        interaction: discord.Interaction,
        short_name: str,
        feature_to_edit: Literal[
            "official name", "short name", "emoji", "tournament date"
        ],
    ):
        # Check for staff permissions
        commandchecks.is_staff_from_ctx(interaction)

        # Send notice that process has started
        await interaction.response.send_message(
            content=f"{EMOJI_LOADING} Attempting to edit invitational..."
        )

        # Attempt to find invitational
        invitationals = await self.bot.mongo_database.get_invitationals()
        found_invitationals = [
            i for i in invitationals if i["channel_name"] == short_name
        ]

        # If no invitational was found
        if len(found_invitationals) < 1:
            await interaction.edit_original_message(
                content=f"Sorry, I couldn't find an invitational with the short name of `{short_name}`."
            )

        # If one invitational was found
        elif len(found_invitationals) == 1:
            invitational = found_invitationals[0]

            # Send notice to user about editing invitational
            info_message_text = f"{EMOJI_LOADING} Please send the new {feature_to_edit} relevant to the tournament."
            if feature_to_edit == "emoji":
                info_message_text += (
                    "\n\nTo use a custom image as the new emoji for the invitational, please send a "
                    "file that is no larger than 256KB. If you would like to use a new standard "
                    "emoji for the invitational, please send only the new standard emoji. "
                )
            elif feature_to_edit == "tournament date":
                info_message_text += (
                    "\n\nTo update the tournament date, please send the date formatted as "
                    "YYYY-mm-dd, such as `2022-01-12`. "
                )
            await interaction.edit_original_message(content=info_message_text)

            # Ask user for the new content!
            content_message = await self.bot.listen_for_response(
                follow_id=interaction.user.id,
                timeout=120,
            )

            # If a message was found
            if content_message:
                rename_dict = {}
                await content_message.delete()

                # If editing tournament's name
                if feature_to_edit == "official name":
                    # Make sure to rename the roles
                    rename_dict = {
                        "roles": {
                            invitational["official_name"]: content_message.content
                        }
                    }
                    # and update the DB
                    await update(
                        "data",
                        "invitationals",
                        invitational["_id"],
                        {"$set": {"official_name": content_message.content}},
                    )
                    await interaction.edit_original_message(
                        content=f"`{invitational['official_name']}` was renamed to **`{content_message.content}`**."
                    )

                # If editing tournament's short name
                elif feature_to_edit == "short name":
                    # Make sure to rename the channel
                    rename_dict = {
                        "channels": {
                            invitational["channel_name"]: content_message.content
                        }
                    }
                    # and update the DB
                    await self.bot.mongo_database.update(
                        "data",
                        "invitationals",
                        invitational["_id"],
                        {"$set": {"channel_name": content_message.content}},
                    )
                    await interaction.edit_original_message(
                        content=f"The channel for {invitational['official_name']} was renamed from `{invitational['channel_name']}` to **`{content_message.content}`**."
                    )

                # If editing tournament's emoji
                elif feature_to_edit == "emoji":
                    emoji = None
                    if len(content_message.attachments):

                        # User provided custom emoji
                        emoji_attachment = content_message.attachments[0]
                        if emoji_attachment.size > 256000:
                            await interaction.edit_original_message(
                                content="Please use an emoji that is less than 256KB. Operation cancelled."
                            )

                        # Check for type
                        if emoji_attachment.content_type not in [
                            "image/gif",
                            "image/jpeg",
                            "image/png",
                        ]:
                            await interaction.edit_original_message(
                                content="Please use a file that is a GIF, JPEG, or PNG. Operation cancelled."
                            )

                        # Create new emoji, delete old emoji
                        created_emoji = False
                        for guild_id in EMOJI_GUILDS:
                            guild = self.bot.get_guild(guild_id)
                            for emoji in guild.emojis:
                                if (
                                    emoji.name
                                    == f"tournament_{invitational['channel_name']}"
                                ):
                                    await emoji.delete(
                                        reason=f"Replaced with alternate emoji by {interaction.user}."
                                    )
                            if (
                                len(guild.emojis) < guild.emoji_limit
                                and not created_emoji
                            ):
                                # The guild can fit more custom emojis
                                emoji = await guild.create_custom_emoji(
                                    name=f"tournament_{invitational['channel_name']}",
                                    image=await emoji_attachment.read(),
                                    reason=f"Created by {interaction.user}.",
                                )
                                created_emoji = True

                        if not created_emoji:
                            return await interaction.edit_original_message(
                                content=f"Sorry {interaction.user}! The emoji guilds are currently full; a bot "
                                f"administrator will need to add more emoji guilds. "
                            )

                    # User provided standard emoji
                    else:
                        emoji = content_message.content

                    # Update the DB with info
                    await self.bot.mongo_database.update(
                        "data",
                        "invitationals",
                        invitational["_id"],
                        {"$set": {"emoji": emoji}},
                    )

                    # Send confirmation message
                    await interaction.edit_original_message(
                        content=f"The emoji for `{invitational['official_name']}` was updated to: {emoji}."
                    )

                # If editing the tournament date
                elif feature_to_edit == "tournament date":
                    # Get vars
                    date_str = content_message.content
                    date_dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
                    # and update DB
                    await self.bot.mongo_database.update(
                        "data",
                        "invitationals",
                        invitational["_id"],
                        {"$set": {"tourney_date": date_dt}},
                    )
                    # and send user confirmation
                    await interaction.edit_original_message(
                        content=f"The tournament date for `{invitational['official_name']}` was updated to {discord.utils.format_dt(date_dt, 'D')}."
                    )
                await update_tournament_list(self.bot, rename_dict)
            else:
                await interaction.edit_original_message(
                    content=f"No message was provided. Operation timed out after 120 seconds."
                )

    @invitational_status_group.command(
        name="archive",
        description="Staff command. Archives an invitational channel.",
    )
    @app_commands.checks.has_any_role(ROLE_STAFF, ROLE_VIP)
    @app_commands.describe(
        short_name="The short name referring to the invitational, such as 'mit'."
    )
    async def invitational_archive(
        self, interaction: discord.Interaction, short_name: str
    ):
        # Check for staff permissions
        commandchecks.is_staff_from_ctx(interaction)

        # Let staff know process has started
        await interaction.response.send_message(
            content=f"{EMOJI_LOADING} Attempting to archive the `{short_name}` invitational..."
        )

        invitationals = await self.bot.mongo_database.get_invitationals()
        found_invitationals = [
            i for i in invitationals if i["channel_name"] == short_name
        ]
        if not len(found_invitationals):
            await interaction.edit_original_message(
                content=f"Sorry, I couldn't find an invitational with a short name of {short_name}."
            )

        # Invitational was found
        invitational = found_invitationals[0]

        # Update the database and tournament list
        await self.bot.mongo_database.update(
            "data",
            "invitationals",
            invitational["_id"],
            {"$set": {"status": "archived"}},
        )
        await interaction.edit_original_message(
            content=f"The **`{invitational['official_name']}`** is now being archived."
        )
        await update_tournament_list(self.bot, {})

    @invitational_status_group.command(
        name="delete",
        description="Staff command. Deletes an invitational channel from the server.",
    )
    @app_commands.checks.has_any_role(ROLE_STAFF, ROLE_VIP)
    @app_commands.describe(
        short_name="The short name referring to the invitational, such as 'mit'."
    )
    async def invitational_delete(
        self, interaction: discord.Interaction, short_name: str
    ):
        # Check for staff permissions again
        commandchecks.is_staff_from_ctx(interaction)

        # Let staff know process started
        await interaction.response.send_message(
            content=f"{EMOJI_LOADING} Attempting to delete the `{short_name}` invitational..."
        )

        # Attempt to find invitational
        invitationals = await self.bot.mongo_database.get_invitationals()
        found_invitationals = [
            i for i in invitationals if i["channel_name"] == short_name
        ]

        if not len(found_invitationals):
            await interaction.edit_original_message(
                content=f"Sorry, I couldn't find an invitational with a short name of {short_name}."
            )

        else:
            # Find the relevant invitational
            invitational = found_invitationals[0]

            # Get the relevant channel and role
            server = self.bot.get_guild(SERVER_ID)
            ch = discord.utils.get(
                server.text_channels, name=invitational["channel_name"]
            )
            r = discord.utils.get(server.roles, name=invitational["official_name"])

            # Delete the channel and role
            if (
                ch
                and ch.category
                and ch.category.name
                in [
                    CATEGORY_ARCHIVE,
                    CATEGORY_TOURNAMENTS,
                ]
            ):
                await ch.delete()
            if r:
                await r.delete()

            # Delete the invitational emoji
            search = re.findall(r"<:.*:\d+>", invitational["emoji"])
            if len(search):
                emoji = self.bot.get_emoji(search[0])
                if emoji:
                    await emoji.delete()

            # Delete from the DB
            await self.bot.mongo_database.delete(
                "data", "invitationals", invitational["_id"]
            )
            await interaction.edit_original_message(
                content=f"Deleted the **`{invitational['official_name']}`**."
            )

            # Update the tournament list to reflect
            await update_tournament_list(self.bot, {})

    @invitational_status_group.command(
        name="season",
        description="Staff command. Changes the invitational season, meant to be run once per year.",
    )
    @app_commands.checks.has_any_role(ROLE_STAFF, ROLE_VIP)
    async def invitational_season(self, interaction: discord.Interaction):
        # Check for staff permissions again
        commandchecks.is_staff_from_ctx(interaction)

        # Let staff know process started
        await interaction.response.send_message(
            content=f"{EMOJI_LOADING} Attempting to run command..."
        )

        assert isinstance(src.discord.globals.SETTINGS["invitational_season"], int)
        description = f"""
        This will update the season for the invitational season from `{src.discord.globals.SETTINGS['invitational_season']}` to `{src.discord.globals.SETTINGS['invitational_season'] + 1}`.

        This **will not remove any data**, but the invitational display in the invitationals channel will be updated to only display invitationals relevant to the new season.

        **This command is only meant to be run once per year.**
        """

        # Ask for permission again
        confirm_embed = discord.Embed(
            title=f"WARNING: Attempting to update invitational season.",
            color=discord.Color.brand_red(),
            description=description,
        )

        # Use Yes/No view for final confirmation
        view = YesNo()
        await interaction.edit_original_message(
            content=f"Please confirm that you would like to update the invitational season:",
            embed=confirm_embed,
            view=view,
        )
        await view.wait()
        if view.value:
            # Let staff member know of success
            await interaction.edit_original_message(
                content=f"{EMOJI_LOADING} Attempting to update the invitational year and refresh tournament list...",
                view=None,
                embed=None,
            )

            # Actually update season
            src.discord.globals.SETTINGS["invitational_season"] += 1
            tasks_cog: Union[commands.Cog, CronTasks] = self.bot.get_cog("CronTasks")
            await tasks_cog.update_setting(
                "invitational_season",
                src.discord.globals.SETTINGS["invitational_season"] + 1,
            )

            # Update the tournament list to reflect
            await update_tournament_list(self.bot, {})

            # Send message to staff
            await interaction.edit_original_message(
                content="The operation succeeded, and the tournament list was refreshed."
            )
        else:
            await interaction.edit_original_message(
                content="The operation was cancelled.", view=None, embed=None
            )


async def setup(bot: PiBot):
    await bot.add_cog(StaffInvitational(bot))
