from splinter import Browser
import asyncio
import random
import os
from datetime import date
from dotenv import load_dotenv
load_dotenv()

from src.forums.markov import get_responses
from info import version

dev_mode = os.getenv("DEV_MODE") == "TRUE"
logged_in = False

if dev_mode:
    # If in development mode, open the Browser so it can be seen
    browser = Browser('chrome', headless=True)
    thread_id = "18240"
else:
    # If not, do not open the Browser in a way where it can be seen
    browser = Browser('chrome', headless=True)
    thread_id = "23"

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
    global logged_in
    logged_in = True

async def make_disclaimer_string():
    """Makes the post disclaimer string for Pi-Bot."""
    if dev_mode:
        dm_string = "yes"
        nc_string = "no"
    else:
        dm_string = "no"
        nc_string = "yes"
    return "\n[size=70]~~~ This message was posted completely with code (dm: " + dm_string + ", ver: " + version + "). If there is an error, please contact pepperonipi in the signature. ~~~[/size]"

async def make_post(all_posts):
    """Main method responsible for constructing Pi-Bot's new post."""
    global_username = ""
    global_content = ""
    post_objects = []

    for i in all_posts:
        print(i['id'])
        if len(i.find_by_css(".username")) == 0:
            un = i.find_by_css(".username-coloured")[0].value
        else:
            un = i.find_by_css(".username")[0].value
        content = i.find_by_css(".content")[0].value
        post_objects.append(Post(un, content))
        global_username = un
        global_content = content

    random_index = random.randrange(0, len(all_posts))
    post_object = post_objects[random_index]
    post = all_posts[random_index]
    final_username = post_object.username
    final_content = post_object.content
    post.find_by_text("Quote").find_by_xpath("..").click()
    message_text = browser.find_by_css("#message").value
    message_text += await get_responses(1)
    disclaimer = await make_disclaimer_string()
    message_text += disclaimer
    print(message_text)
    browser.find_by_css("#message").fill(message_text)
    await asyncio.sleep(6)
    browser.find_by_css(".default-submit-action").click()

async def open_browser():
    """Opens the browser for Pi-Bot to interact with."""
    if not logged_in:
        await login()
    browser.visit(f"https://scioly.org/forums/viewtopic.php?f=335&t={thread_id}&start=100000")
    await asyncio.sleep(1)
    all_posts = browser.find_by_css('.post')
    print("Posts on Page: ", len(all_posts))
    await make_post(all_posts)