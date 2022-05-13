from __future__ import annotations

import re
from typing import TYPE_CHECKING, Literal

import commandchecks
import discord
import src.discord.globals
from discord import app_commands
from discord.ext import commands
from src.discord.globals import (
    EMOJI_LOADING,
    ROLE_STAFF,
    ROLE_VIP,
    SERVER_ID,
    SLASH_COMMAND_GUILDS,
)

if TYPE_CHECKING:
    from bot import PiBot


class StaffEvents(commands.Cog):
    def __init__(self, bot: PiBot):
        self.bot = bot
        print("Initialized staff events cog.")

    event_commands_group = app_commands.Group(
        name="event",
        description="Updates the bot's list of events.",
        guild_ids=[SLASH_COMMAND_GUILDS],
        default_permissions=discord.Permissions(manage_roles=True),
    )

    @event_commands_group.command(
        name="add", description="Staff command. Adds a new event."
    )
    @app_commands.checks.has_any_role(ROLE_STAFF, ROLE_VIP)
    @app_commands.describe(
        event_name="The name of the new event.",
        event_aliases="The aliases for the new event. Format as 'alias1, alias2'.",
    )
    async def event_add(
        self,
        interaction: discord.Interaction,
        event_name: str,
        event_aliases: str = None,
    ):
        # Check for staff permissions
        commandchecks.is_staff_from_ctx(interaction)

        # Send user notice that process has begun
        await interaction.response.send_message(
            f"{EMOJI_LOADING} Attempting to add `{event_name}` as a new event..."
        )

        # Check to see if event has already been added.
        if event_name in [e["name"] for e in src.discord.globals.EVENT_INFO]:
            return await interaction.edit_original_message(
                content=f"The `{event_name}` event has already been added."
            )

        # Construct dictionary to represent event; will be stored in database
        # and local storage
        aliases_array = []
        if event_aliases:
            aliases_array = re.findall(r"\w+", event_aliases)
        new_dict = {"name": event_name, "aliases": aliases_array}

        # Add dict into events container
        src.discord.globals.EVENT_INFO.append(new_dict)
        await self.bot.mongo_database.insert("data", "events", new_dict)

        # Create role on server
        server = self.bot.get_guild(SERVER_ID)
        await server.create_role(
            name=event_name,
            color=discord.Color(0x82A3D3),
            reason=f"Created by {str(interaction.user)} using /eventadd with Pi-Bot.",
        )

        # Notify user of process completion
        await interaction.edit_original_message(
            content=f"The `{event_name}` event was added."
        )

    @event_commands_group.command(
        name="remove",
        description="Removes an event's availability and optionally, its role from all users.",
    )
    @app_commands.checks.has_any_role(ROLE_STAFF, ROLE_VIP)
    @app_commands.describe(
        event_name="The name of the event to remove.",
        delete_role="Whether to delete the event role from all users. 'no' allows role to remain.",
    )
    async def event_remove(
        self,
        interaction: discord.Interaction,
        event_name: str,
        delete_role: Literal["no", "yes"] = "no",
    ):
        # Check for staff permissions
        commandchecks.is_staff_from_ctx(interaction)

        # Send user notice that process has begun
        await interaction.response.send_message(
            f"{EMOJI_LOADING} Attempting to remove the `{event_name}` event..."
        )

        # Check to make sure event has previously been added
        event_not_in_list = event_name not in [
            e["name"] for e in src.discord.globals.EVENT_INFO
        ]

        # Check to see if role exists on server
        server = self.bot.get_guild(SERVER_ID)
        potential_role = discord.utils.get(server.roles, name=event_name)

        if event_not_in_list and potential_role:
            # If no event in list and no role exists on server
            return await interaction.edit_original_message(
                content=f"The `{event_name}` event does not exist."
            )

        # If staff member has selected to delete role from all users, delete role entirely
        if delete_role == "yes":
            server = self.bot.get_guild(SERVER_ID)
            role = discord.utils.get(server.roles, name=event_name)
            assert isinstance(role, discord.Role)
            await role.delete()
            if event_not_in_list:
                return await interaction.edit_original_message(
                    content=f"The `{event_name}` role was completely deleted from the server. All members with the role no longer have it."
                )

        # Complete operation of removing event
        event = [e for e in src.discord.globals.EVENT_INFO if e["name"] == event_name][
            0
        ]
        src.discord.globals.EVENT_INFO.remove(event)
        await self.bot.mongo_database.delete("data", "events", event["_id"])

        # Notify staff member of completion
        if delete_role == "yes":
            await interaction.edit_original_message(
                content=f"The `{event_name}` event was deleted entirely. The role has been removed from all users, "
                f"and can not be added to new users. "
            )
        else:
            await interaction.edit_original_message(
                content=f"The `{event_name}` event was deleted partially. Users who have the role currently will keep "
                f"it, but new members can not access the role.\n\nTo delete the role entirely, re-run the "
                f"command with `delete_role = yes`. "
            )


async def setup(bot: PiBot):
    await bot.add_cog(StaffEvents(bot))
