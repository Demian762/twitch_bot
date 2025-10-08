"""
Comandos básicos y fundamentales del BotDelEstadio

Este módulo contiene los comandos más simples y esenciales del bot,
incluyendo saludos, recordatorios y funcionalidades de administración básica.

Commands:
    !hola/!buenas - Saludo con puntito diario
    !guardar/!salvar - Recordatorio para guardar partida
    !proteccion - Control de horario de protección al menor
    !spam - Envío de mensajes predefinidos (solo admins)

Author: Demian762
Version: 250927
"""

from twitchio.ext import commands
from utils.mensaje import mensaje
from utils.puntitos_manager import funcion_puntitos
from utils.configuracion import admins, spam_messenges
from .base_command import BaseCommand

class BasicCommands(BaseCommand):
    """
    Cog que maneja comandos básicos y funcionalidades esenciales
    
    Attributes:
        puntitos_dados (list): Lista de usuarios que ya recibieron su puntito diario
        proteccion_activa (bool): Estado del horario de protección al menor
    """
    
    def __init__(self, bot):
        """
        Inicializa el cog de comandos básicos
        
        Args:
            bot: Instancia del bot principal
        """
        super().__init__(bot)
        self.puntitos_dados = []
        self.proteccion_activa = False

    @commands.command(aliases=("buenas",))
    async def hola(self, ctx: commands.Context):
        """
        Comando de saludo con sistema de puntito diario
        
        Saluda al usuario y otorga un puntito una vez por día por usuario.
        Implementa un sistema simple de control de frecuencia para evitar
        spam de puntitos del mismo usuario.
        
        Args:
            ctx (commands.Context): Contexto del comando con información del usuario
            
        Aliases: !buenas
        
        Example:
            Usuario: !hola
            Bot: hola Usuario!
            Bot: @Usuario acaba de sumar un puntito!
            
        Note:
            - Solo otorga un puntito por usuario por sesión del bot
            - Lista se resetea cuando se reinicia el bot
        """
        if await self.check_coma_etilico():
            return
        nombre = ctx.author.name
        await mensaje([f"hola {nombre}!"])
        if nombre not in self.puntitos_dados:
            self.puntitos_dados.append(nombre)
            funcion_puntitos(nombre, 1)
            await mensaje(f'@{nombre.lstrip("@")} acaba de sumar un puntito!')
        else:
            await mensaje(f'Ya tenés tu puntito de hoy @{nombre.lstrip("@")}, no jodas....')

    @commands.command(aliases=("salvar",))
    async def guardar(self, ctx: commands.Context):
        """
        Recordatorio para que el streamer guarde la partida
        
        Comando útil para que los viewers puedan recordar al streamer
        que guarde el progreso del juego, especialmente importante
        en juegos largos o con checkpoints poco frecuentes.
        
        Args:
            ctx (commands.Context): Contexto del comando
            
        Aliases: !salvar
        
        Example:
            Usuario: !guardar
            Bot: Usuario quiere recordarles que....
            Bot: ¡¡¡GUARDEN LA PARTIDA!!!
        """
        if await self.check_coma_etilico():
            return
        nombre = ctx.author.name
        msj1 = f"{nombre} quiere recordarles que...."
        msj2 = "¡¡¡GUARDEN LA PARTIDA!!!"
        await mensaje([msj1,msj2])

    @commands.command()
    async def proteccion(self, ctx: commands.Context):
        """
        Toggle del horario de protección al menor
        
        Cambia el estado de protección al menor, usado para indicar
        cuando el contenido del stream es apropiado para menores.
        
        Args:
            ctx (commands.Context): Contexto del comando
            
        Example:
            !proteccion -> "Aqui comienza el horario de proteccion al menor."
            !proteccion -> "Aqui finaliza el horario de proteccion al menor."
        """
        if await self.check_coma_etilico():
            return
        if self.proteccion_activa == False:
            await mensaje("Aqui comienza el horario de proteccion al menor.")
            self.proteccion_activa = True
        else:
            await mensaje("Aqui finaliza el horario de proteccion al menor.")
            self.proteccion_activa = False

    @commands.command()
    async def spam(self, ctx: commands.Context):
        """
        Envía mensajes de spam predefinidos (solo administradores)
        
        Comando exclusivo para administradores que permite enviar
        mensajes predefinidos múltiples veces seguidas.
        
        Args:
            ctx (commands.Context): Contexto del comando
            
        Note:
            - Solo disponible para usuarios en la lista de admins
            - Envía el mismo mensaje 3 veces consecutivas
            - Los mensajes están definidos en spam_messenges
        """
        if await self.check_coma_etilico():
            return
        autor = ctx.author.name
        if autor not in admins:
            return
        await mensaje(spam_messenges)
        await mensaje(spam_messenges)
        await mensaje(spam_messenges)

    @commands.command()
    async def quiensos(self, ctx: commands.Context):
        """
        Comando de broma que revela la "identidad" del bot
        
        Easter egg que rompe la cuarta pared y revela que el bot
        es en realidad "Sergio". Comando puramente humorístico.
        
        Args:
            ctx (commands.Context): Contexto del comando
            
        Example:
            Usuario: !quiensos
            Bot: En realidad soy Sergio... me descubrieron.
        """
        if await self.check_coma_etilico():
            return
        await mensaje(['En realidad soy Sergio... me descubrieron.'])

    @commands.command()
    async def chiste(self, ctx: commands.Context):
        """
        Comando de broma que hace un "anti-chiste"
        
        Responde con una broma sarcástica dirigida al usuario que pidió
        el chiste. Es un comando puramente humorístico.
        
        Args:
            ctx (commands.Context): Contexto del comando
            
        Example:
            Usuario: !chiste
            Bot: Vos sos un chiste Usuario.
        """
        if await self.check_coma_etilico():
            return
        await mensaje([f"Vos sos un chiste {ctx.author.name}."])
