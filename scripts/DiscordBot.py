import discord
import os
import logging
import asyncio
import json
import sys
import threading
import importlib.util
import pytz
import praw
import random
import feedparser
import html2text
from queue import Queue
from json import JSONDecodeError
from datetime import datetime
from scripts import Zone
from scripts import SpreadsheetAccessor
from scripts import JSONLoader


class DiscordBot(discord.Client):
    def __init__(self, shell=False):
        if not shell:
            discord.Client.__init__(self)
            # Timezone
            self.timezone = Zone.Zone(10, False, 'AEST')
            self.localtime = pytz.timezone('Australia/Sydney')

            self.five_alert = False
            self.one_alert = False
            self.alert_times = [[1, 3, 5, 7, 9, 19, 21, 23], [0, 2, 4, 6, 8, 18, 20, 22]]
            self.alert_clear = []

            self.todayTZ = self.localtime.localize(datetime.today())

            self.kritiasChannel = discord.Channel(id='386135531483955220', server=discord.Server(id='260325692040937472'))
            self.kritiasWatch = discord.Role(id='386135324918808576', server=discord.Server(id='260325692040937472'))

            # Logger
            self.logger = None

            # JSON Properties
            self.json_data = None
            self.get_json_properties()
            self.commands = []
            self.sub_commands = []
            self.command_level = {}
            self.load_commands()
            for x in self.json_data['Commands'].keys():
                self.sub_command_crawler(x)

            # Spreadsheet Accessor
            self.spreadsheet_accessor = SpreadsheetAccessor.SpreadsheetAccessor(self.logger)
            self.locals = {}

            # Reddit API

            redditAPI = None
            self.subreddits = []

            self.load_subreddit_pages()
            self.pool = {}

            self.reddit = praw.Reddit(client_id=os.environ['rapi_client_id'],
                                      client_secret=os.environ['rapi_client_secret'],
                                      username=os.environ['rapi_username'],
                                      password=os.environ['rapi_password'],
                                      user_agent=os.environ['rapi_user_agent'])

            # Commands and command handlers
            self.command_queue = Queue()

            for x in range(4):
                t = threading.Thread(target=self.message_worker)
                t.daemon = True
                t.start()
            self.local_data_queue = Queue()
            # Local data creator handlers
            for x in range(4):
                t = threading.Thread(target=self.local_worker)
                t.daemon = True
                t.start()

            self.prefix = self.json_data['Prefix']
            self.load_to_local()
            self.loop.create_task(self.kritias_alert())
            self.loop.create_task(self.spreadsheet_connection_refresher())
            self.loop.create_task(self.daily_puzzle())
            for x, entry in enumerate(self.subreddits):
                self.loop.create_task(self.submission_puller(entry))

    '''-----------------------------------------------------------------------------------------------------------------
                                                                            Instantiation Methods
    -----------------------------------------------------------------------------------------------------------------'''
    def create_logger(self):
        current_time = datetime.now(self.timezone).strftime('%H.%M.%S')
        current_day = 'DiscordBot-{}-{}-{} {}.log'.format(datetime.now().day, datetime.now().month, datetime.now().year, current_time)

        if not os.path.exists(os.getcwd()+'/logs/'):
            os.makedirs(os.getcwd()+'/logs/')

        prev_dir = os.getcwd()
        os.chdir(os.getcwd()+'/logs/')
        self.logger = logging.getLogger('discord')
        self.logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler(filename=current_day, encoding='utf-8', mode='w')
        handler.setFormatter(logging.Formatter('{} %(asctime)s: %(levelname)s:\t%(message)s'.format(self.get_current_day())))
        self.logger.addHandler(handler)
        os.chdir(prev_dir)

    def get_json_properties(self):
        try:
            with open('config.json', 'r') as json_file:
                self.json_data = json.load(json_file)
        except FileNotFoundError as e:
            self.logger.warning(str(e)[len('{Errno 22]'):])
            self.logger.warning('creating default config then exiting.')
            JSONLoader.CreateJSON()
            sys.exit()
        except JSONDecodeError as e:
            self.logger.critical(e)
            sys.exit()

    def update_json(self):
        with open('config.json', 'w') as json_file:
            entries = json.dumps(self.json_data)
            data = json.loads(entries)
            json.dump(data, json_file, indent=4)

    def load_commands(self):
        for entries in self.json_data['Commands']:
            if self.json_data['Commands'][entries]['Enabled']:
                self.commands.append(entries)

    def load_subreddit_pages(self):
        self.spreadsheet_accessor.open_spreadsheet('SubredditList',
                                                   'https://docs.google.com/spreadsheets/d/16qpIkI_Hieat2CQzC0e01iO1X8JVQ-VOMgnqh4ealV4/edit?usp=sharing')
        self.spreadsheet_accessor.open_worksheet('SubredditList', 'main')
        channels = self.spreadsheet_accessor.get_column_values('SubredditList', 'main', 1, 1)
        for x, channel in enumerate(channels):
            self.subreddits.append([channel, self.spreadsheet_accessor.get_row_values('SubredditList', 'main', x + 2, 1)])

    def sub_command_crawler(self, command):
        self.command_level[command] = {command: 0}
        if 'Sub-Commands' in self.json_data['Commands'][command].keys():
            for sub_command in self.json_data['Commands'][command]['Sub-Commands'].keys():
                if sub_command not in self.sub_commands and self.json_data['Commands'][command]['Sub-Commands'][sub_command]['Enabled']:
                    self.sub_commands.append(sub_command)
                    self.command_level[command][sub_command] = 1
                    self.crawl_through(self.json_data['Commands'][command]['Sub-Commands'], command, sub_command, 2)

    @asyncio.coroutine
    def spreadsheet_connection_refresher(self):
        yield from self.wait_until_ready()
        while not self.is_closed:
            yield from asyncio.sleep(600)
            self.spreadsheet_accessor.load_credentials()

    @asyncio.coroutine
    def load_to_local(self):
        yield from self.wait_until_ready()
        for command in self.commands:
            if 'Locals' in self.json_data['Commands'][command]:
                if self.json_data['Commands'][command]['Locals']:
                    yield from self.create_local_data(command)
                    # self.local_data_queue.put(command)

    @asyncio.coroutine
    def create_local_data(self, command):
        script = self.get_script(command)
        location = os.getcwd() + "/commands/" + script
        spec = importlib.util.spec_from_file_location("commands." + script[-3:], location)
        main_attr = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(main_attr)
        yield from main_attr.fetch_data_to_local(self)
        del spec
        del main_attr

    @asyncio.coroutine
    def on_ready(self):
        while not self.local_data_queue.empty():
            yield from asyncio.sleep(5)
        print('ready')
    '''-----------------------------------------------------------------------------------------------------------------
                                                                            End Instantiation Methods
    -----------------------------------------------------------------------------------------------------------------'''

    '''-----------------------------------------------------------------------------------------------------------------
                                                                            Reddit/RSS API
    -----------------------------------------------------------------------------------------------------------------'''
    @asyncio.coroutine
    def submission_puller(self, entry):
        yield from self.wait_until_ready()

        channel = discord.Channel(server=discord.Server(id='260325692040937472'), id=entry[0])

        self.pool[entry[0]] = entry[1][:]
        b = True
        while not self.is_closed:
            if self.localtime.localize(datetime.today()).minute in [0, 15, 30, 45]:
                if b:
                    b = False
                    if len(self.pool[entry[0]]) == 0:
                        self.pool[entry[0]] = entry[1][:]

                    pop_index = random.randint(0, len(self.pool[entry[0]]) - 1)
                    selection = self.pool[entry[0]].pop(pop_index)

                    for submission in self.reddit.subreddit(selection).hot(limit=10):
                        if not submission.is_self:
                            yield from self.send_message(channel, submission.url)
                            submission.hide()
                            break
            else:
                if not b:
                    b = True
                    self.todayTZ = self.localtime.localize(datetime.today())
            yield from asyncio.sleep(30)

    @asyncio.coroutine
    def daily_puzzle(self):
        yield from self.wait_until_ready()

        channel = discord.Channel(server=discord.Server(id='260325692040937472'), id='314032599838359553')

        parser = html2text.HTML2Text()
        parser.ignore_links = True
        done = False

        while not self.is_closed:
            if self.localtime.localize(datetime.today()).hour == 10:
                if self.localtime.localize(datetime.today()).minute == 0:
                    feed = feedparser.parse('https://thinkwitty.com/feed')
                    index = 0
                    while not done and index < 5:
                        if feed.entries[index]['tags'][1]['term'] == 'Puzzle of the day':
                            done = True
                            text = parser.handle(feed.entries[4]['content'][0]['value'])
                            index = text.find('https://')
                            end = index

                            for x, val in enumerate(text[index:]):
                                if val == '?':
                                    end += x
                                    break

                            image_link = text[index:end].replace('\n', '')
                            yield from self.send_message(channel, image_link)
                        else:
                            index += 1
            else:
                if not done:
                    done = False
                    self.todayTZ = self.localtime.localize(datetime.today())
            yield from asyncio.sleep(30)

    '''-----------------------------------------------------------------------------------------------------------------
                                                                            End Reddit API
    -----------------------------------------------------------------------------------------------------------------'''

    '''-----------------------------------------------------------------------------------------------------------------
                                                                            Message/Command Handler
    -----------------------------------------------------------------------------------------------------------------'''

    @asyncio.coroutine
    def on_message(self, message):
        if message.content[0:len(self.prefix)] == self.prefix:
            if message.content[len(self.prefix):].split(' ', 1)[0] in self.commands:
                if self.validate_command(message):
                    print('{}: {}'.format(message.author, message.content))
                    self.command_queue.put(message)

    @asyncio.coroutine
    def run_command(self, message):
        command_structure = self.parse_message(message.content)
        commands = []
        try:
            possible_sub_commands = self.get_sub_commands(command_structure[0][len(self.json_data['Prefix']):], self.json_data)
            for entry in command_structure:
                if self.prefix in entry:
                    if entry[len(self.json_data['Prefix']):] in self.json_data['Commands'].keys():
                        commands.append(entry[len(self.prefix):])
                elif entry in possible_sub_commands:
                    commands.append(entry)
            if self.check_permission(message.author, commands):
                script = self.get_script(commands[0])
                location = os.getcwd() + "/commands/" + script
                spec = importlib.util.spec_from_file_location("commands." + script[-3:], location)
                main_attr = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(main_attr)
                if len(commands) > 1 and len(possible_sub_commands) > 0:
                    self.loop.create_task(main_attr.SUB_COMMANDS[commands[-1]](message, self))
                else:
                    self.loop.create_task(main_attr.main(message, self))
            else:
                yield from self.forbidden(message)
        except Exception as e:
            if isinstance(e, FileNotFoundError):
                self.json_data['Commands'][commands[0]]['Enabled'] = False
                self.update_json()
            raise Exception(e)

    @asyncio.coroutine
    def on_member_join(self, member):
        non_default = self.json_data['Commands']['on_join']['User-Defined']
        default = self.json_data['Commands']['on_join']['Default-Message']
        server = discord.Server(id=member.server.id, name=member.server)
        server.name = member.server.name
        server.id = member.server.id
        container = discord.Message(author={'id': member.id, 'server': member.server.id}, reactions=[], content='')
        container.server = server
        container.author.name = member.name
        if non_default is not None:
            yield from self.send_message(discord.Channel(server=server, id='346821860589305858'), self.format_string(non_default, container))
        else:
            yield from self.send_message(discord.Channel(server=server, id='346821860589305858'), self.format_string(default, container))

    def validate_command(self, message):
        message_structure = self.parse_message(message.content)
        base_command = None
        sub_command_list = []
        structure = []
        for command in message_structure:
            if self.json_data['Prefix'] in command:
                c = command[len(self.json_data['Prefix']):]
                if c in self.commands:
                    base_command = c
                    structure.append(c)
            elif command in self.get_sub_commands(base_command, self.json_data):
                sub_command_list.append(command)
                structure.append(command)

        valid = True
        for x, command in enumerate(structure):
            if command in self.command_level[base_command].keys():
                if self.command_level[base_command][command] != x:
                    valid = False
        return valid

    def parse_message(self, message):  # Messy - needs cleanup
        char_pos = {'[': [], ']': []}
        level = 0
        last_space = 0
        literal = False
        lit = ''

        parsed = []

        for x, char in enumerate(message):
            if char == '[':
                if level == 0:
                    char_pos['['].append(x)
                level += 1
            elif char == ']':
                if level == 1:
                    char_pos[']'].append(x)
                level -= 1

        for x, char in enumerate(message):
            if char == '[':
                if level == 0:
                    parsed.append(message[last_space:x])
                    parsed.append(self.parse_message(message[char_pos['['][0] + 1:char_pos[']'][0]]))
                    last_space += len(message[char_pos['['][0] + 1:char_pos[']'][0]]) + 2
                    char_pos['['].pop(0)
                    char_pos[']'].pop(0)
                level += 1
            elif char == ']':
                last_space = x + 1
                if level > 0:
                    level -= 1
            elif char == " ":
                if not literal:
                    if level == 0:
                        parsed.append(message[last_space:x])
                        last_space = x + 1
                elif literal:
                    if level == 0:
                        lit += char
            elif char == '"':
                if not literal:
                    if level == 0:
                        literal = True
                elif literal:
                    if level == 0:
                        literal = False
                        parsed.append(lit)
                        last_space += len(lit) + 2
                        lit = ''
            elif x == len(message) - 1:
                parsed.append(message[last_space:x + 1])
            else:
                if literal:
                    if level == 0:
                        lit += char
        return list(filter(None, parsed))

    def crawl_through(self, dictionary, command, sub_command, level):
        if 'Sub-Commands' in dictionary[sub_command].keys():
            for sub in dictionary[sub_command]['Sub-Commands'].keys():
                if sub not in self.sub_commands and dictionary[sub_command]['Sub-Commands'][sub]['Enabled']:
                    self.sub_commands.append(sub)
                    self.command_level[command][sub] = level
                    self.crawl_through(dictionary[sub_command]['Sub-Commands'], command, sub, level + 1)

    def get_sub_commands(self, command, dictionary):
        commands = []
        if dictionary == self.json_data:
            if command in dictionary['Commands'].keys():
                if 'Sub-Commands' in dictionary['Commands'][command]:
                    for sub_command in dictionary['Commands'][command]['Sub-Commands']:
                        commands += self.get_sub_commands(sub_command, dictionary['Commands'][command]['Sub-Commands'])
        else:
            if 'Sub-Commands' in dictionary[command].keys():
                for sub_command in dictionary['Commands'][command]['Sub-Commands']:
                    commands += self.get_sub_commands(sub_command, dictionary['Sub-Commands'][command])
            else:
                commands.append(command)
        return commands

    @asyncio.coroutine
    def forbidden(self, message):
        string = ' You do not have the required permissions for that command'
        yield from self.send_message(message.channel, message.author.mention + string)
    '''                                                                     End Message/Command Handler
    '''

    '''                                                                     Utility Methods
    '''
    @asyncio.coroutine
    def kritias_alert(self):
        yield from self.wait_until_ready()
        self.todayTZ = self.localtime.localize(datetime.today())

        while not self.is_closed:
            if self.localtime.localize(datetime.today()).minute == 0:
                if self.localtime.localize(datetime.today()).hour in self.alert_times[bool(not bool(self.todayTZ.dst()))]:
                    if not self.five_alert:
                        self.five_alert = True
                        ret = yield from self.send_message(self.kritiasChannel, self.kritiasWatch.mention + ' Invasion is about to commence in 5 minutes.')
                        self.alert_clear.append(ret)
            elif self.localtime.localize(datetime.today()).minute == 4:
                if datetime.now().time().hour in self.alert_times[bool(not bool(self.todayTZ.dst()))]:
                    if not self.one_alert:
                        self.one_alert = True
                        ret = yield from self.send_message(self.kritiasChannel, self.kritiasWatch.mention + ' Invasion is about to commence in 1 minute.')
                        self.alert_clear.append(ret)
            if self.localtime.localize(datetime.today()).minute == 6:
                if self.five_alert or self.one_alert:
                    self.five_alert = False
                    self.one_alert = False
                if len(self.alert_clear) > 0:
                    for msg in self.alert_clear:
                        yield from self.delete_message(msg)
                    self.alert_clear = []
            yield from asyncio.sleep(5)  # run every 5 seconds

    @staticmethod
    def get_current_day():
        return '{}/{}/{}'.format(datetime.now().day, datetime.now().month, datetime.now().year)

    def get_current_time(self):
        return datetime.now(self.timezone).strftime('%H:%M:%S')

    def get_script(self, command):
        return self.json_data['Commands'][command]['Script']

    def format_string(self, string, message):
        string = string.replace('(%mentionuser)', message.author.mention)
        string = string.replace('(%discordserver)', message.server.name)
        string = string.replace('(%user)', message.author.name)
        string = string.replace('(%time)', self.get_current_time())
        string = string.replace('(%day)', self.get_current_day())
        return string
    '''                                                                     End Utility Methods
    '''

    '''                                                                     Command Permissions Methods
    '''
    def get_permission(self, command):
        return [x.lower() for x in self.json_data['Commands'][command]['Permissions']]

    def has_permission(self, rank, command):
        if self.get_permission(command) == ['*']:
            return True
        return str(rank).lower() in self.get_permission(command)

    def check_permission(self, user, command_list):
        if command_list[0] in self.json_data['Commands'].keys():
            for rank in user.roles:
                id_permission = str(rank.id) in [x.lower() for x in self.json_data['Commands'][command_list[0]]['Permissions']]
                if len(command_list) > 1:
                    if 'Sub-Commands' in self.json_data['Commands'][command_list[0]].keys():
                        sub_permission = self.sub_command_permission(rank, command_list[1:], self.json_data['Commands'][command_list[0]], user.id)
                        if sub_permission != -1 and sub_permission is True:
                            return sub_permission
                retVal = self.json_data['Commands'][command_list[0]]['Permissions'] == ['*'] or id_permission
                if retVal is True:
                    return retVal
            return False
        return False

    def sub_command_permission(self, rank, command_list, dictionary, id):
        if command_list[0] in dictionary['Sub-Commands'].keys():
            if 'Permissions' in dictionary['Sub-Commands'][command_list[0]].keys():
                base_permission = str(rank).lower() in [x.lower() for x in dictionary['Sub-Commands'][command_list[0]]['Permissions']]
                id_permission = str(id) in [x.lower() for x in dictionary['Sub-Commands'][command_list[0]]['Permissions']]
                if len(command_list) > 1:
                    sub_permission = self.sub_command_permission(rank, command_list[1:], dictionary['Sub-Commands'][command_list[0]], id)
                    if sub_permission == -1:
                        return base_permission or dictionary['Sub-Commands'][command_list[0]]['Permissions'] == ['*'] or id_permission
                return base_permission or dictionary['Sub-Commands'][command_list[0]]['Permissions'] == ['*'] or id_permission
            return -1
    '''                                                                     End Command Permissions Methods
    '''

    '''                                                                     Queue Utility Methods
    '''
    def message_worker(self):
        while True:
            message = self.command_queue.get()
            asyncio.run_coroutine_threadsafe(self.run_command(message), self.loop)
            self.command_queue.task_done()

    def local_worker(self):
        while True:
            command = self.local_data_queue.get()
            asyncio.run_coroutine_threadsafe(self.create_local_data(command), self.loop)
            self.local_data_queue.task_done()
    '''                                                                     End Queue Utility Methods
    '''

    '''                                                                     Error Handler
    '''
    '''
    @asyncio.coroutine
    def on_error(self, event_method, *args, **kwargs):
        self.logger.error(event_method)
    '''
    '''                                                                     End Error Handler
    '''