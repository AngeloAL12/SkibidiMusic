import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os
import spotipy
import random
import shutil
from spotipy.oauth2 import SpotifyClientCredentials
import base64

# --- DIAGNÓSTICO AL INICIO ---
print("🔍 DIAGNÓSTICO DE NODE:")
node_path = shutil.which("node") or shutil.which("nodejs")
print(f"👉 Python ve a Node en: {node_path}")

# Gestión de Cookies
if os.getenv('YOUTUBE_COOKIES_B64'):
    try:
        with open('cookies.txt', 'wb') as f:
            f.write(base64.b64decode(os.getenv('YOUTUBE_COOKIES_B64')))
        print("🍪 Cookies regeneradas desde variable de entorno.")
    except Exception as e:
        print(f"⚠️ Error regenerando cookies: {e}")

# --- CONFIGURACIÓN DISCORD ---
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)
bot.remove_command('help')

# --- CONFIGURACIÓN SPOTIFY ---
sp = None
if os.getenv('SPOTIPY_CLIENT_ID'):
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
        client_id=os.getenv('SPOTIPY_CLIENT_ID'),
        client_secret=os.getenv('SPOTIPY_CLIENT_SECRET')
    ))

# --- CONFIGURACIÓN YOUTUBE ---
ydl_opts = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'player_client': ['ios', 'android', 'web'], # Rotación de clientes para evitar bloqueos
    'source_address': '0.0.0.0',
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'cachedir': False
}

try:
    ytdl = yt_dlp.YoutubeDL(ydl_opts)
except Exception as e:
    print(f"Error inicializando yt-dlp: {e}")

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

# --- VARIABLES GLOBALES ---
queues = {}

# --- FUNCIONES ---

async def search_youtube(query):
    loop = bot.loop or asyncio.get_running_loop()
    try:
        if "youtube.com" in query or "youtu.be" in query:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(query, download=False))
        else:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(f"ytsearch1:{query}", download=False))
        
        if 'entries' in data:
            data = data['entries'][0]
        return {'url': data['url'], 'title': data['title']}
    except Exception as e:
        print(f"Error buscando en YT: {e}")
        return None

async def play_next(ctx):
    if ctx.guild.id in queues and len(queues[ctx.guild.id]) > 0:
        query = queues[ctx.guild.id].pop(0)
        
        # Verificar conexión antes de reproducir
        if not ctx.voice_client or not ctx.voice_client.is_connected():
            return # Se desconectó, paramos la cola

        try:
            print(f"🔎 Buscando: {query}")
            track_info = await search_youtube(query)
            
            if not track_info:
                await ctx.send(f"⚠️ No pude encontrar: {query}. Pasando a la siguiente.")
                await play_next(ctx)
                return

            source = discord.FFmpegPCMAudio(track_info['url'], **ffmpeg_options)
            
            # Callback seguro para la siguiente canción
            def after_playing(error):
                if error:
                    print(f"Error de reproducción: {error}")
                coro = play_next(ctx)
                fut = asyncio.run_coroutine_threadsafe(coro, bot.loop)
                try:
                    fut.result()
                except:
                    pass

            ctx.voice_client.play(source, after=after_playing)
            await ctx.send(f"🎶 Reproduciendo: **{track_info['title']}**")
            
        except Exception as e:
            print(f"Error reproduciendo {query}: {e}")
            await ctx.send(f"❌ Error reproduciendo esa canción. Pasando a la siguiente...")
            await play_next(ctx)
    else:
        # Cola vacía
        pass

