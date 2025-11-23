import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import config

sp = None
if config.SPOTIPY_CLIENT_ID:
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
        client_id=config.SPOTIPY_CLIENT_ID,
        client_secret=config.SPOTIPY_CLIENT_SECRET
    ))

def get_spotify_tracks(search):
    """
    Busca tracks en Spotify y devuelve una lista de strings "Artista - Canción audio".
    """
    if not sp:
        return []

    tracks = []
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
        elif "album" in search:
            results = sp.album_tracks(search)
            items = results['items']
            for track in items:
                tracks.append(f"{track['artists'][0]['name']} - {track['name']} audio")
    except Exception as e:
        print(f"❌ Error Spotify: {e}")
        return []
    
    return tracks
