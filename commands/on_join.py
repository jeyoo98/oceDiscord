import asyncio
from scripts import DiscordBot
COMMAND = 'on_join'


@asyncio.coroutine
def main(message, discord_object: DiscordBot.DiscordBot):
    non_default = discord_object.json_data['Commands']['on_join']['User-Defined']
    _default = discord_object.json_data['Commands']['on_join']['Default-Message']
    if non_default is not None:
        val = non_default
    else:
        val = _default
    yield from discord_object.send_message(message.channel, message.author.mention + ' on_join message:\n' + val)


def edit(message, discord_object: DiscordBot.DiscordBot):
    message_structure = discord_object.parse_message(message.content)
    if len(message_structure) != 3:
        yield from discord_object.send_message(message.channel, 'Invalid syntax')
    else:
        discord_object.json_data['Commands']['on_join']['User-Defined'] = message_structure[-1]
        discord_object.update_json()
        yield from discord_object.send_message(message.channel, 'Done updating')


def default(message, discord_object: DiscordBot.DiscordBot):
    discord_object.json_data['Commands']['on_join']['User-Defined'] = None
    discord_object.update_json()
    yield from discord_object.send_message(message.channel, 'Default message restored')

SUB_COMMANDS = {'edit': edit, 'default': default}
