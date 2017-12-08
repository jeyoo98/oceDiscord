import asyncio
import prawcore
from scripts import DiscordBot
from threading import Thread
COMMAND = 'subscribe'


thread_pool = []
@asyncio.coroutine
def main(message, discord_object: DiscordBot.DiscordBot):
    content = discord_object.parse_message(message.content)

    if len(content) == 2:
        if content[1] == '-list':
            channel_id = message.channel.id
            index = -1
            for x, val in enumerate(discord_object.subreddits):
                if val[0] == channel_id:
                    index = x
                    break

            msg = ""
            if index != -1:
                msg += " This channel is subscribed to the following subreddits: "
                for x, subreddit in enumerate(discord_object.subreddits[index][1]):
                    msg += subreddit
                    if x < len(discord_object.subreddits[index][1]) - 1:
                        msg += ", "
                    else:
                        msg += "."
            else:
                msg += " This channel is not subscribed to any subreddits."

            yield from discord_object.send_message(message.channel, message.author.mention + msg)
        else:
            channel = message.channel
            sr = content[1]

            try:
                # tests if the subreddit exists
                discord_object.reddit.subreddit(sr).moderator()

                channel_is_registered = False
                for entry in discord_object.subreddits:
                    channel_is_registered = bool(entry[0] == str(channel.id))
                    if channel_is_registered:
                        break

                if channel_is_registered:
                    for x, ch in enumerate(discord_object.subreddits):
                        if ch[0] == str(channel.id):
                            if sr not in ch[1]:
                                discord_object.subreddits[x][1].append(sr)
                                discord_object.pool[str(channel.id)].append(sr)
                                add_subreddit(sr, x + 1, discord_object)
                                yield from discord_object.send_message(message.channel,
                                                                       message.author.mention + ' This channel is now subscribed to /r/' + sr + '!')
                            else:
                                yield from discord_object.send_message(message.channel,
                                                                       message.author.mention + ' This channel is already subscribed to /r/' + sr + '.')
                            break
                else:
                    discord_object.subreddits.append([str(channel.id), [sr]])
                    add_channel(channel.id, discord_object)
                    add_subreddit(sr, len(discord_object.subreddits), discord_object)
                    discord_object.loop.create_task(discord_object.submission_puller(discord_object.subreddits[-1]))
                    yield from discord_object.send_message(message.channel,
                                                           message.author.mention + ' This channel is now subscribed to /r/' + sr + '!')
            except prawcore.exceptions.Redirect:
                yield from discord_object.send_message(message.channel,
                                                       message.author.mention + ' That subreddit does not exist.')

            for thread in thread_pool:
                thread.join()
    else:
        yield from discord_object.send_message(message.channel, message.author.mention + ' Please specify what subreddits to subscribe to.')


def add_channel(channel, discord_object: DiscordBot.DiscordBot):
    thread = Thread(target=discord_object.spreadsheet_accessor.set_value,
                    args=('SubredditList', 'main', channel, len(discord_object.subreddits) + 1, 1))
    thread.start()
    thread_pool.append(thread)


def add_subreddit(sr, row, discord_object: DiscordBot.DiscordBot):
    thread = Thread(target=discord_object.spreadsheet_accessor.set_value,
                    args=('SubredditList', 'main',  sr, row + 1, len(discord_object.subreddits[row - 1][1]) + 1),)
    thread.start()
    thread_pool.append(thread)