from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import discord
from beanie.odm.operators.update.array import Pull, Push
from discord import app_commands
from discord.ext import commands

import commandchecks
import src.discord.globals
from env import env
from src.discord.globals import (
    EMOJI_LOADING,
    ROLE_STAFF,
    ROLE_VIP,
)
from src.mongo.models import Censor

if TYPE_CHECKING:
    from bot import PiBot


class StaffCensor(commands.Cog):
    def __init__(self, bot: PiBot):
        self.bot = bot

    censor_group = app_commands.Group(
        name="censor",
        description="Controls Pi-Bot's censor.",
        guild_ids=env.slash_command_guilds,
        default_permissions=discord.Permissions(manage_messages=True),
    )

    @censor_group.command(
        name="add",
        description="Staff command. Adds a new entry into the censor.",
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
            f"{EMOJI_LOADING} Attempting to add {censor_type} to censor list.",
        )

        if censor_type == "word":
            if phrase in src.discord.globals.CENSOR.words:
                await interaction.edit_original_response(
                    content=f"`{phrase}` is already in the censored words list. Operation cancelled.",
                )
            else:
                await src.discord.globals.CENSOR.update(Push({Censor.words: phrase}))
                first_letter = phrase[0]
                last_letter = phrase[-1]
                await interaction.edit_original_response(
                    content=f"Added `{first_letter}...{last_letter}` to the censor list.",
                )
        elif censor_type == "emoji":
            if phrase in src.discord.globals.CENSOR.emojis:
                await interaction.edit_original_response(
                    content="Emoji is already in the censored emoijs list. Operation cancelled.",
                )
            else:
                await src.discord.globals.CENSOR.update(Push({Censor.emojis: phrase}))
                await interaction.edit_original_response(
                    content="Added emoji to the censor list.",
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
            f"{EMOJI_LOADING} Attempting to remove {censor_type} from censor list.",
        )

        if censor_type == "word":
            if phrase not in src.discord.globals.CENSOR.words:
                await interaction.edit_original_response(
                    content=f"`{phrase}` is not in the list of censored words.",
                )
            else:
                await src.discord.globals.CENSOR.update(Pull({Censor.words: phrase}))
                await interaction.edit_original_response(
                    content=f"Removed `{phrase}` from the censor list.",
                )
        elif censor_type == "emoji":
            if phrase not in src.discord.globals.CENSOR.emojis:
                await interaction.edit_original_response(
                    content=f"{phrase} is not in the list of censored emojis.",
                )
            else:
                await src.discord.globals.CENSOR.update(Pull({Censor.emojis: phrase}))
                await interaction.edit_original_response(
                    content=f"Removed {phrase} from the emojis list.",
                )


async def setup(bot: PiBot):
    await bot.add_cog(StaffCensor(bot))
