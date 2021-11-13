import discord

class YesNo(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None

    @discord.ui.button(label = "Yes", style = discord.ButtonStyle.green)
    async def yes(self, button: discord.Button, interaction: discord.Interaction):
        self.value = True
        self.stop()

    @discord.ui.button(label = "No", style = discord.ButtonStyle.red)
    async def no(self, button: discord.Button, interaction: discord.Interaction):
        self.value = False
        self.stop()
