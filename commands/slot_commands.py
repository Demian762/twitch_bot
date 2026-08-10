"""
Comando de juego !slot / !slots - Tragamonedas

Este módulo implementa el comando !slot, un minijuego de tragamonedas de
3 rodillos. El usuario apuesta una cantidad de puntitos (1-10) que además
funciona como multiplicador de la ganancia.

Mecánica del juego:
    - !slot [apuesta] tira 3 emojis al azar (apuesta por defecto: 1)
    - 3 iguales: gana apuesta x multiplicador del símbolo (símbolo más raro = más multiplicador)
    - 2 iguales: gana el doble de la apuesta
    - sin coincidencias: pierde la apuesta
    - El símbolo ⭐ es el jackpot (más raro, mayor multiplicador) y queda registrado
    - Los admins juegan gratis, sin apostar puntos reales
    - Estadísticamente favorable al jugador: EV ≈ +18.7% por puntito apostado
    - Los no-admins tienen máximo 5 tiradas por sesión del bot (se resetea al reiniciar)
    - Exclusivo de Kick: en Twitch responde que los slots son solo de Kick

Commands:
    !slot [apuesta] - Tira los rodillos apostando 1-10 puntitos (default 1)
    !slots [apuesta] - Alias de !slot

Author: Demian762
Version: 260810 (implementación inicial)
"""

import asyncio
from random import choices
from twitchio.ext import commands

# Imports locales
from utils.mensaje import mensaje, es_kick
from utils.configuracion import admins
from utils.puntitos_manager import consulta_puntitos, funcion_puntitos, registrar_victoria_jackpot
from .base_command import BaseCommand

# (emoji, peso, multiplicador si salen 3 iguales) - a menor peso, más raro y más multiplicador
SLOT_SIMBOLOS = (
    ("🍒", 30, 2),
    ("🍋", 26, 2),
    ("🍊", 20, 3),
    ("🍇", 14, 4),
    ("🔔", 7, 8),
    ("⭐", 3, 20),
)
SLOT_EMOJIS = [s[0] for s in SLOT_SIMBOLOS]
SLOT_PESOS = [s[1] for s in SLOT_SIMBOLOS]
SLOT_MULTIPLICADORES = {s[0]: s[2] for s in SLOT_SIMBOLOS}
SLOT_JACKPOT = "⭐"
SLOT_MAX_JUGADAS = 5  # Límite de tiradas por sesión del bot para no-admins


class SlotCommands(BaseCommand):
    """
    Cog que maneja el comando de juego !slot / !slots
    """

    @commands.command(aliases=("slots",))
    async def slot(self, ctx: commands.Context, *args):
        """
        Comando principal !slot - Tira los rodillos y resuelve la apuesta

        Sintaxis:
            !slot - Tira apostando 1 puntito
            !slot [1-10] - Tira apostando esa cantidad de puntitos

        Args:
            ctx (commands.Context): Contexto del comando
            *args: Argumentos del comando (la apuesta, opcional)
        """
        if await self.check_coma_etilico():
            return

        if not es_kick():
            await mensaje(f"@{ctx.author.name.lower()}, los slots son exclusivos de Kick.")
            return

        handler = await self.handle_command(self._slot)
        await handler(ctx, *args)

    async def _slot(self, ctx: commands.Context, *args):
        """
        Implementación interna del comando slot

        Valida la apuesta, tira los 3 emojis y resuelve el resultado.

        Args:
            ctx (commands.Context): Contexto del comando
            *args: Argumentos del comando (la apuesta, opcional)
        """
        nombre = ctx.author.name.lower()

        apuesta_raw = args[0] if args else "1"
        try:
            apuesta = int(apuesta_raw)
        except ValueError:
            await mensaje(f"@{nombre}, la apuesta tiene que ser un número entre 1 y 10.")
            return

        if apuesta < 1 or apuesta > 10:
            await mensaje(f"@{nombre}, la apuesta tiene que ser un número entre 1 y 10.")
            return

        es_admin = nombre in admins
        if not es_admin:
            jugadas_usadas = self.bot.state.slot_jugadas.get(nombre, 0)
            if jugadas_usadas >= SLOT_MAX_JUGADAS:
                await mensaje(f"@{nombre}, ya usaste tus {SLOT_MAX_JUGADAS} tiradas de !slot en esta sesión. ¡Probá de nuevo en el próximo stream!")
                return

            puntos_actuales = consulta_puntitos(nombre)
            if puntos_actuales < apuesta:
                await mensaje(f"@{nombre}, no tenés suficientes puntitos para apostar {apuesta} (tenés {puntos_actuales}).")
                return

            self.bot.state.slot_jugadas[nombre] = jugadas_usadas + 1

        tirada = choices(SLOT_EMOJIS, weights=SLOT_PESOS, k=3)
        resultado = " ".join(tirada)

        # 3 iguales
        if tirada[0] == tirada[1] == tirada[2]:
            simbolo = tirada[0]
            multiplicador = SLOT_MULTIPLICADORES[simbolo]
            ganancia = apuesta * multiplicador
            es_jackpot = simbolo == SLOT_JACKPOT

            if es_jackpot:
                registrar_victoria_jackpot(nombre)

            prefijo = "🌟 ¡JACKPOT! " if es_jackpot else ""
            if es_admin:
                await mensaje(f"🎰 {resultado} — {prefijo}@{nombre} sacó 3 {simbolo} (los admins juegan gratis, sin puntitos en juego).")
            else:
                await asyncio.to_thread(funcion_puntitos, nombre, ganancia)
                await mensaje(f"🎰 {resultado} — {prefijo}¡@{nombre} ganó {ganancia} puntitos!")
            return

        # 2 iguales (cualquier par entre los 3)
        if tirada[0] == tirada[1] or tirada[1] == tirada[2] or tirada[0] == tirada[2]:
            if es_admin:
                await mensaje(f"🎰 {resultado} — @{nombre} empató (los admins juegan gratis).")
            else:
                ganancia = apuesta
                await asyncio.to_thread(funcion_puntitos, nombre, ganancia)
                await mensaje(f"🎰 {resultado} — @{nombre} empató, ¡ganó {ganancia} puntitos (el doble de la apuesta)!")
            return

        # Sin coincidencias
        if es_admin:
            await mensaje(f"🎰 {resultado} — @{nombre} no tuvo suerte (los admins juegan gratis, sin puntitos en juego).")
        else:
            await asyncio.to_thread(funcion_puntitos, nombre, -apuesta)
            await mensaje(f"🎰 {resultado} — @{nombre} perdió {apuesta} puntitos.")
