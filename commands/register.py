import asyncio
from scripts import DiscordBot
from discord import Message
from threading import Thread
COMMAND = 'register'
REGEX = {'a': ['ä', 'à', 'á'], 'e': ['è', 'é', 'ë'], 'i': ['ï', 'ì', 'í'], 'o': ['ò', 'ó', 'ö', 'ø'],
         'u': ['ú', 'ù', 'ü'], 'y': ['ý']}


@asyncio.coroutine
def main(message: Message, discord_object: DiscordBot.DiscordBot):
    message_data = discord_object.parse_message(message.content)
    if len(message_data) == 2:
        name = message_data[1]
        ss = 'oceaniaGuildActivity'
        ws = 'Oceania'
        local_id = discord_object.locals[COMMAND][ss][ws]['discordID']
        local_name = discord_object.locals[COMMAND][ss][ws]['Capitalized']
        local_ez = discord_object.locals[COMMAND][ss][ws]['eznameUpper']

        if str(message.author.id) in local_id:
            index = discord_object.locals[COMMAND][ss][ws]['discordID'].index(str(message.author.id))
            name = discord_object.locals[COMMAND][ss][ws]['Name'][index]
            yield from discord_object.send_message(message.channel, message.author.mention + ' You are already registered as {}.'.format(name))
        elif (name.upper() in local_name and local_id[local_name.index(name.upper())] != '') or (name.upper() in local_ez and local_id[local_ez.index(name.upper())] != ''):
            yield from discord_object.send_message(message.channel, message.author.mention + ' {} is already a registered IGN.'.format(name))
        else:
            editable = yield from discord_object.send_message(message.channel, message.author.mention + ' You are about to be registered as {}. Type *confirm to continue or *cancel to cancel.'.format(name))
            yield from get_reply(message, discord_object, editable)


@asyncio.coroutine
def confirmed(message: Message, discord_object: DiscordBot.DiscordBot, editable: Message):
    ss = 'oceaniaGuildActivity'
    ws = 'Oceania'
    message_data = discord_object.parse_message(message.content)
    name = message_data[1]
    local_id = discord_object.locals[COMMAND][ss][ws]['discordID']
    local_names = discord_object.locals[COMMAND][ss][ws]['Capitalized']
    local_ez_names = discord_object.locals[COMMAND][ss][ws]['eznameUpper']
    last_pos = discord_object.locals[COMMAND][ss][ws]['lastpos']
    if len(message_data) == 2:
        ezname = replace_special_chars(name)
        if message.author.id not in local_id and name not in local_names and name not in local_ez_names:
            if name.upper() in discord_object.locals[COMMAND][ss][ws]['Capitalized']:
                index = discord_object.locals[COMMAND][ss][ws]['Capitalized'].index(name.upper()) + 2
                start = (index, 4)
                end = (index, 7)
                data = [message.author.id, '', ezname, ezname.upper(), discord_object.get_current_day()]
                discord_object.spreadsheet_accessor.write_range(ss, ws, start, end, data)
                discord_object.locals[COMMAND][ss][ws]['discordID'][index] = message.author.id
                discord_object.locals[COMMAND][ss][ws]['ezname'][index] = ezname
                discord_object.locals[COMMAND][ss][ws]['eznameUpper'][index] = ezname.upper()
                yield from discord_object.edit_message(editable, message.author.mention + ' Registration successful.')
            elif name.upper() in discord_object.locals[COMMAND][ss][ws]['eznameUpper']:
                index = discord_object.locals[COMMAND][ss][ws]['eznameUpper'].index(name.upper()) + 2
                start = (index, 1)
                end = (index, 8)
                data = [name, name.upper(), '', message.author.id, '', ezname, ezname.upper(), discord_object.get_current_day()]
                discord_object.spreadsheet_accessor.write_range(ss, ws, start, end, data)
                discord_object.locals[COMMAND][ss][ws]['discordID'][index] = message.author.id
                discord_object.locals[COMMAND][ss][ws]['Name'][index] = name
                discord_object.locals[COMMAND][ss][ws]['Capitalized'][index] = name.upper()
                discord_object.locals[COMMAND][ss][ws]['ezname'][index] = ezname
                discord_object.locals[COMMAND][ss][ws]['eznameUpper'][index] = ezname.upper()
                yield from discord_object.edit_message(editable, message.author.mention + ' Registration successful.')
            else:
                start = (last_pos, 1)
                end = (last_pos, 8)
                data = [name, name.upper(), '', message.author.id, '', ezname, ezname.upper(), discord_object.get_current_day()]
                discord_object.spreadsheet_accessor.write_range(ss, ws, start, end, data)
                discord_object.locals[COMMAND][ss][ws]['discordID'].append(message.author.id)
                discord_object.locals[COMMAND][ss][ws]['Name'].append(name)
                discord_object.locals[COMMAND][ss][ws]['Capitalized'].append(name.upper())
                discord_object.locals[COMMAND][ss][ws]['ezname'].append(ezname)
                discord_object.locals[COMMAND][ss][ws]['eznameUpper'].append(ezname.upper())
                discord_object.locals[COMMAND][ss][ws]['lastpos'] += 1
                yield from discord_object.edit_message(editable, message.author.mention + ' Registration successful.')


