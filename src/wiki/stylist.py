import os

import wikitextparser as wtp
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())
import asyncio

import pywikibot
from aioify import aioify

from src.discord.globals import CURRENT_WIKI_PAGE
from src.wiki.wiki import all_pages, set_page_text

aiopwb = aioify(obj=pywikibot, name="aiopwb")


async def prettify_templates():
    global CURRENT_WIKI_PAGE
    pages = await all_pages(CURRENT_WIKI_PAGE)
    page_id = 0
    for page in pages:
        text = page.text
        title = page.title()

        ## Action 1: Replacing {{PAGENAME}} magic word with actual page title
        text = text.replace(r"{{PAGENAME}}", title)
        CURRENT_WIKI_PAGE = title
        if page_id > 5:
            page_id = 0
            parsed = wtp.parse(text)
        await set_page_text(
            str(title),
            str(text),
            "Styled the page according to my stylist. For concerns, see my user page.",
            minor=True,
        )
        await asyncio.sleep(20)
        page_id += 1
