import asyncio
from discord import Message
from scripts import DiscordBot
from threading import Thread
COMMAND = 'carryme'
CRA = ['cq', 'ccq', 'cvb', 'cp', 'cvel', 'cvell']
BOSSES = ['hmag', 'hellux', 'hhilla', 'cq', 'cp', 'cvb', 'cvel']
INDEX = {'cq': 1, 'ccq': 1, 'cp': 4, 'cvb': 7, 'cvel': 10, 'cvell': 10, 'hmag': 1, 'hellux': 4, 'hhilla': 7}
NAMES = {'cq': 'Chaos Crimson Queen', 'ccq': 'Chaos Crimson Queen',
         'cp': 'Chaos Pierre',
         'cvb': 'Chaos Von Bon',
         'cvel': 'Chaos Vellum', 'cvell': 'Chaos Vellum',
         'hmag': 'Hard Magnus',
         'hellux': 'Hell Gollux',
         'hhilla': 'Hard Hilla'}
PATCH = {'ccq': 'cq', 'cvell': 'cvel', 'cvb': 'cvb', 'cp': 'cp', 'hhilla': 'hhilla', 'hmag': 'hmag', 'hellux': 'hellux', 'cvel': 'cvel', 'cq': 'cq'}


@asyncio.coroutine
def main(message: Message, discord_object: DiscordBot.DiscordBot):
    yield from discord_object.send_message(message.channel, 'Type `*help carryme <command>` for a guide on how each command works.\n'
                                                            'Available commands:```\nbosses\ncancel\npos```')


@asyncio.coroutine
def pos(message: Message, discord_object: DiscordBot.DiscordBot):
    message_data = discord_object.parse_message(message.content)
    if len(message_data) == 2:
        boss_list = BOSSES
    elif len(message_data) == 3:
        boss_list = message_data[2]
    else:
        raise TypeError('Incorrect number of arguments')
    in_boss = {}
    try:
        name_index = discord_object.locals['register']['oceaniaGuildActivity']['Oceania']['discordID'].index(message.author.id)
        name = discord_object.locals['register']['oceaniaGuildActivity']['Oceania']['Name'][name_index]
        unrecognized = []
        for boss in boss_list:
            if boss in CRA:
                sheet = 'CRA'
            else:
                sheet = 'OTHER'
            try:
                if name in discord_object.locals[COMMAND]['oceaniaCarryQueue'][sheet][boss]:
                    in_boss[boss] = discord_object.locals[COMMAND]['oceaniaCarryQueue'][sheet][boss].index(name)
            except KeyError:
                unrecognized.append(boss)
                continue
        msg = ' You are currently in the boss queue for:\n```'
        for key in in_boss.keys():
            msg += '{}:{}{}\n'.format(NAMES[key], ''.join([' ']*(25-len(NAMES[key]))), in_boss[key])
        if len(unrecognized) > 0:
            msg += '```The following bosses were not recognized: {}'.format(', '.join(unrecognized))
        else:
            msg += '```'
        yield from discord_object.send_message(message.channel, message.author.mention + msg)
    except ValueError:
        yield from discord_object.send_message(message.channel, message.author.mention + ' You are not currently registered!')


