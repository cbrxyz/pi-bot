import random
import math

BEAR_ID = 353730886577160203
BEAR_MESSAGES = [
    r"*{1} eats {2}* :fork_and_knife:",
    r"*{1} consumes {2}!* :fork_knife_plate:",
    r"*{1} thinks that {2} tasted pretty good...* :yum:",
    r"*{1} thinks that {2} tasted pretty awful...* :face_vomiting:",
    r"*{1} enjoyed eating {2}!* :yum:",
    r"*{1} hopes he gets to eat {2} again!* :smile:",
    r"*{1} thinks that {2} is delicious!* :yum:",
    r"*{1} likes eating {2} better than fish* :yum:",
    r"*{1} thinks that {2} was yummy!!* :blush:",
    r"*{1} is pretty full after eating {2}* :blush:",
    r"*{1} liked eating {2}* :heart:",
    r"*{1} isn't cuckoo for Cocoa Puffs, but rather {2}* :zany_face:",
    r"*{1} wonders when he gets to eat more {2}* :thinking:",
    r"*{1} has a hot take: {2} tastes pretty bomb* :fire:",
    r"*{1} can't believe he doesn't eat {2} more often!* :exploding_head:",
    r"*{1} would be lying to say he didn't like eating {2}* :liar:",
    r"*{1} would eat {2} at any time of the day!* :candy:",
    r"*{1} wonders where he can get more of {2}* :spoon:",
    r"*{1} thinks that {2} tastes out of this world* :alien:",
]

async def get_bear_message(user):
    i = random.random()
    message_index = math.floor(i*len(BEAR_MESSAGES))
    message = BEAR_MESSAGES[message_index]
    message = message.replace(r"{1}", fr"<@{BEAR_ID}>").replace(r"{2}", f"{user}")
    return message