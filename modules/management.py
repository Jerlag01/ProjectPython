import discord
from discord.ext import commands

class Management:
    """Owner-Only Commands."""

    def __init__(self, client):
        self.client = client


def setup(client):
    client.add_cog(Management(client))
