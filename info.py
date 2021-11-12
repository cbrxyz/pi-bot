import discord

version = "4.5.19"
developers = "Created and developed mainly by <@715048392408956950>. All contributors can be found here: <https://github.com/cbrxyz/pi-bot/graphs/contributors>"
repo = "https://github.com/cbrxyz/pi-bot"
wiki_link = "https://scioly.org/wiki/index.php/User:Pi-Bot"
forums_link = "https://scioly.org/forums/memberlist.php?mode=viewprofile&u=62443"

def get_about(avatar_url):
    embed = discord.Embed(
        title = f"**Pi-Bot {version}**",
        color = discord.Color(0xF86D5F),
        description = f"""
        Hey there! I'm Pi-Bot, and I help to manage the Scioly.org forums, wiki, and chat. You'll often see me around this Discord server to help users get roles and information about Science Olympiad.

        I'm developed by the community. If you'd like to find more about development, you can find more by visiting the links below.
        """
    )
    embed.add_field(name = "Code Repository", value = repo, inline = False)
    embed.add_field(name = "Wiki Page", value = wiki_link, inline = False)
    embed.add_field(name = "Forums Page", value = forums_link, inline = False)
    embed.set_thumbnail(url = avatar_url)
    return embed
