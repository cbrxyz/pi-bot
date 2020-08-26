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

There are many components to Pi-Bot that you will need to set up before you can begin to develop with him.

### Discord

To set up your Pi-Bot testing environment for Discord, follow the following instructions:

1. Add a bot account in the [Discord Developers Portal](https://discord.com/developers/applications/).  Create a new application and add a bot in the Bot section. There, get your bot token.                       
2. Create a new `.env` file locally, and add your first entry:
    ```
    DEV_MODE=TRUE
    DISCORD_TOKEN=abc <-- literally
    DISCORD_DEV_TOKEN=(your token)
    ```
3. In the code, find the `PI_BOT_IDS` constant, and add your bot's **user ID** to the array. Your bot's user ID can be found by enabling Developer Mode in Discord and right clicking on your bot, and copying it's ID.
4. You can now create a new server to test your bot in. Here, you can make the
   various channels and roles you need to simulate the server environment.
5. Add the ID of your development server to the `.env` file, as so:
    ```
    DEV_SERVER_ID=1234567890
    ```
6. Join the Pi-Bot Development server, where developers can discuss various
   ideas surrounding the bot. Available [here](https://discord.gg/tNBNgTH).

### Google Sheets

1. To get your bot set up with Google Sheets, you are going to need to create a service account to test your bot with.
2. Head to the [Google Cloud Console](https://www.console.cloud.google.com).
3. Create a new project for testing your bot.
4. Enable the Google Sheets and Google Drive APIs for  your project in the `APIs & Services` tab.
5. Head to the `API & Services > Credentials` tab, and create a new credential. Make a `Service account`.
6. Give it a name and ID, and create the service account.
7. Click on your newly created service account in the `Credentials` tab. Create a new key in the `JSON` format.
8. This will download a new file.
9. Take these values from the new file and add them to the `.env` file in the following format:
    ```
    ...
    GCP_PROJECT_ID= value of "project_id"
    GCP_PRIVATE_KEY_ID = value of "private_key_id"
    GCP_PRIVATE_KEY = value of "private_key"
    GCP_CLIENT_EMAIL = value of "client_email"
    GCP_CLIENT_ID = value of "client_id"
    GCP_AUTH_URI = value of "auth_uri"
    GCP_TOKEN_URI = value of "token_uri"
    GCP_AUTH_PROVIDER_X509 = value of "auth_provider_x509_cert_url"
    GCP_CLIENT_X509_CERT_URL = value of "client_x509_cert_url"
    ```
10. Create a new Google Sheet using the account you used to make the service account. If you would like the Pi-Bot Google Sheet template, please contact pepperonipi.
11. Share this Google Sheet with the value of `"client_email"` in the JSON file. If you do not do this, your bot will not be able to read/write to the sheet.

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

At this point you should be ready to develop! If you have any questions, don't hesistate to reach out to me on the Pi-Bot Discord server listed above.

Thank you. :heart: