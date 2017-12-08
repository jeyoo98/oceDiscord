import asyncio
import discord
from discord import Message
from scripts import DiscordBot
COMMAND = "nsfw"

@asyncio.coroutine
def main(message: Message, discord_object: DiscordBot.DiscordBot):
    user = message.author
    isMember = False
    NSFW = discord.utils.get(message.server.roles, name='Guilty Eyes')
    for role in user.roles[1:]:
        if role == NSFW:
            isMember = True

    if not isMember:
        yield from discord_object.add_roles(user, NSFW)
        yield from discord_object.send_message(message.channel, user.mention + ' You now have access to the NSFW channel.')
    else:
        yield from discord_object.remove_roles(user, NSFW)
        yield from discord_object.send_message(message.channel, user.mention + ' Your access to the NSFW channel has been revoked.')