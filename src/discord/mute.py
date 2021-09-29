import discord
import dateparser
import pytz
from src.discord.globals import PI_BOT_IDS, ROLE_SELFMUTE, ROLE_MUTED, CRON_LIST

async def _mute(ctx, user:discord.Member, time: str, self: bool):
    """
    Helper function for muting commands.

    :param user: User to be muted.
    :type user: discord.Member
    :param time: The time to mute the user for.
    :type time: str
    """
    if user.id in PI_BOT_IDS:
        return await ctx.send("Hey! You can't mute me!!")
    if time == None:
        return await ctx.send("You need to specify a length that this used will be muted. Examples are: `1 day`, `2 months, 1 day`, or `indef` (aka, forever).")
    role = None
    if self:
        role = discord.utils.get(user.guild.roles, name=ROLE_SELFMUTE)
    else:
        role = discord.utils.get(user.guild.roles, name=ROLE_MUTED)
    parsed = "indef"
    if time != "indef":
        parsed = dateparser.parse(time, settings={"PREFER_DATES_FROM": "future"})
        if parsed == None:
            return await ctx.send("Sorry, but I don't understand that length of time.")
        CRON_LIST.append({"date": parsed, "do": f"unmute {user.id}"})
    await user.add_roles(role)
    eastern = pytz.timezone("US/Eastern")
    await ctx.send(f"Successfully muted {user.mention} until `{str(eastern.localize(parsed))} EST`.")