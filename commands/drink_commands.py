"""
Comandos relacionados con bebidas y estado de embriaguez del bot

Este módulo maneja los comandos que afectan el nivel de intoxicación del bot,
incluyendo el consumo progresivo de grog y la hidratación.

Author: Demian762
Version: 250927
"""

from twitchio.ext import commands
from utils.mensaje import mensaje
from utils.configuracion import grog_list
from .base_command import BaseCommand

class DrinkCommands(BaseCommand):
    """
    Cog para comandos de bebidas y estado de embriaguez
    
    Maneja el sistema de intoxicación progresiva del bot mediante el comando grog
    y permite la sobriedad mediante el comando agua.
    
    Attributes:
        bot: Instancia del bot principal
        grog_list: Lista de frases progresivas de embriaguez
    """
    @commands.command()
    async def grog(self, ctx: commands.Context):
        """
        Comando para hacer que el bot tome grog y aumente su embriaguez
        
        Incrementa progresivamente el nivel de intoxicación del bot mostrando
        frases cada vez más borrachas de una lista predefinida.
        
        Args:
            ctx: Contexto del comando de Twitch
            
        Returns:
            None
            
        Example:
            !grog -> "Ahh, un buen grog"
        """
        if await self.check_coma_etilico():
            return
        
        # Verificar si el contador no excede la lista
        if self.bot.state.grog_count >= len(grog_list):
            self.bot.state.grog_count = len(grog_list) - 1
            
        texto = grog_list[self.bot.state.grog_count]
        await mensaje(texto)
        self.bot.state.grog_count += 1
    
    @commands.command(aliases=("agüita","aguita"))
    async def agua(self, ctx: commands.Context):
        """
        Comando para hidratar al bot y resetear su embriaguez
        
        Resetea el contador de grog a 0, devolviendo al bot a un estado sobrio.
        Tiene alias aguita y agüita para mayor accesibilidad.
        
        Args:
            ctx: Contexto del comando de Twitch
            
        Returns:
            None
            
        Example:
            !agua -> "Gracias {usuario} por darle agua al Bot."
        """
        self.bot.state.grog_count = 0
        await mensaje(f'Gracias {ctx.author.name} por darle agua al Bot.')
