import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os
import spotipy
import random
import base64

from spotipy.oauth2 import SpotifyClientCredentials

if os.getenv('YOUTUBE_COOKIES_B64'):
    with open('cookies.txt', 'wb') as f:
        f.write(base64.b64decode(os.getenv('YOUTUBE_COOKIES_B64')))
    print("🍪 Archivo cookies.txt regenerado desde Variable de Entorno.")


# --- CONFIGURACIÓN ---
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)
# Borramos el comando help por defecto para poner uno bonito
bot.remove_command('help')

# Configuración de Spotify
sp = None
if os.getenv('SPOTIPY_CLIENT_ID'):
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
        client_id=os.getenv('SPOTIPY_CLIENT_ID'),
        client_secret=os.getenv('SPOTIPY_CLIENT_SECRET')
    ))

# Configuración de YouTube y FFmpeg
yt_dl_options = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    # 'cookiefile': 'cookies.txt', <--- COMENTA O BORRA ESTA LÍNEA
    'cachedir': False,
    'extractor_args': {
        'youtube': {
            # Probamos iOS primero, luego Android, luego Web como último recurso
            'player_client': ['ios', 'android', 'web']
        }
    }
}
ytdl = yt_dlp.YoutubeDL(yt_dl_options)

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

# --- VARIABLES GLOBALES ---
queues = {}


# --- FUNCIONES DE AYUDA ---

async def search_youtube(query):
    loop = asyncio.get_event_loop()
    if "youtube.com" in query or "youtu.be" in query:
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(query, download=False))
    else:
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(f"ytsearch1:{query}", download=False))

    if 'entries' in data:
        data = data['entries'][0]
    return {'url': data['url'], 'title': data['title']}


async def play_next(ctx):
    if ctx.guild.id in queues and len(queues[ctx.guild.id]) > 0:
        query = queues[ctx.guild.id].pop(0)
        try:
            track_info = await search_youtube(query)
            source = discord.FFmpegPCMAudio(track_info['url'], **ffmpeg_options)
            ctx.voice_client.play(source, after=lambda e: bot.loop.create_task(play_next(ctx)))

            # Título limpio para el chat
            display_title = track_info['title']
            await ctx.send(f"🎶 Reproduciendo: **{display_title}**")
        except Exception as e:
            await ctx.send(f"❌ Error al reproducir '{query}': {e}")
            await play_next(ctx)


async def get_tracks_from_query(ctx, search):
    tracks = []
    # Lógica Spotify
    if "open.spotify.com" in search and sp:
        status_msg = await ctx.send("🟢 Procesando enlace de Spotify...")
        try:
            if "track" in search:
                track = sp.track(search)
                tracks.append(f"{track['artists'][0]['name']} - {track['name']} audio")
            elif "playlist" in search:
                results = sp.playlist_items(search)
                items = results['items']
                while results['next']:
                    results = sp.next(results)
                    items.extend(results['items'])
                for item in items:
                    if item['track']:
                        tracks.append(f"{item['track']['artists'][0]['name']} - {item['track']['name']} audio")
                await status_msg.edit(content=f"✅ Playlist cargada ({len(tracks)} canciones).")
            elif "album" in search:
                results = sp.album_tracks(search)
                items = results['items']
                while results['next']:
                    results = sp.next(results)
                    items.extend(results['items'])
                for track in items:
                    tracks.append(f"{track['artists'][0]['name']} - {track['name']} audio")
                await status_msg.edit(content=f"✅ Álbum cargado ({len(tracks)} canciones).")
        except Exception as e:
            await ctx.send(f"❌ Error con Spotify: {e}")
            return []
    else:
        # Lógica YouTube
        if not search.startswith("http"):
            search += " audio"
        tracks.append(search)
    return tracks


# --- EVENTOS ---

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user} (Listo para la acción)')


