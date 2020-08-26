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
        ]
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
        ]
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
        ]
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
        ]
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
        ]
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
        ]
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
            "Wiki Moderator"
        ]
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
            "Wiki Moderator"
        ]
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
            "Wiki Moderator"
        ]
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
            "Wiki Moderator"
        ]
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
            "Wiki Moderator"
        ]
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
            "Wiki Moderator"
        ]
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
        ]
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
            "Wiki Moderator"
        ]
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
        ]
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
        ]
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
        ]
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
        ]
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
            "Wiki Moderator"
        ]
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
            "Wiki Moderator"
        ]
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
        ]
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
        ]
    },
    {
        "name": "ping",
        "description": "allows users to add/remove/list their ping expressions/words",
        "aliases": [],
        "parameters": [
            {
                "name": "command",
                "description": "the ping command to run (add/delete/list)"
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
        ]
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
        ]
    },
    {
        "name": "wiki",
        "description": "returns a wiki page",
        "aliases": [],
        "parameters": [
            {
                "name": "wikiPage1",
                "description": "the first wiki page to get"
            },
            {
                "name": "[wikiPage2]",
                "description": "the second wiki page to get"
            },
            {
                "name": "[wikiPageN]",
                "description": "the nth wiki page to get"
            },
            {
                "name": "flag: -multiple",
                "description": "specifies you are retrieving multiple page links"
            },
            {
                "name": "flag: -ignoreCase",
                "description": "specifies you want to use your own case for page titles"
            }
        ],
        "usage":[
            {
                "cmd": "!wiki Troy Invitational",
                "result": "gives you the `Troy Invitational` wiki page"
            },
            {
                "cmd": "!wiki Florida California -mulitple",
                "result": "gives you both the Florida and California pages"
            },
            {
                "cmd": "!wiki WWPN WWPS -ignoreCase -mulitple",
                "result": "gives you both the `WWPN` and `WWPS` pages"
            }
        ],
        "access":[
            "Member"
        ]
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
        ]
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
        ]
    }
]