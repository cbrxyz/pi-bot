import discord
import math

# Files
from embed import assembleEmbed
from commandinfo import COMMAND_INFO

async def _generateList(member: discord.Member, isQuick = False):
    """
    Generates a list of available commands for a user.

    :param member: The user that wants to generate a list of commands
    :type member: discord.Member
    :param isQuick: True if quick list should be generated. False if full list should be generated.
    :type isQuick: bool, optional

    :return availableCommands: A list of commands to be displayed.
    :rtype availableCommands: List[Dictionary]
    """
    availableCommands = []
    for command in COMMAND_INFO:
        if not isQuick or command['inQuickList']:
            access = command['access']
            for roleName in access:
                role = discord.utils.get(member.guild.roles, name=roleName)
                if role in member.roles:
                    availableCommands.append({
                        'name': command['name'],
                        'description': command['description']
                    })
                    break
    return availableCommands

async def getList(author, page):
    """Gets the list of commands a user can access."""
    availableCommands = await _generateList(author, False)
    availableCommands.sort(key=lambda x: x['name'])
    totalPages = math.floor(len(availableCommands)/10) + 1
    if page == 100:
        page = totalPages
    if page > totalPages or page < 1:
        return False
    availableCommands = availableCommands[(page-1)*10:(page)*10]
    return assembleEmbed(
        title=f"List of Commands for `{author}` (Page {page}/{totalPages})",
        desc="\n".join([f"`{c['name']}` - {c['description']}" for c in availableCommands])
    )

async def getQuickList(ctx):
    """Gets the quick list of commands a user can access."""
    availableCommands = await _generateList(ctx.message.author, True)
    availableCommands.sort(key=lambda x: x['name'])
    return assembleEmbed(
        title=f"Quick List of Available Commands for {ctx.message.author}",
        desc="To view full list, please type `!list all`.",
        fields=[{
            "name": "Commands",
            "value": "\n".join([f"`{c['name']}` - {c['description']}" for c in availableCommands]),
            "inline": False
        }]
    )

async def getHelp(ctx, cmd):
    """Gets the help embed for a command."""
    wikiMods = discord.utils.get(ctx.message.author.guild.roles, name="Wiki Moderator")
    cmdInfo = next((c for c in COMMAND_INFO if c["name"] == cmd or cmd in c["aliases"]), None)
    if cmdInfo == None:
        return assembleEmbed(
            title=f"`{cmd}`",
            desc="Cannot find command with this name. Try again buddy.",
            webcolor="red"
        )
    else:
        roles = [(discord.utils.get(ctx.message.author.guild.roles, name=r)) for r in cmdInfo['access']]
        commandFields = [
            {
                "name": "Parameters",
                "value": "\n".join([f"`{p['name']}` - {p['description']}" for p in cmdInfo['parameters']]) if len(cmdInfo['parameters']) > 0 else "`none`",
                "inline": False
            }
        ]
        # If command has flags show those, if not do nothing
        if 'flags' in cmdInfo:
            commandFields.append({
                "name": "Flags",
                "value": "\n".join([f"`-{u['name']}` - {u['description']}" for u in cmdInfo['flags']]),
                "inline": False
            })
        # Add available roles
        commandFields.extend([
                {
                    "name": "Usage",
                    "value": "\n".join([f"`{u['cmd']}` - {u['result']}" for u in cmdInfo['usage']]),
                    "inline": False
                },
                {
                    "name": "Available To",
                    "value": "\n".join([f"{r.mention}" for r in roles]),
                    "inline": False
                }
            ]
        )
        return assembleEmbed(
            title=f"`!{cmdInfo['name']}`",
            desc=f"{cmdInfo['description']}",
            fields=commandFields,
            webcolor="gold"
        )