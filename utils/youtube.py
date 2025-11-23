import yt_dlp
import asyncio
import os
import base64
import config

# Gestión de Cookies
if config.YOUTUBE_COOKIES_B64:
    try:
        with open('cookies.txt', 'wb') as f:
            f.write(base64.b64decode(config.YOUTUBE_COOKIES_B64))
        print("🍪 Cookies regeneradas desde variable de entorno.")
    except Exception as e:
        print(f"⚠️ Error regenerando cookies: {e}")

try:
    ytdl = yt_dlp.YoutubeDL(config.YDL_OPTS)
except Exception as e:
    print(f"Error inicializando yt-dlp: {e}")
    ytdl = None

async def search_youtube(query):
    if not ytdl:
        return None
        
    loop = asyncio.get_running_loop()
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
