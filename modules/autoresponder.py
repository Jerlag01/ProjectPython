import discord

class Autoresponder:
    """Autoreponds"""

    def __init__(self, client):
        self.client = client

    async def on_message(self, message):
        msg = 'Hello {0.author.mention}. How are you today?'.format(message)
    
        if message.author == self.client.user:
            return

        if message.content == ('hello'):
            await self.client.send_message(message.channel, msg)
            await self.client.process_commands(message)

        if message.content == ('Hello'):
            await self.client.send_message(message.channel, msg)
            await self.client.process_commands(message)


def setup(client):
    client.add_cog(Autoresponder(client))