from __future__ import annotations

import asyncio
import json
import re
from typing import TYPE_CHECKING

import webcolors

import discord
from discord import app_commands
from discord.ext import commands

if TYPE_CHECKING:
    from bot import PiBot

import commandchecks
from src.discord.globals import (
    EMOJI_LOADING,
    ROLE_STAFF,
    ROLE_VIP,
    SLASH_COMMAND_GUILDS,
)


class EmbedFieldManagerButton(discord.ui.Button["EmbedFieldManagerView"]):
    def __init__(
        self, view: "EmbedFieldManagerView", bot: PiBot, name, raw_name, status
    ):
        self.field_manager_view = view
        self.name = name
        self.raw_name = raw_name
        self.status = status
        self.bot = bot

        if self.status == "add":
            super().__init__(label=f"Add {name}", style=discord.ButtonStyle.green)
        elif self.status == "edit":
            super().__init__(label=f"Edit {name}", style=discord.ButtonStyle.gray)
        elif self.status == "toggle":
            super().__init__(label=self.name, style=discord.ButtonStyle.blurple)
        elif self.status == "complete":
            super().__init__(label="Complete Field", style=discord.ButtonStyle.green)

    async def callback(self, interaction: discord.Interaction):

        if self.raw_name == "complete":
            if not (
                "name" in self.field_manager_view.field
                and "value" in self.field_manager_view.field
            ):
                help_message = await self.field_manager_view.channel.send(
                    "This field can not yet be completed, because you haven't defined both the field name and value."
                )
                await asyncio.sleep(10)
                await help_message.delete()
                self.field_manager_view.stop()
            else:
                self.field_manager_view.stopped_status = "completed"
                self.field_manager_view.stop()
                return

        if self.raw_name != "inline":
            await interaction.response.defer()
            info_message = await self.field_manager_view.channel.send(
                f"Please send the new value for the {self.raw_name}. The operation will be cancelled if no operation "
                f"was sent within 2 minutes. "
            )
            response_message = await self.bot.listen_for_response(
                follow_id=self.field_manager_view.user.id,
                timeout=120,
            )

            await info_message.delete()

            if response_message is None:
                self.field_manager_view.stopped_status = "failed"

            await response_message.delete()

            if not len(response_message.content):
                help_message = await self.field_manager_view.channel.send(
                    "I couldn't find any text response in the message you just sent. Remember that for images, "
                    "only URLs will work. I can't accept files for the {self.raw_name}! "
                )
                await asyncio.sleep(10)
                await help_message.delete()
                self.field_manager_view.stop()
                return

            # Check for limits
            limits = {"name": 256, "value": 1024}
            for k, v in limits.items():
                if self.raw_name == k and len(response_message.content) > v:
                    help_message = await self.field_manager_view.channel.send(
                        f"Unforunately, you can not provide a {k} longer than {v} characters. Please try again!"
                    )
                    await help_message.delete(delay=10)
                    self.field_manager_view.stop()
                    return

        if self.raw_name == "inline":
            # Editing name
            self.field_manager_view.field["inline"] = not self.field_manager_view.field[
                "inline"
            ]
        else:
            self.field_manager_view.field[self.raw_name] = response_message.content

        # Update fields
        if self.field_manager_view.index >= len(self.field_manager_view.fields):
            self.field_manager_view.fields.append(self.field_manager_view.field)
        else:
            self.field_manager_view.fields[
                self.field_manager_view.index
            ] = self.field_manager_view.field
            self.field_manager_view.embed_update = {
                "fields": self.field_manager_view.fields
            }
        self.field_manager_view.stop()


class EmbedFieldManagerView(discord.ui.View):
    stopped_status = None

    def __init__(self, interaction: discord.Interaction, bot: PiBot, fields, index):
        self.channel = interaction.channel
        self.user = interaction.user
        self.fields = fields
        self.index = index
        self.bot = bot
        self.embed_update = {}
        super().__init__()

        self.field = {}
        if index < len(fields):
            self.field = fields[index]

        if "name" in self.field:
            self.add_item(
                EmbedFieldManagerButton(self, self.bot, "Name", "name", status="edit")
            )
        else:
            self.add_item(
                EmbedFieldManagerButton(self, self.bot, "Name", "name", status="add")
            )

        if "value" in self.field:
            self.add_item(
                EmbedFieldManagerButton(self, self.bot, "Value", "value", status="edit")
            )
        else:
            self.add_item(
                EmbedFieldManagerButton(self, self.bot, "Value", "value", status="add")
            )

        if "inline" not in self.field:
            self.field["inline"] = False

        self.add_item(
            EmbedFieldManagerButton(
                self,
                self.bot,
                f"Inline: {self.field['inline']} (Toggle)",
                "inline",
                status="toggle",
            )
        )
        self.add_item(
            EmbedFieldManagerButton(
                self, self.bot, "Complete", "complete", status="complete"
            )
        )


