from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

import asyncio
import os
import re

import pywikibot
import wikitextparser as wtp
from aioify import aioify

aiopwb = aioify(obj=pywikibot, name="aiopwb")

site = None


async def init_wiki():
    """Initializes the wiki function."""
    with open("password.py", "w+") as f:
        f.write(
            f"(\"{os.getenv('PI_BOT_WIKI_USERNAME')}\", \"{os.getenv('PI_BOT_WIKI_PASSWORD')}\")"
        )
    global site
    site = await aiopwb.Site()
    site.login()
    print("Wiki initalized.")


async def get_page_text(pageName):
    """Gets the text of a page on the wiki."""
    site = await aiopwb.Site()
    return aiopwb.Page(site, pageName).text


async def get_page_tables(pageName, temp_format):
    site = await aiopwb.Site()
    text = aiopwb.Page(site, pageName).text
    parsed = wtp.parse(str(text))
    if temp_format:
        return parsed.templates
    else:
        return parsed.tables


async def set_page_text(pageName, text, summary, minor=False):
    page = aiopwb.Page(site, pageName)
    page.text = text
    await page.save(summary=summary, minor=minor, asynchronous=True)


async def upload_file(filePath, title, comment):
    site = await aiopwb.Site()
    await site.upload()


async def all_pages(startTitle):
    return site.allpages(start=startTitle)


async def implement_command(action, page_title):
    site = await aiopwb.Site()
    page = aiopwb.Page(site, page_title)
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
        return re.split(r"(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s", pt)[:1] + [
            "\n\nRead more on the Scioly.org Wiki here: <" + link + ">!"
        ]

    if action == "search":
        searches = site.search(page_title, where="title")
        res = []
        for search in searches:
            t = search.title()
            res.append(t)
        return res[:5]


event_loop = asyncio.get_event_loop()
asyncio.ensure_future(init_wiki(), loop=event_loop)
