## Contributing to Pi-Bot

Thanks for your interest in contributing to Pi-Bot. Below are the steps that allow you to get started with contributing.

## The Mission

Remember that the mission of Pi-Bot is to assist the Science Olympiad community by transforming the way data is transferred and maintained in the community. This includes, for example:

* Maintaining style guidelines on the wiki
* Servicing Discord commands
* Allowing users to get compiled data about tournaments, users, or events
* Automatically moving data between the wiki, forums, and tournament sites (with permission)
* Engaging with the community, such as by posting fun comments throughout the forums

## Development

There are many components to Pi-Bot that you will need to set up before you can begin to develop.

To begin, first clone the repo:
```sh
git clone https://github.com/cbrxyz/pi-bot
cd pi-bot
```

### Discord

To set up your Pi-Bot testing environment for Discord, follow the following instructions:

1. Add a bot account in the [Discord Developers Portal](https://discord.com/developers/applications/). 
   Create a new application and add a bot in the Bot section. There, get your bot token.                       
1. In your Discord client, create a brand new guild, and invite your bot using the
   instructions in your development portal. Give your bot `Administrator` permissions across
   the entire guild, for the time being. Then, run the `scripts/createserver.py`
   file, which will setup the guild in accordance with how the Scioly.org server
   is setup. After this step, you should most of the channels that you see on the
   official Scioly.org server!
1. You can now adjust the bot's permissions to match those of Pi-Bot on the official
   Scioly.org. This helps to ensure that your testing bot doesn't accidentally have
   more permissions than the true bot has. The bot has the following permissions:
   View Channels, Manage Channels, Manage Roles, Manage Emojis and Stickers,
   View Server Insights, Manage Webhooks, Change Nickname, Manage Nicknames, Kick Members,
   Ban Members, Send Messages, Embed Links, Attach Files, Add Reactions, Use External
   Emoji, Manage Messages, Read Message History, Send Text-to-Speech Messages, Use Application
   Commands, Request to Speak.

### MongoDB

To manage its information, Pi-Bot uses a MongoDB database. To create a database of
your own, you can use `mongoimport`. This takes in some amount of data and puts
it into a MongoDB database for you. You can setup a local instance of MongoDB, or
alternatively use [MongoDB Atlas](https://www.mongodb.com/atlas/database).

1. Run the `scripts/mongoimport.py` script, which will generate a JSON file that
   resembles the MongoDB database you can setup.
1. Use `mongoimport` to import the database:
    ```
    mongoimport --file mongo_export.json --jsonArray
    ```

### Forums / Wiki

1. Add this line to your `.env` file, just so the [`pywikibot`](https://www.mediawiki.org/wiki/Manual:Pywikibot) module is configured:
    ```
    PYWIKIBOT_DIR=$PWD/src/wiki
    ```
2. Create a new account on Scioly.org for testing your bot. Name it something so that it can be recognized as your Pi-Bot testing account.
3. **YOU MUST REACH OUT TO A STAFF MEMBER ABOUT YOUR NEW BOT TESTING ACCOUNT SO THAT IT CAN RECEIVE THE BOT FLAG.** Failure to follow this step can result in your bot account and/or your account being banned from the site.
4. Get it's username and password, and add them to the `.env` file as shown:
    ```
    PI_BOT_WIKI_USERNAME= (account username)
    PI_BOT_WIKI_PASSWORD= (account wiki password)
    PI_BOT_FORUMS_USERNAME= (account username)
    PI_BOT_FORUMS_PASSWORD= (account forums password)
    ```

### Local Environment Variables

1. Create a `.env` file to store your private environment variables. This helps
   to get your bot setup. You will need to update the file with the following variables.
    ```
    DEV_MODE=TRUE
    DISCORD_TOKEN=<not needed since you will be developing only>
    DISCORD_DEV_TOKEN=<bot token from step 1>
    DEV_SERVER_ID=<your development server ID>
    SLASH_COMMAND_GUILDS=<your development server ID>
    EMOJI_GUILDS=<your emoji guild ID>
    PI_BOT_WIKI_USERNAME=<only needed if you will be testing wiki functionality>
    PI_BOT_WIKI_PASSWORD=<only needed if you will be testing wiki functionality>
    MONGO_URL=<connection to your mongo database, see below>
    ```

At this point you should be ready to develop! If you have any questions, don't hesistate to reach out to me on the Pi-Bot Discord server listed above.

Thank you. :heart:
