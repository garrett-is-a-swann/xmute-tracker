from utils import register
from requests import post
from config import config

@register(command='skip'
    ,parameters='player_name xmute'
    ,description='notify my system that you have crafted/sent your xmute, and that your CD has started.'
    ,example='Geofrey Arcanite')
async def skip(message, contents):
    if len(contents) != 3: 
        return await message.channel.send('Invalid number of parameters. Expected exactly 2.')
    
    if contents[2].capitalize() not in config['xmutes']:
        return await message.channel.send('Unknown xmute.  -  Sent: `{content}`  -  Expected: `{xmutes}`'
                .format(content=contents[2].capitalize(), xmutes=', '.join(config['xmutes'])))

    response = post(config['api_url'] + '/skip-transmute', data = {
        'discordid': message.author.id,
        'send_to': contents[1].capitalize(),
        'product': contents[2].capitalize(),
        'super_secret_shh': config['apikey']
        })

    if response.status_code == 200:
        await message.add_reaction(':yougotitdude:710548073302065152')
    else:
        await message.add_reaction(':server_fire:709906768393797636')
        await message.channel.send(response.json())
    pass

