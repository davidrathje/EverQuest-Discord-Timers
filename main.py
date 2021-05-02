import discord
from discord.ext import tasks
from pygtail import Pygtail
import glob
import re
from dateutil.parser import parse
from dateutil.tz import UTC
from configparser import ConfigParser

# GET SETTINGS FROM CONFIG
parser = ConfigParser()
parser.read('config.ini')

PATH = parser.get('SETTINGS', 'PATH') + 'eqlog_*_P1999PVP.txt'
CHANNEL = int(parser.get('DISCORD', 'CHANNEL'))

# POPULATE NPC LIST
NPC_LIST = []
for key, npc in parser.items('NPC_LIST'):
    NPC_LIST.append(npc)

# REGEX FOR PARSING LOG FILE AGAINST NPC LIST.
npc_re = re.compile(r'^\[[^]]+\] ((You have slain ({}))|(({}) has been slain by [a-zA-Z ]+))!$'
                    .format('|'.join(NPC_LIST), '|'.join(NPC_LIST)))

# CREATE DISCORD BOT WITH BACKGROUND TASK
class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tail_files.start()

    async def on_ready(self):
        print(f'Connected to {self.user.name}\n')
        print(f'Parsing {PATH}\n')
        print('Current NPC list:')
        for item in NPC_LIST:
            print('  ' + item)
        print('\n')

    # CREATE TASK THAT RUNS EVERY 10 SECONDS
    @tasks.loop(seconds=10)
    async def tail_files(self):
        for files in glob.glob(PATH):
            for line in Pygtail(files, read_from_end=True):
                if npc_re.match(line):
                    # CONVERT TIMESTAMP TO GMT AND REPLACE ORIGINAL TIME STAMP.
                    utc_time = parse(line[1:25]).astimezone(UTC).strftime("%a %b %d %H:%M:%S %Y")
                    new_line = line.replace(line[1:25], utc_time)

                    # SEND INFO TO DISCORD CHANNEL
                    channel = self.get_channel(CHANNEL)
                    await channel.send('killed ' + new_line)
                    print(new_line)

    @tail_files.before_loop
    async def before_tail_files(self):
        await self.wait_until_ready()

# CONNECT TO BOT
client = MyClient()
client.run('YOUR-TOKEN')
