import discord
import datetime
from discord.ext import commands
import src.discord.globals
from src.discord.globals import CHANNEL_EDITEDM, CHANNEL_DELETEDM, CHANNEL_DMLOG, SERVER_ID
import re

class Logger(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        print("Initialized Logger cog.")

    async def log_edit_message_payload(self, payload):
        """
        Logs a payload for the 'Edit Message' event.
        """
        # Get the required resources for logging
        channel = self.bot.get_channel(payload.channel_id)
        guild = self.bot.get_guild(SERVER_ID) if channel.type == discord.ChannelType.private else channel.guild
        edited_channel = discord.utils.get(guild.text_channels, name=CHANNEL_EDITEDM)

        # Ignore payloads for events in logging channels (which would cause recursion)
        if channel.type != discord.ChannelType.private and channel.name in [CHANNEL_EDITEDM, CHANNEL_DELETEDM, CHANNEL_DMLOG]:
            return

        # Attempt to log from the cached message if found, else just report on what is available
        try:
            message = payload.cached_message
            if (discord.utils.utcnow() - message.created_at).total_seconds() < 2:
                # No need to log edit event for a message that was just created
                return

            message_now = await channel.fetch_message(message.id)
            channel_name = f"{message.author.mention}'s DM" if channel.type == discord.ChannelType.private else message.channel.mention

            embed = discord.Embed(
                title=":pencil: Edited Message"
            )
            fields = [
                {
                    "name": "Author",
                    "value": message.author,
                    "inline": "True"
                },
                {
                    "name": "Channel",
                    "value": channel_name,
                    "inline": "True"
                },
                {
                    "name": "Message ID",
                    "value": f"{payload.message_id} ([jump!]({message_now.jump_url}))",
                    "inline": "True"
                },
                {
                    "name": "Created At",
                    "value": discord.utils.format_dt(message.created_at, 'R'),
                    "inline": "True"
                },
                {
                    "name": "Edited At",
                    "value": discord.utils.format_dt(message_now.edited_at, 'R'),
                    "inline": "True"
                },
                {
                    "name": "Attachments",
                    "value": " | ".join([f"**{a.filename}**: [Link]({a.url})" for a in message.attachments]) if len(message.attachments) > 0 else "None",
                    "inline": "False"
                },
                {
                    "name": "Past Content",
                    "value": message.content[:1024] if len(message.content) > 0 else "None",
                    "inline": "False"
                },
                {
                    "name": "New Content",
                    "value": message_now.content[:1024] if len(message_now.content) > 0 else "None",
                    "inline": "False"
                },
                {
                    "name": "Embed",
                    "value": "\n".join([str(e.to_dict()) for e in message.embeds]) if len(message.embeds) > 0 else "None",
                    "inline": "False"
                }
            ]
            for field in fields:
                embed.add_field(
                    name = field['name'],
                    value = field['value'],
                    inline = field['inline']
                )

            await edited_channel.send(embed=embed)

        except Exception as _: # No cached message is available
            message_now = await channel.fetch_message(payload.message_id)
            embed = discord.Embed(
                title=":pencil: Edited Message"
            )

            fields=[
                {
                    "name": "Channel",
                    "value": self.bot.get_channel(payload.channel_id).mention,
                    "inline": "True"
                },
                {
                    "name": "Message ID",
                    "value": f"{payload.message_id} ([jump!]({message_now.jump_url}))",
                    "inline": "True"
                },
                {
                    "name": "Author",
                    "value": message_now.author,
                    "inline": "True"
                },
                {
                    "name": "Created At",
                    "value": discord.utils.format_dt(message_now.created_at, 'R'),
                    "inline": "True"
                },
                {
                    "name": "Edited At",
                    "value": discord.utils.format_dt(message_now.edited_at, 'R'),
                    "inline": "True"
                },
                {
                    "name": "New Content",
                    "value": message_now.content[:1024] if len(message_now.content) > 0 else "None",
                    "inline": "False"
                },
                {
                    "name": "Current Attachments",
                    "value": " | ".join([f"**{a.filename}**: [Link]({a.url})" for a in message_now.attachments]) if len(message_now.attachments) > 0 else "None",
                    "inline": "False"
                },
                {
                    "name": "Current Embed",
                    "value": "\n".join([str(e.to_dict()) for e in message_now.embeds])[:1024] if len(message_now.embeds) > 0 else "None",
                    "inline": "False"
                }
            ]
            for field in fields:
                embed.add_field(
                    name = field['name'],
                    value = field['value'],
                    inline = field['inline']
                )

            await edited_channel.send(embed=embed)

    async def log_delete_message_payload(self, payload):
        """
        Logs a message payload that came from a 'Delete Message' payload.
        """
        # Get the required resources
        channel = self.bot.get_channel(payload.channel_id)
        guild = self.bot.get_guild(SERVER_ID) if channel.type == discord.ChannelType.private else channel.guild
        deleted_channel = discord.utils.get(guild.text_channels, name=CHANNEL_DELETEDM)

        # Do not send a log for messages deleted out of the deleted messages channel (could cause a possible bot recursion)
        if channel.type != discord.ChannelType.private and channel.name in [CHANNEL_DELETEDM]:
            return

        try:
            message = payload.cached_message
            channel_name = f"{message.author.mention}'s DM" if channel.type == discord.ChannelType.private else message.channel.mention
            embed = discord.Embed(
                title=":fire: Deleted Message"
            )
            fields=[
                {
                    "name": "Author",
                    "value": message.author,
                    "inline": "True"
                },
                {
                    "name": "Channel",
                    "value": channel_name,
                    "inline": "True"
                },
                {
                    "name": "Message ID",
                    "value": payload.message_id,
                    "inline": "True"
                },
                {
                    "name": "Created At",
                    "value": discord.utils.format_dt(message.created_at, 'R'),
                    "inline": "True"
                },
                {
                    "name": "Deleted At",
                    "value": discord.utils.format_dt(discord.utils.utcnow(), 'R'),
                    "inline": "True"
                },
                {
                    "name": "Attachments",
                    "value": " | ".join([f"**{a.filename}**: [Link]({a.url})" for a in message.attachments]) if len(message.attachments) > 0 else "None",
                    "inline": "False"
                },
                {
                    "name": "Content",
                    "value": str(message.content)[:1024] if len(message.content) > 0 else "None",
                    "inline": "False"
                },
                {
                    "name": "Embed",
                    "value": "\n".join([str(e.to_dict()) for e in message.embeds])[:1024] if len(message.embeds) > 0 else "None",
                    "inline": "False"
                }
            ]
            for field in fields:
                embed.add_field(
                    name = field['name'],
                    value = field['value'],
                    inline = field['inline']
                )

            await deleted_channel.send(embed=embed)

        except Exception as _:

            embed = discord.Embed(
                title = ":fire: Deleted Message",
                description = "Because this message was not cached, I was unable to retrieve its content before it was deleted."
            )
            fields=[
                {
                    "name": "Channel",
                    "value": self.bot.get_channel(payload.channel_id).mention,
                    "inline": "True"
                },
                {
                    "name": "Message ID",
                    "value": payload.message_id,
                    "inline": "True"
                }
            ]
            for field in fields:
                embed.add_field(
                    name = field['name'],
                    value = field['value'],
                    inline = field['inline']
                )

            await deleted_channel.send(embed=embed)

def setup(bot):
    bot.add_cog(Logger(bot))
