import discord
from discord.ext import commands
import asyncio
import random
from utils.spotify import get_spotify_tracks
from utils.deezer import get_deezer_tracks
from utils.youtube import search_youtube
import config

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}
        self.ffmpeg_options = config.FFMPEG_OPTIONS
        self.disconnect_timers = {}
        self.preload_tasks = {}  # Tareas de precarga por guild
        self.preloaded_sources = {}  # Información de canciones precargadas por guild

    def cancel_disconnect_timer(self, guild_id):
        if guild_id in self.disconnect_timers:
            self.disconnect_timers[guild_id].cancel()
            del self.disconnect_timers[guild_id]

    async def disconnect_after_inactivity(self, ctx):
        guild_id = ctx.guild.id
        await asyncio.sleep(300)  # 5 minutos
        if ctx.voice_client and ctx.voice_client.is_connected() and not ctx.voice_client.is_playing():
            self.queues[guild_id] = []
            await ctx.voice_client.disconnect()
            await ctx.send("💤 **Me desconecté por inactividad.**")
        if guild_id in self.disconnect_timers:
            del self.disconnect_timers[guild_id]

    async def preload_next_task(self, guild_id):
        """Precarga la siguiente canción en la cola (solo extrae URL, no descarga)"""
        try:
            # Verificar que hay una siguiente canción
            if guild_id not in self.queues or len(self.queues[guild_id]) == 0:
                return
            
            next_query = self.queues[guild_id][0]
            
            # Verificar que no esté ya precargada
            if guild_id in self.preloaded_sources and self.preloaded_sources[guild_id]['query'] == next_query:
                return
            
            print(f"🔄 Precargando: {next_query}")
            
            # Extraer información con yt-dlp (solo URL, no descarga)
            track_info = await search_youtube(next_query)
            
            if track_info:
                self.preloaded_sources[guild_id] = {
                    'query': next_query,
                    'track_info': track_info
                }
                print(f"✅ Precargado: {track_info['title']}")
            else:
                print(f"⚠️ No se pudo precargar: {next_query}")
                
        except Exception as e:
            # Error silencioso - no debe afectar la reproducción actual
            print(f"❌ Error en precarga (silencioso): {e}")
        finally:
            # Limpiar referencia a la tarea
            if guild_id in self.preload_tasks:
                del self.preload_tasks[guild_id]

    async def play_next(self, ctx):
        if ctx.guild.id in self.queues and len(self.queues[ctx.guild.id]) > 0:
            self.cancel_disconnect_timer(ctx.guild.id)
            guild_id = ctx.guild.id
            query = self.queues[guild_id].pop(0)
            
            # Verificar conexión antes de reproducir
            if not ctx.voice_client or not ctx.voice_client.is_connected():
                return # Se desconectó, paramos la cola

            try:
                # Intentar usar datos precargados
                track_info = None
                if guild_id in self.preloaded_sources and self.preloaded_sources[guild_id]['query'] == query:
                    print(f"⚡ Usando canción precargada: {query}")
                    track_info = self.preloaded_sources[guild_id]['track_info']
                    del self.preloaded_sources[guild_id]  # Limpiar después de usar
                else:
                    # Si hay una tarea de precarga en curso, esperarla
                    if guild_id in self.preload_tasks:
                        print(f"⏳ Esperando precarga...")
                        try:
                            await asyncio.wait_for(self.preload_tasks[guild_id], timeout=5.0)
                            # Verificar de nuevo si se precargó
                            if guild_id in self.preloaded_sources and self.preloaded_sources[guild_id]['query'] == query:
                                track_info = self.preloaded_sources[guild_id]['track_info']
                                del self.preloaded_sources[guild_id]
                                print(f"⚡ Precarga completada justo a tiempo")
                        except asyncio.TimeoutError:
                            print(f"⚠️ Timeout esperando precarga, buscando normalmente...")
                    
                    # Si no se precargó o falló, buscar normalmente
                    if not track_info:
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
                
                # 🚀 LANZAR TAREA DE PRECARGA EN SEGUNDO PLANO
                # Cancelar cualquier tarea de precarga anterior
                if guild_id in self.preload_tasks:
                    self.preload_tasks[guild_id].cancel()
                
                # Crear nueva tarea de precarga para la siguiente canción
                if len(self.queues[guild_id]) > 0:
                    self.preload_tasks[guild_id] = asyncio.create_task(self.preload_next_task(guild_id))
                
            except Exception as e:
                print(f"Error reproduciendo {query}: {e}")
                await ctx.send(f"❌ Error reproduciendo esa canción. Pasando a la siguiente...")
                await self.play_next(ctx)
        else:
            # Cola vacía, iniciar timer de desconexión
            if ctx.guild.id not in self.disconnect_timers:
                self.disconnect_timers[ctx.guild.id] = self.bot.loop.create_task(self.disconnect_after_inactivity(ctx))

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
        # Deezer
        elif "deezer.com" in search or "deezer.page.link" in search:
            status_msg = await ctx.send("🌈 Leyendo Deezer...")
            found_tracks = get_deezer_tracks(search)
            if found_tracks:
                tracks.extend(found_tracks)
                await status_msg.edit(content=f"✅ Playlist cargada ({len(tracks)} canciones).")
            else:
                await status_msg.edit(content="❌ No se pudieron obtener canciones de Deezer.")
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
        guild_id = ctx.guild.id
        self.cancel_disconnect_timer(guild_id)
        self.queues[guild_id] = []
        
        # Cancelar tarea de precarga si existe
        if guild_id in self.preload_tasks:
            self.preload_tasks[guild_id].cancel()
            del self.preload_tasks[guild_id]
        
        # Limpiar datos precargados
        if guild_id in self.preloaded_sources:
            del self.preloaded_sources[guild_id]
        
        if ctx.voice_client:
            await ctx.voice_client.disconnect(force=True)
        await ctx.send("🔄 **Bot reseteado.** Intenta usar !p ahora.")

    @commands.command(name='stop')
    async def stop(self, ctx):
        if ctx.voice_client:
            guild_id = ctx.guild.id
            self.cancel_disconnect_timer(guild_id)
            self.queues[guild_id] = []
            
            # Cancelar tarea de precarga si existe
            if guild_id in self.preload_tasks:
                self.preload_tasks[guild_id].cancel()
                del self.preload_tasks[guild_id]
            
            # Limpiar datos precargados
            if guild_id in self.preloaded_sources:
                del self.preloaded_sources[guild_id]
            
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
            # Iniciar timer al pausar
            if ctx.guild.id not in self.disconnect_timers:
                self.disconnect_timers[ctx.guild.id] = self.bot.loop.create_task(self.disconnect_after_inactivity(ctx))
        else:
            await ctx.send("No hay música sonando para pausar.")

    @commands.command(name='resume', aliases=['r'])
    async def resume(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            self.cancel_disconnect_timer(ctx.guild.id)
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
            await asyncio.sleep(300)
            if voice_client.is_connected() and len(voice_client.channel.members) == 1:
                self.queues[member.guild.id] = []
                await voice_client.disconnect()

async def setup(bot):
    await bot.add_cog(Music(bot))
