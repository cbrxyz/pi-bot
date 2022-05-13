from __future__ import annotations

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
    SLASH_COMMAND_GUILDS,
)

if TYPE_CHECKING:
    from bot import PiBot


class StaffTags(commands.Cog):
    def __init__(self, bot: PiBot):
        self.bot = bot
        print("Initialized staff tags cog.")

    tag_commands_group = app_commands.Group(
        name="tagupdate",
        description="Updates the bot's tag list.",
        guild_ids=[SLASH_COMMAND_GUILDS],
        default_permissions=discord.Permissions(manage_messages=True),
    )

    @tag_commands_group.command(
        name="add",
        description="Staff command. Adds a new tag.",
    )
    @app_commands.checks.has_any_role(ROLE_STAFF, ROLE_VIP)
    @app_commands.describe(
        tag_name="The name of the tag to add.",
        launch_helpers="Whether launch helpers can use this tag. Defaults to yes.",
        members="Whether all members can use this tag. Defaults to yes.",
    )
    async def tag_add(
        self,
        interaction: discord.Interaction,
        tag_name: str,
        launch_helpers: Literal["yes", "no"] = "yes",
        members: Literal["yes", "no"] = "yes",
    ):
        # Check for staff permissions
        commandchecks.is_staff_from_ctx(interaction)

        # Notify user that process has started
        await interaction.response.send_message(
            content=f"{EMOJI_LOADING} Attempting to add the `{tag_name}` tag..."
        )

        # Check if tag has already been added
        if tag_name in [t["name"] for t in src.discord.globals.TAGS]:
            return await interaction.edit_original_message(
                content=f"The `{tag_name}` tag has already been added. To edit this tag, please use `/tagedit` instead."
            )

        # Send directions to caller
        await interaction.edit_original_message(
            content=f"{EMOJI_LOADING} Please send the new text for the tag. You can use formatting and newlines. All "
            f"text sent in your next message will be included in the tag. "
        )
        content_message = await self.bot.listen_for_response(
            follow_id=interaction.user.id,
            timeout=120,
        )

        # If user does not respond, alert them
        if not content_message:
            return await interaction.edit_original_message(
                content="No message was found within 2 minutes. Operation cancelled."
            )

        # Grab text from user's response and delete their response
        text = content_message.content
        await content_message.delete()

        # Construct dict to represent tag
        new_dict = {
            "name": tag_name,
            "output": text,
            "permissions": {
                "staff": True,
                "launch_helpers": True if launch_helpers == "yes" else False,
                "members": True if members == "yes" else False,
            },
        }

        # Add tag to logs
        src.discord.globals.TAGS.append(new_dict)
        await self.bot.mongo_database.insert("data", "tags", new_dict)
        await interaction.edit_original_message(
            content=f"The `{tag_name}` tag was added!"
        )

    @tag_commands_group.command(
        name="edit",
        description="Staff command. Edits an existing tag.",
    )
    @app_commands.checks.has_any_role(ROLE_STAFF, ROLE_VIP)
    @app_commands.describe(
        tag_name="The tag name to edit the text of.",
        launch_helpers="Whether launch helpers can use. Defaults to 'do not change'.",
        members="Whether all members can use this tag. Defaults to 'do not change'.",
    )
    async def tag_edit(
        self,
        interaction: discord.Interaction,
        tag_name: str,
        launch_helpers: Literal["yes", "no", "do not change"] = "do not change",
        members: Literal["yes", "no", "do not change"] = "do not change",
    ):
        # Check for staff permissions
        commandchecks.is_staff_from_ctx(interaction)

        # Notify user that process has started
        await interaction.response.send_message(
            content=f"{EMOJI_LOADING} Attempting to update the `{tag_name}` tag..."
        )

        # Check that tag exists.
        if tag_name not in [t["name"] for t in src.discord.globals.TAGS]:
            return await interaction.edit_original_message(
                content=f"No tag with name `{tag_name}` could be found."
            )

        # Get relevant tag
        tag = [t for t in src.discord.globals.TAGS if t["name"] == tag_name][0]

        # Send info message about updating tag
        info_message = await interaction.edit_original_message(
            content=f"{EMOJI_LOADING}The current content of the tag is:\n----------\n{tag['output']}\n----------\n"
            + "Please send the new text for the tag below:"
        )

        # Listen for user response
        content_message = await self.bot.listen_for_response(
            follow_id=interaction.user.id,
            timeout=120,
        )

        # If user did not respond
        if not content_message:
            await interaction.edit_original_message(
                content="No message was found within 2 minutes. Operation cancelled."
            )
            return

        # Get message content
        text = content_message.content
        await content_message.delete()

        # update_dict will contain values that need to be updated in DB
        update_dict = {}

        # Changing tag object changes tag locally
        # Always set the new text of tag
        tag["output"] = text
        update_dict["output"] = text

        # Change permissions if desired
        if launch_helpers != "do not change":
            tag["permissions"]["launch_helpers"] = (
                True if launch_helpers == "yes" else False
            )
            update_dict["permissions.launch_helpers"] = (
                True if launch_helpers == "yes" else False
            )
        if members != "do not change":
            tag["permissions"]["members"] = True if members == "yes" else False
            update_dict["permissions.members"] = True if members == "yes" else False

        # Update tag
        await self.bot.mongo_database.update(
            "data", "tags", tag["_id"], {"$set": update_dict}
        )
        await interaction.edit_original_message(
            content=f"The `{tag_name}` tag was updated."
        )

    @tag_commands_group.command(
        name="remove",
        description="Staff command. Removes a tag completely.",
    )
    @app_commands.checks.has_any_role(ROLE_STAFF, ROLE_VIP)
    @app_commands.describe(tag_name="The name of the tag to remove.")
    async def tag_remove(
        self,
        interaction: discord.Interaction,
        tag_name: str,
    ):
        # Check for staff permissions again
        commandchecks.is_staff_from_ctx(interaction)

        # Notify user that process has started
        await interaction.response.send_message(
            content=f"{EMOJI_LOADING} Attempting to delete the `{tag_name}` tag..."
        )

        # If tag does not exist
        if tag_name not in [t["name"] for t in src.discord.globals.TAGS]:
            return await interaction.edit_original_message(
                content=f"No tag with the name of `{tag_name}` was found."
            )

        # Get tag
        tag = [t for t in src.discord.globals.TAGS if t["name"] == tag_name][0]
        # and remove it!
        src.discord.globals.TAGS.remove(tag)
        # and delete it from the DB!
        await self.bot.mongo_database.delete("data", "tags", tag["_id"])

        # Send confirmation message
        return await interaction.edit_original_message(
            content=f"The `{tag_name}` tag was deleted."
        )


async def setup(bot: PiBot):
    await bot.add_cog(StaffTags(bot))
