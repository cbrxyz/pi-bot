"""
A script file to manually sync the file

Run:
```
python sync_commands.py
```
within your venv and it will sync all commands including the /sync command
"""

import asyncio
import logging

from rich.logging import RichHandler

import bot
from src.discord.globals import DEV_TOKEN, TOKEN, dev_mode


async def main():
    logger = logging.getLogger()
    logger.addHandler(RichHandler(rich_tracebacks=True))
    token = DEV_TOKEN if dev_mode else TOKEN
    async with bot.bot:
        await bot.bot.login(token)
        await bot.bot.sync_commands()

    exit(0)


if __name__ == "__main__":
    asyncio.run(main())
