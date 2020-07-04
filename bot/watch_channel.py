from asyncio import sleep, get_event_loop, CancelledError
from utils import register, getClient
from config import config
from requests import get, post, put
from collections import defaultdict
from re import match

import discord  

import pprint
pp = pprint.PrettyPrinter(indent=4)

channel_id = None
spinner = None

def chunkList(l, length):
    for i in range(0, len(l), length):
        yield l[i:i + length]

async def doPings():
    channel = getClient().get_channel(channel_id)
    payload = await getTransmutes(channel=channel)

    lines = []
    lines += messageMaker(payload['awaiting_mats'], needsMaterialFormat, 'Need Materials', False, channel, admin_ping=True)
    lines += messageMaker(payload['on_cd'], onCooldownFormat, 'On Cooldown', False, channel)
    lines += messageMaker(payload['off_cd'], offCooldownFormat, 'Off Cooldown', True, channel,
        lambda user_alts: len(list(filter(lambda x: x['has_mats'] == True, user_alts))) > 0)
    
    print(lines)

    content = ''
    category = None

    messages = []
    for line in lines:
        if isinstance(line, str):
            content += line + '\n'
            category = line
        else:
            chunks = chunkList(line, 8)
            for i, chunk in enumerate(chunks):
                if i > 0:
                    content += category.replace('**', '_') + '...\n'
                content += '```' + '\n'.join(chunk) + '```'
                print('\n', content)
                message = await channel.send(content)
                if 'On Cooldown' not in category:
                    messages.append((message, len(chunk)))
                content = ''

    for message, num_reactions in messages:
        for num_reaction in range(num_reactions):
            await message.add_reaction("{}\N{COMBINING ENCLOSING KEYCAP}".format(num_reaction+1))


async def spin(signum=None, frame=None):
    while True:
        #print('hello', signum, frame)

        await doPings()

        await sleep(4 * 60 * 60) # H / M / S
        if channel_id == None:
            return


async def sendMaterials(reaction_payload, xmute, items, index):
    print(type(reaction_payload.user_id))
    if reaction_payload.user_id != config['admin_user']:
        return

    item = items.split('\n')[index - 1].replace('*', '')
    m = match('([^ ]+)', item)

    response = post(config['api_url'] + '/send-materials', data = {
        'sender': 'Bank',
        'send_to': m.group(1),
        'product': xmute,
        'dumb_key': config['apikey']
    })

    if response.status_code != 200:
        print('Error sending materials')
    else:
        channel = getClient().get_channel(reaction_payload.channel_id)
        message = await channel.fetch_message(reaction_payload.message_id)
        await message.edit(content = message.content.replace(item, '<>' + item))
    print(response.json())


async def sendXmute(reaction_payload, nick_or_id, items, index):
    id_name = match('<@!?(\d+)>', nick_or_id)
    if id_name:
        id_name = int(id_name.group(1))
        if reaction_payload.user_id != id_name:
            return
    elif reaction_payload.member.nick != nick_or_id:
        return

    item = items.split('\n')[index - 1]
    name, xmute = item.replace('*', '').split(' - ')

    response = put(config['api_url'] + '/craft-transmute', data = {
        'discordid': reaction_payload.user_id,
        'send_to': name,
        'product': xmute,
        'super_secret_shh': config['apikey']
        })

    if response.status_code != 200:
        print('Error recording xmute')
    else:
        channel = getClient().get_channel(reaction_payload.channel_id)
        message = await channel.fetch_message(reaction_payload.message_id)
        await message.edit(content = message.content.replace(item, '<>' + item))
    print(response.json())


def nameOrMention(user_id, channel, with_mentions):
    if isinstance(user_id, str):
        try:
            user_id = int(user_id)
        except ValueError:
            return user_id
    user = channel.guild.get_member(user_id)

    # For testing?
    if user == None:
        user = getClient().get_user(user_id)
        with_mentions = False

    print(user_id, user);
    if with_mentions:
        return user.mention
    return user.display_name


def depluralize(time_part, word_part):
    if time_part == 1:
        return str(time_part) + ' ' + word_part[:-1]
    return str(time_part) + ' ' + word_part