@asyncio.coroutine
def get_reply(message: Message, discord_object: DiscordBot.DiscordBot, editable):
    reply = yield from discord_object.wait_for_message(author=message.author, channel=message.channel)
    if reply.content == '*confirm':
        yield from confirmed(message, discord_object, editable)
    elif reply.content == '*cancel':
        pass
    else:
        yield from get_reply(message, discord_object, editable)


def replace_special_chars(name):
    for char in REGEX.keys():
        for replaceable in REGEX[char]:
            name = name.replace(replaceable, char)
    return name


def load_data(discord_object: DiscordBot.DiscordBot, arguments, location):
    discord_object.locals[COMMAND]['oceaniaGuildActivity'][location[0]][location[1]] = discord_object.spreadsheet_accessor.get_column_values(arguments[0], arguments[1], arguments[2], arguments[3], arguments[4])


@asyncio.coroutine
def fetch_data_to_local(discord_object: DiscordBot.DiscordBot):
    ss = 'oceaniaGuildActivity'
    spreadsheet = {ss: {'Oceania': {}}}
    thread_pool = []
    discord_object.spreadsheet_accessor.open_spreadsheet(ss, 'https://docs.google.com/spreadsheets/d/1VWg6INme20CV9BJnhgCLYbtlwnC3xl41Opz8Tzq9Auo/edit#gid=0')
    discord_object.spreadsheet_accessor.open_worksheet(ss, 'Oceania')
    arguments = [(ss, 'Oceania', 1, 1, False), (ss, 'Oceania', 2, 1, False), (ss, 'Oceania', 4, 1, False),
                 (ss, 'Oceania', 6, 1, False), (ss, 'Oceania', 7, 1, False)]
    pointer = [['Oceania', 'Name'], ['Oceania', 'Capitalized'], ['Oceania', 'discordID'], ['Oceania', 'ezname'], ['Oceania', 'eznameUpper']]

    spreadsheet[ss]['Oceania']['lastpos'] = len(discord_object.spreadsheet_accessor.get_column_values(ss, 'Oceania', 1, 0, True))
    discord_object.locals[COMMAND] = spreadsheet
    for x, argument in enumerate(arguments):
        thread = Thread(target=load_data, args=(discord_object, argument, pointer[x]))
        thread.setName(pointer[x][1])
        thread_pool.append(thread)
        thread.start()
    while len(thread_pool) > 0:
        removable = []
        for thread in thread_pool:
            if not thread.is_alive():
                removable.append(thread)
        for x in removable:
            print('thread ' + x.getName() + '  completed')
            thread_pool.pop(thread_pool.index(x))
