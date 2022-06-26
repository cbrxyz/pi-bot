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
$ git clone https://github.com/cbrxyz/pi-bot
$ cd pi-bot
```

Then, active a Python virtual environment (Windows will use a slightly different syntax):

```sh
$ python3 -m venv venv
$ source venv/bin/active
```

Install the required pip dependencies:

```sh
$ pip install -r requirements.txt
```

### Discord

To set up your Pi-Bot testing environment for Discord, follow the following instructions:

1. Add a bot account in the [Discord Developers Portal](https://discord.com/developers/applications/). 
   Create a new application and add a bot in the Bot section. There, get your bot token.                       
1. You can use a custom Discord server template to make your own testing guild that
   has an identical channel and permissions structure similar to that of Scioly.org.
   You and your bot (and maybe other testing accounts) should be the only accounts
   in that guild. Testing multiple bots in the same server could result in the bots
   overwriting each other. The [server template can be found here](https://discord.new/Gsk2jP9KnYJv).

Now, you should have a guild with your own testing bot inside. The bot won't work,
but you should be able to see it in your guild. Making progress!

### Docker

To run the bot, we will use `docker-compose`. Docker is a handy tool to setup
a containerized development environment for the bot. Docker will launch both the
bot, along with a MongoDB container. This will allow the bot to store data in a quick
and efficient way, without needing to use an external service.

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

Another important aspect of the bot is its ability to interact with the forums
and wiki, two other critical site components. These interactions are primarily done
through a headless browser (for the fourms), or the MediaWiki API (for the wiki).

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
