import datetime
import os

from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
DEV_TOKEN = os.getenv("DISCORD_DEV_TOKEN")
dev_mode = os.getenv("DEV_MODE") == "TRUE"

if dev_mode:
    BOT_PREFIX = "?"
    SERVER_ID = int(os.getenv("DEV_SERVER_ID"))
else:
    BOT_PREFIX = "!"
    SERVER_ID = 698306997287780363

##############
# CONSTANTS
##############
PI_BOT_IDS = [723767075427844106, 743254543952904197, 637519324072116247]
DISCORD_INVITE_ENDINGS = [
    "9Z5zKtV",
    "C9PGV6h",
    "s4kBmas",
    "ftPTxhC",
    "gh3aXbq",
    "skGQXd4",
    "RnkqUbK",
    "scioly",
]
SLASH_COMMAND_GUILDS = int(os.getenv("SLASH_COMMAND_GUILDS"))
EMOJI_GUILDS = [int(iden) for iden in [os.getenv("EMOJI_GUILDS")]]

# Roles
ROLE_WM = "Wiki/Gallery Moderator"
ROLE_GM = "Global Moderator"
ROLE_AD = "Administrator"
ROLE_VIP = "VIP"
ROLE_STAFF = "Staff"
ROLE_BT = "Bots"
ROLE_LH = "Launch Helper"
ROLE_AT = "All Tournaments"
ROLE_GAMES = "Games"
ROLE_MR = "Member"
ROLE_UC = "Unconfirmed"
ROLE_DIV_A = "Division A"
ROLE_DIV_B = "Division B"
ROLE_DIV_C = "Division C"
ROLE_EM = "Exalted Member"
ROLE_ALUMNI = "Alumni"
ROLE_MUTED = "Muted"
ROLE_PRONOUN_HE = "He / Him / His"
ROLE_PRONOUN_SHE = "She / Her / Hers"
ROLE_PRONOUN_THEY = "They / Them / Theirs"
ROLE_SELFMUTE = "Self Muted"
ROLE_QUARANTINE = "Quarantine"
ROLE_ALL_STATES = "All States"

# Channels
CHANNEL_TOURNAMENTS = "invitationals"
CHANNEL_BOTSPAM = "bot-spam"
CHANNEL_SUPPORT = "site-support"
CHANNEL_GAMES = "games"
CHANNEL_DMLOG = "dm-log"
CHANNEL_WELCOME = "welcome"
CHANNEL_LOUNGE = "lounge"
CHANNEL_LEAVE = "member-leave"
CHANNEL_DELETEDM = "deleted-messages"
CHANNEL_EDITEDM = "edited-messages"
CHANNEL_REPORTS = "reports"
CHANNEL_CLOSED_REPORTS = "closed-reports"
CHANNEL_JOIN = "join-logs"
CHANNEL_UNSELFMUTE = "un-self-mute"
CHANNEL_COMPETITIONS = "competitions"
CHANNEL_ROLES = "roles"

# Categories
CATEGORY_TOURNAMENTS = "invitationals"
CATEGORY_SO = "Science Olympiad"
CATEGORY_STATES = "states"
CATEGORY_GENERAL = "general"
CATEGORY_ARCHIVE = "archives"
CATEGORY_STAFF = "staff"

# Emoji reference
EMOJI_FAST_REVERSE = "\U000023EA"
EMOJI_LEFT_ARROW = "\U00002B05"
EMOJI_RIGHT_ARROW = "\U000027A1"
EMOJI_FAST_FORWARD = "\U000023E9"
EMOJI_UNSELFMUTE = "click_to_unmute"
EMOJI_FULL_UNSELFMUTE = "<:click_to_unmute:799389279385026610>"
EMOJI_LOADING = "<a:loading:909706909404237834>"

# Rules
RULES = [
    "Treat *all* users with respect.",
    "No profanity or inappropriate language, content, or links.",
    "Treat delicate subjects delicately. When discussing religion, politics, instruments, or other similar topics, please remain objective and avoid voicing strong opinions.",
    "Do not spam or flood (an excessive number of messages sent within a short timespan).",
    "Avoid intentional repeating pinging of other users (saying another user’s name).",
    "Avoid excessive use of caps, which constitutes yelling and is disruptive.",
    "Never name-drop (using a real name without permission) or dox another user.",
    "No witch-hunting (requests of kicks or bans for other users).",
    "While you are not required to use your Scioly.org username as your nickname for this Server, please avoid assuming the username of or otherwise impersonating another active user.",
    "Do not use multiple accounts within this Server, unless specifically permitted. A separate tournament account may be operated alongside a personal account.",
    "Do not violate Science Olympiad Inc. copyrights. In accordance with the Scioly.org Resource Policy, all sharing of tests on Scioly.org must occur in the designated Test Exchanges. Do not solicit test trades on this Server.",
    "Do not advertise other servers or paid services with which you have an affiliation.",
    "Use good judgment when deciding what content to leave in and take out. As a general rule of thumb: 'When in doubt, leave it out.'",
]

##############
# VARIABLES
##############
fish_now = 0
CENSOR = {}
EVENT_INFO = []
PING_INFO = []
INVITATIONAL_INFO = []
REPORTS = []
TAGS = []
CURRENT_WIKI_PAGE = None

SETTINGS = {
    "_id": None,
    "custom_bot_status_type": None,
    "custom_bot_status_text": None,
    "invitational_season": None,
}


async def update_setting(values, bot):
    for k, v in values.items():
        SETTINGS[k] = v
        await bot.mongo_database.update(
            "data", "settings", SETTINGS["_id"], {"$set": values}
        )
