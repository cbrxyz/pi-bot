import discord.ext.commands as commands
class CommandNotAllowedInChannel(commands.CommandError):
    def __init__(self, channel, *args, **kwargs):
        self.channel = channel
        super().__init__(*args, **kwargs)
        
class CommandNotInvokedInBotSpam(commands.CommandError):
    def __init__(self, channel, message, *args, **kwargs):
        self.channel = channel
        self.message = message

class SelfMuteCommandStaffInvoke(commands.CommandError):
    def __init__(self, message, *args, **kwargs):
        self.message = message