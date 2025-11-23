import os
from dotenv import load_dotenv

load_dotenv()

# Discord
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

# Spotify
SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')

# YouTube Cookies
YOUTUBE_COOKIES_B64 = os.getenv('YOUTUBE_COOKIES_B64')

# YouTube DL Options
YDL_OPTS = {
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

# FFMPEG Options
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -reconnect_on_network_error 1',
    'options': '-vn'
}
