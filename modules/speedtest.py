import discord
from discord.ext import commands

class Speedtest:
    """Speedtest for the bot's server"""

    def __init__(self, bot):
        self.bot = bot
        self.filepath = "data/speedtest/settings.json"
        self.ssettings = dataIO.load_json(self.filepath)

    def speed_test(self):
        return str(subprocess.check_output(['speedtest-cli'], stderr=subprocess.STDOUT))

    @commands.command(pass_context=True, no_pm=True)
    async def speedtest(self, ctx):
        try:
            channel = ctx.message.channel
            uthor = ctx.message.author
            user = author
            high = self.settings[author.id]['upperbound']
            low = self.settings[author.id]['lowerbound']
            multiplyer = (self.settings[author.id]['data_type'])
            message12 = await self.bot.say(" :stopwatch: **Running speedtest. This may take a while!** :stopwatch:")

            DOWNLOAD_RE = re.compile(r"Download: ([\d.]+) .bit")
            UPLOAD_RE = re.compile(r"Upload: ([\d.]+) .bit")
            PING_RE = re.compile(r"([\d.]+) ms")

            speedtest_result = await self.bot.loop.run_in_executor(None, self.speed_test)
            download = float(DOWNLOAD_RE.search(speedtest_result).group(1)) + float(multiplyer)
            upload = float(UPLOAD_RE.search(speedtest_result).group(1)) + float(multiplyer)
            ping = float(PING_RE.search(speedtest_result).group(1)) + float(multiplyer)

            message = 'Your speedtest results are'
            message_down = '**{}** mbps'.format(download)
            message_up = '**{}** mbps'.format(upload)
            message_ping = '**{}** ms'.format(ping)

            if download >= float(high):
                colour = 0x45FF00
                indicator = 'Fast'
            if download > float(low) and download < float(high):
                colour = 0xFF4500
                indicator = 'Fair'
            if download <= float(low):
                colour = 0xFF3A00
                indicator = 'Slow'

            embed = discord.Embed(colour=colour, description=message)
            embed.title = 'Speedtest Results'
            embed.add_field(name='Download', value=message_down)
            embed.add_field(name=' Upload', value=message_up)
            embed.add_field(name=' Ping', value=message_ping)
            embed.set_footer(text='The Bots Internet is pretty {}'.format(indicator))
            await self.bot.say(embed=embed)
        except KeyError:
            await self.bot.say('Please setup the speedtest settings using **{}parameters**'.format(ctx.prefix))

    @commands.command(pass_context=True, no_pm=False)
    async def parameters(self, ctx, high: int, low: int, units='bits'):
        """Settingss for the speedtest
        
        High stands for the value above which your download is considered fast.
        Low stands for the value above which your download is considered slow.
        units stands for units of measurement of speed, either megaBITS/s or megaBYTES/s (By default it is megaBITS/s)"""

        author = ctx.message.author
        self.settings[author.id] = {}
        unitz = ['bits', 'bytes']

        if units.lower() in unitz:
            if units == 'bits':
                self.settings[author.id].update({'data_type': '1'})
                dataIO.save_json(self.filepath, self.settings)
            else:
                self.settings[author.id].update({'data_type': '0.125'})
                dataIO.save_json(self.filepath, self.settings)

            if float(high) < float(low):
                await self.bot.say('Error High is less then low')
            else:
                self.settings[author.id].update({'upperbound': high})
                self.settings[author.id].update({'lowerbound': low})
                dataIO.save_json(self.filepath, self.settings)

                embed2 = discord.Embed(colour=0x45FF00, description='These are your settings')
                embed2.title = 'Speedtest Settings'
                embed2.add_field(name='High', value='{}'.format(high))
                embed2.add_field(name='Low', value='{}'.format(low))
                embed2.add_field(name='Units', value='mega{}/s'.format(units))
                await self.bot.say(embed=embed2)
        elif not units.lower() in unitz:
            await self.bot.say('Invalid Units Input')

def check_folder():
    if not os.path.exists("data/speedtest"):
        print("Creating data/speedtest folder")
        os.makedirs("data/speedtest")

def check_file():
    data = {}
    f = "data/speedtest/settings.json"
    if not dataIO.is_valid_json(f):
        print("Creating data/speedtest/settings.json")
        dataIO.save_json(f, data)

def setup(bot):
    check_folder()
    check_file()
    n = Speedtest(bot)
    vot.add_cog(n)
