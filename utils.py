import discord
from re import finditer
from functools import reduce

client = None

def getClient():
    global client
    if client == None:
        client = discord.Client()
    return client

def absDiff(a, b):
    return abs(a - b)

def splitSentence(sentence, splits):
    split_point = reduce(lambda prev, n:
        n if 
            absDiff(prev[0], len(sentence)/splits) >= absDiff(n[0], len(sentence)/splits)
        else prev,
        [m.span() for m in finditer(' ', sentence)])
    return sentence[:split_point[0]] + '\n' + sentence[split_point[1]:]


mux = {}
def register(command='', parameters='', description='', example='', hidden=False):
    def register_decorator(func):
        mux[command] = {
            'fn': func,
            'params': parameters,
            'description': description,
            'example': example,
            'hidden': hidden
        }
        print('Register (', command, ')', sep='')
    return register_decorator


reaction_mux =  {}
def registerCommandReaction(command=''):
    def register_decorator(func):
        reaction_mux[command] = {
            'fn': func,
        }
        print('Register (', command, ')', sep='')
    return register_decorator
