from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

import re
import os
import pywikibot
import asyncio
import wikitextparser as wtp

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

async def getPageTables(pageName, tempFormat):
    site = await aiopwb.Site()
    text = aiopwb.Page(site, pageName).text
    parsed = wtp.parse(str(text))
    if tempFormat:
        return parsed.templates
    else:
        return parsed.tables

async def setPageText(pageName, text, summary, minor=False):
    page = aiopwb.Page(site, pageName)
    page.text = text
    await page.save(summary=summary, minor=minor, asynchronous=True)

async def uploadFile(filePath, title, comment):
    site = await aiopwb.Site()
    await site.upload()

async def allPages(startTitle):
    return site.allpages(start=startTitle)

async def implementCommand(action, pageTitle):
    site = await aiopwb.Site()
    page = aiopwb.Page(site, pageTitle)
    try:
        # If page redirects, get the page it redirects to
        page = await page.getRedirectTarget()
        page = aiopwb.Page(site, page.title())
    except Exception as e:
        pass

    if action == "link": 
        text = page.text
        if len(text) < 1:
            # If page does not exist, return False
            return False
        # If page does exist, return URL
        return await page.full_url()
    
    if action == "summary":
        text = page.text
        if len(text) < 1:
            # If page does not exist, return False
            return False
        # Continue if page does exist
        pt = wtp.parse(rf"{text}").plain_text()
        title = await page.title()
        link = site.base_url(site.article_path + title.replace(" ", "_"))
        return re.split(r"(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s", pt)[:1] + ["\n\nRead more on the Scioly.org Wiki here: <" + link + ">!"]

    if action == "search":
        searches = site.search(pageTitle, where='title')
        res = []
        for search in searches:
            t = search.title()
            res.append(t)
        return res[:5]

event_loop = asyncio.get_event_loop()
asyncio.ensure_future(initWiki(), loop = event_loop)