import discord
from discord.ext import commands
import asyncio
import random
from utils.spotify import get_spotify_tracks
from utils.youtube import search_youtube
import config

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}
        self.ffmpeg_options = config.FFMPEG_OPTIONS

    async def play_next(self, ctx):
        if ctx.guild.id in self.queues and len(self.queues[ctx.guild.id]) > 0:
            query = self.queues[ctx.guild.id].pop(0)
            
            # Verificar conexión antes de reproducir
            if not ctx.voice_client or not ctx.voice_client.is_connected():
                return # Se desconectó, paramos la cola

            try:
                print(f"🔎 Buscando: {query}")
                track_info = await search_youtube(query)
                
                if not track_info:
                    await ctx.send(f"⚠️ No pude encontrar: {query}. Pasando a la siguiente.")
                    await self.play_next(ctx)
                    return

                source = discord.FFmpegPCMAudio(track_info['url'], **self.ffmpeg_options)
                
                # Callback seguro para la siguiente canción
                def after_playing(error):
                    if error:
                        print(f"Error de reproducción: {error}")
                    coro = self.play_next(ctx)
                    fut = asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
                    try:
                        fut.result()
                    except:
                        pass

                ctx.voice_client.play(source, after=after_playing)
                await ctx.send(f"🎶 Reproduciendo: **{track_info['title']}**")
                
            except Exception as e:
                print(f"Error reproduciendo {query}: {e}")
                await ctx.send(f"❌ Error reproduciendo esa canción. Pasando a la siguiente...")
                await self.play_next(ctx)
        else:
            # Cola vacía
            pass

    async def ensure_voice_connection(self, ctx):
        if not ctx.author.voice:
            await ctx.send("❌ Entra a un canal de voz.")
            return False
        
        vc = ctx.voice_client
        try:
            if vc is None:
                # Intentamos conectar
                await ctx.author.voice.channel.connect(self_deaf=True, timeout=20)
            elif vc.channel != ctx.author.voice.channel:
                # Estamos en otro canal, nos movemos
                await vc.move_to(ctx.author.voice.channel)
            # Si ya estamos conectados en el mismo canal, NO hacemos nada (evita errores)
            return True
        except asyncio.TimeoutError:
            await ctx.send("⚠️ Timeout conectando. Intentando forzar reconexión...")
            # Limpieza de emergencia
            if ctx.guild.voice_client:
                await ctx.guild.voice_client.disconnect(force=True)
            await asyncio.sleep(1)
            try:
                await ctx.author.voice.channel.connect(self_deaf=True, timeout=20)
                return True
            except Exception as e:
                await ctx.send(f"❌ Error fatal de conexión: {e}. Prueba !reset")
                return False
        except Exception as e:
            await ctx.send(f"❌ Error de conexión: {e}")
            return False

    async def get_tracks_from_query(self, ctx, search):
        tracks = []
        # Spotify
        if "spotify.com" in search:
            status_msg = await ctx.send("🟢 Leyendo Spotify...")
            found_tracks = get_spotify_tracks(search)
            if found_tracks:
                tracks.extend(found_tracks)
                await status_msg.edit(content=f"✅ Playlist cargada ({len(tracks)} canciones).")
            else:
                await status_msg.edit(content="❌ No se pudieron obtener canciones de Spotify.")
        else:
            # YouTube
            if not search.startswith("http"):
                search += " audio"
            tracks.append(search)
        return tracks

    @commands.command(name='play', aliases=['p'])
    async def play(self, ctx, *, search):
        if not await self.ensure_voice_connection(ctx):
            return

        # --- CARGA DE CANCIONES ---
        tracks = await self.get_tracks_from_query(ctx, search)
        if not tracks: return

        guild_id = ctx.guild.id
        if guild_id not in self.queues: self.queues[guild_id] = []

        self.queues[guild_id].extend(tracks)

        # Si ya está sonando, avisar que se agregó a la cola
        if ctx.voice_client and (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
            await ctx.send(f"✅ Añadido a la cola. Canciones en espera: {len(self.queues[guild_id])}")
        else:
            # Si no suena nada, reproducir de inmediato
            await self.play_next(ctx)

    @commands.command(name='playnext', aliases=['pn'])
    async def playnext(self, ctx, *, search):
        if not await self.ensure_voice_connection(ctx):
            return

        tracks = await self.get_tracks_from_query(ctx, search)
        if not tracks: return

        guild_id = ctx.guild.id
        if guild_id not in self.queues: self.queues[guild_id] = []

        self.queues[guild_id][0:0] = tracks

        if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
            await self.play_next(ctx)
        else:
            clean = tracks[0].replace(" audio", "")
            await ctx.send(f"⚡ **Siguiente en la cola:** {clean}")

    @commands.command(name='shuffle', aliases=['mix'])
    async def shuffle(self, ctx):
        guild_id = ctx.guild.id
        if guild_id in self.queues and len(self.queues[guild_id]) > 0:
            random.shuffle(self.queues[guild_id])
            await ctx.send("🔀 **Cola mezclada aleatoriamente.**")
        else:
            await ctx.send("No hay canciones en la cola.")

    @commands.command(name='reset')
    async def reset(self, ctx):
        """Comando de emergencia para desbugear el bot"""
        self.queues[ctx.guild.id] = []
        if ctx.voice_client:
            await ctx.voice_client.disconnect(force=True)
        await ctx.send("🔄 **Bot reseteado.** Intenta usar !p ahora.")

    @commands.command(name='stop')
    async def stop(self, ctx):
        if ctx.voice_client:
            self.queues[ctx.guild.id] = []
            await ctx.voice_client.disconnect()
            await ctx.send("👋 Adiós.")

    @commands.command(name='skip', aliases=['s'])
    async def skip(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("⏭️ Saltando...")

    @commands.command(name='pause')
    async def pause(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send("⏸️ **Música pausada.**")
        else:
            await ctx.send("No hay música sonando para pausar.")

    @commands.command(name='resume', aliases=['r'])
    async def resume(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send("▶️ **Música reanudada.**")
        else:
            await ctx.send("La música no está pausada.")

    @commands.command(name='queue', aliases=['q'])
    async def queue(self, ctx):
        if ctx.guild.id in self.queues and self.queues[ctx.guild.id]:
            msg = "**Cola de reproducción:**\n"
            for i, track in enumerate(self.queues[ctx.guild.id][:10], 1):
                clean = track.replace(" audio", "")
                msg += f"**{i}.** {clean}\n"
            await ctx.send(msg)
        else:
            await ctx.send("La cola está vacía.")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member == self.bot.user: return
        voice_client = member.guild.voice_client
        if voice_client and len(voice_client.channel.members) == 1:
            await asyncio.sleep(60)
            if voice_client.is_connected() and len(voice_client.channel.members) == 1:
                self.queues[member.guild.id] = []
                await voice_client.disconnect()

async def setup(bot):
    await bot.add_cog(Music(bot))
