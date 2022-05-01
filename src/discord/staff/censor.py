import discord
from discord.commands import slash_command

from discord.ext import commands
from discord.commands import Option, permissions
import commandchecks

import src.discord.globals

from src.discord.globals import CENSOR, SLASH_COMMAND_GUILDS, INVITATIONAL_INFO, CHANNEL_BOTSPAM, CATEGORY_ARCHIVE, ROLE_AT, ROLE_MUTED, EMOJI_GUILDS, TAGS, EVENT_INFO, EMOJI_LOADING
from src.discord.globals import CATEGORY_SO, CATEGORY_GENERAL, ROLE_MR, CATEGORY_STATES, ROLE_WM, ROLE_GM, ROLE_AD, ROLE_BT
from src.discord.globals import PI_BOT_IDS, ROLE_EM, CHANNEL_TOURNAMENTS
from src.discord.globals import CATEGORY_TOURNAMENTS, ROLE_ALL_STATES, ROLE_SELFMUTE, ROLE_QUARANTINE, ROLE_GAMES
from src.discord.globals import SERVER_ID, CHANNEL_WELCOME, ROLE_UC, ROLE_LH, ROLE_STAFF, ROLE_VIP

from src.mongo.mongo import update

from src.discord.views import YesNo

class StaffCensor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("Initialized staff censor cog.")

    censor_group = discord.commands.SlashCommandGroup(
        "censor",
        "Controls Pi-Bot's censor.",
        guild_ids = [SLASH_COMMAND_GUILDS],
        permissions = [
            discord.commands.CommandPermission(ROLE_STAFF, 1, True),
            discord.commands.CommandPermission(ROLE_VIP, 1, True),
        ]
    )

    @censor_group.command(
        name = 'add',
        description = 'Staff command. Adds a new entry into the censor.'
    )
    @permissions.has_any_role(ROLE_STAFF, ROLE_VIP, guild_id = SERVER_ID)
    async def censor_add(self,
        ctx,
        censor_type: Option(str, "Whether to add a new word or emoji to the list.", choices = ["word", "emoji"], required = True),
        phrase: Option(str, "The new word or emoji to add. For a new word, type the word. For a new emoji, send the emoji.", required = True)
        ):
        # Check for staff permissions
        commandchecks.is_staff_from_ctx(ctx)

        # Send notice message
        await ctx.interaction.response.send_message(f"{EMOJI_LOADING} Attempting to add {censor_type} to censor list.")

        print(src.discord.globals.CENSOR)
        if censor_type == "word":
            if phrase in src.discord.globals.CENSOR['words']:
                await ctx.interaction.edit_original_message(content = f"`{phrase}` is already in the censored words list. Operation cancelled.")
            else:
                src.discord.globals.CENSOR['words'].append(phrase)
                await update("data", "censor", src.discord.globals.CENSOR['_id'], {"$push": {"words": phrase}})
                first_letter = phrase[0]
                last_letter = phrase[-1]
                await ctx.interaction.edit_original_message(content = f"Added `{first_letter}...{last_letter}` to the censor list.")
        elif censor_type == "emoji":
            if phrase in src.discord.globals.CENSOR['emojis']:
                await ctx.interaction.edit_original_message(content = f"Emoji is already in the censored emoijs list. Operation cancelled.")
            else:
                src.discord.globals.CENSOR['emojis'].append(phrase)
                await update("data", "censor", src.discord.globals.CENSOR['_id'], {"$push": {"emojis": phrase}})
                await ctx.interaction.edit_original_message(content = f"Added emoji to the censor list.")

    @censor_group.command(
        name = 'remove',
        description = 'Staff command. Removes a word/emoji from the censor list.'
    )
    @permissions.has_any_role(ROLE_STAFF, ROLE_VIP, guild_id = SERVER_ID)
    async def censor_remove(self,
        ctx,
        censor_type: Option(str, "Whether to remove a word or emoji.", choices = ["word", "emoji"], required = True),
        phrase: Option(str, "The word or emoji to remove from the censor list.", required = True)
        ):
        # Check for staff permissions again
        commandchecks.is_staff_from_ctx(ctx)

        # Send notice message
        await ctx.interaction.response.send_message(f"{EMOJI_LOADING} Attempting to remove {censor_type} from censor list.")

        if censor_type == "word":
            if phrase not in src.discord.globals.CENSOR["words"]:
                await ctx.interaction.response.send_message(content = f"`{phrase}` is not in the list of censored words.")
            else:
                src.discord.globals.CENSOR["words"].remove(phrase)
                await update("data", "censor", src.discord.globals.CENSOR['_id'], {"$pull": {"words": phrase}})
                await ctx.interaction.edit_original_message(content = f"Removed `{phrase}` from the censor list.")
        elif censor_type == "emoji":
            if phrase not in src.discord.globals.CENSOR["emojis"]:
                await ctx.interaction.response.send_message(content = f"{phrase} is not in the list of censored emojis.")
            else:
                src.discord.globals.CENSOR["emojis"].remove(phrase)
                await update("data", "censor", src.discord.globals.CENSOR["_id"], {"$pull": {"emojis": phrase}})
                await ctx.interaction.edit_original_message(content = f"Removed {phrase} from the emojis list.")

def setup(bot):
    bot.add_cog(StaffCensor(bot))