@bot.event
async def on_voice_state_update(member, before, after):
    if member == bot.user: return
    voice_client = member.guild.voice_client
    if voice_client and len(voice_client.channel.members) == 1:
        await asyncio.sleep(60)
        if voice_client.is_connected() and len(voice_client.channel.members) == 1:
            queues[member.guild.id] = []
            await voice_client.disconnect()


# --- COMANDOS PRINCIPALES ---

@bot.command(name='help', aliases=['h'])
async def help_command(ctx):
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
        name="▶️ Reproducción",
        value="**`!p <canción>`**: Reproduce o añade a la cola.\n"
              "**`!pn <canción>`**: Pone la canción SIGUIENTE (Play Next).\n"
              "**`!pause` / `!resume`**: Pausa o reanuda la música.\n"
              "**`!stop`**: Detiene y desconecta al bot.",
        inline=False
    )

    embed.set_footer(text="Soporta enlaces de YouTube y Spotify (Playlists/Albums)")
    await ctx.send(embed=embed)


@bot.command(name='play', aliases=['p'])
async def play(ctx, *, search):
    if not ctx.author.voice: return await ctx.send("❌ Entra a un canal de voz.")
    if ctx.voice_client is None:
        await ctx.author.voice.channel.connect()
    elif ctx.voice_client.channel != ctx.author.voice.channel:
        await ctx.voice_client.move_to(ctx.author.voice.channel)

    tracks = await get_tracks_from_query(ctx, search)
    if not tracks: return

    guild_id = ctx.guild.id
    if guild_id not in queues: queues[guild_id] = []

    queues[guild_id].extend(tracks)

    if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
        await play_next(ctx)
    elif len(tracks) == 1:
        clean = tracks[0].replace(" audio", "")
        await ctx.send(f"✅ Añadido a la cola: **{clean}**")


@bot.command(name='playnext', aliases=['pn'])
async def playnext(ctx, *, search):
    if not ctx.author.voice: return await ctx.send("❌ Entra a un canal de voz.")
    if ctx.voice_client is None: await ctx.author.voice.channel.connect()

    tracks = await get_tracks_from_query(ctx, search)
    if not tracks: return

    guild_id = ctx.guild.id
    if guild_id not in queues: queues[guild_id] = []

    queues[guild_id][0:0] = tracks

    if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
        await play_next(ctx)
    else:
        clean = tracks[0].replace(" audio", "")
        await ctx.send(f"⚡ **Siguiente en la cola:** {clean}")


@bot.command(name='shuffle', aliases=['mix'])
async def shuffle(ctx):
    guild_id = ctx.guild.id
    if guild_id in queues and len(queues[guild_id]) > 0:
        random.shuffle(queues[guild_id])
        await ctx.send("🔀 **Cola mezclada aleatoriamente.**")
    else:
        await ctx.send("No hay canciones en la cola.")


@bot.command(name='skip', aliases=['s'])
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭️ Saltando...")


@bot.command(name='pause')
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸️ **Música pausada.**")
    else:
        await ctx.send("No hay música sonando para pausar.")

@bot.command(name='resume', aliases=['r'])
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️ **Música reanudada.**")
    else:
        await ctx.send("La música no está pausada.")



@bot.command(name='queue', aliases=['q'])
async def queue(ctx):
    if ctx.guild.id in queues and queues[ctx.guild.id]:
        msg = "**Cola de reproducción:**\n"
        for i, track in enumerate(queues[ctx.guild.id][:10], 1):
            display_name = track.replace(" audio", "")
            msg += f"**{i}.** {display_name}\n"
        if len(queues[ctx.guild.id]) > 10:
            msg += f"... y {len(queues[ctx.guild.id]) - 10} más."
        await ctx.send(msg)
    else:
        await ctx.send("La cola está vacía.")


@bot.command(name='stop')
async def stop(ctx):
    if ctx.voice_client:
        queues[ctx.guild.id] = []
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Adiós.")


if __name__ == "__main__":
    token = os.getenv('DISCORD_TOKEN')
    if token:
        bot.run(token)
    else:
        print("Error: DISCORD_TOKEN no encontrado.")