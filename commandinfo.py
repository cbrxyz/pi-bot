COMMAND_INFO = [
    {
        "name": "getchannelid",
        "description": "gets the ID of the current channel",
        "aliases": ["gci"],
        "parameters": [],
        "usage":[
            {
                "cmd": "!gci",
                "result": "prints the channel ID"
            }
        ],
        "access":[
            "Member"
        ],
        "inQuickList": False
    },
    {
        "name": "getuserid",
        "description": "gets the ID of yourself, or another user",
        "aliases": ["ui"],
        "parameters": [
            {
                "name": "[user]",
                "description": "the user you want to get the id of"
            }
        ],
        "usage":[
            {
                "cmd": "!ui",
                "result": "prints your user ID"
            },
            {
                "cmd": "!ui @user",
                "result": "prints the user ID of @user"
            }
        ],
        "access":[
            "Member"
        ],
        "inQuickList": False
    },
    {
        "name": "about",
        "description": "prints information about Pi-Bot",
        "aliases": [],
        "parameters": [],
        "usage":[
            {
                "cmd": "!about",
                "result": "prints information about Pi-Bot"
            }
        ],
        "access":[
            "Member"
        ],
        "inQuickList": False
    },
    {
        "name": "fish",
        "description": "feeds bear one fish",
        "aliases": [],
        "parameters": [],
        "usage":[
            {
                "cmd": "!fish",
                "result": "feeds bear another fish"
            }
        ],
        "access":[
            "Member"
        ],
        "inQuickList": True
    },
    {
        "name": "nofish",
        "description": "takes away all of bear's fish",
        "aliases": [],
        "parameters": [],
        "usage":[
            {
                "cmd": "!nofish",
                "result": "removes all of bear's fish"
            }
        ],
        "access":[
            "Member"
        ],
        "inQuickList": False
    },
    {
        "name": "help",
        "description": "provides help for a command",
        "aliases": [],
        "parameters": [
            {
                "name": "[command]",
                "description": "the command you want help with"
            }
        ],
        "usage":[
            {
                "cmd": "!help",
                "result": "provides help with the `help` command"
            },
            {
                "cmd": "!help fish",
                "result": "provides help with the `fish` command"
            }
        ],
        "access":[
            "Member"
        ],
        "inQuickList": True
    },
    {
        "name": "exalt",
        "description": "exalts a user",
        "aliases": [],
        "parameters": [
            {
                "name": "user",
                "description": "the user you would like to exalt"
            }
        ],
        "usage":[
            {
                "cmd": "!exalt @user",
                "result": "exalts @user"
            }
        ],
        "access":[
            "Administrator",
            "Global Moderator",
            "Wiki/Gallery Moderator"
        ],
        "inQuickList": False
    },
    {
        "name": "unexalt",
        "description": "unexalts a user",
        "aliases": [],
        "parameters": [
            {
                "name": "user",
                "description": "the user you would like to unexalt"
            }
        ],
        "usage":[
            {
                "cmd": "!unexalt @user",
                "result": "unexalts @user"
            }
        ],
        "access":[
            "Administrator",
            "Global Moderator",
            "Wiki/Gallery Moderator"
        ],
        "inQuickList": False
    },
    {
        "name": "mute",
        "description": "mutes a user",
        "aliases": [],
        "parameters": [
            {
                "name": "user",
                "description": "the user that needs to be muted"
            },
            {
                "name": "time",
                "description": "the length of the mute"
            }
        ],
        "usage":[
            {
                "cmd": "!mute @user \"1 day\"",
                "result": "mutes @user for 1 day"
            },
            {
                "cmd": "!mute @user \"indef\"",
                "result": "mutes @user for an indefinite amount of time"
            }
        ],
        "access":[
            "Administrator",
            "Global Moderator",
            "Wiki/Gallery Moderator"
        ],
        "inQuickList": False
    },
    {
        "name": "unmute",
        "description": "unmutes a user",
        "aliases": [],
        "parameters": [
            {
                "name": "user",
                "description": "the user that needs to be unmuted"
            }
        ],
        "usage":[
            {
                "cmd": "!unmute @user",
                "result": "unmutes @user"
            }
        ],
        "access":[
            "Administrator",
            "Global Moderator",
            "Wiki/Gallery Moderator"
        ],
        "inQuickList": False
    },
    {
        "name": "ban",
        "description": "bans a user",
        "aliases": [],
        "parameters": [
            {
                "name": "user",
                "description": "the user that needs to be banned"
            },
            {
                "name": "reason",
                "description": "the reason for the ban"
            },
            {
                "name": "time",
                "description": "the length for the ban"
            }
        ],
        "usage":[
            {
                "cmd": "!ban @user \"spamming\" \"7 days\"",
                "result": "bans @user for \"spamming\" for 7 days"
            },
            {
                "cmd": "!ban @user \"spamming\" \"indef\"",
                "result": "bans @user for \"spamming\" for an infinite amount of time"
            }
        ],
        "access":[
            "Administrator",
            "Global Moderator",
            "Wiki/Gallery Moderator"
        ],
        "inQuickList": False
    },
    {
        "name": "unban",
        "description": "unbans a user",
        "aliases": [],
        "parameters": [
            {
                "name": "user id",
                "description": "the id of the user that needs to be unbanned"
            }
        ],
        "usage":[
            {
                "cmd": "!unban 12345678910",
                "result": "unbans @user"
            }
        ],
        "access":[
            "Administrator",
            "Global Moderator",
            "Wiki/Gallery Moderator"
        ],
        "inQuickList": False
    },
    {
        "name": "states",
        "description": "toggles specific state roles for a user",
        "aliases": ["state"],
        "parameters": [
            {
                "name": "state1",
                "description": "the first state role to toggle for a user"
            },
            {
                "name": "<state2>",
                "description": "the second state role to toggle for a user"
            },
            {
                "name": "<staten>",
                "description": "the nth state role to toggle for a user"
            }
        ],
        "usage":[
            {
                "cmd": "!state FL",
                "result": "toggles the Florida role on a user"
            },
            {
                "cmd": "!state FL NJ CA-S",
                "result": "toggles the Florida, New Jersey, and California South roles on a user"
            }
        ],
        "access":[
            "Member"
        ],
        "inQuickList": True
    },
    {
        "name": "nuke",
        "description": "nukes up to 100 of the last messages in a channel",
        "aliases": [],
        "parameters": [
            {
                "name": "# of messages",
                "description": "the number of messages to nuke"
            }
        ],
        "usage":[
            {
                "cmd": "!nuke 10",
                "result": "nukes the 10 most recent messages"
            }
        ],
        "access":[
            "Administrator",
            "Global Moderator",
            "Wiki/Gallery Moderator"
        ],
        "inQuickList": False
    },
    {
        "name": "division",
        "description": "gives the user a division role",
        "aliases": ["div"],
        "parameters": [
            {
                "name": "division",
                "description": "the division to apply"
            }
        ],
        "usage":[
            {
                "cmd": "!division a",
                "result": "gives the user the Division A role"
            },
            {
                "cmd": "!division d",
                "result": "gives the user the Division D role"
            }
        ],
        "access":[
            "Member"
        ],
        "inQuickList": True
    },
    {
        "name": "dogbomb",
        "description": "dog bombs a user :dog:",
        "aliases": [],
        "parameters": [
            {
                "name": "user",
                "description": "the user to dog bomb!"
            }
        ],
        "usage":[
            {
                "cmd": "!dogbomb @user",
                "result": "dog bombs @user!"
            }
        ],
        "access":[
            "Member"
        ],
        "inQuickList": False
    },
    {
        "name": "shibabomb",
        "description": "shiba bombs a user :dog2:",
        "aliases": [],
        "parameters": [
            {
                "name": "user",
                "description": "the user to shiba bomb!"
            }
        ],
        "usage":[
            {
                "cmd": "!shibabomb @user",
                "result": "shiba bombs @user!"
            }
        ],
        "access":[
            "Member"
        ],
        "inQuickList": False
    },
    {
        "name": "events",
        "description": "assigns or removes event roles to the user",
        "aliases": ["event", "e"],
        "parameters": [
            {
                "name": "event1",
                "description": "The first event to assign"
            },
            {
                "name": "[event2]",
                "description": "The second (optional) event to assign"
            },
            {
                "name": "[eventn]",
                "description": "The nth (optional) event to assign"
            }
        ],
        "usage":[
            {
                "cmd": "!events pm",
                "result": "assigns the Protein Modeling role to the user if they do not have it, else removes it"
            },
            {
                "cmd": "!events pm gm",
                "result": "assigns the Protein Modeling role to the user if they do not have it, else removes it, and does the same for the Geologic Mapping role"
            }
        ],
        "access":[
            "Member"
        ],
        "inQuickList": True
    },
    {
        "name": "kick",
        "description": "kicks a user from the server",
        "aliases": ["k"],
        "parameters": [
            {
                "name": "user",
                "description": "the user to kick"
            }
        ],
        "usage":[
            {
                "cmd": "!kick @user \"reason\"",
                "result": "kicks @user from the server due to reason \"reason\""
            }
        ],
        "access":[
            "Administrator",
            "Global Moderator",
            "Wiki/Gallery Moderator"
        ],
        "inQuickList": False
    },
    {
        "name": "prepembed",
        "description": "allows a customizable embed to be sent to a channel for better message formatting",
        "aliases": [],
        "parameters": [
            {
                "name": "channel",
                "description": "the channel to send the embed"
            },
            {
                "name": "json",
                "description": "the json used to generate the embed (remember that all keys and values in the object should be in double quotes)"
            },
            {
                "name": "title (in json)",
                "description": "the title of the embed"
            },
            {
                "name": "titleUrl (in json)",
                "description": "the URL to link the title to"
            },
            {
                "name": "thumbnailUrl (in json)",
                "description": "the URL of the thumbnail image"
            },
            {
                "name": "description (in json)",
                "description": "the text body of the embed"
            },
            {
                "name": "author (in json)",
                "description": "can be set to \"me\" to set authorName to your username and authorIcon to your profile picture automatically"
            },
            {
                "name": "authorName / authorIcon / authorUrl (in json)",
                "description": "the name / icon URL / URL of the author of the embed"
            },
            {
                "name": "fields (in json)",
                "description": "array of objects consisting of a name, value, and inline value used to generate the fields of the embed"
            },
            {
                "name": "hexColor (in json)",
                "description": "the hex color to set the embed to, such as #ffffff or #000bbb"
            },
            {
                "name": "webColor (in json)",
                "description": "the web color to set the embed to, such as magenta or steelBlue"
            },
            {
                "name": "footerText / footerUrl (in json)",
                "description": "the footer text or url of the embed"
            },
        ],
        "usage":[
            {
                "cmd": "!prepembed #announcements {\"title\": \"Happy Saturday!\"}",
                "result": "sends an embed with the title \"Happy Saturday!\" to the #announcements channel"
            }
        ],
        "access":[
            "Administrator",
            "Global Moderator",
            "Wiki/Gallery Moderator"
        ],
        "inQuickList": False
    },
    {
        "name": "report",
        "description": "sends a report to staff",
        "aliases": [],
        "parameters": [
            {
                "name": " message",
                "description": "the message to send to staff"
            }
        ],
        "usage":[
            {
                "cmd": "!report \"message\"",
                "result": "sends a report containing the message to staff"
            }
        ],
        "access":[
            "Member"
        ],
        "inQuickList": True
    },
    {
        "name": "games",
        "description": "adds or removes the calling user to/from the games channel",
        "aliases": [],
        "parameters": [],
        "usage":[
            {
                "cmd": "!games",
                "result": "adds or removes the user to/from the games channel"
            }
        ],
        "access":[
            "Member"
        ],
        "inQuickList": False
    },
    {
        "name": "ping",
        "description": "allows users to add/remove/list their ping expressions/words",
        "aliases": [],
        "parameters": [
            {
                "name": "command",
                "description": "the ping command to run - can be `add`, `addregex`, `list`, or `remove`"
            },
            {
                "name": "<expression>",
                "description": "if adding/deleting a ping expression, it should be included"
            }
        ],
        "usage":[
            {
                "cmd": "!ping add \"florida\"",
                "result": "adds \"florida\" to the user's ping list"
            },
            {
                "cmd": "!ping addregex \"^\d{5}(?:[-\s]\d{4})?$\"",
                "result": "adds \"^\d{5}(?:[-\s]\d{4})?$\" (a formula to match zip codes) to the user's ping list"
            },
            {
                "cmd": "!ping remove \"florida\"",
                "result": "removes \"florida\" from the user's ping list"
            },
            {
                "cmd": "!ping list",
                "result": "lists all of the user's pings"
            }
        ],
        "access":[
            "Member"
        ],
        "inQuickList": True
    },
    {
        "name": "pronouns",
        "description": "allows users to add/remove pronoun roles",
        "aliases": [],
        "parameters": [
            {
                "name": "pronoun",
                "description": "the pronoun to add (this can be set to `remove` to remove all pronoun roles)"
            }
        ],
        "usage":[
            {
                "cmd": "!pronouns she",
                "result": "gives you the `She / Her / Hers` role"
            },
            {
                "cmd": "!pronouns remove",
                "result": "removes all of your pronoun roles"
            },
        ],
        "access":[
            "Member"
        ],
        "inQuickList": True
    },
    {
        "name": "wiki",
        "description": "searches the wiki or returns a wiki page link or summary",
        "aliases": [],
        "parameters": [
            {
                "name": "command",
                "description": "the command to run - can be `link`, `summary`, or `search`"
            },
            {
                "name": "term",
                "description": "the page to reference, or the term to search with"
            },
            {
                "name": "[wikiPage2]",
                "description": "if acceptable in the context, the second wiki page to get"
            },
            {
                "name": "[wikiPageN]",
                "description": "if acceptable in the context, the nth wiki page to get"
            },
            {
                "name": "flag: -multiple",
                "description": "specifies you are retrieving multiple page links/summaries"
            },
        ],
        "usage":[
            {
                "cmd": "!wiki link Troy Invitational",
                "result": "gives you the link to the `Troy Invitational` wiki page"
            },
            {
                "cmd": "!wiki summary Florida",
                "result": "gives you a summary of the `Florida` page"
            },
            {
                "cmd": "!wiki link Food Science",
                "result": "gives you the link to the `Food Science` wiki page"
            },
            {
                "cmd": "!wiki link \"Food Science\" WWPN -multiple",
                "result": "gives you the links to the `Food Science` and `WWPN` wiki pages"
            },
            {
                "cmd": "!wiki summary \"Southeast Florida Regional\" WWPN -multiple",
                "result": "gives you the summaries of the `Southeast Florida Regional` and `WWPN` wiki pages"
            }
        ],
        "access":[
            "Member"
        ],
        "inQuickList": False
    },
    {
        "name": "profile",
        "description": "retrieves a user's profile information",
        "aliases": [],
        "parameters": [
            {
                "name": "[user]",
                "description": "the optional user's profile information you'd like to retrieve"
            }
        ],
        "usage":[
            {
                "cmd": "!profile",
                "result": "returns the caller's profile information"
            },
            {
                "cmd": "!profile @user",
                "result": "returns @user's profile information"
            },
        ],
        "access":[
            "Member"
        ],
        "inQuickList": False
    },
    {
        "name": "list",
        "description": "gives the user a list of commands/states/events",
        "aliases": [],
        "parameters": [
            {
                "name": "[information]",
                "description": "the information the user would like to retrieve"
            }
        ],
        "usage":[
            {
                "cmd": "!list",
                "result": "returns commands accessible to the caller"
            },
            {
                "cmd": "!list states",
                "result": "returns the list of state roles/channels to the caller"
            },
            {
                "cmd": "!list events",
                "result": "returns the list of event roles to the caller"
            }
        ],
        "access":[
            "Member"
        ],
        "inQuickList": True
    },
    {
        "name": "count",
        "description": "returns a member count for the server",
        "aliases": [],
        "parameters": [],
        "usage": [{
            "cmd": "!count",
            "result": "returns the current member count"
        }],
        "access": [
            "Member"
        ],
        "inQuickList": False
    },
    {
        "name": "wikipedia",
        "description": "returns informtion about a wikipedia page",
        "aliases": ["wp"],
        "parameters": [
            {
                "name": "command",
                "description": "the command to run - can be `search`, `summary`, or `link`"
            },
            {
                "name": "page",
                "description": "the page to reference"
            }
        ],
        "usage": [
            {
                "cmd": "!wp search \"calculus\"",
                "result": "searches Wikipedia for pages relating to `calculus`"
            },
            {
                "cmd": "!wp summary \"Astronomy\"",
                "result": "returns the summmary for the `Astronomy` Wikipedia page"
            },
            {
                "cmd": "!wp summary \"FTOC\"",
                "result": "returns the summmary for the `Fundamental Theorem of Calculus` Wikipedia page"
            },
            {
                "cmd": "!wp link \"Red fox\"",
                "result": "returns the link for the `Red fox` Wikipedia page"
            }
        ],
        "access": [
            "Member"
        ],
        "inQuickList": False
    },
    {
        "name": "hello",
        "description": "makes the bot say hi - can be used to check if the bot is functioning",
        "aliases": [],
        "parameters": [],
        "usage": [{
            "cmd": "!hi",
            "result": "the bot says hi!"
        }],
        "access": [
            "Member"
        ],
        "inQuickList": False
    },
    {
        "name": "refresh",
        "description": "refreshes data from pi-bot's administrative panel",
        "aliases": [],
        "parameters": [],
        "usage": [{
            "cmd": "!refresh",
            "result": "refreshes the data"
        }],
        "access":[
            "Administrator",
            "Global Moderator",
            "Wiki/Gallery Moderator"
        ],
        "inQuickList": False
    },
    {
        "name": "me",
        "description": "refrences a user's actions from the third person",
        "aliases": [],
        "parameters": [
            {
                "name": "message",
                "description": "the message to implement"
            }
        ],
        "usage": [
            {
                "cmd": "!me can't believe that happened!",
                "result": "@user can't believe that happened!"
            }
        ],
        "access":[
            "Member"
        ],
        "inQuickList": True
    },
    {
        "name": "dnd",
        "description": "toggles Do Not Disturb mode for pings",
        "aliases": ["donotdisturb"],
        "parameters": [],
        "usage": [
            {
                "cmd": "!dnd",
                "result": "toggles Do Not Disturb mode for pings"
            }
        ],
        "access":[
            "Member"
        ],
        "inQuickList": True
    },
    {
        "name": "slowmode",
        "description": "toggles slowmode for a channel",
        "aliases": ["slow", "sm"],
        "parameters": [
            {
                "name": "seconds",
                "description": "the amount of seconds to enable slowmode for"
            }
        ],
        "usage": [
            {
                "cmd": "!slowmode",
                "result": "toggles a 10 second slowmode"
            },
            {
                "cmd": "!slowmode 35",
                "result": "enables a 35 second slowmode"
            },
            {
                "cmd": "!slowmode 0",
                "result": "removes any slowmode effects"
            }
        ],
        "access":[
            "Administrator",
            "Global Moderator",
            "Wiki/Gallery Moderator"
        ],
        "inQuickList": False
    },
    {
        "name": "school",
        "description": "gets school data in wiki format",
        "aliases": [],
        "parameters": [
            {
                "name": "school name (in quotes)",
                "description": "the school name to search for **(note: if you cannot find the school you are looking for at first, broaden your search by removing terms such as \"school\" or \"elementary\")**"
            },
            {
                "name": "state abbreviation",
                "description": "the abbreviation of the state the school is in"
            }
        ],
        "usage": [
            {
                "cmd": "!school \"Boca Raton Community High\" \"FL\"",
                "result": "returns school listings for `Boca Raton Community High` in `FL`"
            },
            {
                "cmd": "!school \"Interlake High\" \"WA\"",
                "result": "returns school listings for `Interlake High` in `WA`"
            }
        ],
        "access":[
            "Member"
        ],
        "inQuickList": False
    },
    {
        "name": "invite",
        "description": "returns the server's invite link",
        "aliases": ["link", "server", "invitelink"],
        "parameters": [],
        "usage": [{
            "cmd": "!link",
            "result": "https://discord.gg/9Z5zKtV"
        }],
        "access": [
            "Member"
        ],
        "inQuickList": True
    },
    {
        "name": "lock",
        "description": "locks the current channel to non-staff",
        "aliases": [],
        "parameters": [],
        "usage": [{
            "cmd": "!lock",
            "result": "locks the current channel to non-staff"
        }],
        "access": [
            "Administrator",
            "Global Moderator",
            "Wiki/Gallery Moderator"
        ],
        "inQuickList": False
    },
    {
        "name": "unlock",
        "description": "unlocks the current channel to non-staff",
        "aliases": [],
        "parameters": [],
        "usage": [{
            "cmd": "!unlock",
            "result": "unlocks the current channel to non-staff"
        }],
        "access": [
            "Administrator",
            "Global Moderator",
            "Wiki/Gallery Moderator"
        ],
        "inQuickList": False
    },
    {
        "name": "clrreact",
        "description": "clears the reactions on a given message",
        "aliases": [],
        "parameters": [
            {
                "name": "message ID",
                "description": "the ID of the message to remove reactions from"
            },
            {
                "name": "user list",
                "description": "the list of users to remove reactions from"
            }
        ],
        "usage": [
            {
                "cmd": "!clrreact 1234567890",
                "result": "clears all reactions on message id 1234567890"
            },
            {
                "cmd": "!clrreact 1234567890 @Nydauron",
                "result": "clears all reactions from Nydauron on message id 1234567890"
            }
        ],
        "access": [
            "Administrator",
            "Global Moderator",
            "Wiki/Gallery Moderator"
        ],
        "inQuickList": False
    },
    {
        "name": "obb",
        "description": "returns the link to the Scioly.org Open Bulletin Board",
        "aliases": [],
        "parameters": [],
        "usage": [{
            "cmd": "!obb",
            "result": "https://scioly.org/obb"
        }],
        "access": [
            "Member"
        ],
        "inQuickList": False
    },
    {
        "name": "exchange",
        "description": "returns the link to the Scioly.org Test Exchange",
        "aliases": ["tests", "testexchange"],
        "parameters": [],
        "usage": [{
            "cmd": "!exchange",
            "result": "https://scioly.org/tests"
        }],
        "access": [
            "Member"
        ],
        "inQuickList": False
    },
    {
        "name": "gallery",
        "description": "returns the link to the Scioly.org Image Gallery",
        "aliases": [],
        "parameters": [],
        "usage": [{
            "cmd": "!gallery",
            "result": "https://scioly.org/gallery"
        }],
        "access": [
            "Member"
        ],
        "inQuickList": False
    },
    {
        "name": "getemojiid",
        "description": "gets the ID of the given emoji",
        "aliases": ["gei", "eid"],
        "parameters": [
            {
                "name": "emoji",
                "description": "the emoji to get the ID of"
            }
        ],
        "usage":[
            {
                "cmd": "!eid :test_emoji:",
                "result": "prints the ID of :test_emoji:"
            }
        ],
        "access":[
            "Member"
        ],
        "inQuickList": False
    }
]