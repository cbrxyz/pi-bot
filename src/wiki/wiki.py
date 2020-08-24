from dotenv import load_dotenv, find_dotenv
import os
load_dotenv(find_dotenv())
import pywikibot
import asyncio
from aioify import aioify

aiopwb = aioify(obj=pywikibot, name='aiopwb')

site = None

async def initWiki():
    """Initializes the wiki function."""
    with open("password.py", "w+") as f:
        f.write(f"(\"{os.getenv('PI_BOT_WIKI_USERNAME')}\", \"{os.getenv('PI_BOT_WIKI_PASSWORD')}\")")
    global site
    site = await aiopwb.Site()
    site.login()
    print("Wiki initalized.")

async def getPageText(pageName):
    """Gets the text of a page on the wiki."""
    site = await aiopwb.Site()
    return aiopwb.Page(site, pageName).text

async def setPageText(pageName, text, summary, minor=False):
    page = aiopwb.Page(site, pageName)
    page.text = text
    await page.save(summary=summary, minor=minor, asynchronous=True)

async def uploadFile(filePath, title, comment):
    site = await aiopwb.Site()
    await site.upload()

async def allPages(startTitle):
    return site.allpages(start=startTitle)

event_loop = asyncio.get_event_loop()
asyncio.ensure_future(initWiki(), loop = event_loop)