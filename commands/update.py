import asyncio
from scripts import DiscordBot
COMMAND = 'update'


@asyncio.coroutine
def main(message, discord_object: DiscordBot.DiscordBot):
    yield from discord_object.send_message(message.channel, message.author.mention + ' ' + ' Incomplete')


@asyncio.coroutine
def fetch_data_to_local(discord_object: DiscordBot.DiscordBot):
    ss = 'oceaniaGuildActivity'
    spreadsheet = {ss: {}}
    discord_object.spreadsheet_accessor.open_spreadsheet(ss, 'https://docs.google.com/spreadsheets/d/1VWg6INme20CV9BJnhgCLYbtlwnC3xl41Opz8Tzq9Auo/edit#gid=0')
    discord_object.spreadsheet_accessor.open_worksheet(ss,  'Oceania')
    spreadsheet[ss]['Names'] = discord_object.spreadsheet_accessor.get_column_values(ss, 'Oceania', 1, 1, False)
    spreadsheet[ss]['Capitalized'] = discord_object.spreadsheet_accessor.get_column_values(ss, 'Oceania', 2, 1, False)
    spreadsheet[ss]['discordID'] = discord_object.spreadsheet_accessor.get_column_values(ss, 'Oceania', 4, 1, False)
    spreadsheet[ss]['ezname'] = discord_object.spreadsheet_accessor.get_column_values(ss, 'Oceania', 6, 1, False)
    spreadsheet[ss]['eznameUpper'] = discord_object.spreadsheet_accessor.get_column_values(ss, 'Oceania', 7, 1, False)
    discord_object.locals[COMMAND] = spreadsheet
