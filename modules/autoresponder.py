import discord

class Autoresponder:
    """Autoreponds"""

    def __init__(self, bot):
        self.bot = bot

    async def on_message(self, message):
        msg = 'Hello {0.author.mention}. How are you today?'.format(message)
    
        if message.author == self.bot.user:
            return

        if message.content == ('hello'):
            await self.bot.send_message(message.channel, msg)
            await self.bot.process_commands(message)

        if message.content == ('Hello'):
            await self.bot.send_message(message.channel, msg)
            await self.bot.process_commands(message)


def setup(bot):
    n = Autoresponder(bot)
    bot.add_cog(n)