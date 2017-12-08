import asyncio
from scripts import DiscordBot
COMMAND = '_reload_config'


@asyncio.coroutine
def main(message, discord_object: DiscordBot.DiscordBot):
    discord_object.get_json_properties()
    discord_object.load_commands()
    yield from discord_object.send_message(message.channel, message.author.mention + ' config.json reparsed.')