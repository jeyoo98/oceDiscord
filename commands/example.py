import asyncio
from scripts import DiscordBot
COMMAND = 'example'


@asyncio.coroutine
def main(message, discord_object: DiscordBot.DiscordBot):
    yield from discord_object.send_message(message.channel, message.author.mention + ' Hi!')