async def get_tracks_from_query(ctx, search):
    tracks = []
    # Spotify
    if "spotify.com" in search and sp:
        status_msg = await ctx.send("🟢 Leyendo Spotify...")
        try:
            if "track" in search:
                track = sp.track(search)
                tracks.append(f"{track['artists'][0]['name']} - {track['name']} audio")
            elif "playlist" in search:
                results = sp.playlist_items(search)
                items = results['items']
                while results['next'] and len(tracks) < 50: 
                    results = sp.next(results)
                    items.extend(results['items'])
                for item in items:
                    if item['track']:
                        tracks.append(f"{item['track']['artists'][0]['name']} - {item['track']['name']} audio")
                await status_msg.edit(content=f"✅ Playlist cargada ({len(tracks)} canciones).")
            elif "album" in search:
                results = sp.album_tracks(search)
                items = results['items']
                for track in items:
                    tracks.append(f"{track['artists'][0]['name']} - {track['name']} audio")
                await status_msg.edit(content=f"✅ Álbum cargado ({len(tracks)} canciones).")
        except Exception as e:
            await ctx.send(f"❌ Error Spotify: {e}")
            return []
    else:
        # YouTube
        if not search.startswith("http"):
            search += " audio"
        tracks.append(search)
    return tracks

# --- EVENTOS ---

@bot.event
async def on_ready():
    print(f'✅ Bot conectado como {bot.user} (ID: {bot.user.id})')

@bot.event
async def on_voice_state_update(member, before, after):
    if member == bot.user: return
    voice_client = member.guild.voice_client
    if voice_client and len(voice_client.channel.members) == 1:
        await asyncio.sleep(60)
        if voice_client.is_connected() and len(voice_client.channel.members) == 1:
            queues[member.guild.id] = []
            await voice_client.disconnect()

# --- COMANDOS BLINDADOS ---

@bot.command(name='play', aliases=['p'])
async def play(ctx, *, search):
    if not ctx.author.voice: return await ctx.send("❌ Entra a un canal de voz.")
    
    # --- LOGICA DE CONEXIÓN ROBUSTA (AUTO-HEALING) ---
    vc = ctx.voice_client
    try:
        if vc is None:
            # Intentamos conectar
            await ctx.author.voice.channel.connect(self_deaf=True, timeout=20)
        elif vc.channel != ctx.author.voice.channel:
            # Estamos en otro canal, nos movemos
            await vc.move_to(ctx.author.voice.channel)
        # Si ya estamos conectados en el mismo canal, NO hacemos nada (evita errores)
    except asyncio.TimeoutError:
        await ctx.send("⚠️ Timeout conectando. Intentando forzar reconexión...")
        # Limpieza de emergencia
        if ctx.guild.voice_client:
            await ctx.guild.voice_client.disconnect(force=True)
        await asyncio.sleep(1)
        try:
            await ctx.author.voice.channel.connect(self_deaf=True, timeout=20)
        except Exception as e:
            return await ctx.send(f"❌ Error fatal de conexión: {e}. Prueba !reset")
    except Exception as e:
        return await ctx.send(f"❌ Error de conexión: {e}")

    # --- CARGA DE CANCIONES ---
    tracks = await get_tracks_from_query(ctx, search)
    if not tracks: return

    guild_id = ctx.guild.id
    if guild_id not in queues: queues[guild_id] = []

    queues[guild_id].extend(tracks)
    await ctx.send(f"✅ Añadido a la cola ({len(tracks)} items).")

    # Si no está reproduciendo, iniciar.
    if ctx.voice_client and not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
        await play_next(ctx)

@bot.command(name='reset')
async def reset(ctx):
    """Comando de emergencia para desbugear el bot"""
    queues[ctx.guild.id] = []
    if ctx.voice_client:
        await ctx.voice_client.disconnect(force=True)
    await ctx.send("🔄 **Bot reseteado.** Intenta usar !p ahora.")

@bot.command(name='stop')
async def stop(ctx):
    if ctx.voice_client:
        queues[ctx.guild.id] = []
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Adiós.")

@bot.command(name='skip', aliases=['s'])
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭️ Saltando...")

@bot.command(name='queue', aliases=['q'])
async def queue(ctx):
    if ctx.guild.id in queues and queues[ctx.guild.id]:
        msg = "**Cola de reproducción:**\n"
        for i, track in enumerate(queues[ctx.guild.id][:10], 1):
            clean = track.replace(" audio", "")
            msg += f"**{i}.** {clean}\n"
        await ctx.send(msg)
    else:
        await ctx.send("La cola está vacía.")

# --- RUN ---
if __name__ == "__main__":
    token = os.getenv('DISCORD_TOKEN')
    if token:
        bot.run(token)