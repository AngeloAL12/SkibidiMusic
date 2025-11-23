import requests
import re

def get_deezer_tracks(url):
    """
    Busca tracks en Deezer y devuelve un diccionario con:
    - 'tracks': lista de strings "Artista - Canción audio"
    - 'type': tipo de contenido ('track', 'album', 'playlist')
    Soporta tracks, albums y playlists.
    """
    tracks = []
    content_type = 'unknown'
    
    # Extraer ID del enlace
    # Ejemplos: https://www.deezer.com/track/12345, https://deezer.page.link/abcd
    
    # Si es un enlace corto (deezer.page.link o link.deezer.com), hay que resolverlo primero
    if "deezer.page.link" in url or "link.deezer.com" in url:
        try:
            response = requests.head(url, allow_redirects=True)
            url = response.url
        except Exception as e:
            print(f"❌ Error resolviendo enlace Deezer: {e}")
            return {'tracks': [], 'type': 'unknown'}

    # Regex para identificar tipo e ID
    match = re.search(r"deezer\.com/(?:\w{2}/)?(track|album|playlist)/(\d+)", url)
    if not match:
        return {'tracks': [], 'type': 'unknown'}

    type_ = match.group(1)
    id_ = match.group(2)
    content_type = type_
    
    api_url = f"https://api.deezer.com/{type_}/{id_}"
    
    try:
        response = requests.get(api_url)
        data = response.json()
        
        if 'error' in data:
            print(f"❌ Error API Deezer: {data['error']}")
            return {'tracks': [], 'type': 'unknown'}

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
        return {'tracks': [], 'type': 'unknown'}

    return {'tracks': tracks, 'type': content_type}
