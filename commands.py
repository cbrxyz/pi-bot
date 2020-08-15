import discord

# Files
from embed import assembleEmbed
from commandinfo import COMMAND_INFO

async def getList(ctx):
    """Gets the list of commands a user can access."""
    availableCommands = []
    member = ctx.message.author
    for command in COMMAND_INFO:
        access = command['access']
        for roleName in access:
            role = discord.utils.get(member.guild.roles, name=roleName)
            if role in member.roles:
                availableCommands.append({
                    'name': command['name'],
                    'description': command['description']
                })
                break
    return assembleEmbed(
        title=f"Available Commands for {ctx.message.author}",
        desc="\n".join([f"`{c['name']}` - {c['description']}" for c in availableCommands])
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
        print(cmdInfo)
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