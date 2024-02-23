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

### Installing requirements

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

Alternatively, you can use `docker-compose` to launch the app if you don't want
to use a virtual environment. Both a containerized MongoDB database and app will
be launched with the user of this command.

### Setting up Discord

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

### MongoDB

To manage its information, Pi-Bot uses a MongoDB database. For development, there
are a few ways that you can set this up:

1. Setup a MongoDB database running locally on your computer.
1. Setup a MongoDB database through [MongoDB Atlas](https://www.mongodb.com/atlas/database).
1. Use the `docker-compose` setup provided below.

Whichever method you choose, you will need to get a URL that allows the bot to
connect to your testing database. This URL can use the `srv` feature or not. You
can set this URL in the `.env` file through the `MONGO_URL` attribute.

To test if the bot will be able to see your instance, you can run the following:
```python
>>> from pymongo import MongoClient
>>> client = MongoClient("your very special URL", tz_aware = True)
>>> client.data.command('ping')
{'ok': 1.0}
```

### Wiki

Another aspect of the bot is its interaction with the Scioly.org wiki. This interaction
powers some of the current Discord commands used by the bot.

Currently, you do not need to supply credentials to allow the bot to interact with
the wiki - it should be able to complete all needed operations without signing
into an account.

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

At this point you should be ready to develop! If you have any questions, don't
hesitate to reach out to me on the Pi-Bot Discord server listed above.

## Docker

To develop the bot using Docker, you can use `docker-compose`. Compose will
build two containers for the bot: one for MongoDB and one for the bot itself, which
depends on the MongoDB container.

```bash
$ docker-compose up
```

To make Docker work, you will need to update your MongoDB URL to include the default
database credentials and the proper host address. To connect to the Mongo database
spun up by Docker, you can set `MONOGO_URL` to `mongodb://mongodb:27017`.

If you want to connect to the database from your host machine, in cases you wish to use
tools like `mongosh` to connect to the database for inspection and debugging, then you
can connect using the following URI: `mongodb://localhost:28017`.

## Contributing changes

When you are ready to contribute changes, feel free to fork the project and submit
a PR. You are highly encouraged to set up `pre-commit` before committing and pushing
your changes, as this lessens the chance of your PR being rejected because of failing
CI tests.

You can install `pre-commit` through:

```bash
$ pip install pre-commit
$ pre-commit install
```

This will install hooks into your Git configuration that allow various tests to
run right before you commit. All of these hooks are specific to our repository,
and they will not affect any other projects you may be working on.

Thank you. :heart:
