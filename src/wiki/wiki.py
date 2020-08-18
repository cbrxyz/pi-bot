from dotenv import load_dotenv, find_dotenv
import os
load_dotenv(find_dotenv())
import pywikibot

site = None

def initWiki():
    """Initializes the wiki function."""
    with open("password.py", "w+") as f:
        f.write(f"(\"{os.getenv('PI_BOT_WIKI_USERNAME')}\", \"{os.getenv('PI_BOT_WIKI_PASSWORD')}\")")
    global site
    site = pywikibot.Site()
    print("Wiki initalized.")

def getPageText(pageName):
    """Gets the text of a page on the wiki."""
    return pywikibot.Page(site, pageName).text

def uploadFile(filePath, title, comment):
    site = pywikibot.Site()
    site.upload()

initWiki()