@asyncio.coroutine
def done(message: Message, discord_object: DiscordBot.DiscordBot):
    data_message = discord_object.parse_message(message.content)
    thread_pool = []
    if len(data_message) == 4:
        editable = yield from discord_object.send_message(message.channel, message.author.mention + ' Updating carry sheet...')
        names = data_message[3]
        boss_list = data_message[2]
        local_data = discord_object.locals['register']['oceaniaGuildActivity']['Oceania']
        real_names = []
        not_found = []
        last_index = int(discord_object.locals[COMMAND]['oceaniaCarryQueue']['CARRYLOG']['length']) + 1
        today = '{} {}'.format(discord_object.get_current_day(), discord_object.get_current_time())
        for name in names:
            try:
                index = local_data['eznameUpper'].index(name.upper())
                name = local_data['Name'][index]
                if name != "":
                    real_names.append(name)
                else:
                    real_names.append(name)
            except ValueError:
                not_found.append(name)
        carry_index = local_data['discordID'].index(message.author.id)
        carry_name = local_data['Name'][carry_index]
        not_in_boss = {}
        done_bosses = []
        for boss_upper in boss_list:
            try:
                boss = PATCH[boss_upper.lower()]
                for name in real_names:
                    index = None
                    if boss in CRA:
                        sheet = 'CRA'
                    else:
                        sheet = 'OTHER'
                    if name in discord_object.locals[COMMAND]['oceaniaCarryQueue'][sheet][boss]:
                        index = discord_object.locals[COMMAND]['oceaniaCarryQueue'][sheet][boss].index(name)
                        discord_object.locals[COMMAND]['oceaniaCarryQueue'][sheet][boss].pop(index)
                    else:
                        if boss in not_in_boss.keys():
                            not_in_boss[boss].append(name)
                        else:
                            not_in_boss[boss] = [name]
                    if NAMES[boss] not in done_bosses:
                        done_bosses.append(NAMES[boss])
                    new_list = list(filter(None, discord_object.locals[COMMAND]['oceaniaCarryQueue'][sheet][boss])) + (len(real_names)) * ['']
                    start = (1, INDEX[boss])
                    end = (len(new_list), INDEX[boss])

                    thread1 = Thread(target=discord_object.spreadsheet_accessor.write_range, args=('oceaniaCarryQueue', sheet, start, end, new_list))
                    thread1.start()
                    thread_pool.append(thread1)

                    comment_list = discord_object.locals[COMMAND]['oceaniaCarryQueue'][sheet]['comment_' + boss]
                    if index is not None:
                        original_length = len(discord_object.locals[COMMAND]['oceaniaCarryQueue'][sheet][boss])
                        comment_list.pop(index)
                        comments = list(comment_list[:original_length] + len(real_names) * [''])
                        start = (1, INDEX[boss] + 2)
                        end = (len(comments), INDEX[boss] + 2)

                        thread2 = Thread(target=discord_object.spreadsheet_accessor.write_range, args=('oceaniaCarryQueue', sheet, start, end, comments))
                        thread2.start()
                        thread_pool.append(thread2)

                writer = list(filter(None, [today, carry_name, NAMES[boss]] + real_names + not_found))
                thread3 = Thread(target=discord_object.spreadsheet_accessor.write_range, args=('oceaniaCarryQueue', 'CARRYLOG', (last_index, 1), (last_index, 3 + len(real_names + not_found)), writer))
                thread3.start()
                thread_pool.append(thread3)

                discord_object.locals[COMMAND]['oceaniaCarryQueue']['CARRYLOG']['length'] += 1
                last_index += 1
            except KeyError:
                continue
            except UnboundLocalError:
                continue
            except Exception as e:
                raise e
        if len(done_bosses) > 0:
            msg = ' Done updating carry queue for {}.\n'.format(', '.join(done_bosses))
            if len(not_in_boss) > 0:
                temp = 'These names also did not appear in the boss list for the following bosses:\n'
                for boss in not_in_boss.keys():
                    temp += '{}: {}\n'.format(NAMES[boss], ', '.join(not_in_boss[boss]))
                msg += temp
            if len(not_found) > 0:
                msg += '\nThese names were not recognized:\n{}'.format(', '.join(not_found))
        else:
            msg = ' The carry queue was updated for no bosses. '
        yield from discord_object.edit_message(editable, message.author.mention + msg)
        for threads in thread_pool:
            threads.join()


@asyncio.coroutine
def cancel(message: Message, discord_object: DiscordBot.DiscordBot):
    data_message = discord_object.parse_message(message.content)
    local_id = discord_object.locals['register']['oceaniaGuildActivity']['Oceania']['discordID']
    thread_list = []
    if message.author.id in local_id:
        name_id = local_id.index(message.author.id)
        name = discord_object.locals['register']['oceaniaGuildActivity']['Oceania']['Name'][name_id]
        if len(data_message) == 3:
            boss_list = data_message[2]
            ss = 'oceaniaCarryQueue'
            cancelled = []

            for boss_upper in boss_list:
                boss = PATCH[boss_upper.lower()]

                if boss in CRA:
                    ws = 'CRA'
                else:
                    ws = 'OTHER'

                boss_queue = discord_object.locals[COMMAND][ss][ws][boss]

                if name in boss_queue:
                    cancelled.append(NAMES[boss])
                    index = boss_queue.index(name)

                    discord_object.locals[COMMAND][ss][ws][boss].pop(index)
                    discord_object.locals[COMMAND][ss][ws]['comment_' + boss].pop(index)

                    last_pos = len(discord_object.locals[COMMAND][ss][ws][boss])
                    new_list = list(filter(None, discord_object.locals[COMMAND][ss][ws][boss][index:last_pos])) + ['']
                    comment_list = discord_object.locals[COMMAND][ss][ws]['comment_' + boss][index:last_pos] + ['']

                    start = (index + 1, INDEX[boss])
                    end = (last_pos + 1, INDEX[boss])
                    thread1 = Thread(target=discord_object.spreadsheet_accessor.write_range, args=(ss, ws, start, end, new_list))
                    thread_list.append(thread1)
                    thread1.start()

                    thread2 = Thread(target=discord_object.spreadsheet_accessor.write_range, args=(ss, ws, (index + 1, INDEX[boss] + 2), (last_pos + 1, INDEX[boss] + 2), comment_list))
                    thread_list.append(thread2)
                    thread2.start()
            if len(cancelled) > 0:
                yield from discord_object.send_message(message.channel, message.author.mention + ' You have cancelled your carry for: {}'.format(', '.join(cancelled)))
            else:
                yield from discord_object.send_message(message.channel, message.author.mention + ' You were not registered for any boss carries.')
    for thread in thread_list:
        thread.join()


