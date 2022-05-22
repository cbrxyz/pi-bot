"""
Stores various specific errors. These can be used to better describe why specific
exceptions occurred, avoiding the need to use general exceptions.
"""
from discord.ext import commands


class CommandNotAllowedInChannel(commands.CommandError):
    """
    There was an attempt to execute a command in a channel that the command was not
    permitted to be executed in. Currently not used.
    """

    def __init__(self, channel, *args, **kwargs):
        self.channel = channel
        super().__init__(*args, **kwargs)


class CommandNotInvokedInBotSpam(commands.CommandError):
    """
    A command which was only permitted to be invoked in #bot-spam was invoked in
    another channel. Currently not used.
    """

    def __init__(self, channel, message, *args, **kwargs):
        self.channel = channel
        self.message = message
        super().__init__(*args, **kwargs)


class SelfMuteCommandStaffInvoke(commands.CommandError):
    """
    A staff member attempted to self-mute themselves. Currently not used.
    """

    def __init__(self, message, *args, **kwargs):
        self.message = message
        super().__init__(*args, **kwargs)
