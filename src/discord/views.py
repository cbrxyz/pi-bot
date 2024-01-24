from __future__ import annotations

from typing import TYPE_CHECKING

import discord

from src.discord.globals import ROLE_SELFMUTE

if TYPE_CHECKING:
    from bot import PiBot


class YesNo(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        self.stop()

    @discord.ui.button(label="No", style=discord.ButtonStyle.red)
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        self.stop()


class UnselfmuteView(discord.ui.View):
    def __init__(self, bot: PiBot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(
        label="Remove Self-Mute",
        custom_id="click_to_unmute",
        style=discord.ButtonStyle.gray,
    )
    async def unselfmute_button(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        await interaction.response.defer(ephemeral=True)
        role = discord.utils.get(interaction.guild.roles, name=ROLE_SELFMUTE)
        await interaction.user.remove_roles(role)
        try:
            item = next(
                x
                for x in await self.bot.mongo_database.get_cron()
                if (x["type"] == "UNSELFMUTE" and x["user"] == interaction.user.id)
            )
            await self.bot.mongo_database.remove_doc("data", "cron", item["_id"])
        except Exception:  # not in the database - maybe was removed!
            pass

        return await interaction.followup.send(
            "I removed your selfmute role!",
            ephemeral=True,
        )
