import discord
from discord.commands import slash_command

from discord.ext import commands
from discord.commands import Option, permissions
import commandchecks

from src.discord.globals import CENSOR, SLASH_COMMAND_GUILDS, INVITATIONAL_INFO, CHANNEL_BOTSPAM, CATEGORY_ARCHIVE, ROLE_AT, ROLE_MUTED, EMOJI_GUILDS, TAGS, EVENT_INFO, EMOJI_LOADING
from src.discord.globals import CATEGORY_SO, CATEGORY_GENERAL, ROLE_MR, CATEGORY_STATES, ROLE_WM, ROLE_GM, ROLE_AD, ROLE_BT
from src.discord.globals import PI_BOT_IDS, ROLE_EM, CHANNEL_TOURNAMENTS
from src.discord.globals import CATEGORY_TOURNAMENTS, ROLE_ALL_STATES, ROLE_SELFMUTE, ROLE_QUARANTINE, ROLE_GAMES
from src.discord.globals import SERVER_ID, CHANNEL_WELCOME, ROLE_UC, ROLE_LH, ROLE_STAFF, ROLE_VIP

from src.mongo.mongo import update

class StaffTags(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("Initialized staff tags cog.")

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        name = "tagadd",
        description = "Staff command. Adds a new tag."
    )
    @permissions.has_any_role(ROLE_STAFF, ROLE_VIP, guild_id = SERVER_ID)
    async def tag_add(self,
        ctx,
        tag_name: Option(str, "The name of the tag to add.", required = True),
        launch_helpers: Option(str, "Whether launch helpers can use. Defaults to yes.", choices = ["yes", "no"], default = "yes"),
        members: Option(str, "Whether all members can use this tag. Defaults to yes.", choices = ["yes", "no"], default = "yes")
        ):
        commandchecks.is_staff_from_ctx(ctx)

        if tag_name in [t['name'] for t in src.discord.globals.TAGS]:
            await ctx.interaction.response.send_message(content = f"The `{tag_name}` tag has already been added. To edit this tag, please use `/tagedit` instead.")
        else:
            await ctx.interaction.response.defer()

            succesful = False
            while not succesful:
                info_message = await ctx.send("Please send the new text for the tag enclosed in a preformatted block. The block should begin and end with three backticks, with no content on the line of the backticks. If no response is found in 2 minutes, the operation will be cancelled.")
                content_message = await listen_for_response(
                    follow_id = ctx.user.id,
                    timeout = 120,
                )

                if content_message == None:
                    await ctx.interaction.edit_original_message(content = "No message was found within 2 minutes. Operation cancelled.")
                    return

                text = content_message.content
                await content_message.delete()
                await info_message.delete()
                matches = re.findall(r"(?<=```\n)(.*)(?=\n```)", text, flags = re.MULTILINE | re.DOTALL)
                if len(matches) < 0:
                    await ctx.interaction.edit_original_message(content = "No matching preformatted block was found. Operation cancelled.")
                    return
                else:
                    new_dict = {
                        'name': tag_name,
                        'output': matches[0],
                        'permissions': {
                            'staff': True,
                            'launch_helpers': True if launch_helpers == "yes" else False,
                            'members': True if members == "yes" else False
                        }
                    }

                    src.discord.globals.TAGS.append(new_dict)
                    await insert("data", "tags", new_dict)
                    succesful = True
                    await ctx.interaction.edit_original_message(content = f"The `{tag_name}` tag was added!")

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        name = "tagedit",
        description = "Staff command. Edits an existing tag."
    )
    @permissions.has_any_role(ROLE_STAFF, ROLE_VIP, guild_id = SERVER_ID)
    async def tag_edit(self,
        ctx,
        tag_name: Option(str, "The tag name to edit the text of.", required = True),
        launch_helpers: Option(str, "Whether launch helpers can use. Defaults to 'do not change'.", choices = ["yes", "no", "do not change"], default = "do not change"),
        members: Option(str, "Whether all members can use this tag. Defaults to 'do not change'.", choices = ["yes", "no", "do not change"], default = "do not change")
        ):
        commandchecks.is_staff_from_ctx(ctx)

        if tag_name not in [t['name'] for t in src.discord.globals.TAGS]:
            return await ctx.interaction.response.send_message(content = f"No tag with name `{tag_name}` could be found.")

        tag = [t for t in src.discord.globals.TAGS if t['name'] == tag_name][0]

        await ctx.interaction.response.defer()
        info_message = await ctx.send(f"The current content of the tag is:\n```\n{tag['output']}\n```\nPlease enclose a new message to associate with the tag by entering a message in a preformatted block (a block of text between three backticks).")

        content_message = await listen_for_response(
            follow_id = ctx.user.id,
            timeout = 120,
        )

        if content_message == None:
            await ctx.interaction.edit_original_message(content = "No message was found within 2 minutes. Operation cancelled.")
            return

        text = content_message.content
        await content_message.delete()
        await info_message.delete()

        matches = re.findall(r"(?<=```\n)(.*)(?=\n```)", text, flags = re.MULTILINE | re.DOTALL)
        if len(matches) < 0:
            await ctx.interaction.edit_original_message(content = "No matching preformatted block was found. Operation cancelled.")
            return
        else:
            update_dict = {}

            tag['output'] = matches[0]
            update_dict['output'] = matches[0]
            if launch_helpers != "do not change":
                tag['permissions']['launch_helpers'] = True if launch_helpers == "yes" else False
                update_dict['permissions.launch_helpers'] = True if launch_helpers == "yes" else False
            if members != "do not change":
                tag['permissions']['members'] = True if members == "yes" else False
                update_dict['permissions.members'] = True if members == "yes" else False

            await update("data", "tags", tag['_id'], {"$set": update_dict})
            await ctx.interaction.edit_original_message(content = f"The `{tag_name}` tag was updated.")

    @discord.commands.slash_command(
        guildids = [SLASH_COMMAND_GUILDS],
        name = "tagremove",
        description = "Staff command. Removes a tag completely."
    )
    @permissions.has_any_role(ROLE_STAFF, ROLE_VIP, guild_id = SERVER_ID)
    async def tag_remove(self,
        ctx,
        tag_name: Option(str, "The name of the tag to remove.", required = True)
        ):
        commandchecks.is_staff_from_ctx(ctx)

        if tag_name not in [t['name'] for t in src.discord.globals.TAGS]:
            return await ctx.interaction.response.send_message(content = f"No tag with the name of `{tag_name}` was found.")

        tag = [t for t in src.discord.globals.TAGS if t['name'] == tag_name][0]
        src.discord.globals.TAGS.remove(tag)
        await delete("data", "tags", tag['_id'])
        return await ctx.interaction.response.send_message(content = f"The `{tag_name}` tag was deleted.")

def setup(bot):
    bot.add_cog(StaffTags(bot))
