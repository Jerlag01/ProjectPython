import discord
import secrets
import logging
import logging.handlers
import asyncio
import settings

from discord.ext.commands import Bot
from discord import Game

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
