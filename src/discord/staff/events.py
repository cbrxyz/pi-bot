import discord
import re
from discord.commands import slash_command

from discord.ext import commands
from discord.commands import Option, permissions
import commandchecks

import src.discord.globals

from src.discord.globals import (
    SLASH_COMMAND_GUILDS,
    EMOJI_LOADING,
    SERVER_ID,
    ROLE_STAFF,
    ROLE_VIP,
)

from src.mongo.mongo import insert, delete


class StaffEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("Initialized staff events cog.")

    event_commands_group = discord.commands.SlashCommandGroup(
        "event",
        "Updates the bot's list of events.",
        guild_ids=[SLASH_COMMAND_GUILDS],
        permissions=[
            discord.commands.CommandPermission(ROLE_STAFF, 1, True),
            discord.commands.CommandPermission(ROLE_VIP, 1, True),
        ],
    )

    @event_commands_group.command(
        name="add", description="Staff command. Adds a new event."
    )
    @permissions.has_any_role(ROLE_STAFF, ROLE_VIP, guild_id=SERVER_ID)
    async def event_add(
        self,
        ctx,
        event_name: Option(str, "The name of the new event.", required=True),
        event_aliases: Option(
            str, "The aliases for the new event. Format as 'alias1, alias2'."
        ),
    ):
        # Check for staff permissions
        commandchecks.is_staff_from_ctx(ctx)

        # Send user notice that process has begun
        await ctx.interaction.response.send_message(
            f"{EMOJI_LOADING} Attempting to add `{event_name}` as a new event..."
        )

        # Check to see if event has already been added.
        if event_name in [e["name"] for e in src.discord.globals.EVENT_INFO]:
            return await ctx.interaction.edit_original_message(
                content=f"The `{event_name}` event has already been added."
            )

        # Construct dictionary to represent event; will be stored in database
        # and local storage
        aliases_array = re.findall(r"\w+", event_aliases)
        new_dict = {"name": event_name, "aliases": aliases_array}

        # Add dict into events container
        src.discord.globals.EVENT_INFO.append(new_dict)
        await insert("data", "events", new_dict)

        # Create role on server
        server = self.bot.get_guild(SERVER_ID)
        await server.create_role(
            name=event_name,
            color=discord.Color(0x82A3D3),
            reason=f"Created by {str(ctx.author)} using /eventadd with Pi-Bot.",
        )

        # Notify user of process completion
        await ctx.interaction.edit_original_message(
            content=f"The `{event_name}` event was added."
        )

    @event_commands_group.command(
        name="remove",
        description="Removes an event's availability and optionally, its role from all users.",
    )
    @permissions.has_any_role(ROLE_STAFF, ROLE_VIP, guild_id=SERVER_ID)
    async def event_remove(
        self,
        ctx,
        event_name: Option(str, "The name of the event to remove.", required=True),
        delete_role: Option(
            str,
            "Whether to delete the event role from all users. 'no' allows role to remain.",
            choices=["no", "yes"],
            default="no",
            required=True,
        ),
    ):
        # Check for staff permissions
        commandchecks.is_staff_from_ctx(ctx)

        # Send user notice that process has begun
        await ctx.interaction.response.send_message(
            f"{EMOJI_LOADING} Attempting to remove the `{event_name}` event..."
        )

        # Check to make sure event has previously been added
        event_not_in_list = event_name not in [
            e["name"] for e in src.discord.globals.EVENT_INFO
        ]

        # Check to see if role exists on server
        server = self.bot.get_guild(SERVER_ID)
        potential_role = discord.utils.get(server.roles, name=event_name)

        if event_not_in_list and potential_role == None:
            # If no event in list and no role exists on server
            return await ctx.interaction.edit_original_message(
                content=f"The `{event_name}` event does not exist."
            )

        # If staff member has selected to delete role from all users, delete role entirely
        if delete_role == "yes":
            server = self.bot.get_guild(SERVER_ID)
            role = discord.utils.get(server.roles, name=event_name)
            assert isinstance(role, discord.Role)
            await role.delete()
            if event_not_in_list:
                return await ctx.interaction.edit_original_message(
                    content=f"The `{event_name}` role was completely deleted from the server. All members with the role no longer have it."
                )

        # Complete operation of removing event
        event = [e for e in src.discord.globals.EVENT_INFO if e["name"] == event_name][0]
        src.discord.globals.EVENT_INFO.remove(event)
        await delete("data", "events", event["_id"])

        # Notify staff member of completion
        if delete_role == "yes":
            await ctx.interaction.edit_original_message(
                content=f"The `{event_name}` event was deleted entirely. The role has been removed from all users, and can not be added to new users."
            )
        else:
            await ctx.interaction.edit_original_message(
                content=f"The `{event_name}` event was deleted partially. Users who have the role currently will keep it, but new members can not access the role.\n\nTo delete the role entirely, re-run the command with `delete_role = yes`."
            )


def setup(bot):
    bot.add_cog(StaffEvents(bot))
