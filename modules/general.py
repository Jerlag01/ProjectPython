import discord
import datetime
import time
import aiohttp
import asyncio
from random import choice
from random import randint
from discord.ext import commands
from .utils.chatformat import escape_mass_mentions, italics, pagify
from enum import Enum
from urllib.parse import quote_plus

settings = {"POLL_DURATION" : 60}

class RPS(Enum):
    rock     = "\N{MOYAI}"
    paper    = "\N{PAGE FACING UP}"
    scissors = "\N{BLACK SCISSORS}"

class RPSParser:
    def __init__(self, argument):
        argument = argument.lower()
        if argument == "rock":
            self.choice = RPS.rock
        elif argument == "paper":
            self.choice = RPS.paper
        elif argument == "scissors":
            self.choice = RPS.scissors
        else:
            raise

class General:
    """General Commands."""

    def __init__(self, bot):
        self.bot = bot
        self.stopwatches = {}
        self.ball = ["As I see it, yes", "It is certain", "It is decidedly so", "Most likely", "Outlook good",
                     "Signs point to yes", "Without a doubt", "Yes", "Yes – definitely", "You may rely on it", "Reply hazy, try again",
                     "Ask again later", "Better not tell you now", "Cannot predict now", "Concentrate and ask again",
                     "Don't count on it", "My reply is no", "My sources say no", "Outlook not so good", "Very doubtful"]
        self.poll_sessions = []

    @commands.command(pass_context=True,
                    name='ping',
                    description='Responds with the time needed to respond',
                    brief='Responds with the time needed to respond' )
    async def ping(self, ctx):
        pingtime = time.time()
        pingms = await self.bot.say("Pinging...")
        ping = time.time() - pingtime
        await self.bot.edit_message(pingms, ":ping_pong:  time is %.01f seconds" % ping)

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

        colour = ''.join([choice('0123456789ABCDEF') for x in range(6)])
        colour = int(colour, 16)

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

    @commands.command(pass_context=True)
    async def rps(self, ctx, your_choice : RPSParser):
        """Play rock paper scissors"""
        author = ctx.message.author
        player_choice = your_choice.choice
        red_choice = choice((RPS.rock, RPS.paper, RPS.scissors))
        cond = {
                (RPS.rock,     RPS.paper)    : False,
                (RPS.rock,     RPS.scissors) : True,
                (RPS.paper,    RPS.rock)     : True,
                (RPS.paper,    RPS.scissors) : False,
                (RPS.scissors, RPS.rock)     : False,
                (RPS.scissors, RPS.paper)    : True
               }

        if red_choice == player_choice:
            outcome = None # Tie
        else:
            outcome = cond[(player_choice, red_choice)]

        if outcome is True:
            await self.bot.say("{} You win {}!"
                               "".format(red_choice.value, author.mention))
        elif outcome is False:
            await self.bot.say("{} You lose {}!"
                               "".format(red_choice.value, author.mention))
        else:
            await self.bot.say("{} We're square {}!"
                               "".format(red_choice.value, author.mention))

    @commands.command(aliases=["sw"], pass_context=True)
    async def stopwatch(self, ctx):
        """Starts/Stop stopwatch"""
        author = ctx.message.author
        if not author.id in self.stopwatches:
            self.stopwatches[author.id] = int(time.perf_counter())
            await self.bot.say(author.mention + " Stopwatch started!")
        else:
            tmp = abs(self.stopwatches[author.id] - int(time.perf_counter()))
            tmp = str(datetime.timedelta(seconds=tmp))
            await self.bot.say(author.mention + " Stopwatch stopped! Time: **" + tmp + "**")
            self.stopwatches.pop(author.id, None)

    @commands.command()
    async def lmgtfy(self, *, search_terms : str):
        """Creates a lmgtfy link"""
        search_terms = escape_mass_mentions(search_terms.replace(" ", "+"))
        await self.bot.say("https://lmgtfy.com/?q={}".format(search_terms))

    @commands.command(pass_context=True, no_pm=True)
    async def userinfo(self, ctx, *, user: discord.Member=None):
        """Shows user's informations"""
        author = ctx.message.author
        server = ctx.message.server

        if not user:
            user = author

        roles = [x.name for x in user.roles if x.name != "@everyone"]

        joined_at = self.fetch_joined_at(user, server)
        since_created = (ctx.message.timestamp - user.created_at).days
        since_joined = (ctx.message.timestamp - joined_at).days
        user_joined = joined_at.strftime("%d %b %Y %H:%M")
        user_created = user.created_at.strftime("%d %b %Y %H:%M")
        member_number = sorted(server.members,
                               KeyboardInterrupt=lambda m: m.joined_at).index(user) + 1
        created_on = "{}\n({} days ago)".format(user_created, since_created)
        joined_on = "{}\n({} days ago)".format(user_joined, since_joined)

        game = "Chilling in {} status".format(user.status)

        if user.game is None:
            pass
        elif user.game.url is None:
            game = "Playing {}".format(user.game)
        else:
            game = "Streaming: [{}]({})".format(user.game, user.game.url)

        if roles:
            roles = sorted(roles, key=[x.name for x in server.role_hierarchy if x.name != "@everyone"].index)
            roles = ", ".join(roles)
        else:
            roles = "None"

        data = discord.Embed(description=game, colour=user.colour)
        data.add_field(name="Joined Discord on", value=created_on)
        data.add_field(name="Joined this server on", value=joined_on)
        data.add_field(name="Roles", value=roles, inline=False)
        data.set_footer(text="Member #{} | User ID:{}"
                        "".format(member_number, user.id))
        name = str(user)
        name = " ~ ".join((name, user.nick)) if user.nick else name

        if user.avatar_url:
            data.set_author(name=name, url=user.avatar_url)
            data.set_thumbnail(url=user.avatar_url)
        else:
            data.set_author(name=name)

        try:
            await self.bot.say(embed=data)
        except discord.HTTPException:
            await self.bot.say("I need the 'Embed Links' permission to send this.")

        
        print('{0.author} executed command userinfo')

    @commands.command(pass_context=True, no_pm=True)
    async def poll(self, ctx, *text):
        """Starts/stops a poll
        
        Usage example:
        poll Is this a poll?;Yes;No;Maybe
        poll stop"""
        message = ctx.message
        if len(text) == 1:
            if text[0].lower() == "stop":
                await self.endpoll(message)
                return
        if not self.getPollByChannel(message):
            check = " ".join(text).lower()
            if "@everyone" in check or "@here" in check:
                await self.bot.say("Nice try.")
                return
            p = NewPoll(message, " ".join(text), self)
            if p.valid:
                self.poll_sessions.append(p)
                await p.start()
            else:
                await self.bot.say("poll question:optional;optional2 (...)")
        else:
            await self.bot.say("A poll is already ongoing in this channel.")

    async def endpoll(self, message):
        if self.getPollByChannel(message):
            p = self.getPollByChannel(message)
            if p.author == message.author.id: # or isMemberAdmin(message)
                await self.getPollByChannel(message).endPoll()
            else:
                await self.bot.say("Only admins and the author can stop the poll.")
        else:
            await self.bot.say("There's no poll ongoing in this channel.")

    def getPollByChannel(self, message):
        for poll in self.poll_sessions:
            if poll.channel == message.channel:
                return poll
        return False

    async def check_poll_votes(self, message):
        if message.author.id != self.bot.userinfo.id:
            if self.getPollByChannel(message):
                self.hetPollByChannel(message).checkAnswer(message)

    def fetch_joined_at(self, user, server):
        """Just a special case for someone special :^)"""
        if user.id == "96130341705637888" and server.id == "133049272517001216":
            return datetime.datetime(2016, 1, 10, 6, 8, 4, 4433000)
        else:
            return user.joined_at

