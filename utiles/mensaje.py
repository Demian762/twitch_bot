import socket
import asyncio

from configuracion import configuracion_basica
from utiles.secretos import channel_name, HOST, PORT, access_token, bot_channel_name


PASS = "oauth:" + access_token # your Twitch OAuth token
IDENT = "BotDelEstadio"  # Twitch username your using for your bot


def openSocket():
    s = socket.socket()
    s.connect((HOST, PORT))
    s.send(bytes("PASS " + PASS + "\r\n", 'UTF-8'))
    s.send(bytes("NICK " + bot_channel_name + "\r\n", 'UTF-8'))
    s.send(bytes("JOIN #" + channel_name + "\r\n", 'UTF-8'))
    return s

def sendMessage(s, message):
    messageTemp = "PRIVMSG #" + channel_name + " :" + message
    s.send(bytes(messageTemp + "\r\n", 'UTF-8'))

async def mensaje(input):
    s = openSocket()
    
    if isinstance(input, str):
        sendMessage(s, input)
        return
    
    for texto in input:
        sendMessage(s, texto)
        await asyncio.sleep(configuracion_basica.get("dont_spam"))