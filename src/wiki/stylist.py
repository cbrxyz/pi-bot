import wikitextparser as wtp
from dotenv import load_dotenv, find_dotenv
import os
load_dotenv(find_dotenv())
import pywikibot
import asyncio
from aioify import aioify
from src.wiki.wiki import allPages, setPageText

aiopwb = aioify(obj=pywikibot, name='aiopwb')

async def prettifyTemplates():
    pages = await allPages()
    for page in pages:
        text = page.text
        title = page.title()
        parsed = wtp.parse(text)
        for template in parsed.templates:
            if len(template.arguments) > 3:
                pformat = template.pformat()
                text = text.replace(str(template), pformat)
        await setPageText(str(title), str(text), "Styled templates into pretty format. For any comments/concerns, please contact [[User:Pepperonipi]].", minor=True)
        await asyncio.sleep(20)