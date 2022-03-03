import re
import discord
import datetime
from discord.commands import slash_command

from discord.ext import commands
from discord.commands import Option, permissions
import commandchecks

from src.discord.globals import CENSOR, SLASH_COMMAND_GUILDS, INVITATIONAL_INFO, CHANNEL_BOTSPAM, CATEGORY_ARCHIVE, ROLE_AT, ROLE_MUTED, EMOJI_GUILDS, TAGS, EVENT_INFO, EMOJI_LOADING
from src.discord.globals import CATEGORY_SO, CATEGORY_GENERAL, ROLE_MR, CATEGORY_STATES, ROLE_WM, ROLE_GM, ROLE_AD, ROLE_BT
from src.discord.globals import PI_BOT_IDS, ROLE_EM, CHANNEL_TOURNAMENTS
from src.discord.globals import CATEGORY_TOURNAMENTS, ROLE_ALL_STATES, ROLE_SELFMUTE, ROLE_QUARANTINE, ROLE_GAMES
from src.discord.globals import SERVER_ID, CHANNEL_WELCOME, ROLE_UC, ROLE_LH, ROLE_STAFF, ROLE_VIP
from bot import listen_for_response

from src.mongo.mongo import get_invitationals, insert, update, delete

from src.discord.views import YesNo

from src.discord.tournaments import update_tournament_list

