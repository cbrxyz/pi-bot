from commandchecks import is_staff

class StaffCommands(commands.Cog):
    async def __init__(self, bot):
        self.bot = bot
    
    @commands.check
    async def is_staff(self, ctx):
        return await is_staff(ctx)

class StaffEssential(StaffCommands, name="StaffEsntl"):
    async def __init__(self, bot):
        super().__init__(bot)
    

class StaffNonessential(StaffCommands, name="StaffNonesntl"):
    async def __init__(self, bot):
        super().__init__(bot)
        
        
def setup(bot):
    bot.add_cog(StaffEssential(bot))
    bot.add_cog(StaffNonessential(bot))