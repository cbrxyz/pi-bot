"""
Holds global variables shared between cogs and variables that are initialized when
the bot is first setup.
"""
import os

from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
DEV_TOKEN = os.getenv("DISCORD_DEV_TOKEN")
dev_mode = os.getenv("DEV_MODE") == "TRUE"

# Use the dev server, else the official Scioly.org server
SERVER_ID = int(os.getenv("DEV_SERVER_ID")) if dev_mode else 698306997287780363
STATES_SERVER_ID = int(os.getenv("STATES_SERVER_ID"))
BOT_PREFIX = "?" if dev_mode else "!"

##############
# CONSTANTS
##############
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
SLASH_COMMAND_GUILDS = [
    int(iden) for iden in os.getenv("SLASH_COMMAND_GUILDS").split(",")
]
EMOJI_GUILDS = [int(iden) for iden in os.getenv("EMOJI_GUILDS").split(",")]

# Roles
ROLE_WM = "Wiki/Gallery Moderator"
ROLE_GM = "Global Moderator"
ROLE_AD = "Administrator"
ROLE_VIP = "VIP"
ROLE_STAFF = "Staff"
ROLE_BT = "Bots"
ROLE_LH = "Launch Helper"
ROLE_AT = "All Invitationals"
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
CHANNEL_INVITATIONALS = "invitationals"
CHANNEL_BOTSPAM = "bot-spam"
CHANNEL_SUPPORT = "support-and-suggestions"
CHANNEL_GAMES = "games"
CHANNEL_DMLOG = "dm-log"
CHANNEL_WELCOME = "welcome"
CHANNEL_RULES = "rules"
CHANNEL_LOUNGE = "lounge"
CHANNEL_LEAVE = "member-leave"
CHANNEL_DELETEDM = "deleted-messages"
CHANNEL_EDITEDM = "edited-messages"
CHANNEL_REPORTS = "reports"
CHANNEL_CLOSED_REPORTS = "closed-reports"
CHANNEL_JOIN = "join-logs"
CHANNEL_UNSELFMUTE = "un-self-mute"
CHANNEL_COMPETITIONS = "competitions"

# Categories
CATEGORY_INVITATIONALS = "invitationals"
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
    "Do not spam or flood.",
    "Avoid intentional repeating pinging of other users.",
    "Avoid excessive use of caps, which constitutes yelling.",
    "Never name-drop, dox, or share personal information about another user without their permission.",
    "No witch-hunting (requests of kicks or bans for other users), personal attacks, or malicious rumors.",
    (
        "Treat delicate subjects delicately. When discussing "
        "religion, politics, instruments, or other similar topics, please "
        "remain objective and avoid voicing strong opinions."
    ),
    "Do not try to circumvent built-in restrictions (e.g. censors) or punishments.",
    "Avoid assuming the username of or otherwise impersonating another active user.",
    "Do not use multiple accounts unless specially permitted (e.g. <@&739640429896663040> rank/role).",
    (
        "In accordance with the Scioly.org Disclaimer, "
        "Scioly.org is not a place to get the rules, official rules clarifications, or FAQs.",
    ),
    "Do not violate Science Olympiad Inc. copyrights (including any Rules Manual).",
    (
        "All sharing of resources on Scioly.org must occur in the designated Test Exchanges. "
        "Do not solicit trades of private resources. See the Scioly.org Resource Policy."
    ),
    "Do not advertise other servers or paid services with which you have an affiliation.",
    (
        "Students should never use Scioly.org as an alternative to official platforms for scoring "
        "inquiries and appeals. Tournament directors are discouraged from using Scioly.org as their "
        "primary means of communication."
    ),
    (
        "Use good judgment when deciding what content to leave in and take out. As a general rule of thumb: "
        '"When in doubt, leave it out."'
    ),
    "Issues not addressed by these rules are left to the discretion of Scioly.org Staff.",
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