class NewPoll():
    def __init__(self, message, text, main):
        self.channel = message.channel
        self.author = message.author.id
        self.client = main.bot
        self.poll_sessions = main.poll_sessions
        msg = [ans.strip() for ans in text.split(";")]
        if len(msg) < 2: # Need at least one question and 2 choices
            self.valid = False
            return None
        else:
            self.valid = True
        self.already_voted = []
        self.question = msg[0]
        self.remove(self.question)
        self.answers = {}
        i = 1 
        for answer in msg : # {id : {answer, votes}}
            self.answers[i] = {"ANSWER" : answer, "VOTES" : 0}
            i += 1

    async def start(self):
        msg = "**POLL STARTED!**\n\n{}\n\n".format(self.question)
        for id, data in self.answers.items():
            msg += "*{}. - *{}*\n".format(id, data["ANSWER"])
        msg += "\nType the number to vote!"
        await self.client.send_message(self.channel, msg)
        await asyncio.sleep(settings["POLL_DURATION"])
        if self.valid:
            await seld.endPoll()

    async def endPoll(self):
        self.valid = Falsemsg = "**POLL ENDED!**\n\n{}\n\n".format(self.question)
        for id, data in self.answers.items():
            msg += "*{}* - {}\n".format(data["ANSWER"], str(data["VOTES"]))
        msg += "\nType the number to vote!"
        await self.client.send_message(self.channel, msg)
        self.poll_sessions.remove(self)

    def checkAnswer(self, message):
        try:
            i = int(message.content)
            if i in self.answers.keys():
                if message.author.id not in self.already_voted:
                    data = self.answers[i]
                    data["VOTES"] += 1
                    self.answers[i] = data
                    self.already_voted.append(message.author.id)
        except ValueError:
                pass
    
def setup(bot):
    n = General(bot)
    bot.add_listener(n.check_poll_votes, "on_message")
    bot.add_cog(n)