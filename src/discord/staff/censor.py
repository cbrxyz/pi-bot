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


class StaffCensor(commands.Cog):
    def __init__(self, bot: PiBot):
        self.bot = bot
        print("Initialized staff censor cog.")

    censor_group = app_commands.Group(
        name="censor",
        description="Controls Pi-Bot's censor.",
        guild_ids=SLASH_COMMAND_GUILDS,
        default_permissions=discord.Permissions(manage_messages=True),
    )

    @censor_group.command(
        name="add", description="Staff command. Adds a new entry into the censor."
    )
    @app_commands.checks.has_any_role(ROLE_STAFF, ROLE_VIP)
    @app_commands.describe(
        censor_type="Whether to add a new word or emoji to the list.",
        phrase="The new word or emoji to add. For a new word, type the word. For a new emoji, send the emoji.",
    )
    async def censor_add(
        self,
        interaction: discord.Interaction,
        censor_type: Literal["word", "emoji"],
        phrase: str,
    ):
        # Check for staff permissions
        commandchecks.is_staff_from_ctx(interaction)

        # Send notice message
        await interaction.response.send_message(
            f"{EMOJI_LOADING} Attempting to add {censor_type} to censor list."
        )

        print(src.discord.globals.CENSOR)
        if censor_type == "word":
            if phrase in src.discord.globals.CENSOR["words"]:
                await interaction.edit_original_response(
                    content=f"`{phrase}` is already in the censored words list. Operation cancelled."
                )
            else:
                src.discord.globals.CENSOR["words"].append(phrase)
                await self.bot.mongo_database.update(
                    "data",
                    "censor",
                    src.discord.globals.CENSOR["_id"],
                    {"$push": {"words": phrase}},
                )
                first_letter = phrase[0]
                last_letter = phrase[-1]
                await interaction.edit_original_response(
                    content=f"Added `{first_letter}...{last_letter}` to the censor list."
                )
        elif censor_type == "emoji":
            if phrase in src.discord.globals.CENSOR["emojis"]:
                await interaction.edit_original_response(
                    content=f"Emoji is already in the censored emoijs list. Operation cancelled."
                )
            else:
                src.discord.globals.CENSOR["emojis"].append(phrase)
                await self.bot.mongo_database.update(
                    "data",
                    "censor",
                    src.discord.globals.CENSOR["_id"],
                    {"$push": {"emojis": phrase}},
                )
                await interaction.edit_original_response(
                    content=f"Added emoji to the censor list."
                )

    @censor_group.command(
        name="remove",
        description="Staff command. Removes a word/emoji from the censor list.",
    )
    @app_commands.checks.has_any_role(ROLE_STAFF, ROLE_VIP)
    @app_commands.describe(
        censor_type="Whether to remove a word or emoji.",
        phrase="The word or emoji to remove from the censor list.",
    )
    async def censor_remove(
        self,
        interaction: discord.Interaction,
        censor_type: Literal["word", "emoji"],
        phrase: str,
    ):
        # Check for staff permissions again
        commandchecks.is_staff_from_ctx(interaction)

        # Send notice message
        await interaction.response.send_message(
            f"{EMOJI_LOADING} Attempting to remove {censor_type} from censor list."
        )

        if censor_type == "word":
            if phrase not in src.discord.globals.CENSOR["words"]:
                await interaction.response.send_message(
                    content=f"`{phrase}` is not in the list of censored words."
                )
            else:
                src.discord.globals.CENSOR["words"].remove(phrase)
                await self.bot.mongo_database.update(
                    "data",
                    "censor",
                    src.discord.globals.CENSOR["_id"],
                    {"$pull": {"words": phrase}},
                )
                await interaction.edit_original_response(
                    content=f"Removed `{phrase}` from the censor list."
                )
        elif censor_type == "emoji":
            if phrase not in src.discord.globals.CENSOR["emojis"]:
                await interaction.response.send_message(
                    content=f"{phrase} is not in the list of censored emojis."
                )
            else:
                src.discord.globals.CENSOR["emojis"].remove(phrase)
                await self.bot.mongo_database.update(
                    "data",
                    "censor",
                    src.discord.globals.CENSOR["_id"],
                    {"$pull": {"emojis": phrase}},
                )
                await interaction.edit_original_response(
                    content=f"Removed {phrase} from the emojis list."
                )


async def setup(bot: PiBot):
    await bot.add_cog(StaffCensor(bot))
