import asyncio
import os
import yaml
from scripts import DiscordBot
COMMAND = 'help'


@asyncio.coroutine
def main(message, discord_object: DiscordBot.DiscordBot):
    parameters = discord_object.parse_message(message.content)[1:]

    cwd = os.getcwd()
    os.chdir('commands/')
    yml_file = open('help.yml', 'r')
    data = yaml.load(yml_file)
    os.chdir(cwd)

    if len(parameters) > 0:
        if parameters[0] in data['help'].keys():
            help_string = ''
            try:
                help_string = find_message(parameters, data['help'])
                if isinstance(help_string, dict):
                    help_string = help_string['default']
            except:
                pass
            if help_string != -1:
                formatted = discord_object.format_string(help_string, message)
                yield from discord_object.send_message(message.channel, formatted)
    else:
        base_string = discord_object.format_string(data['help']['help'], message)
        available = []
        for c in discord_object.commands:
            if discord_object.has_permission(message.author.top_role, c) and c in data['help'].keys():
                available.append(c)
        available.sort()
        commands = '`{}`'.format('`\n`'.join(available))
        yield from discord_object.send_message(message.channel, base_string + '\n' + commands)


def find_message(iterable, dictionary):
    if len(iterable) > 1:
        if iterable[0] in dictionary.keys():
            return find_message(iterable[1:], dictionary[iterable[0]])
        return -1
    if iterable[0] in dictionary.keys():
        return dictionary[iterable[0]]
    return -1
