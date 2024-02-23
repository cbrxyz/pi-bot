import asyncio
import logging
import re

import pywikibot
import wikitextparser as wtp
from aioify import aioify

from env import env

aiopwb = aioify(obj=pywikibot, name="aiopwb")

site = None
logger = logging.getLogger(__name__)


async def init_wiki(username: str, password: str):
    """Initializes the wiki function."""
    with open("password.py", "w+") as f:
        f.write(
            f'("{username}", "{password}")',
        )
    global site
    site = await aiopwb.Site()
    site.login()
    print("Wiki initialized.")


async def get_page_text(page_name):
    """Gets the text of a page on the wiki."""
    site = await aiopwb.Site()
    return aiopwb.Page(site, page_name).text


async def get_page_tables(page_name, temp_format):
    site = await aiopwb.Site()
    text = aiopwb.Page(site, page_name).text
    parsed = wtp.parse(str(text))
    if temp_format:
        return parsed.templates
    else:
        return parsed.tables


async def set_page_text(page_name, text, summary, minor=False):
    page = aiopwb.Page(site, page_name)
    page.text = text
    await page.save(summary=summary, minor=minor, asynchronous=True)


async def upload_file(file_path, title, comment):
    site = await aiopwb.Site()
    await site.upload()


async def all_pages(start_title):
    return site.allpages(start=start_title)


async def implement_command(action, page_title):
    site = await aiopwb.Site()
    page = aiopwb.Page(site, page_title)
    try:
        # If page redirects, get the page it redirects to
        page = await page.getRedirectTarget()
        page = aiopwb.Page(site, page.title())
    except Exception:
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
            "\n\nRead more on the Scioly.org Wiki here: <" + link + ">!",
        ]

    if action == "search":
        searches = site.search(page_title, where="title")
        res = []
        for search in searches:
            t = search.title()
            res.append(t)
        return res[:5]


if env.pi_bot_wiki_username and env.pi_bot_wiki_password:
    asyncio.run(init_wiki(env.pi_bot_wiki_username, env.pi_bot_wiki_password))
else:
    logger.info("User did not supply keys for wiki functionality; not turned on.")
