import discord
from discord.ext import commands
from commanderrors import CommandNotAllowedInChannel
from src.discord.globals import ROLE_VIP, ROLE_STAFF, ROLE_WM, ROLE_GM, ROLE_AD, ROLE_LH, SERVER_ID

async def is_bear(ctx):
    """Checks to see if the user is bear, or pepperonipi (for debugging purposes)."""
    return ctx.message.author.id == 353730886577160203 or ctx.message.author.id == 715048392408956950

async def is_staff(ctx):
#     """Checks to see if the user is a staff member."""
    return await is_author_staff(ctx.message.author)
    # vipRole = discord.utils.get(member.guild.roles, name=ROLE_VIP)
    # staffRole = discord.utils.get(member.guild.roles, name=ROLE_STAFF)
    # return vipRole in member.roles or staffRole in member.roles
    
async def is_author_staff(author: discord.abc.User):
    """Checks to see if the user is a staff member."""
    vipRole = discord.utils.get(author.guild.roles, name=ROLE_VIP)
    staffRole = discord.utils.get(author.guild.roles, name=ROLE_STAFF)
    return vipRole in author.roles or staffRole in author.roles

async def is_launcher(ctx):
    """Checks to see if the user is a launch helper."""
    member = ctx.message.author
    staff = await is_staff(ctx)
    lhRole = discord.utils.get(member.guild.roles, name=ROLE_LH)
    if staff or lhRole in member.roles: return True

async def is_launcher_no_ctx(member):
    server = bot.get_guild(SERVER_ID)
    wmRole = discord.utils.get(server.roles, name=ROLE_WM)
    gm_role = discord.utils.get(server.roles, name=ROLE_GM)
    aRole = discord.utils.get(server.roles, name=ROLE_AD)
    vipRole = discord.utils.get(server.roles, name=ROLE_VIP)
    lhRole = discord.utils.get(server.roles, name=ROLE_LH)
    roles = [wmRole, gm_role, aRole, vipRole, lhRole]
    member = server.get_member(member)
    for role in roles:
        if role in member.roles: return True
    return False

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