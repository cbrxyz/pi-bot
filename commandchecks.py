"""
Stores various checks for specific commands, including priveleged commands.
"""
from typing import Union

import discord
from discord.ext import commands
from src.discord.globals import ROLE_STAFF, ROLE_VIP


def is_staff_from_ctx(
    ctx: Union[commands.Context, discord.Interaction], no_raise: bool = False
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
    assert isinstance(guild, discord.Guild)

    staff_role = discord.utils.get(guild.roles, name=ROLE_STAFF)
    vip_role = discord.utils.get(guild.roles, name=ROLE_VIP)
    assert isinstance(staff_role, discord.Role)
    assert isinstance(vip_role, discord.Role)

    if isinstance(member, discord.User):
        member = guild.get_member(member.id)
        assert isinstance(
            member, discord.Member
        )  # If this fails, user isn't in server anyways

    if any(r in [staff_role, vip_role] for r in member.roles):
        return True

    if no_raise:
        return False  # Option for evading default behavior of raising error

    raise commands.MissingAnyRole([str(staff_role), str(vip_role)])
