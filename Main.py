import os
from scripts import DiscordBot

client = DiscordBot.DiscordBot()
print('starting')
client.run(os.environ['dkey'])
client.close()
