from discord.ext import commands


# TODO - Add PropRep Module

class Vote(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


def setup(bot):
    bot.add_cog(Vote(bot))
