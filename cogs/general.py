import discord
from discord.ext import commands

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='help', aliases=['h'])
    async def help_command(self, ctx):
        embed = discord.Embed(
            title="🎧 Skibidi Bot - Comandos",
            description="Aquí tienes la lista de comandos para controlar la música.",
            color=discord.Color.from_rgb(29, 185, 84)  # Color verde Spotify
        )

        embed.add_field(
            name="▶️ Reproducción",
            value="**`!p <canción/link>`**: Reproduce o añade al final de la cola.\n"
                  "**`!pn <canción>`**: **Play Next**. Pone la canción SIGUIENTE en la fila (se cuela).\n"
                  "**`!stop`**: Detiene la música y desconecta al bot.",
            inline=False
        )

        embed.add_field(
            name="📜 Cola y Control",
            value="**`!q`**: Muestra la cola de reproducción actual.\n"
                  "**`!s`**: Salta la canción actual (`skip`).\n"
                  "**`!shuffle`**: Mezcla aleatoriamente la cola.",
            inline=False
        )

        embed.add_field(
            name="⏯️ Controles Extra",
            value="**`!pause` / `!resume`**: Pausa o reanuda la música.\n"
                  "**`!reset`**: Resetea el bot si se queda pillado.",
            inline=False
        )

        embed.set_footer(text="Soporta enlaces de YouTube y Spotify (Playlists/Albums)")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(General(bot))
