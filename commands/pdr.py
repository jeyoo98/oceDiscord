import asyncio
from scripts import DiscordBot
COMMAND = 'pdr'


@asyncio.coroutine
def main(message, discord_object: DiscordBot.DiscordBot):
    try:
        pdr_values = [int(x) for x in message.content[len('*pdr '):].split(' ')]
        for value in pdr_values:
            if value >= 100 or value < 0:
                yield from discord_object.send_message(message.channel, message.author.mention + ' Invalid pdr sources (values not between 1 and 99)')
                return
        base_pdr = pdr_values[0] / 100
        for value in pdr_values[1:]:
            base_pdr = 1 - ((1 - base_pdr) * (100 - value) / 100)

        base_pdr = float(round(base_pdr * 100, 2))
        yield from discord_object.send_message(message.channel, message.author.mention + ' Your pdr is: {}%'.format(str(base_pdr)))
    except Exception as e:
        if isinstance(e, ValueError):
            yield from discord_object.send_message(message.channel, message.author.mention + ' Invaid pdr sources (not integer values)')
            return
        pass
