import discord
from discord.ext import commands
from commanderrors import CommandNotAllowedInChannel
from src.discord.globals import ROLE_VIP, ROLE_STAFF, ROLE_AD, ROLE_LH, SERVER_ID

async def is_bear(ctx):
    """Checks to see if the user is bear, or pepperonipi (for debugging purposes)."""
    return ctx.message.author.id == 353730886577160203 or ctx.message.author.id == 715048392408956950

def is_staff():
    """Checks to see if the author of ctx message is a staff member."""
    def predicate(ctx):
        guild = ctx.bot.get_guild(SERVER_ID)
        member = guild.get_member(ctx.message.author.id)
        staffRole = discord.utils.get(guild.roles, name=ROLE_STAFF)
        vipRole = discord.utils.get(guild.roles, name=ROLE_VIP)
        if any(r in [staffRole, vipRole] for r in member.roles): return True
        raise commands.MissingAnyRole([staffRole, vipRole])
    return commands.check(predicate)

def is_staff_from_ctx(ctx, no_raise = False):
    guild = ctx.guild
    member = ctx.author
    staff_role = discord.utils.get(guild.roles, name=ROLE_STAFF)
    vip_role = discord.utils.get(guild.roles, name=ROLE_VIP)
    if any(r in [staff_role, vip_role] for r in member.roles): return True
    if no_raise: return False # Option for evading default behavior of raising error
    raise commands.MissingAnyRole([staff_role, vip_role])

async def is_author_staff(author: discord.Member):
    """Checks to see if the author is a staff member."""
    vipRole = discord.utils.get(author.guild.roles, name=ROLE_VIP)
    staffRole = discord.utils.get(author.guild.roles, name=ROLE_STAFF)
    return vipRole in author.roles or staffRole in author.roles

async def is_launcher(ctx):
    """Checks to see if the user is a launch helper."""
    guild = ctx.bot.get_guild(SERVER_ID)
    member = guild.get_member(ctx.message.author.id)
    staffRole = discord.utils.get(guild.roles, name=ROLE_STAFF)
    vipRole = discord.utils.get(guild.roles, name=ROLE_VIP)
    lhRole = discord.utils.get(guild.roles, name=ROLE_LH)
    print(any(r in [staffRole, vipRole, lhRole] for r in member.roles))
    if any(r in [staffRole, vipRole, lhRole] for r in member.roles): return True
    raise commands.MissingAnyRole([staffRole, vipRole, lhRole])

def check_is_launcher():
    return commands.check(is_launcher)

async def is_admin(ctx):
    """Checks to see if the user is an administrator, or pepperonipi (for debugging purposes)."""
    member = ctx.message.author
    aRole = discord.utils.get(member.guild.roles, name=ROLE_AD)
    if aRole in member.roles or member.id == 715048392408956950: return True

def not_blacklisted_channel(blacklist):
    """Given a string array blacklist, check if command was not invoked in specified blacklist channels."""
    async def predicate(ctx):
        channel = ctx.message.channel
        server = ctx.bot.get_guild(SERVER_ID)
        for c in blacklist:
            if channel == discord.utils.get(server.text_channels, name=c):
                raise CommandNotAllowedInChannel(channel, "Command was invoked in a blacklisted channel.")
        return True

    return commands.check(predicate)

def is_whitelisted_channel(whitelist):
    """Given a string array whitelist, check if command was invoked in specified whitelisted channels."""
    async def predicate(ctx):
        channel = ctx.message.channel
        server = ctx.bot.get_guild(SERVER_ID)
        for c in whitelist:
            if channel == discord.utils.get(server.text_channels, name=c):
                return True
        raise CommandNotAllowedInChannel(channel, "Command was invoked in a non-whitelisted channel.")

    return commands.check(predicate)
