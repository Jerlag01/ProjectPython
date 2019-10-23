import discord
import datetime
import time
import logging

from discord.ext import commands
from .utils.dataIO import dataIO
from .utils import checks

class Support:

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True, no_pm=True)
    async def new(self, ctx):
        """Creates a Support ticket"""
        embed = discord.Embed
        server = ctx.message.server
        await bot.create_channel(server, type=discord.ChannelType.text)


    @commands.command(no_pm=True)
    async def close(self):
        """Closes a Support ticket"""

    @commands.command(pass_context=True, no_pm=True)
    async def add(self, ctx, user : discord.Member, *, nickname=""):
        """Adds a user to the specific ticket"""

    @commands.command(pass_context=True, no_pm=True)
    async def remove(self, ctx, user : discord.Member, *, nickname=""):
        """Removes a user from the specific ticket"""

def setup(bot):
    n = Support(bot)
    bot.add_cog(n)