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

from src.discord.views import YesNo

class StaffCensor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("Initialized staff censor cog.")

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        name = 'censoradd',
        description = 'Staff commands. Adds a word or emoji to the censor list.'
    )
    @permissions.has_any_role(ROLE_STAFF, ROLE_VIP, guild_id = SERVER_ID)
    async def censor_add(self,
        ctx,
        censor_type: Option(str, "Whether to add a new word or emoji to the list.", choices = ["word", "emoji"], required = True),
        phrase: Option(str, "The new word or emoji to add. For a new word, type the word. For a new emoji, send the emoji.", required = True)
        ):
        commandchecks.is_staff_from_ctx(ctx)

        if censor_type == "word":
            if phrase in CENSOR['words']:
                await ctx.interaction.response.send_message(content = f"`{phrase}` is already in the censored words list. Operation cancelled.")
            else:
                CENSOR['words'].append(phrase)
                await update("data", "censor", CENSOR['_id'], {"$push": {"words": phrase}})
        elif censor_type == "emoji":
            if phrase in CENSOR['emojis']:
                await ctx.interaction.response.send_message(content = f"{phrase} is already in the censored emoijs list. Operation cancelled.")
            else:
                CENSOR['emojis'].append(phrase)
                await update("data", "censor", CENSOR['_id'], {"$push": {"emojis": phrase}})

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        name = 'censorremove',
        description = 'Staff command. Removes a word/emoji from the censor list.'
    )
    @permissions.has_any_role(ROLE_STAFF, ROLE_VIP, guild_id = SERVER_ID)
    async def censor_remove(self,
        ctx,
        censor_type: Option(str, "Whether to remove a word or emoji.", choices = ["word", "emoji"], required = True),
        phrase: Option(str, "The word or emoji to remove from the censor list.", required = True)
        ):
        commandchecks.is_staff_from_ctx(ctx)

        if censor_type == "word":
            if phrase not in CENSOR["words"]:
                await ctx.interaction.response.send_message(content = f"`{phrase}` is not in the list of censored words.")
            else:
                del CENSOR["words"][phrase]
                await update("data", "censor", CENSOR['_id'], {"$pull": {"words": phrase}})
        elif censor_type == "emoji":
            if phrase not in CENSOR["emojis"]:
                await ctx.interaction.response.send_message(content = f"`{phrase}` is not in the list of censored emojis.")
            else:
                del CENSOR["emojis"][phrase]
                await update("data", "censor", CENSOR["_id"], {"$pull": {"emojis": phrase}})

def setup(bot):
    bot.add_cog(StaffCensor(bot))