@asyncio.coroutine
def bosses(message: Message, discord_object: DiscordBot.DiscordBot):
    message_data = discord_object.parse_message(message.content)
    local_id = discord_object.locals['register']['oceaniaGuildActivity']['Oceania']['discordID']
    local_names = discord_object.locals['register']['oceaniaGuildActivity']['Oceania']['Name']
    thread_pool = []
    if message.author.id in local_id:
        if len(message_data) == 3:
            boss_list = message_data[2]
            username = local_names[local_id.index(str(message.author.id))]
            ss = 'oceaniaCarryQueue'
            already_in_list = []
            joined = []
            for boss_upper in boss_list:
                if ':' in boss_upper:
                    values = boss_upper.split(':', 1)
                    boss = values[0].lower()
                    comment = values[1]
                else:
                    boss = boss_upper.lower()
                    comment = ''
                if boss not in ['hellux', 'hmag']:
                    if boss in CRA:
                        sheet = 'CRA'
                    else:
                        sheet = 'OTHER'
                    if username not in discord_object.locals[COMMAND][ss][sheet][PATCH[boss]]:
                        row = len(discord_object.locals[COMMAND][ss][sheet][PATCH[boss]]) + 1
                        col = INDEX[PATCH[boss]]
                        thread = Thread(target=discord_object.spreadsheet_accessor.write_range, args=(ss, sheet, (row, col), (row, col+2), [username, '', comment], ))
                        thread_pool.append(thread)
                        thread.start()
                        joined.append(NAMES[PATCH[boss]])
                        discord_object.locals[COMMAND][ss][sheet][PATCH[boss]].append(username)
                    else:
                        already_in_list.append(NAMES[PATCH[boss]])
            if len(joined) > 0:
                x = ', '.join(joined)
                yield from discord_object.send_message(message.channel, message.author.mention + ' You have joined the boss queue for:\n'+x)
            if len(already_in_list) > 0:
                y = ', '.join(already_in_list)
                yield from discord_object.send_message(message.channel, message.author.mention + ' You are already in the boss queue for:\n'+y)
    else:
        yield from discord_object.send_message(message.channel, message.author.mention + ' You need to register first! Use *register (MapleIGN) to link your discord ID with your maple IGN.'
                                                                                       '\n Warning: You can only register your discord ID to one IGN.')
    for thread in thread_pool:
        thread.join()


def gp(message: Message, discord_object: DiscordBot.DiscordBot):
    pass


def load_data(discord_object: DiscordBot.DiscordBot, arguments, location):
    discord_object.locals[COMMAND]['oceaniaCarryQueue'][location[0]][location[1]] = discord_object.spreadsheet_accessor.get_column_values(arguments[0], arguments[1], arguments[2], filtered=arguments[3])


@asyncio.coroutine
def fetch_data_to_local(discord_object: DiscordBot.DiscordBot):
    ss = 'oceaniaCarryQueue'
    thread_pool = []
    spreadsheet = {ss: {'OTHER': {}, 'CRA': {}, 'CARRYLOG': {}}}
    discord_object.spreadsheet_accessor.open_spreadsheet(ss, 'https://docs.google.com/spreadsheets/d/1ojGWmWtgqZuwfSgIMJsvFf00DqayWoCJtwUhrYEmes8/edit#gid=1152797146')
    discord_object.spreadsheet_accessor.open_worksheet(ss, 'OTHER')
    discord_object.spreadsheet_accessor.open_worksheet(ss, 'CRA')
    discord_object.spreadsheet_accessor.open_worksheet(ss, 'CARRYLOG')
    arguments = [(ss, 'OTHER', 1, True), (ss, 'OTHER', 3, False), (ss, 'OTHER', 4, True), (ss, 'OTHER', 6, False), (ss, 'OTHER', 7, True), (ss, 'OTHER', 9, False), (ss, 'CRA', 1, True),
                 (ss, 'CRA', 3, False), (ss, 'CRA', 4, True), (ss, 'CRA', 6, False), (ss, 'CRA', 7, True), (ss, 'CRA', 9, False), (ss, 'CRA', 10, True), (ss, 'CRA', 12, False)]

    pointer = [['OTHER', 'hmag'], ['OTHER', 'comment_hmag'], ['OTHER', 'hellux'], ['OTHER', 'comment_hellux'],
               ['OTHER', 'hhilla'], ['OTHER', 'comment_hhilla'], ['CRA', 'cq'], ['CRA', 'comment_cq'],
               ['CRA', 'cp'], ['CRA', 'comment_cp'], ['CRA', 'cvb'], ['CRA', 'comment_cvb'],
               ['CRA', 'cvel'], ['CRA', 'comment_cvel']]

    discord_object.locals[COMMAND] = spreadsheet
    print('starting threads')
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
            print('thread ' + x.getName() + ' completed')
            thread_pool.pop(thread_pool.index(x))
    spreadsheet[ss]['CARRYLOG']['length'] = len(discord_object.spreadsheet_accessor.get_column_values(ss, 'CARRYLOG', 1))

SUB_COMMANDS = {'bosses': bosses, 'cancel': cancel, 'pos': pos, 'done': done}