class EmbedButton(discord.ui.Button["EmbedView"]):
    def __init__(
        self,
        view: "EmbedView",
        bot: PiBot,
        text: str,
        style: discord.ButtonStyle,
        row: int,
        update_value,
        help_message="",
    ):
        super().__init__(label=text, style=style, row=row)
        self.bot = bot
        self.embed_view: "EmbedView" = view
        self.update_value = update_value
        self.help_message = help_message

    async def callback(self, interaction: discord.Interaction):
        # Check if the Complete button was pressed - if so, stop process
        if self.update_value == "complete":
            # If complete button is clicked, stop the view immediately
            self.embed_view.stopped_status = "completed"
            self.embed_view.stop()
            return

        if self.update_value == "cancel":
            # If abort button is clicked, stop the view immediately
            self.embed_view.stopped_status = "aborted"
            self.embed_view.stop()
            return

        if self.update_value in ["import", "export"]:
            self.embed_view.embed_update[self.update_value] = True
            self.embed_view.stop()
            return

        if self.update_value in ["author_icon", "author_url"] and not any(
            [
                value in self.embed_view.embed_dict
                for value in ["author_name", "authorName"]
            ]
        ):
            help_message = await self.embed_view.channel.send(
                "You can not set the author URL/icon without first setting the author name."
            )
            await help_message.delete(delay=10)
            self.embed_view.stop()
            return

        if self.update_value == "url" and "title" not in self.embed_view.embed_dict:
            help_message = await self.embed_view.channel.send(
                "You can not set the title URL without first setting the title."
            )
            await help_message.delete(delay=10)
            self.embed_view.stop()
            return

        if self.update_value == "add_field":
            if (
                "fields" in self.embed_view.embed_dict
                and len(self.embed_view.embed_dict["fields"]) == 25
            ):
                help_message = await self.embed_view.channel.send(
                    "You can't have more than 25 embed fields! Don't be so selfish, keeping all of the embed fields "
                    "to yourself! "
                )
                await help_message.delete(delay=10)
                self.embed_view.stop()
                return
            self.embed_view.embed_update["add_field"] = {
                "index": len(self.embed_view.embed_dict["fields"])
                if "fields" in self.embed_view.embed_dict
                else 0
            }
            return self.embed_view.stop()

        if self.update_value in ["edit_field", "remove_field"]:
            # Check to see if any fields actually exist
            if "fields" not in self.embed_view.embed_dict or not len(
                self.embed_view.embed_dict["fields"]
            ):
                await self.embed_view.channel.send(
                    "It appears no fields exist in the embed currently."
                )
                self.embed_view.stopped_status = "failed"
                return self.embed_view.stop()

            await interaction.response.defer()
            fields = self.embed_view.embed_dict["fields"]
            min_num = 1
            max_num = len(fields)

            info_message = await self.embed_view.channel.send(
                f"Please type in the index of the field you would like to {'edit' if self.update_value == 'edit_field' else 'remove'}. `1` refers to the first field, `2` to the second, etc...\n\nThe minimum accepted value is `1` and the maximum accepted value is `{len(fields)}`!"
            )

            valid_response = False
            while not valid_response:
                response_message = await self.bot.listen_for_response(
                    follow_id=self.embed_view.user.id,
                    timeout=120,
                )

                await info_message.delete()
                await response_message.delete()

                if response_message == None:
                    self.embed_view.stopped_status = "failed"
                    await self.embed_view.channel.send(
                        "I couldn't find any content in your message. Aborting."
                    )
                    return self.embed_view.stop()

                if not response_message.content.isnumeric():
                    self.embed_view.stopped_status = "failed"
                    await self.embed_view.channel.send(
                        "It appears that your message did not solely contain a number. Please try again."
                    )
                    return self.embed_view.stop()

                if min_num <= int(response_message.content) <= max_num:
                    self.embed_view.embed_update[self.update_value] = {
                        "index": int(response_message.content) - 1
                    }
                    valid_response = True

            return self.embed_view.stop()

        await interaction.response.defer()
        info_message = await self.embed_view.channel.send(
            f"Please send the new value for the parameter. The operation will be cancelled if no operation was sent "
            f"within 2 minutes.\n\n{self.help_message} "
        )
        response_message = await self.bot.listen_for_response(
            follow_id=self.embed_view.user.id,
            timeout=120,
        )

        await info_message.delete()
        await response_message.delete()
        if response_message == None:
            self.embed_view.stopped_status = "failed"

        if not len(response_message.content):
            help_message = await self.embed_view.channel.send(
                "I couldn't find any text response in the message you just sent. Remember that for images, only URLs will work. I can't accept files for any value!"
            )
            await asyncio.sleep(10)
            await help_message.delete()
            self.embed_view.stop()
            return

        # Check for embed limits
        limits = {
            "title": 256,
            "description": 4096,
            "footer_text": 2048,
            "author_name": 256,
        }
        for k, v in limits.items():
            if self.update_value == k and len(response_message.content) > v:
                help_message = await self.embed_view.channel.send(
                    f"Unfortunately, you provided a string that is longer than the allowable length for that value. Please provide a value that is less than {v} characters."
                )
                await help_message.delete(delay=10)
                self.embed_view.stop()
                return

        if self.update_value == "color" and not len(
            re.findall(r"#[0-9a-f]{6}", response_message.content.lower())
        ):
            help_message = await self.embed_view.channel.send(
                f"The color you provide must be a hex code. For example, `#abbb02` or `#222ddd`."
            )
            await help_message.delete(delay=10)
            self.embed_view.stop()
            return

        self.embed_view.embed_update[self.update_value] = response_message.content
        self.embed_view.stop()


