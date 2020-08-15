from splinter import Browser
import asyncio
import random
import os
from datetime import date
from dotenv import load_dotenv
load_dotenv()

from src.forums.markov import getResponses
from info import version

devMode = os.getenv("DEV_MODE") == "TRUE"
loggedIn = False

if devMode:
    # If in development mode, open the Browser so it can be seen
    browser = Browser('chrome', headless=True)
    threadId = "18240"
else:
    # If not, do not open the Browser in a way where it can be seen
    browser = Browser('chrome', headless=True)
    threadId = "23"

class Post:
    def __init__(self, username, content):
        self.username = username
        self.content = content

async def login():
    """Logs Pi-Bot in to the forums. Should be run once per session."""
    browser.visit("https://scioly.org/login")
    browser.find_by_id('username').fill(os.getenv("PI_BOT_FORUMS_USERNAME"))
    browser.find_by_id('password').fill(os.getenv("PI_BOT_FORUMS_PASSWORD"))
    browser.find_by_css('dd .button1').first.click()
    global loggedIn
    loggedIn = True

async def makeDisclaimerString():
    """Makes the post disclaimer string for Pi-Bot."""
    if devMode:
        dMString = "yes"
        nCString = "no"
    else:
        dMString = "no"
        nCString = "yes"
    return "\n[size=70]~~~ This message was posted completely with code (dm: " + dMString + ", ver: " + version + "). If there is an error, please contact pepperonipi in the signature. ~~~[/size]"

async def makePost(allPosts):
    """Main method responsible for constructing Pi-Bot's new post."""
    globalUn = ""
    globalContent = ""
    postObjects = []

    for i in allPosts:
        print(i['id'])
        if len(i.find_by_css(".username")) == 0:
            un = i.find_by_css(".username-coloured")[0].value
        else:
            un = i.find_by_css(".username")[0].value
        content = i.find_by_css(".content")[0].value
        postObjects.append(Post(un, content))
        globalUn = un
        globalContent = content

    randIndex = random.randrange(0, len(allPosts))
    postObject = postObjects[randIndex]
    post = allPosts[randIndex]
    finalUn = postObject.username
    finalContent = postObject.content
    post.find_by_text("Quote").find_by_xpath("..").click()
    messageText = browser.find_by_css("#message").value
    messageText += await getResponses(1)
    disclaimer = await makeDisclaimerString()
    messageText += disclaimer
    print(messageText)
    browser.find_by_css("#message").fill(messageText)
    await asyncio.sleep(6)
    browser.find_by_css(".default-submit-action").click()

async def openBrowser():
    """Opens the browser for Pi-Bot to interact with."""
    if not loggedIn:
        await login()
    browser.visit(f"https://scioly.org/forums/viewtopic.php?f=335&t={threadId}&start=100000")
    await asyncio.sleep(1)
    allPosts = browser.find_by_css('.post')
    print("Posts on Page: ", len(allPosts))
    await makePost(allPosts)