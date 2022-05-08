import discord
from commanderrors import CommandNotAllowedInChannel
from discord.ext import commands
from src.discord.globals import ROLE_AD, ROLE_LH, ROLE_STAFF, ROLE_VIP, SERVER_ID
from typing import Union


async def is_bear(ctx) -> bool:
    """
    Checks to see if the user is bear, or pepperonipi (for debugging purposes).

    Returns:
        bool: Whether the check is valid.
    """
    return (
            ctx.message.author.id == 353730886577160203
            or ctx.message.author.id == 715048392408956950
    )


def is_staff_from_ctx(
        ctx: Union[commands.Context, discord.Interaction], no_raise=False
) -> bool:
    """
    Checks to see whether the user is a staff member from the provided context.

    Args:
        ctx (Union[discord.ext.commands.Context, discord.Interaction]):
          The relevant context to use for checking.
        no_raise (bool): Whether to raise an exception if the user is not a staff
          member.

    Raises:
        discord.ext.commands.MissingAnyRole: If no_raise is False, this exception is
          raised if the check does not pass.

    Returns:
        bool: Whether the check passed.
    """
    guild = ctx.guild
    member = ctx.author if isinstance(ctx, commands.Context) else ctx.user
    staff_role = discord.utils.get(guild.roles, name=ROLE_STAFF)
    vip_role = discord.utils.get(guild.roles, name=ROLE_VIP)
    if any(r in [staff_role, vip_role] for r in member.roles):
        return True
    if no_raise:
        return False  # Option for evading default behavior of raising error
    raise commands.MissingAnyRole([str(staff_role), str(vip_role)])