class EmbedView(discord.ui.View):
    # This will be updated when the user updates an embed property
    embed_update = {}
    embed_dict = {}
    user = None
    channel = None
    stopped_status = None

    def __init__(self, bot: PiBot, embed_dict: dict, interaction: discord.Interaction):
        super().__init__()
        self.bot = bot
        self.embed_dict = embed_dict
        self.embed_update = {}
        self.user = interaction.user
        self.channel = interaction.channel
        self.stopped_status = None

        associations = [
            {
                "proper_name": "Title",
                "dict_values": ["title"],
                "row": 0,
                "help": "To remove the title, simply respond with `remove`.",
            },
            {"proper_name": "Description", "dict_values": ["description"], "row": 0},
            {
                "proper_name": "Title URL",
                "dict_values": ["url", "title_url", "titleUrl"],
                "row": 0,
                "help": "To remove the URL from the title, simply respond with `remove`.",
            },
            {
                "proper_name": "Color",
                "dict_values": ["color"],
                "row": 0,
                "help": "Please send the color formatted as a hex color. For Scioly.org-related color codes, see <https://scioly.org/wiki/index.php/Scioly.org:Design>. To remove the color, simply respond with `remove`.",
            },
            {
                "proper_name": "Thumbnail Image (from URL)",
                "dict_values": ["thumbnail_url", "thumbnailUrl"],
                "row": 1,
                "help": "Please note that only HTTPS URLs will work. To remove the thumbnail, respond simply with `remove`.",
            },
            {
                "proper_name": "Image (from URL)",
                "dict_values": ["image_url", "imageUrl"],
                "row": 1,
                "help": "Please note that only HTTPS URLs will work. To remove the image, simply respond with `remove`.",
            },
            {
                "proper_name": "Author Name",
                "dict_values": ["author_name", "authorName"],
                "row": 2,
                "help": "To remove the author name (and therefore, the author icon/URL), simply respond with `remove`.",
            },
            {
                "proper_name": "Author Icon (from URL)",
                "dict_values": ["author_icon", "authorIcon"],
                "row": 2,
                "help": "To remove the author icon, simply respond with `remove`.",
            },
            {
                "proper_name": "Author URL",
                "dict_values": ["author_url", "authorUrl"],
                "row": 2,
                "help": "To remove the URL link from the author value, simply respond with `remove`.",
            },
            {
                "proper_name": "Footer Text",
                "dict_values": ["footer_text", "footerText"],
                "row": 2,
                "help": "To remove the footer text, simply respond with `remove`.",
            },
            {
                "proper_name": "Footer Icon (from URL)",
                "dict_values": ["footer_icon", "footerIcon"],
                "row": 2,
                "help": "To remove the footer icon, simply respond with `remove`.",
            },
        ]
        for association in associations:
            if len(
                [
                    dict_value
                    for dict_value in association["dict_values"]
                    if dict_value in embed_dict
                ]
            ):
                button = EmbedButton(
                    self,
                    self.bot,
                    f"Edit {association['proper_name']}",
                    discord.ButtonStyle.gray,
                    association["row"],
                    association["dict_values"][0],
                    association["help"] if "help" in association else "",
                )
                self.add_item(button)
            else:
                button = EmbedButton(
                    self,
                    self.bot,
                    f"Set {association['proper_name']}",
                    discord.ButtonStyle.green,
                    association["row"],
                    association["dict_values"][0],
                    association["help"] if "help" in association else "",
                )
                self.add_item(button)

        # Field operations
        self.add_item(
            EmbedButton(
                self, self.bot, "Add Field", discord.ButtonStyle.green, 3, "add_field"
            )
        )
        self.add_item(
            EmbedButton(
                self, self.bot, "Edit Fields", discord.ButtonStyle.gray, 3, "edit_field"
            )
        )
        self.add_item(
            EmbedButton(
                self,
                self.bot,
                "Remove Field",
                discord.ButtonStyle.danger,
                3,
                "remove_field",
            )
        )

        # Add complete operation
        self.add_item(
            EmbedButton(
                self, self.bot, "Complete", discord.ButtonStyle.green, 4, "complete"
            )
        )
        self.add_item(
            EmbedButton(
                self, self.bot, "Abort", discord.ButtonStyle.danger, 4, "cancel"
            )
        )
        self.add_item(
            EmbedButton(
                self, self.bot, "Import", discord.ButtonStyle.blurple, 4, "import"
            )
        )
        self.add_item(
            EmbedButton(
                self, self.bot, "Export", discord.ButtonStyle.blurple, 4, "export"
            )
        )


