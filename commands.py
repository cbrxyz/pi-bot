import discord
import math

# Files
from embed import assemble_embed
from commandinfo import COMMAND_INFO

async def _generateList(member: discord.Member, is_quick = False):
    """
    Generates a list of available commands for a user.

    :param member: The user that wants to generate a list of commands
    :type member: discord.Member
    :param is_quick: True if quick list should be generated. False if full list should be generated.
    :type is_quick: bool, optional

    :return: A list of commands to be displayed.
    :rtype: List[Dictionary]
    """
    available_commands = []
    for command in COMMAND_INFO:
        if not is_quick or command['inQuickList']:
            access = command['access']
            for role_name in access:
                role = discord.utils.get(member.guild.roles, name=role_name)
                if role in member.roles:
                    available_commands.append({
                        'name': command['name'],
                        'description': command['description']
                    })
                    break
    return available_commands

async def get_list(author, page):
    """Gets the list of commands a user can access."""
    available_commands = await _generateList(author, False)
    available_commands.sort(key=lambda x: x['name'])
    total_pages = math.floor(len(available_commands)/10) + 1
    if page == 100:
        page = total_pages
    if page > total_pages or page < 1:
        return False
    available_commands = available_commands[(page-1)*10:(page)*10]
    return assemble_embed(
        title=f"List of Commands for `{author}` (Page {page}/{total_pages})",
        desc="\n".join([f"`{c['name']}` - {c['description']}" for c in available_commands])
    )

async def get_quick_list(ctx):
    """Gets the quick list of commands a user can access."""
    available_commands = await _generateList(ctx.message.author, True)
    available_commands.sort(key=lambda x: x['name'])
    return assemble_embed(
        title=f"Quick List of Available Commands for {ctx.message.author}",
        desc="To view full list, please type `!list all`.",
        fields=[{
            "name": "Commands",
            "value": "\n".join([f"`{c['name']}` - {c['description']}" for c in available_commands]),
            "inline": False
        }]
    )

async def get_help(ctx, cmd):
    """Gets the help embed for a command."""
    cmd_info = next((c for c in COMMAND_INFO if c["name"] == cmd or cmd in c["aliases"]), None)
    if cmd_info == None:
        return assemble_embed(
            title=f"`{cmd}`",
            desc="Cannot find command with this name. Try again buddy.",
            webcolor="red"
        )
    else:
        roles = [(discord.utils.get(ctx.message.author.guild.roles, name=r)) for r in cmd_info['access']]
        command_fields = [
            {
                "name": "Parameters",
                "value": "\n".join([f"`{p['name']}` - {p['description']}" for p in cmd_info['parameters']]) if len(cmd_info['parameters']) > 0 else "`none`",
                "inline": False
            }
        ]
        # If command has flags show those, if not do nothing
        if 'flags' in cmd_info:
            command_fields.append({
                "name": "Flags",
                "value": "\n".join([f"`-{u['name']}` - {u['description']}" for u in cmd_info['flags']]),
                "inline": False
            })
        # Add available roles
        command_fields.extend([
                {
                    "name": "Usage",
                    "value": "\n".join([f"`{u['cmd']}` - {u['result']}" for u in cmd_info['usage']]),
                    "inline": False
                },
                {
                    "name": "Available To",
                    "value": "\n".join([f"{r.mention}" for r in roles]),
                    "inline": False
                }
            ]
        )
        return assemble_embed(
            title=f"`!{cmd_info['name']}`",
            desc=f"{cmd_info['description']}",
            fields=command_fields,
            webcolor="gold"
        )