import logging
import logging.handlers
import asyncio
import os
import sys
import datetime
import subprocess
import traceback

try:
    from discord.ext import commands
    import discord
except ImportError:
    print("Discord.py is not installed.\n"
          "Consult the guide for your operating system "
          "and do ALL the steps in order.\n"
          "https://projectpython.flanderscraft.be/docs/")
    sys.exit(1)

from modules.utils.settings import Settings
from modules.utils.dataIO import dataIO
from modules.utils.chatformat import inline
from collections import Counter
from io import TextIOWrapper

description = "ProjectPython - A discord bot made for the course Python at Thomas More"

class Client(commands.Bot):
    def __init__(self, *args, **kwargs):

        def prefix_manager(bot, message):
            """Returns prfixes of the message's server if set.
            If none are set or if the message's server is None
            then it will return the global prefixes instead"""
            return Bot.settings.get_prefixes(message.server)

        self.counter = Counter()
        self.uptime = datetime.datetime.utcnow()
        self._message_modifiers = []
        self.settings = Settings()
        self._intro_displayed = False
        self._shutdown_mode = None
        self.logger = set_logger(self)
        self.oauth_url = ""

        if 'self_bot' in kwargs:
            self.settings.self_bot = kwargs['self_bot']
        else:
            kwargs ['self_bot'] = self.settings.self_bot
            if self.settings.self_bot:
                kwargs['pm_help'] = False
        super().__init__(*args, command_prefix=prefix_manager, **kwargs)

    async def send_message(self, *args, **kwargs):
        if self._message_modifiers:
            if "content" in kwargs:
                pass
            elif len(args) == 2:
                args = list(args)
                kwargs["content"] = args.pop()
            else:
                return await super().send_message(*argd, **kwargs)
            
            content = kwargs['content']
            for m in self._message_modifiers:
                try:
                    content = str(m(content))
                except:
                    pass
            kwargs['']


extensions = ['general', 'management', 'autoresponder']

client = Bot(command_prefix=settings.PREFIX2)

@client.command(name='load',
                description='Loads a module',
                brief='Loads a module')
async def load(extension):
    try:
        client.load_extension(extension)
        print('Loaded module {}'.format(extension))
        await client.say('Module {} has been loaded.'.format(extension))
    except Exception as error:
        print('Module {} cannot be loaded.[{}]'.format(extension, error))
        await client.say('There has been a problem while loading module {}'.format(extension))

@client.command(name='unload',
                description='Unloads a module',
                brief='Unoads a module')

async def unload(extension):
    try:
        client.unload_extension(extension)
        print('Unloaded module {}'.format(extension))
        await client.say('Module {} has been unloaded.'.format(extension))
    except Exception as error:
        print('Module {} cannot be unloaded.[{}]'.format(extension, error))
        await client.say('There has been a problem while unloading module {}'.format(extension))

if __name__ == '__main__':
    for extension in extensions:
        try:
            client.load_extension(extension)
        except Exception as error:
            print('{} cannot be loaded.[{}]'.format(extension, error))

@client.event
async def on_ready():

    await client.change_presence(game=Game(name="Released"))

    users = len(set(client.get_all_members()))
    servers = len(client.servers)
    channels = len([c for c in client.get_all_channels()])
    owner = secrets.OWNER

    print('--------------------------------')
    print('-      Project Python Bot      -')
    print('- Multi-functional Discord Bot -')
    print('-     Created by ' + owner + '     -')
    print('--------------------------------\n')

    print('-------------Info---------------')
    print('         Logged in as')
    print("    Name: " + client.user.name)
    print("   ID: " + client.user.id)
    print("\nConnected to:")
    print("{} server(s)".format(servers))
    print("{} channels".format(channels))
    print("{} users\n".format(users))
    print('--------------------------------\n')

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)

project_format = logging.Formatter (
    '%(asctime)s %(levelname)s %(module)s %(funcName)s %(lineno)d: '
    '%(message)s',
    datefmt="[%d/%m/%Y %H:%M]")

handler = logging.handlers.RotatingFileHandler(filename='projectpython.log', encoding='utf-8', mode='a', maxBytes=10**7, backupCount=5)
handler.setFormatter(project_format)
logger.addHandler(handler)

client.run(settings.BOT_TOKEN2)
