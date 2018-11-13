import discord
import datetime
import time
import aiohttp
import asyncio
from random import choice
from chatformat import escape_mass_mentions, italics, pagify
from discord.ext import commands

class General:
    """General Commands."""

    def __init__(self, client):
        self.client = client

    @commands.command(pass_context=True,
                    name='ping',
                    description='Responds with the time needed to respond',
                    brief='Responds with the time needed to respond' )
    async def ping(self, ctx):
        pingtime = time.time()
        pingms = await self.client.say("Pinging...")
        ping = time.time() - pingtime
        await self.client.edit_message(pingms, ":ping_pong:  time is %.01f seconds" % ping)

    @commands.command(pass_context=True, no_pm=True)
    async def serverinfo(self, ctx):
        """Shows server's information"""
        server = ctx.message.server
        online = len([m.status for m in server.members
                      if m.status != discord.Status.offline])
        total_users = len(server.members)
        text_channels = len([x for x in server.channels
                             if x.type == discord.ChannelType.text])
        voice_channels = len([x for x in server.channels
                              if x.type == discord.ChannelType.voice])
        passed = (ctx.message.timestamp - server.created_at).days
        created_at = ("Since {}. That's over {} days ago!"
                      "".format(server.created_at.strftime("%d %b %Y %H:%M"),
                                passed))

        colour = '02A969'
        colour = int(colour, 15)

        data = discord.Embed(
            description=created_at,
            colour=discord.Colour(value=colour))
        data.add_field(name="Region", value=str(server.region))
        data.add_field(name="Users", value="{}/{}".format(online, total_users))
        data.add_field(name="Text Channels", value=text_channels)
        data.add_field(name="Voice Channels", value=voice_channels)
        data.add_field(name="Roles", value=len(server.roles))
        data.add_field(name="Owner", value=str(server.owner))
        data.set_footer(text="Server ID: " + server.id)

        print('{0.author} executed command serverinfo')

        if server.icon_url:
            data.set_author(name=server.name, url=server.icon_url)
            data.set_thumbnail(url=server.icon_url)
        else:
            data.set_author(name=server.name)

        try:
            await self.client.say(embed=data)
        except discord.HTTPException:
            await self.client.say("I need the `Embed links` permission "
                               "to send this")
    
def setup(client):
    client.add_cog(General(client))