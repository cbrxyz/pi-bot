import wikitextparser as wtp
from dotenv import load_dotenv, find_dotenv
import os
load_dotenv(find_dotenv())
import pywikibot
import asyncio
from aioify import aioify

from src.wiki.wiki import allPages, setPageText
from src.sheets.sheets import getWikiPage, updateWikiPage

CURRENT_WIKI_PAGE = ""

aiopwb = aioify(obj=pywikibot, name='aiopwb')

async def prettifyTemplates():
    global CURRENT_WIKI_PAGE
    pages = await allPages(CURRENT_WIKI_PAGE)
    pageId = 0
    for page in pages:
        text = page.text
        title = page.title()
        CURRENT_WIKI_PAGE = title
        if pageId > 5:
            pageId = 0
            await updateWikiPage(title)
        parsed = wtp.parse(text)
        for template in parsed.templates:
            if len(template.arguments) > 3:
                try:
                    text = text.replace(str(template), str(template.pformat()))
                except Exception as e:
                    print("ERROR on text replace:")
                    print(e)
        await setPageText(str(title), str(text), "Styled templates into pretty format. For any comments/concerns, please contact [[User:Pepperonipi]].", minor=True)
        await asyncio.sleep(20)
        pageId += 1

async def init():
    global CURRENT_WIKI_PAGE
    CURRENT_WIKI_PAGE = await getWikiPage()
    print(f"Wiki module set to start at the {CURRENT_WIKI_PAGE} page.")

event_loop = asyncio.get_event_loop()
asyncio.ensure_future(init(), loop = event_loop)