import discord
from discord.ext import commands

class Management:
    """Owner-Only Commands."""

    def __init__(self, bot):
        self.bot = bot


def setup(client):
    n = Management(bot)
    bot.add_cog(n)
