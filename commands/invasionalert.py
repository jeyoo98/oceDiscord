import asyncio
import discord
from discord import Message
from scripts import DiscordBot
COMMAND = "invasionalert"

@asyncio.coroutine
def main(message: Message, discord_object: DiscordBot.DiscordBot):
    user = message.author
    isMember = False
    KritiasWatch = discord.utils.get(message.server.roles, name='Kritias Watch')
    for role in user.roles[1:]:
        if role == KritiasWatch:
            isMember = True

    if not isMember:
        yield from discord_object.add_roles(user, KritiasWatch)
        yield from discord_object.send_message(message.channel, user.mention + ' You have been added to the Kritias Invasion alert.')
    else:
        yield from discord_object.remove_roles(user, KritiasWatch)
        yield from discord_object.send_message(message.channel, user.mention + ' You have been removed from the Kritias Invasion alert.')