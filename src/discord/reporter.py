import discord
import datetime
from discord.ext import commands
import src.discord.globals
from src.discord.globals import CENSOR, DISCORD_INVITE_ENDINGS, CHANNEL_SUPPORT, PI_BOT_IDS, ROLE_MUTED, SERVER_ID
from bot import create_staff_message
import re

"""
Relevant views.
"""
class IgnoreButton(discord.ui.Button):
    """
    A button to mark the report as ignored.

    This causes the report message to be deleted, an informational message to be posted in closed-reports, and the report database to be updated
    """

    view: discord.ui.View

    def __init__(self, view):
        self.view = view
        super().__init__(style = discord.ButtonStyle.gray, label = "Ignore", custom_id = f"{view.report_id}:ignore")

    async def callback(self, interaction: discord.Interaction):
        # Delete the original report
        await interaction.message.delete()

        # Send an informational message about the report being ignored
        closed_reports = discord.utils.get(interaction.guild.text_channels, name = 'closed-reports')
        await closed_reports.send(f"**Report was ignored** by {interaction.user.mention} - {self.view.member.mention} had the innapropriate username `{self.view.offending_username}`, but the report was ignored.")

        # Update the report database
        # TODO

class InnapropriateUsername(discord.ui.View):

    member: discord.Member
    offending_username: str
    report_id: int

    def __init__(self, member: discord.Member, report_id: int, offending_username: str):
        self.member = member
        self.report_id = report_id
        self.offending_username = offending_username
        super().__init__(timeout = 86400) # Timeout after one day
        super().add_item(IgnoreButton(self))

class Reporter(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def create_staff_message(self, embed: discord.Embed):
        guild = self.bot.get_guild(SERVER_ID)
        messages_channel = discord.utils.get(guild.text_channels, name = 'messages')
        await messages_channel.send(embed = embed)

def setup(bot):
    bot.add_cog(Reporter(bot))
