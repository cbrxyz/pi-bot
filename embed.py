import discord
import webcolors

def assemble_embed(
    title="",
    desc="",
    titleUrl="",
    hexcolor="#2E66B6",
    webcolor="",
    thumbnailUrl="",
    authorName="",
    authorUrl="",
    authorIcon="",
    fields={},
    footerText="",
    footerUrl="",
    imageUrl=""
    ):
    """Assembles an embed with the specified parameters."""
    if len(webcolor) > 1:
        hexcolor = webcolors.name_to_hex(webcolor)
    hexcolor = hexcolor[1:]
    embed = discord.Embed(title=title, description=desc, url=titleUrl, color=int(hexcolor, 16))
    embed.set_author(name=authorName, url=authorUrl, icon_url=authorIcon)
    embed.set_thumbnail(url=thumbnailUrl)
    for field in fields:
        embed.add_field(name=field['name'], value=field['value'], inline=(field['inline'] == "True"))
    embed.set_footer(text=footerText, icon_url=footerUrl)
    embed.set_image(url=imageUrl)
    return embed