class StaffInvitational(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        print("Initialized Invitationals cog.")

    @discord.commands.command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        name = "invyadd",
        description = "Staff command. Adds a new invitational for voting."
    )
    @permissions.has_any_role(ROLE_STAFF, ROLE_VIP, guild_id = SERVER_ID)
    async def invitational_add(self,
        ctx,
        official_name: Option(str, "The official name of the tournament, such as MIT Invitational.", required = True),
        channel_name: Option(str, "The name of the Discord channel that will be created, such as 'mit'", required = True),
        tourney_date: Option(str, "The date of the tournament, formatted as YYYY-mm-dd, such as 2022-01-06.", required = True),
        status: Option(str, "Determines if the new tournament channel will be sent to voting or added immediately.", choices = ["voting", "add_immediately"], required = True)
    ):
        commandchecks.is_staff_from_ctx(ctx)

        new_tourney_doc = {
            'official_name': official_name,
            'channel_name': channel_name,
            'tourney_date': datetime.datetime.strptime(tourney_date, '%Y-%m-%d'),
            'aliases': [],
            'open_days': 10,
            'closed_days': 30,
            'voters': [],
            'status': "open" if status == "add_immediately" else "voting"
        }
        await ctx.interaction.response.defer()
        emoji = None
        while emoji == None:
            info_message = await ctx.send("Please send the emoji to use for the tournament. If you would like to use a custom image, **send a message containing a file that is less than 256KB in size.**\n\nIf you would like to use a standard emoji, please send a message with only the standard emoji.")
            emoji_message = await listen_for_response(
                follow_id = ctx.user.id,
                timeout = 120,
            )
            # If emoji message has file, use this as emoji, otherwise, use default emoji provided
            if emoji_message == None:
                await ctx.interaction.response.send_message(content = "No emoji was provided, so the operation was cancelled.")
                return

            if len(emoji_message.attachments) > 0:
                # If no attachments provided
                emoji_attachment = emoji_message.attachments[0]
                await emoji_message.delete()
                await info_message.delete()
                if emoji_attachment.size > 256000:
                    await ctx.send("Please use an emoji that is less than 256KB.")
                    continue
                if emoji_attachment.content_type not in ['image/gif', 'image/jpeg', 'image/png']:
                    await ctx.send("Please use a file that is a GIF, JPEG, or PNG.")
                    continue
                created_emoji = False
                for guild_id in EMOJI_GUILDS:
                    guild = self.bot.get_guild(guild_id)
                    if len(guild.emojis) < guild.emoji_limit:
                        # The guild can fit more custom emojis
                        emoji = await guild.create_custom_emoji(name = f"tournament_{channel_name}", image = await emoji_attachment.read(), reason = f"Created by {ctx.interaction.user}.")
                        created_emoji = True
                if not created_emoji:
                    await ctx.interaction.response.send_message(conten = f"Sorry {ctx.interaction.user}! The emoji guilds are currently full; a bot administrator will need to add more emoji guilds.")
                    return

            if len(emoji_message.content) > 0:
                emoji = emoji_message.content

        description = f"""
            **Official Name:** {official_name}
            **Channel Name:** `#{channel_name}`
            **Tournament Date:** {discord.utils.format_dt(new_tourney_doc['tourney_date'], 'D')}
            **Closes After:** {new_tourney_doc['closed_days']} days (the tournament channel is expected to close on {discord.utils.format_dt(new_tourney_doc['tourney_date'] + datetime.timedelta(days = new_tourney_doc['closed_days']), 'D')})
            **Tournament Emoji:** {emoji}
            """

        if status == "add_immediately":
            description += "\n**This tournament channel will be opened immediately.** This means that it will require no votes by users to open. This option should generally only be used for tournaments that have a very strong attendance or desire to be added to the server."
        else:
            description += "\n**This tournament channel will require a certain number of votes to be opened.** This means that the tournament channel will not immediately be created - rather, users will need to vote on the channel being created before the action is done."

        confirm_embed = discord.Embed(
            title = f"Add New Invitational",
            color = discord.Color(0x2E66B6),
            description = description
        )
        view = YesNo()
        await ctx.interaction.edit_original_message(content = f"Please confirm that you would like to add the following tournament:", embed = confirm_embed, view = view)
        await view.wait()
        if view.value:
            # Staff member responded with "Yes"
            new_tourney_doc['emoji'] = str(emoji)
            await insert("data", "invitationals", new_tourney_doc)
            await ctx.interaction.edit_original_message(content = "The invitational was added successfully.", embed = None, view = None)
            await update_tournament_list(self.bot, {})
        else:
            await ctx.interaction.edit_original_message(content = "The operation was cancelled.", embed = None, view = None)

    @discord.commands.command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        name = "invyapprove",
        description = "Staff command. Approves a invitational to be fully opened."
    )
    @permissions.has_any_role(ROLE_STAFF, ROLE_VIP, guild_id = SERVER_ID)
    async def invitational_approve(self,
        ctx,
        short_name: Option(str, "The short name of the invitational, such as 'mit'.", required = True)
        ):
        commandchecks.is_staff_from_ctx(ctx)

        invitationals = await get_invitationals()
        found_invitationals = [i for i in invitationals if i['channel_name'] == short_name]
        if len(found_invitationals) < 1:
            await ctx.interaction.response.send_message(content = f"Sorry, I couldn't find an invitational with the short name of `{short_name}`.")
        elif len(found_invitationals) == 1:
            if found_invitationals[0]["status"] == "open":
                await ctx.interaction.response.send_message(content = f"The `{short_name}` invitational is already open.")
            await update("data", "invitationals", found_invitationals[0]["_id"], {"$set": {"status": "open"}})
            await ctx.interaction.response.send_message(content = f"The status of the `{short_name}` invitational was updated.")
            await update_tournament_list(self.bot, {})

    @discord.commands.command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        name = "invyedit",
        description = "Staff command. Edits data about an invitational channel."
    )
    @permissions.has_any_role(ROLE_STAFF, ROLE_VIP, guild_id = SERVER_ID)
    async def invitational_edit(self,
        ctx,
        short_name: Option(str, "The short name of the invitational you would like to edit, such as 'mit'.", required = True),
        feature_to_edit: Option(str, "The feature you would like to edit about the invitational.", choices = [
            "official name",
            "short name",
            "emoji",
            "tournament date"
        ])
        ):
        commandchecks.is_staff_from_ctx(ctx)

        invitationals = await get_invitationals()
        found_invitationals = [i for i in invitationals if i['channel_name'] == short_name]
        if len(found_invitationals) < 1:
            await ctx.interaction.response.send_message(content = f"Sorry, I couldn't find an invitational with the short name of `{short_name}`.")
        elif len(found_invitationals) == 1:
            invitational = found_invitationals[0]
            relevant_words = {
                'official name': "official name",
                'short name': "short name",
                'emoji': "emoji",
                'tournament date': "tournament date"
            }
            info_message_text = f"Please send the new {relevant_words[feature_to_edit]} relevant to the tournament."
            if feature_to_edit == "emoji":
                info_message_text += "\n\nTo use a custom image as the new emoji for the invitational, please send a file that is no larger than 256KB. If you would like to use a new standard emoji for the invitational, please send only the new standard emoji."
            elif feature_to_edit == "tournament date":
                info_message_text += "\n\nTo update the tournament date, please send the date formatted as YYYY-mm-dd, such as `2022-01-12`."

            await ctx.interaction.response.defer()
            info_message = await ctx.send(info_message_text)
            content_message = await listen_for_response(
                follow_id = ctx.user.id,
                timeout = 120,
            )

            if content_message != None:
                rename_dict = {}
                await content_message.delete()
                await info_message.delete()
                if feature_to_edit == "official name":
                    rename_dict = {
                        'roles': {
                            invitational['official_name']: content_message.content
                        }
                    }
                    await update("data", "invitationals", invitational["_id"], {"$set": {"official_name": content_message.content}})
                    await ctx.interaction.edit_original_message(content = f"`{invitational['official_name']}` was renamed to **`{content_message.content}`**.")
                elif feature_to_edit == "short name":
                    rename_dict = {
                        'channels': {
                            invitational['channel_name']: content_message.content
                         }
                    }
                    await update("data", "invitationals", invitational["_id"], {"$set": {"channel_name": content_message.content}})
                    await ctx.interaction.edit_original_message(content = f"The channel for {invitational['official_name']} was renamed from `{invitational['channel_name']}` to **`{content_message.content}`**.")
                elif feature_to_edit == "emoji":
                    emoji = None
                    if len(content_message.attachments):
                        # User provided custom emoji
                        emoji_attachment = content_message.attachments[0]
                        if emoji_attachment.size > 256000:
                            await ctx.interaction.response.send_message("Please use an emoji that is less than 256KB. Operation cancelled.")
                        if emoji_attachment.content_type not in ['image/gif', 'image/jpeg', 'image/png']:
                            await ctx.interaction.response.send_message("Please use a file that is a GIF, JPEG, or PNG. Operation cancelled.")
                        created_emoji = False
                        for guild_id in EMOJI_GUILDS:
                            guild = self.bot.get_guild(guild_id)
                            for emoji in guild.emojis:
                                if emoji.name == f"tournament_{invitational['channel_name']}":
                                    await emoji.delete(reason = f"Replaced with alternate emoji by {ctx.interaction.user}.")
                            if len(guild.emojis) < guild.emoji_limit:
                                # The guild can fit more custom emojis
                                emoji = await guild.create_custom_emoji(name = f"tournament_{invitational['channel_name']}", image = await emoji_attachment.read(), reason = f"Created by {ctx.interaction.user}.")
                                created_emoji = True
                        if not created_emoji:
                            await ctx.interaction.edit_original_message(content = f"Sorry {ctx.interaction.user}! The emoji guilds are currently full; a bot administrator will need to add more emoji guilds.")
                            return

                    else:
                        # User provided standard emoji
                        emoji = content_message.content

                    await update("data", "invitationals", invitational["_id"], {"$set": {"emoji": emoji}})
                    await ctx.interaction.edit_original_message(content = f"The emoji for `{invitational['official_name']}` was updated to: {emoji}.")
                elif feature_to_edit == "tournament date":
                    date_str = content_message.content
                    date_dt = datetime.datetime.strptime(date_str, '%Y-%m-%d')
                    await update("data", "invitationals", invitational["_id"], {"$set": {"tourney_date": date_dt}})
                    await ctx.interaction.edit_original_message(content = f"The tournament date for `{invitational['official_name']}` was updated to {discord.utils.format_dt(date_dt, 'D')}.")
                await update_tournament_list(self.bot, rename_dict)
            else:
                await ctx.interaction.edit_original_message(content = f"No message was provided. Operation timed out after 120 seconds.")

    @discord.commands.command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        name = "invyarchive",
        description = "Staff command. Archives an invitational channel."
    )
    @permissions.has_any_role(ROLE_STAFF, ROLE_VIP, guild_id = SERVER_ID)
    async def invitational_archive(self,
        ctx,
        short_name: Option(str, "The short name referring to the invitational, such as 'mit'.", required = True)
        ):
        commandchecks.is_staff_from_ctx(ctx)

        invitationals = await get_invitationals()
        found_invitationals = [i for i in invitationals if i['channel_name'] == short_name]
        if not len(found_invitationals):
            await ctx.interaction.response.send_message(content = f"Sorry, I couldn't find an invitational with a short name of {short_name}.", ephemeral = True)

        # Invitational was found
        invitational = found_invitationals[0]

        # Update the database and tournament list
        await update("data", "invitationals", invitational["_id"], {"$set": {"status": "archived"}})
        await ctx.interaction.response.send_message(content = f"The **`{invitational['official_name']}`** is now being archived.", ephemeral = True)
        await update_tournament_list(self.bot, {})

    @discord.commands.command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        name = "invydelete",
        description = "Staff command. Deletes an invitational channel from the server."
    )
    @permissions.has_any_role(ROLE_STAFF, ROLE_VIP, guild_id = SERVER_ID)
    async def invitational_delete(self,
        ctx,
        short_name: Option(str, "The short name referring to the invitational, such as 'mit'.", required = True)
    ):
        commandchecks.is_staff_from_ctx(ctx)

        invitationals = await get_invitationals()
        found_invitationals = [i for i in invitationals if i['channel_name'] == short_name]
        if not len(found_invitationals):
            await ctx.interaction.response.send_message(content = f"Sorry, I couldn't find an invitational with a short name of {short_name}.")
        else:
            invitational = found_invitationals[0]
            server = self.bot.get_guild(SERVER_ID)
            ch = discord.utils.get(server.text_channels, name = invitational['channel_name'])
            r = discord.utils.get(server.roles, name = invitational['official_name'])
            if ch != None and ch.category.name in [CATEGORY_ARCHIVE, CATEGORY_TOURNAMENTS]:
                await ch.delete()
            if r != None:
                await r.delete()

            search = re.findall(r'<:.*:\d+>', invitational['emoji'])
            if len(search):
                emoji = self.bot.get_emoji(search[0])
                if emoji != None:
                    await emoji.delete()

            await delete("data", "invitationals", invitational["_id"])
            await ctx.interaction.response.send_message(f"Deleted the **`{invitational['official_name']}`**.")
            await update_tournament_list(self.bot, {})

def setup(bot):
    bot.add_cog(StaffInvitational(bot))