class EmbedCommands(commands.Cog):
    def _generate_embed(self, embed_dict: dict) -> discord.Embed:
        new_embed_dict = {}

        # Get primary attributes
        if "title" in embed_dict:
            new_embed_dict["title"] = embed_dict["title"]
        if "description" in embed_dict:
            new_embed_dict["description"] = embed_dict["description"]
        if "url" in embed_dict:
            new_embed_dict["url"] = embed_dict["url"]
        if "title_url" in embed_dict:
            new_embed_dict["url"] = embed_dict["title_url"]
        if "titleUrl" in embed_dict:
            new_embed_dict["url"] = embed_dict["titleUrl"]

        # Convert color properties to one concise color property to check for class
        if "hexColor" in embed_dict:
            embed_dict["color"] = embed_dict["hexColor"]
        if "webColor" in embed_dict:
            try:
                embed_dict["color"] = webcolors.name_to_hex(embed_dict["webColor"])
            except:
                pass
        if "color" in embed_dict and isinstance(embed_dict["color"], discord.Color):
            new_embed_dict["color"] = embed_dict["color"]
        if "color" in embed_dict and isinstance(embed_dict["color"], str):
            if embed_dict["color"].startswith("#"):
                new_embed_dict["color"] = discord.Color(
                    int(embed_dict["color"][1:], 16)
                )
            elif len(embed_dict["color"]) <= 6:
                new_embed_dict["color"] = discord.Color(int(embed_dict["color"], 16))
        if "color" in embed_dict and isinstance(embed_dict["color"], int):
            blue = embed_dict["color"] & 255
            green = (embed_dict["color"] >> 8) & 255
            red = (embed_dict["color"] >> 16) & 255
            new_embed_dict["color"] = discord.Color.from_rgb(red, green, blue)

        if not len(new_embed_dict.items()):
            new_embed_dict[
                "description"
            ] = "This embed contains nothing, so a blank description was set."
        response = discord.Embed(**new_embed_dict)

        if "thumbnail_url" in embed_dict:
            response.set_thumbnail(url=embed_dict["thumbnail_url"])
        if "thumbnailUrl" in embed_dict:
            response.set_thumbnail(url=embed_dict["thumbnailUrl"])
        if "thumbnail" in embed_dict:
            response.set_thumbnail(url=embed_dict["thumbnail"]["url"])

        if "authorName" in embed_dict or "author_name" in embed_dict:
            # Author name must be defined for other attributes to work

            author_dict = {}
            if "authorName" in embed_dict:
                author_dict["name"] = embed_dict["authorName"]
            if "author_name" in embed_dict:
                author_dict["name"] = embed_dict["author_name"]
            if "author_url" in embed_dict:
                author_dict["url"] = embed_dict["author_url"]
            if "authorUrl" in embed_dict:
                author_dict["url"] = embed_dict["authorUrl"]
            if "author_icon" in embed_dict:
                author_dict["icon_url"] = embed_dict["author_icon"]
            if "authorIcon" in embed_dict:
                author_dict["icon_url"] = embed_dict["authorIcon"]
            response.set_author(**author_dict)

        # Native discord.py dict format
        if "author" in embed_dict:
            author_dict = {}
            if "name" in embed_dict["author"]:
                author_dict["name"] = embed_dict["author"]["name"]
            if "url" in embed_dict["author"]:
                author_dict["url"] = embed_dict["author"]["url"]
            if "icon_url" in embed_dict["author"]:
                author_dict["icon_url"] = embed_dict["author"]["icon_url"]
            response.set_author(**author_dict)

        if "fields" in embed_dict:
            # If error, don't stress, just move on
            try:
                for field in embed_dict["fields"]:
                    response.add_field(**field)
            except:
                pass

        footer_dict = {}
        if "footer_text" in embed_dict:
            footer_dict["text"] = embed_dict["footer_text"]
        if "footerText" in embed_dict:
            footer_dict["text"] = embed_dict["footerText"]
        if "footer_icon" in embed_dict:
            footer_dict["icon_url"] = embed_dict["footer_icon"]
        if "footerIcon" in embed_dict:
            footer_dict["icon_url"] = embed_dict["footerIcon"]
        if "footerUrl" in embed_dict:
            footer_dict["icon_url"] = embed_dict["footerUrl"]
        if "footer" in embed_dict:
            if "text" in embed_dict["footer"]:
                footer_dict["text"] = embed_dict["footer"]["text"]
            if "icon_url" in embed_dict["footer"]:
                footer_dict["icon_url"] = embed_dict["footer"]["icon_url"]

        if len(footer_dict.items()):
            response.set_footer(**footer_dict)

        if "image_url" in embed_dict:
            response.set_image(url=embed_dict["image_url"])
        if "imageUrl" in embed_dict:
            response.set_image(url=embed_dict["imageUrl"])
        if "image" in embed_dict:
            response.set_image(url=embed_dict["image"]["url"])

        return response

    def __init__(self, bot: PiBot):
        self.bot = bot
        print("Initialized embed cog.")

    @app_commands.command(
        description="Staff command. Assembles an embed in a particular channel."
    )
    @app_commands.checks.has_any_role(ROLE_STAFF, ROLE_VIP)
    @app_commands.guilds(SLASH_COMMAND_GUILDS)
    @app_commands.describe(
        channel="The channel to send the message to. If editing an embed, the message's channel.",
        message_id="The ID of the message to edit the embed of.",
    )
    @app_commands.default_permissions(manage_messages=True)
    async def prepembed(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        message_id: str = None,
    ):
        """Helps to create an embed to be sent to a channel."""
        # Check for staff permissions
        commandchecks.is_staff_from_ctx(interaction)

        embed_dict = {}
        try:
            message_id = int(message_id) if message_id is not None else None
        except:
            await interaction.response.send_message(
                f":x: `{message_id}` is not a valid message ID."
            )

        await interaction.response.send_message(f"{EMOJI_LOADING} Initializing...")

        complete = False
        embed_field_manager = False
        embed_field_index = None
        response = None

        # Get old embed if relevant
        if message_id:
            try:
                message = await channel.fetch_message(message_id)
            except discord.NotFound:
                return await interaction.edit_original_message(
                    content="No message with that ID was found."
                )

            if not message.embeds:
                await interaction.edit_original_message(
                    content=f"The requested message has no embeds."
                )
            else:
                embed_dict = message.embeds[0].to_dict()

        while not complete:
            response = self._generate_embed(embed_dict)
            view = None
            if embed_field_manager:
                if "fields" not in embed_dict:
                    embed_dict["fields"] = []
                view = EmbedFieldManagerView(
                    interaction, self.bot, embed_dict["fields"], embed_field_index
                )
            else:
                view = EmbedView(self.bot, embed_dict, interaction)
            await interaction.edit_original_message(
                content=f"This embed will be sent to {channel.mention}:",
                embed=response,
                view=view,
            )
            await view.wait()
            if view.stopped_status is None:
                if isinstance(view, EmbedFieldManagerView):
                    embed_dict.update(view.embed_update)

                elif isinstance(view, EmbedView):
                    if any(
                        key in view.embed_update for key in ["add_field", "edit_field"]
                    ):
                        # Switch to field manager mode
                        embed_field_manager = True
                        embed_field_index = view.embed_update[
                            list(view.embed_update.items())[0][0]
                        ]["index"]

                    if "remove_field" in view.embed_update:
                        embed_field_index = view.embed_update[
                            list(view.embed_update.items())[0][0]
                        ]["index"]
                        embed_dict["fields"].pop(embed_field_index)

                    if "import" in view.embed_update:
                        # Import a JSON file as the embed dict
                        await interaction.edit_original_message(
                            content="Please send the JSON file containing the embed message as a `.json` file.",
                            view=None,
                            embed=None,
                        )
                        file_message = await self.bot.listen_for_response(
                            follow_id=interaction.user.id,
                            timeout=120,
                        )
                        # If emoji message has file, use this as emoji, otherwise, use default emoji provided
                        if file_message is None:
                            await interaction.edit_original_message(
                                content="No file was provided, so the operation was cancelled."
                            )
                            return

                        if (
                            not len(file_message.attachments)
                            or file_message.attachments[0].content_type
                            != "application/json"
                        ):
                            await interaction.edit_original_message(
                                content="I couldn't find a `.json` attachment on your message. Opertion aborted."
                            )

                        text = await file_message.attachments[0].read()
                        text = text.decode("utf-8")
                        jso = json.loads(text)
                        await file_message.delete()

                        if "author" in jso:
                            jso["author_name"] = interaction.user.name
                            jso["author_icon"] = interaction.user.avatar_url_as(
                                format="jpg"
                            )

                        embed_dict = jso

                    if "export" in view.embed_update:
                        # Generate a JSON file as the embed dict
                        with open("embed_export.json", "w+") as file:
                            json.dump(embed_dict, file)

                        await interaction.edit_original_message(
                            content="Here is the exported embed! The embed creator will return in approximately 15 "
                            "seconds.",
                            embed=None,
                            view=None,
                        )
                        file_message = await interaction.channel.send(
                            file=discord.File("embed_export.json")
                        )
                        await asyncio.sleep(15)
                        await file_message.delete()

                    removed = False
                    easy_removes = [
                        "title",
                        "url",
                        "color",
                        "thumbnail_url",
                        "image_url",
                        "footer_text",
                        "footer_url",
                        "author_url",
                        "author_icon",
                    ]
                    for removal in easy_removes:
                        if (
                            removal in view.embed_update
                            and view.embed_update[removal] == "remove"
                        ):
                            del embed_dict[removal]
                            removed = True

                    if (
                        "author_name" in view.embed_update
                        and view.embed_update["author_name"] == "remove"
                    ):
                        del embed_dict["author_name"]
                        del embed_dict["author_url"]
                        del embed_dict["author_icon"]
                        removed = True

                    if not removed and not any(
                        key in view.embed_update
                        for key in ["add_field", "edit_field", "import", "export"]
                    ):
                        # If just removed, don't actually set the value to 'remove'
                        # Or, if attempting to add/edit fields
                        embed_dict.update(view.embed_update)

            else:
                if view.stopped_status == "failed":
                    await interaction.edit_original_message(
                        content="An error has occurred. You may not have responded to my query in 2 minutes, or your "
                        "message may not have been formatted correctly. Operation cancelled.",
                        embed=None,
                        view=None,
                    )
                    return
                elif view.stopped_status == "aborted":
                    await interaction.edit_original_message(
                        content="The embed creation was aborted.", embed=None, view=None
                    )
                    return
                elif view.stopped_status == "completed":
                    if isinstance(view, EmbedFieldManagerView):
                        # If embed field manager in play, actually update fields and return to old view
                        embed_dict.update(view.embed_update)
                        embed_field_manager = False
                    elif isinstance(view, EmbedView):
                        complete = True

        if not message_id:
            # Send a new embed
            await channel.send(embed=response)
            await interaction.edit_original_message(
                content="The embed was successfully sent!", embed=None, view=None
            )

        else:
            # Edit an old embed
            try:
                message = await channel.fetch_message(message_id)
            except discord.NotFound:
                return await interaction.edit_original_message(
                    content="No message with that ID was found."
                )

            await message.edit(embed=response)
            await interaction.edit_original_message(
                content="The embed was succesfully edited!", embed=None, view=None
            )


async def setup(bot: PiBot):
    await bot.add_cog(EmbedCommands(bot))
