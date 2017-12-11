import asyncio
import discord
from datetime import datetime
import feedparser
import html2text
from scripts import DiscordBot
COMMAND = 'forceqotd'


@asyncio.coroutine
def main(message, discord_object: DiscordBot.DiscordBot):
    discord_object.todayTZ = discord_object.localtime.localize(datetime.today())
    channel = discord.Channel(server=discord.Server(id='260325692040937472'), id='314032599838359553')
    feed = feedparser.parse('https://thinkwitty.com/feed')
    parser = html2text.HTML2Text()
    parser.ignore_links = True
    done = False

    index = 0
    while not done and index < 5:
        if feed.entries[index]['tags'][1]['terms'] == 'Puzzle of the day':
            done = True
            text = parser.handle(feed.entries[4]['content'][0]['value'])
            index = text.find('https://')
            end = index

            for x, val in enumerate(text[index:]):
                if val == '?':
                    end += x
                    break

            image_link = text[index:end].replace('\n', '')
            yield from discord_object.send_message(channel, image_link)
        else:
            index += 1