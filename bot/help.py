from utils import splitSentence, register, mux
from config import config

def helpDoc(key, depth = 0):
    item = '\n' + ('  '*depth+config['operand'] + key + ' ' + mux[key]['params']).ljust(44)

    # "\n    Ex: ={op} [...] [...]     ...       {description}"
    if mux[key]['example']:
        item += splitSentence(mux[key]['description'], 2).replace('\n',
                ('\n' + '  '*(depth+1) + 'Ex: ' + config['operand'] + key + ' ' + mux[key]['example']).ljust(45))
    else:
        item += mux[key]['description']
    return  item


@register(command='help'
    ,description='print these help docs'
    ,parameters='[command]')
async def botHelp(message, contents):
    response = ''
    if len(contents) == 2:
        try:
            response = '```' + helpDoc(contents[1]) + '```'
        except KeyError:
            response = '{} is an unknown command'.format(contents[1])

    else:
        response = '```cilantrobot commands:' 
        for n in mux.keys():
            if mux[n]['hidden'] == True:
                continue
            response += helpDoc(n, 1) + '\n'

        response += '''\nParameters:
  [player_name] : Your character's in-game name. 
  [xmute]       : {xmutes}       (More to be added later?)```'''.format(xmutes= ', '.join(config['xmutes']))

    await message.channel.send(response)

