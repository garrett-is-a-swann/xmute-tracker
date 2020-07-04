from requests import post, put

import discord

from config import config
from utils import register, registerCommandReaction


@register(command='subscribe'
    ,parameters='player_name xmute'
    ,description='subscribe/resubscribe your character to the xmute cooldown management system.'
    ,example='Geofrey Arcanite')
async def subscribe(message, contents):
    if len(contents) != 3: 
        return await message.channel.send('Invalid number of parameters. Expected exactly 2.')
    
    if contents[2].capitalize() not in config['xmutes']:
        return await message.channel.send('Unknown xmute.  -  Sent: `{content}`  -  Expected: `{xmutes}`'
                .format(content=contents[2].capitalize(), xmutes=', '.join(config['xmutes'])))

    response = post(config['api_url'] + '/subscribe', data = {
        'discordid': message.author.id,
        'subscriber': contents[1].capitalize(),
        'product': contents[2].capitalize(),
        'super_secret_shh': config['apikey']
        })

    if response.status_code == 200:
        await message.add_reaction(':yougotitdude:710548073302065152')
    else:
        await message.add_reaction(':server_fire:709906768393797636')
        await message.channel.send(response.json())

@registerCommandReaction(command='subscribe')
async def subscribeReaction(message, contents, user, emoji):
    # Check if source message was a success
    if type(emoji) is str and reaction.emoji != ':yougotitdude:710548073302065152':
        return

    if type(emoji) is discord.Emoji and reaction.emoji.id != '<:yougotitdude:710548073302065152>':
        return

    if user.id != config['admin_user']:
        return

    response = put(config['api_url'] + '/confirm-subscribe', data = {
        'discordid': message.author.id,
        'subscriber': contents[1].capitalize(),
        'product': contents[2].capitalize(),
        'super_secret_shh': config['apikey']
        })

    if response.status_code == 200:
        await message.add_reaction('✔️')
    else:
        await message.add_reaction(':server_fire:709906768393797636')
        await message.channel.send(response.json())
