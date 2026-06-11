"""
Comando de juego !timba - Duelo de adivinanza de números

Este módulo implementa el comando !timba, un minijuego de reto entre dos jugadores
donde compiten para adivinar un número aleatorio entre 1 y 100. El jugador que
adivine primero el número gana los puntos apostados.

Mecánica del juego:
    - Un jugador reta a otro usando !timba @usuario
    - Ambos jugadores deben tener al menos 5 puntos para jugar
    - El retado acepta usando !timba [número] (su primera adivinanza)
    - Se quitan 5 puntos a cada jugador al iniciar
    - Los jugadores se turnan para adivinar
    - El bot da pistas: "más alto" o "más bajo"
    - El ganador recibe 10 puntos (5 de cada jugador)
    - Solo puede haber 1 juego activo a la vez
    - Los admins pueden jugar sin apostar puntos
    - Los admins pueden finalizar un juego con !timba fin

Commands:
    !timba [usuario] - Retar a un usuario
    !timba [número] - Adivinar un número (durante un juego)
    !timba fin - Finalizar el juego actual (solo admins)

Author: Demian762
Version: 311025 (Nueva implementación)
"""

from twitchio.ext import commands
import asyncio
from random import randint

# Imports locales
from utils.mensaje import mensaje
from utils.logger import logger
from utils.configuracion import admins
from utils.puntitos_manager import consulta_puntitos, funcion_puntitos, registrar_victoria_timba
from .base_command import BaseCommand


