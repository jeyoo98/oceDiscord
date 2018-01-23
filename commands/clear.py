import asyncio
from discord import Message
from scripts import DiscordBot
import threading
from queue import Queue

local_data_queue = Queue()


@asyncio.coroutine
def main(message: Message, discord_object: DiscordBot.DiscordBot):
    try:
        delete_amount = int(discord_object.parse_message(message.content)[1])
        if not (type(delete_amount) is int):
            raise IndexError

        yield from discord_object.send_message(message.channel, message.author.mention +
                                          ' You are about to clear messages in this channel. Type *confirm to proceed or *cancel to cancel.')
        yield from get_reply(message, discord_object, delete_amount)
    except IndexError:
        yield from discord_object.send_message(message.channel, message.author.mention +
                                               ' You did not specify a max number of messages to delete.')


@asyncio.coroutine
def get_reply(message: Message, discord_object: DiscordBot.DiscordBot, delete_amount, limit=10, count=0):
    if count < limit:
        count += 1
        reply = yield from discord_object.wait_for_message(author=message.author, channel=message.channel)
        if reply.content == '*confirm':
            yield from confirmed(reply, discord_object, delete_amount)
        elif reply.content == '*cancel':
            pass
        else:
            yield from get_reply(message, discord_object, delete_amount, limit, count + 1)


@asyncio.coroutine
async def confirmed(message: Message, discord_object: DiscordBot.DiscordBot, delete_amount):
    for x in range(2):
        t = threading.Thread(target=message_worker, args=(discord_object, ))
        t.daemon = True
        t.start()

    async for x in discord_object.logs_from(message.channel, limit=delete_amount):
        local_data_queue.put(x)


def message_worker(discord_object):
    while True:
        message = local_data_queue.get()
        if not message.pinned:
            thread = threading.Thread(target=lambda: discord_object.loop.create_task(discord_object.delete_message(message)))
            thread.start()
            thread.join(timeout=0.2)
        local_data_queue.task_done()
