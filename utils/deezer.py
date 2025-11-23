import requests
import re

def get_deezer_tracks(url):
    """
    Busca tracks en Deezer y devuelve una lista de strings "Artista - Canción audio".
    Soporta tracks, albums y playlists.
    """
    tracks = []
    
    # Extraer ID del enlace
    # Ejemplos: https://www.deezer.com/track/12345, https://deezer.page.link/abcd
    
    # Si es un enlace corto (deezer.page.link), hay que resolverlo primero
    if "deezer.page.link" in url:
        try:
            response = requests.head(url, allow_redirects=True)
            url = response.url
        except Exception as e:
            print(f"❌ Error resolviendo enlace Deezer: {e}")
            return []

    # Regex para identificar tipo e ID
    match = re.search(r"deezer\.com/(?:\w{2}/)?(track|album|playlist)/(\d+)", url)
    if not match:
        return []

    type_ = match.group(1)
    id_ = match.group(2)
    
    api_url = f"https://api.deezer.com/{type_}/{id_}"
    
    try:
        response = requests.get(api_url)
        data = response.json()
        
        if 'error' in data:
            print(f"❌ Error API Deezer: {data['error']}")
            return []

        if type_ == 'track':
            artist = data['artist']['name']
            title = data['title']
            tracks.append(f"{artist} - {title} audio")
            
        elif type_ == 'album':
            if 'tracks' in data and 'data' in data['tracks']:
                for item in data['tracks']['data']:
                    tracks.append(f"{item['artist']['name']} - {item['title']} audio")
                    
        elif type_ == 'playlist':
            if 'tracks' in data and 'data' in data['tracks']:
                for item in data['tracks']['data']:
                    tracks.append(f"{item['artist']['name']} - {item['title']} audio")
                    
    except Exception as e:
        print(f"❌ Error obteniendo datos de Deezer: {e}")
        return []

    return tracks
