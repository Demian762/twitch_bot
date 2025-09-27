"""
Sistema de mensajería para comunicación con Twitch IRC

Este módulo maneja toda la comunicación de salida del bot hacia el chat de Twitch,
implementando el protocolo IRC nativo para envío directo de mensajes sin dependencias
adicionales de TwitchIO.

Features:
    - Conexión directa IRC a servidores de Twitch
    - Envío de mensajes individuales y en lote
    - Control anti-spam automático
    - Manejo asíncrono para múltiples mensajes

Author: Demian762
Version: 250927
"""

import socket
import asyncio

from utils.configuracion import configuracion_basica
from utils.secretos import channel_name, HOST, PORT, access_token, bot_channel_name

# Configuración IRC para autenticación en Twitch
PASS = "oauth:" + access_token  # Token OAuth de Twitch
IDENT = "BotDelEstadio"        # Nombre de usuario del bot


def openSocket():
    """
    Abre una conexión socket IRC con los servidores de Twitch
    
    Establece conexión TCP con el servidor IRC de Twitch y realiza
    la secuencia de autenticación completa (PASS, NICK, JOIN).
    
    Returns:
        socket.socket: Socket conectado y autenticado listo para enviar mensajes
        
    Raises:
        socket.error: Si falla la conexión con el servidor
        
    Example:
        >>> s = openSocket()
        >>> sendMessage(s, "¡Hola chat!")
    """
    s = socket.socket()
    s.connect((HOST, PORT))
    s.send(bytes("PASS " + PASS + "\r\n", 'UTF-8'))
    s.send(bytes("NICK " + bot_channel_name + "\r\n", 'UTF-8'))
    s.send(bytes("JOIN #" + channel_name + "\r\n", 'UTF-8'))
    return s

def sendMessage(s, message):
    """
    Envía un mensaje individual al chat usando socket IRC
    
    Args:
        s (socket.socket): Socket conectado obtenido de openSocket()
        message (str): Mensaje a enviar al chat
        
    Note:
        El mensaje se envía inmediatamente sin delays anti-spam.
        Para múltiples mensajes usar la función mensaje() asíncrona.
    """
    messageTemp = "PRIVMSG #" + channel_name + " :" + message
    s.send(bytes(messageTemp + "\r\n", 'UTF-8'))

async def mensaje(input):
    """
    Función principal para envío de mensajes con control anti-spam
    
    Maneja tanto mensajes individuales como listas de mensajes,
    aplicando delays automáticos para evitar límites de rate de Twitch.
    
    Args:
        input (str or list): Mensaje individual o lista de mensajes a enviar
                           Si es None, la función retorna sin hacer nada
    
    Behavior:
        - Si input es None: No hace nada (útil para comandos condicionales)
        - Si input es str: Envía el mensaje inmediatamente
        - Si input es list: Envía cada mensaje con delay anti-spam entre ellos
    
    Example:
        >>> await mensaje("Mensaje individual")
        >>> await mensaje(["Mensaje 1", "Mensaje 2", "Mensaje 3"])
        >>> await mensaje(None)  # No envía nada
    """
    if input is None:
        return
        
    s = openSocket()
    
    if isinstance(input, str):
        sendMessage(s, input)
        return
    
    # Para listas de mensajes, aplicar delay anti-spam
    for texto in input:
        sendMessage(s, texto)
        await asyncio.sleep(configuracion_basica.get("dont_spam"))
