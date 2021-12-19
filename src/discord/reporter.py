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

class ChangeInnapropriateUsername(discord.ui.Button):
    """
    A button that changes the username of a user.

    This caues the report message to be deleted, an informational message to be posted in closed-reports, and the report database to be updated.
    """

    view: discord.ui.View

    def __init__(self, view):
        self.view = view
        super().__init__(style = discord.ButtonStyle.green, label = "Change Username", custom_id = f"{view.report_id}:change_username")

    async def callback(self, interaction: discord.Interaction):
        # Delete the original message
        await interaction.message.delete()

        # Check to make sure user is still in server before taking action
        member_still_here = self.view.member in self.view.member.guild.members

        # Send an informational message about the report being updated
        closed_reports = discord.utils.get(interaction.guild.text_channels, name = 'closed-reports')
        if member_still_here:
            await closed_reports.send(f"**Member's username was changed** by {interaction.user.mention} - {self.view.member.mention} had the innapropriate username `{self.view.offending_username}`, and their username was changed to `boomilever`.")

            # Change the user's username
            await self.view.member.edit(nick = "boomilever")

        else:
            await closed_reports.send(f"**Member's username was attempted to be changed** by {interaction.user.mention} - {self.view.member.mention} had the innapropriate username `{self.view.offending_username}`, and their username was attempted to be changed to `boomilever`, however, the user had left the server.")

        # Update the report database
        # TODO

class KickUserButton(discord.ui.Button):

    view: discord.ui.View

    def __init__(self, view):
        self.view = view
        super().__init__(style = discord.ButtonStyle.red, label = "Kick User", custom_id = f"{view.report_id}:kick")

    async def callback(self, interaction: discord.Interaction):
        # Delete the original message
        await interaction.message.delete()

        # Check to make sure user is still in server before taking action
        member_still_here = self.view.member in self.view.member.guild.members

        # Send an informational message about the report being updated
        closed_reports = discord.utils.get(interaction.guild.text_channels, name = 'closed-reports')
        if member_still_here:
            await closed_reports.send(f"**Member was kicked** by {interaction.user.mention} - {self.view.member.mention} had the innapropriate username `{self.view.offending_username}`, and the user was kicked from the server.")

            # Kick the user
            await self.view.member.kick()

        else:
            await closed_reports.send(f"**Attemped to kick member* by {interaction.user.mention} - {self.view.member.mention} had the innapropriate username `{self.view.offending_username}` and a kick was attempted on the user, however, the user had left the server.")

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