def largestTime(interval):
    keys = ['years', 'days', 'hours', 'minutes', 'seconds', 'milliseconds']
    for i, key in enumerate(keys):
        if key == 'milliseconds':
            return depluralize(interval[key], key)
        try: 
            next_key = keys[i+1]
            print(interval)
            return depluralize(interval[key], key) + ', ' + depluralize(interval[next_key], next_key)
        except KeyError:
            continue


def needsMaterialFormat(character_payload, channel):
    print(character_payload)
    return '{name} ({discord})'.format(
            name=character_payload['name']
            ,discord=nameOrMention(character_payload['discordid'], channel, False))


def onCooldownFormat(character_payload, channel):
    print(character_payload)
    return '{name}{astrisk} - {xmute} [{time_until}]'.format(
            name=character_payload['name']
            ,astrisk='' if character_payload['has_mats'] else '*'
            ,xmute=character_payload['item']
            ,time_until=largestTime(character_payload['transmute_in']))


def offCooldownFormat(character_payload, channel):
    return '{name}{astrisk} - {xmute}'.format(
            name=character_payload['name']
            ,astrisk='' if character_payload['has_mats'] else '*'
            ,xmute=character_payload['item'])


def messageMaker(payload, fn, title, with_mention=False, channel=channel_id, mentionFn=None, admin_ping=False):
    title = '**' + title + '**'
    if admin_ping:
        title += ' ' + nameOrMention(config['admin_user'], channel, True)
    content = []
    if len(payload.keys()):
        for category in payload.keys():
            if len(payload[category]) == 0:
                continue
            content.append(title + ' ({})'.format(nameOrMention(category, channel, with_mention and (mentionFn(payload[category]) if callable(mentionFn) else True))) )
            alt_list = []
            for alt in payload[category]:
                alt_list.append(fn(alt, channel))
            content.append(alt_list)
    return content


async def getTransmutes(channel=channel_id):
    if channel is str:
        channel = getClient().get_channel(channel)

    if not isinstance(channel, discord.channel.TextChannel):
        return None

    response = get(config['api_url'] + '/transmuter')
    payload = {
        'off_cd': {},
        # {'userid': [
        #   {'has_mats': bool, 'name': str, 'item': str}
        #   ... ] }
        'on_cd': {
        },
        'awaiting_mats': {
            'Arcanite': [],
            'Mooncloth': [],
        }
    }

    if response.status_code == 200:
        #pp.pprint(response.json())
        for i in response.json()['rows']:
            # Need Mats
            if not i['has_mats']:
                payload['awaiting_mats'][i['item']].append(i)

            # Off CD
            if not i['transmute_in'] or i['transmute_in']['milliseconds'] < 0:
                if i['discordid'] not in payload['off_cd']:
                    payload['off_cd'][i['discordid']] = []
                payload['off_cd'][i['discordid']].append(i);
            # On CD
            else:
                if i['discordid'] not in payload['on_cd']:
                    payload['on_cd'][i['discordid']] = []
                payload['on_cd'][i['discordid']].append(i)

    return payload


@register(command='<a:who:597970138951843841>', hidden=True)
async def who(message, contents):
    payload = await getTransmutes(channel=message.channel)

    if payload:
        lines = []
        lines += messageMaker(payload['awaiting_mats'], needsMaterialFormat, 'Need Materials', False, message.channel)
        lines += messageMaker(payload['on_cd'], onCooldownFormat, 'On Cooldown', False, message.channel)
        lines += messageMaker(payload['off_cd'], offCooldownFormat, 'Off Cooldown', False, message.channel)
        await message.channel.send('\n'.join([i if isinstance(i, str) else '```' + ('\n'.join(i)) + '```' for i in lines]))


@register(command='🙈', hidden=True)
async def dewatch(message, contents):
    global channel_id, spinner
    if message.channel.id != channel_id and message.author.id != config['admin_user']:
        return
    channel_id = None


@register(command='👀', hidden=True)
async def watch(message, contents):
    global channel_id, spinner
    if message.author.id != config['admin_user']:
        return


    if not channel_id:
        spinner = get_event_loop()
        task = None
        spinner.call_later(5, lambda: task.cancel() if task == None else None )
        task = spinner.create_task(spin())
    else:
        await doPings()
    channel_id = message.channel.id

