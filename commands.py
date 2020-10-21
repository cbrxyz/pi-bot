import discord

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

async def getList(ctx):
    """Gets the list of commands a user can access."""
    availableCommands = await _generateList(ctx.message.author, False)
    availableCommands.sort(key=lambda x: x['name'])
    return assembleEmbed(
        title=f"Full List of Available Commands for {ctx.message.author}",
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
        return assembleEmbed(
            title=f"`!{cmdInfo['name']}`",
            desc=f"{cmdInfo['description']}",
            fields=[
                {
                    "name": "Parameters",
                    "value": "\n".join([f"`{p['name']}` - {p['description']}" for p in cmdInfo['parameters']]) if len(cmdInfo['parameters']) > 0 else "`none`",
                    "inline": False
                },
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
            ],
            webcolor="gold"
        )