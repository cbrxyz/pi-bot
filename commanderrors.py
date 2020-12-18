import discord.ext.commands as commands
class CommandNotAllowedInChannel(commands.CommandError):
    def __init__(self, channel, *args, **kwargs):
        self.channel = channel
        super().__init__(*args, **kwargs)