class TimbaCommand(BaseCommand):
    """
    Cog que maneja el comando de juego !timba
    
    Gestiona todo el estado del juego incluyendo retos pendientes,
    juego activo, turnos y validaciones.
    """
    
    def __init__(self, bot):
        """
        Inicializa el comando timba con el estado del juego
        
        Args:
            bot: Instancia del bot principal
        """
        super().__init__(bot)
        
        # Estado del juego
        self.reto_pendiente = None  # {'retador': str, 'retado': str}
        self.juego_activo = None  # {'jugador1': str, 'jugador2': str, 'numero_secreto': int, 'turno_actual': str, 'con_apuesta': bool}
        
    @commands.command()
    async def timba(self, ctx: commands.Context, *args):
        """
        Comando principal !timba - Maneja retos, adivinanzas y finalización
        
        Sintaxis:
            !timba @usuario - Retar a un usuario
            !timba [número] - Adivinar durante un juego
            !timba fin - Finalizar juego (solo admins)
            
        Args:
            ctx (commands.Context): Contexto del comando
            *args: Argumentos del comando
        """
        if await self.check_coma_etilico():
            return
            
        handler = await self.handle_command(self._timba)
        await handler(ctx, *args)
    
    async def _timba(self, ctx: commands.Context, *args):
        """
        Implementación interna del comando timba
        
        Distingue entre:
        - Comando para finalizar juego (!timba fin)
        - Comando para retar (!timba usuario)
        - Comando para adivinar (!timba número)
        
        Args:
            ctx (commands.Context): Contexto del comando
            *args: Argumentos del comando
        """
        usuario = ctx.author.name.lower()
        
        # Sin argumentos
        if len(args) == 0:
            await mensaje("Usá el comando correctamente: !timba @usuario para retar, o !timba [número] para adivinar.")
            return
        
        # Comando para finalizar juego (solo admins)
        if args[0].lower() == "fin":
            await self._finalizar_juego(usuario)
            return
        
        # Intentar parsear como número (adivinanza)
        try:
            numero = int(args[0])
            await self._procesar_adivinanza(usuario, numero)
            return
        except ValueError:
            # No es un número, debe ser un usuario (reto)
            await self._procesar_reto(usuario, args[0])
    
    async def _procesar_reto(self, retador: str, retado_raw: str):
        """
        Procesa un intento de retar a otro usuario
        
        Valida:
        - Que no se rete a sí mismo
        - Que no haya un juego activo
        - Que ambos tengan puntos suficientes (si no son admins)
        
        Args:
            retador (str): Usuario que inicia el reto
            retado_raw (str): Usuario retado (puede incluir @)
        """
        # Limpiar el @ del nombre de usuario si existe
        retado = retado_raw.lower().lstrip("@")
        
        # Validar que no se rete a sí mismo
        if retador == retado:
            await mensaje(f"@{retador}, no podés retarte a vos mismo!")
            return
        
        # Validar que no haya un juego activo
        if self.juego_activo:
            jugadores = f"@{self.juego_activo['jugador1']} y @{self.juego_activo['jugador2']}"
            await mensaje(f"Ya hay un juego activo entre {jugadores}. Esperá a que termine!")
            return
        
        # Verificar si son admins
        retador_es_admin = retador in admins
        retado_es_admin = retado in admins
        
        # Si ninguno es admin, verificar puntos
        if not retador_es_admin and not retado_es_admin:
            puntos_retador = consulta_puntitos(retador)
            puntos_retado = consulta_puntitos(retado)
            
            if puntos_retador < 5:
                await mensaje(f"@{retador}, necesitás al menos 5 puntitos para retar a alguien!")
                return
            
            if puntos_retado < 5:
                await mensaje(f"@{retado} no tiene suficientes puntitos para aceptar el reto (necesita 5).")
                return
        
        # Crear el reto pendiente
        self.reto_pendiente = {
            'retador': retador,
            'retado': retado
        }
        
        await mensaje(f"@{retador} retó a @{retado} a una timba! @{retado}, usá !timba [número] para aceptar el reto y hacer tu primera adivinanza.")
    
    async def _procesar_adivinanza(self, usuario: str, numero: int):
        """
        Procesa una adivinanza de número

        Puede ser:
        - Aceptación de un reto (primera adivinanza)
        - Adivinanza durante un juego activo

        Args:
            usuario (str): Usuario que adivina
            numero (int): Número adivinado
        """
        # Validar rango del número
        if numero < 1 or numero > 100:
            await mensaje(f"@{usuario}, el número debe estar entre 1 y 100.")
            return

        # Si hay un reto pendiente y el usuario es el retado, aceptar el reto
        if self.reto_pendiente and self.reto_pendiente['retado'] == usuario:
            await self._aceptar_reto(usuario, numero)
            return

        # Si hay un juego activo, procesar la adivinanza
        if self.juego_activo:
            await self._procesar_turno(usuario, numero)
            return

        # No hay reto pendiente ni juego activo
        await mensaje(f"@{usuario}, no hay ningún juego activo. Usá !timba @usuario para retar a alguien.")
    
    async def _aceptar_reto(self, retado: str, primer_numero: int):
        """
        Acepta un reto pendiente e inicia el juego
        
        Quita puntos a ambos jugadores (si no son admins), genera el número
        secreto y evalúa la primera adivinanza.
        
        Args:
            retado (str): Usuario que acepta el reto
            primer_numero (int): Primera adivinanza del retado
        """
        retador = self.reto_pendiente['retador']
        self.reto_pendiente = None  # Limpiar antes del primer await

        # Verificar si alguno es admin
        retador_es_admin = retador in admins
        retado_es_admin = retado in admins
        con_apuesta = not (retador_es_admin or retado_es_admin)

        # Quitar puntos si no son admins
        if con_apuesta:
            await asyncio.to_thread(funcion_puntitos, retador, -5)
            await asyncio.to_thread(funcion_puntitos, retado, -5)

        # Generar número secreto
        numero_secreto = randint(1, 100)

        # Crear juego activo
        self.juego_activo = {
            'jugador1': retador,
            'jugador2': retado,
            'numero_secreto': numero_secreto,
            'turno_actual': retado,  # El retado juega primero
            'con_apuesta': con_apuesta,
        }

        logger.info(f"Timba iniciada: {retador} vs {retado} | Número secreto: {numero_secreto}")
        
        # Mensaje de inicio
        if con_apuesta:
            await mensaje(f"¡Timba iniciada entre @{retador} y @{retado}! Se apostaron 5 puntitos cada uno. El ganador se lleva 10 puntitos. ¡A adivinar un número del 1 al 100!")
        else:
            await mensaje(f"¡Timba iniciada entre @{retador} y @{retado}! (Sin apuesta porque hay un admin jugando). ¡A adivinar un número del 1 al 100!")
        
        await self._evaluar_numero(retado, primer_numero)
    
    async def _procesar_turno(self, usuario: str, numero: int):
        """
        Procesa el turno de un jugador durante un juego activo
        
        Valida que sea el turno del jugador y evalúa su adivinanza.
        
        Args:
            usuario (str): Usuario que adivina
            numero (int): Número adivinado
        """
        # Verificar que el usuario esté en el juego
        if usuario not in [self.juego_activo['jugador1'], self.juego_activo['jugador2']]:
            await mensaje(f"@{usuario}, no estás participando en este juego.")
            return
        
        # Verificar que sea su turno
        if usuario != self.juego_activo['turno_actual']:
            await mensaje(f"@{usuario}, todavía no es tu turno!")
            return
        
        # Evaluar el número
        await self._evaluar_numero(usuario, numero)
    
    async def _evaluar_numero(self, usuario: str, numero: int):
        """
        Evalúa una adivinanza y determina si ganó o da pistas
        
        Si el número es correcto, otorga puntos y finaliza el juego.
        Si no, da una pista (más alto/bajo) y cambia el turno.
        
        Args:
            usuario (str): Usuario que adivina
            numero (int): Número adivinado
        """
        numero_secreto = self.juego_activo['numero_secreto']
        
        # ¡Adivinó!
        if numero == numero_secreto:
            await self._declarar_ganador(usuario)
            return
        
        # No adivinó, dar pista
        if numero < numero_secreto:
            await mensaje(f"@{usuario} probó con {numero}. ¡El número es más alto!")
        else:
            await mensaje(f"@{usuario} probó con {numero}. ¡El número es más bajo!")
        
        # Cambiar turno
        self._cambiar_turno()
    
    def _cambiar_turno(self):
        """
        Cambia el turno al otro jugador
        """
        if self.juego_activo['turno_actual'] == self.juego_activo['jugador1']:
            self.juego_activo['turno_actual'] = self.juego_activo['jugador2']
        else:
            self.juego_activo['turno_actual'] = self.juego_activo['jugador1']
    
    async def _declarar_ganador(self, ganador: str):
        """
        Declara al ganador, otorga puntos y finaliza el juego
        
        Args:
            ganador (str): Usuario ganador
        """
        # Determinar el otro jugador
        if ganador == self.juego_activo['jugador1']:
            perdedor = self.juego_activo['jugador2']
        else:
            perdedor = self.juego_activo['jugador1']
        
        numero_secreto = self.juego_activo['numero_secreto']
        
        # Registrar victoria en timba para el ganador
        registrar_victoria_timba(ganador)
        
        con_apuesta = self.juego_activo['con_apuesta']
        self.juego_activo = None  # Limpiar antes del primer await

        if con_apuesta:
            await asyncio.to_thread(funcion_puntitos, ganador, 10)
            await mensaje(f"🎉 ¡@{ganador} adivinó el número {numero_secreto} y ganó 10 puntitos! @{perdedor} mejor suerte la próxima.")
        else:
            await mensaje(f"🎉 ¡@{ganador} adivinó el número {numero_secreto} y ganó el juego! @{perdedor} mejor suerte la próxima.")
    
    async def _finalizar_juego(self, usuario: str):
        """
        Finaliza un juego activo (solo admins)
        
        Devuelve los puntos a los jugadores si fue con apuesta y limpia el estado.
        
        Args:
            usuario (str): Usuario que ejecuta el comando
        """
        # Verificar que sea admin
        if usuario not in admins:
            await mensaje(f"@{usuario}, solo los admins pueden finalizar un juego.")
            return
        
        # Verificar que haya un juego activo
        if not self.juego_activo:
            await mensaje("No hay ningún juego activo para finalizar.")
            return
        
        jugador1 = self.juego_activo['jugador1']
        jugador2 = self.juego_activo['jugador2']
        
        # Si fue con apuesta, ambos pierden los 5 puntos (ya se los quitamos al inicio)
        if self.juego_activo['con_apuesta']:
            await mensaje(f"El juego entre @{jugador1} y @{jugador2} fue finalizado por un admin. Ambos perdieron sus 5 puntitos apostados.")
        else:
            await mensaje(f"El juego entre @{jugador1} y @{jugador2} fue finalizado por un admin.")
        
        # Limpiar el juego
        self.juego_activo = None
