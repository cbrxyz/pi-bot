import discord
from discord.ext import commands
from discord.commands import Option
import re
import src.discord.globals
from src.discord.globals import PING_INFO, CHANNEL_BOTSPAM, SLASH_COMMAND_GUILDS

from src.mongo.mongo import insert, update

class PingManager(commands.Cog):

    recent_messages = {}

    def __init__(self, bot):
        self.bot = bot
        self.recent_messages = {}
        print("Initialized Ping cog.")

    @commands.Cog.listener()
    async def on_message(self, message):
        # Do not ping for messages in a private channel
        if message.channel.type == discord.ChannelType.private: return

        # Do not ping for messages from a bot
        if message.author.bot:
            return

        # Do not ping if the message is coming from the botspam channel
        botspam_channel = discord.utils.get(message.guild.text_channels, name = CHANNEL_BOTSPAM)
        if message.channel == botspam_channel:
            return

        # Store the message to generate recent message history
        if message.channel.id not in self.recent_messages:
            self.recent_messages[message.channel.id] = [message]
        else:
            self.recent_messages[message.channel.id].append(message)
            if len(self.recent_messages[message.channel.id]) > 5:
                self.recent_messages[message.channel.id] = self.recent_messages[message.channel.id][1:] # Cut off the message from the longest time ago if there are too many messages stored

        # Send a ping alert to the relevant users
        for user in src.discord.globals.PING_INFO:
            if user['user_id'] == message.author.id:
                continue
            pings = [rf'\b({ping})\b' for ping in user['word_pings']]
            pings.extend(user['regex_pings'])
            for ping in pings:
                if len(re.findall(ping, message.content, re.I)) > 0 and message.author.discriminator != "0000":
                    # Do not send a ping if the user is mentioned
                    user_is_mentioned = user['user_id'] in [m.id for m in message.mentions]
                    if user['user_id'] in [m.id for m in message.channel.members] and ('dnd' not in user or user['dnd'] != True) and not user_is_mentioned:
                        # Check that the user can actually see the message
                        await self.__ping_pm(user['user_id'], message.author, ping, message.channel, message.content, message.jump_url)

    def format_text(self, text, length, expression):
        # Attempt to highlight the ping expression in the text
        try:
            text = re.sub(rf'{expression}', r'**\1**', text, flags=re.I)
        except Exception as e:
            print(f"Could not bold ping due to unfavored RegEx. Error: {e}")

        # Prevent the text from being too long
        if len(text) > length:
            return text[:length - 3] + "..."
        else:
            return text

    async def __ping_pm(self, user_id, pinger, ping_exp, channel, content, jump_url):
        """Allows Pi-Bot to PM a user about a ping."""
        # Get the relevant user to send the alert message to
        user_to_send = self.bot.get_user(user_id)

        # Create the alert embed
        description = "**One of your pings was mentioned by a user in the Scioly.org Discord server!**"
        description = description + "\n\n" + "\n".join([f"{message.author.mention}: {self.format_text(message.content, 100, ping_exp)}" for message in self.recent_messages[channel.id]])
        description = description + "\n\n" + f"Come check out the conversation! [Click here]({jump_url}) to be teleported to the message!"
        embed = discord.Embed(
            title = ":bellhop: Ping Alert!",
            color = discord.Color.brand_red(),
            description = description
        )
        embed.set_thumbnail(url = pinger.display_avatar.url)

        ping_exp = ping_exp.replace(r"\b(", "").replace(r")\b", "")
        embed.set_footer(text = f"If you don't want this ping anymore, type /pingremove {ping_exp} in the Scioly.org Discord server!")

        # Send the user an alert message
        await user_to_send.send(embed = embed)

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Toggles 'Do Not Disturb' mode for pings."
    )
    async def dnd(self, ctx):
        member = ctx.author.id
        if any([True for u in PING_INFO if u['id'] == member]):
            user = next((u for u in PING_INFO if u['id'] == member), None)
            if 'dnd' not in user:
                user['dnd'] = True
                return await ctx.interaction.response.send_message("Enabled DND mode for pings.")
            elif user['dnd'] == True:
                user['dnd'] = False
                return await ctx.interaction.response.send_message("Disabled DND mode for pings.")
            else:
                user['dnd'] = True
                return await ctx.interaction.response.send_message("Enabled DND mode for pings.")
        else:
            return await ctx.interaction.response.send_message("You can't enter DND mode without any pings!")

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Adds a new word to ping on."
    )
    async def pingadd(self,
        ctx,
        word: Option(str, "The new word to add a ping for.", required = True)
        ):
        # Check to see if author in ping info already
        member = ctx.author
        if any([True for u in src.discord.globals.PING_INFO if u['user_id'] == member.id]):
            # User already has an object in the PING_INFO dictionary
            user = next((u for u in src.discord.globals.PING_INFO if u['user_id'] == member.id), None)
            pings = user['word_pings'] + user['regex_pings']
            try:
                re.findall(word, "test phrase")
            except:
                return await ctx.interaction.response.send_message(f"Ignoring adding the `{word}` ping because it uses illegal characters.")
            if f"({word})" in pings or f"\\b({word})\\b" in pings or word in pings:
                return await ctx.interaction.response.send_message(f"Ignoring adding the `{word}` ping because you already have a ping currently set as that.")
            else:
                print(f"adding word: {re.escape(word)}")
                relevant_doc = [doc for doc in src.discord.globals.PING_INFO if doc['user_id'] == member.id][0]
                relevant_doc['word_pings'].append(word)
                await update("data", "pings", user['_id'], {"$push": {"word_pings": word}})
        else:
            # User does not already have an object in the PING_INFO dictionary
            new_user_dict = {
                "user_id": member.id,
                "word_pings": [word],
                "regex_pings": [],
                "dnd": False
            }
            src.discord.globals.PING_INFO.append(new_user_dict)
            await insert("data", "pings", new_user_dict)
        return await ctx.interaction.response.send_message(f"Great! You will now receive an alert for messages that contain the `{word}` word.\n\nPlease be responsible with the pinging feature. Using pings senselessly (such as pinging for \"the\" or \"a\") may result in you being temporarily disallowed from using or receiving pings.")

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Tests your pings against a test phrase."
    )
    async def pingtest(self,
        ctx,
        test: Option(str, "The phrase to test your pings against.", required = True)
        ):
        member = ctx.author
        user = next((u for u in src.discord.globals.PING_INFO if u['user_id'] == member.id), None)
        user_pings = user['word_pings'] + user['regex_pings']
        matched = False
        response = ""
        for ping in user_pings:
            if len(re.findall(ping, test, re.I)) > 0:
                response += (f"Your ping `{ping}` matches `{test}`.")
                matched = True
        if not matched:
            return await ctx.interaction.response.send_message("Your test matched no pings of yours.")
        else:
            return await ctx.interaction.response.send_message(response)

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Lists all of your pings."
    )
    async def pinglist(self, ctx):
        member = ctx.author
        user = next((u for u in src.discord.globals.PING_INFO if u['user_id'] == member.id), None)
        if user == None or len(user['word_pings'] + user['regex_pings']) == 0:
            return await ctx.interaction.response.send_message("You have no registered pings.")
        else:
            response = ""
            if len(user['regex_pings']) > 0:
                response += ("Your RegEx pings are: " + ", ".join([f"`{regex}`" for regex in user['regex_pings']]))
            if len(user['word_pings']) > 0:
                response += ("Your pings are: " + ", ".join([f"`{word}`" for word in user['word_pings']]))
            if not len(response):
                response = "You have no registered pings."
            await ctx.interaction.response.send_message(response)

    @discord.commands.slash_command(
        guild_ids = [SLASH_COMMAND_GUILDS],
        description = "Removes a ping term."
    )
    async def pingremove(self,
        ctx,
        word: Option(str, "The word to remove a ping for. Or use 'all' to remove all pings.", required = True)
        ):
        member = ctx.author
        user = next((u for u in src.discord.globals.PING_INFO if u['user_id'] == member.id), None)
        if user == None or len(user['word_pings'] + user['regex_pings']) == 0:
            return await ctx.interaction.response.send_message("You have no registered pings.")
        if word == "all":
            user['word_pings'] = []
            user['regex_pings'] = []
            await update("data", "pings", user['_id'], {"$pull": {"word_pings": {}, "regex_pings": {}}})
            return await ctx.interaction.response.send_message("I removed all of your pings.")
        if word in user['word_pings']:
            user['word_pings'].remove(word)
            await update("data", "pings", user['_id'], {"$pull": {"word_pings": word}})
            return await ctx.interaction.response.send_message(f"I removed the `{word}` ping you were referencing.")
        elif word in user['regex_pings']:
            user['regex_pings'].remove(word)
            await update("data", "pings", user['_id'], {"$pull": {"regex_pings": word}})
            return await ctx.interaction.response.send_message(f"I removed the `{word}` RegEx ping you were referencing.")
        elif f"\\b({word})\\b" in user['word_pings']:
            user['word_pings'].remove(f"\\e({word})\\b")
            await update("data", "pings", user['_id'], {"$pull": {"word_pings": f"\\e({word})\\b"}})
            return await ctx.interaction.response.send_message(f"I removed the `{word}` ping you were referencing.")
        elif f"({word})" in user['word_pings']:
            user['word_pings'].remove(f"({word})")
            await update("data", "pings", user['_id'], {"$pull": {"word_pings": f"({word})"}})
            return await ctx.interaction.response.send_message(f"I removed the `{word}` RegEx ping you were referencing.")
        else:
            return await ctx.interaction.response.send_message(f"I can't find the **`{word}`** ping you are referencing, sorry. Try another ping, or see all of your pings with `/pinglist`.")

def setup(bot):
    bot.add_cog(PingManager(bot))
