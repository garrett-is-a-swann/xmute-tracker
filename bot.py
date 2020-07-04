import discord
from config import config
from random import randint
from functools import reduce
from re import match
from utils import register, mux, reaction_mux, getClient
from bot.watch_channel import sendXmute, sendMaterials

from bot import help, watch_channel, subscribe, unsubscribe, skip, crafted


client = getClient()

@register(command=None, hidden=True)
async def oops(message):
    resp = "I don't understand"
    await message.channel.send(resp)


reaction_emojis = [
        ':prog_pog:708021649286627399',
        ':peppa_prog:708023953108631604',
        ':2020_schizoid_man:708025323538612293',
        ':heartvom:709481576484044872',
        ':server_fire:709906768393797636',
        ':yougotitdude:710548073302065152',
        ':prognaros:715052221779148801',
] # for i in client.get_all_emojis(): print(i)


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
    #print(message)
    if message.author == client.user:
        return
    if message.content.startswith(config['operand']):
        contents = message.content.split(' ')
        #print(message.author, message.author.id, message.channel, message.created_at, message.id, message.content)
        if contents[0][1:] in mux.keys():
            await mux[contents[0][1:]]['fn'](message, contents)
        else:
            await mux[None]['fn'](message)
        #await message.channel.send('Hello!')
        #await message.add_reaction(reaction_emojis[randint(0, len(reaction_emojis) - 1)])

@client.event
async def on_raw_reaction_add(payload):
    # Self reactions
    if payload.member.id == client.user.id:
        return 

    message = await client.get_channel(payload.channel_id).fetch_message(payload.message_id)
    user = client.get_user(payload.user_id)
    emoji = payload.emoji

    if message.content.startswith(config['operand']):
        contents = message.content.split(' ')
        #print(message.author, message.author.id, message.channel, message.created_at, message.id, message.content)
        if contents[0][1:] in reaction_mux.keys():
            await reaction_mux[contents[0][1:]]['fn'](message, contents, user, emoji)

    if message.author == client.user:
        emoji_str = str(emoji.name.encode('unicode_escape'))
        print(emoji_str)
        emoji_match = match("^b'(\d)", emoji_str)
        print(emoji_match)
        if not emoji_match:
            return
        res = match('^(?:\*\*|_)(?P<descriptor>[a-zA-Z ]+)(?:\*\*|_).*\((?P<params>.*)\)\n```(?P<items>(?:.|\n)*?)```', message.content)
        if res.group('descriptor') == 'Need Materials':
            await sendMaterials(payload, res.group('params'), res.group('items'), int(emoji_match.group(1)))

        if res.group('descriptor') == 'Off Cooldown':
            await sendXmute(payload, res.group('params'), res.group('items'), int(emoji_match.group(1)))
        return



print(mux)

client.run(config['token'])
