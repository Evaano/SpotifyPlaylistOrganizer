import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

# Load env vars from parent directory if needed, or local .env
load_dotenv(dotenv_path="../.env") 

app = FastAPI()

# Allow CORS for React frontend (default Port 5173)
# We allow both localhost and 127.0.0.1 to avoid cross-origin pitfalls during dev.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        os.getenv("FRONTEND_URL", "http://localhost:5173"),
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")
# Default to 127.0.0.1 since user's Spotify App is configured that way
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://127.0.0.1:5173").rstrip("/")
SCOPE = "playlist-read-private playlist-modify-public playlist-modify-private user-library-read"

# Global Auth Manager (Stateless for Vercel)
# We don't use cache_path here. We handle tokens manually via cookies.
sp_oauth = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SCOPE,
    show_dialog=True,
    cache_handler=None # Disable file caching
)

import json
from base64 import b64encode, b64decode

def get_token_from_cookie(request: Request):
    token_str = request.cookies.get("spotify_auth")
    if not token_str:
        return None
    try:
        return json.loads(b64decode(token_str).decode('utf-8'))
    except:
        return None

def get_spotify_client(request: Request = None, token_info=None):
    # If token_info is passed directly (e.g. inside callback), use it
    if not token_info and request:
        token_info = get_token_from_cookie(request)
    
    if not token_info:
        return None

    # Check validity and refresh if needed
    if sp_oauth.is_token_expired(token_info):
        try:
            token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        except Exception as e:
            print(f"Error refreshing token: {e}")
            return None

    return spotipy.Spotify(auth=token_info['access_token'])

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Spotify Sorter Backend is Running"}

@app.get("/login")
def login():
    auth_url = sp_oauth.get_authorize_url()
    return RedirectResponse(auth_url)

@app.get("/callback")
def callback(code: str):
    token_info = sp_oauth.get_access_token(code)
    
    # Serialize token info
    token_str = b64encode(json.dumps(token_info).encode('utf-8')).decode('utf-8')
    
    # Redirect to frontend with the cookie set
    response = RedirectResponse(f"{FRONTEND_URL}/dashboard")
    
    # Determine if we are in production based on FRONTEND_URL
    is_production = FRONTEND_URL.startswith("https")
    
    # Vital: Set path="/" to ensure cookie is available for all routes
    # We use SameSite="None" and Secure=True to allow cross-port usage on 127.0.0.1
    # Modern browsers allow Secure cookies on localhost/127.0.0.1 even without HTTPS.
    response.set_cookie(
        key="spotify_auth", 
        value=token_str, 
        httponly=True, 
        max_age=3600*24*7, # 1 week
        path="/",
        samesite="None",
        secure=True 
    )
    return response

@app.get("/api/playlists")
def get_playlists(request: Request):
    sp = get_spotify_client(request=request)
    if not sp:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        saved_tracks = sp.current_user_saved_tracks(limit=1)
        liked_songs_count = saved_tracks['total']
        
        # Create a pseudo-playlist object for Liked Songs
        liked_songs_playlist = {
            "id": "liked",
            "name": "Liked Songs",
            "images": [{"url": "https://misc.scdn.co/liked-songs/liked-songs-300.png"}],
            "tracks": {"total": liked_songs_count},
            "owner": {"display_name": "You"},
            "description": "Your Liked Songs"
        }
        
        results = sp.current_user_playlists(limit=50)
        playlists = results['items']
        while results['next']:
            results = sp.next(results)
            playlists.extend(results['items'])
            
        # Prepend Liked Songs to the list
        playlists.insert(0, liked_songs_playlist)
            
        return {"playlists": playlists}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Spotify API Error: {str(e)}")

@app.get("/api/status")
def get_status(request: Request):
    sp = get_spotify_client(request=request)
    if sp:
        return {"authenticated": True, "user": sp.current_user()['display_name']}
    return {"authenticated": False}

from pydantic import BaseModel
from typing import List

class CreatePlaylistRequest(BaseModel):
    name: str
    track_uris: List[str]

class CreateVibePlaylistRequest(BaseModel):
    name: str
    source_playlist_ids: str
    vibe: str

class DeletePlaylistRequest(BaseModel):
    playlist_id: str

@app.delete("/api/delete_playlist/{playlist_id}")
def delete_playlist(playlist_id: str, request: Request):
    """Unfollow/delete a playlist from the user's library."""
    sp = get_spotify_client(request=request)
    if not sp:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        # Spotify API uses "unfollow" to remove a playlist
        sp.current_user_unfollow_playlist(playlist_id)
        return {"status": "success", "message": "Playlist removed from your library"}
    except Exception as e:
        print(f"Error deleting playlist: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting playlist: {str(e)}")

VIBE_DEFINITIONS = {
    # DEPRESSY/SAD: Low valence is the KEY indicator (research confirms < 0.3-0.4)
    # Energy can vary, but typically lower for truly melancholic tracks
    "depressy": {
        "valence_max": 0.35,       # PRIMARY: Sad, melancholic mood (< 0.3-0.4 per research)
        "energy_max": 0.5,         # Generally calmer (can vary for "sad-energy" songs)
        "danceability_max": 0.55,  # Less danceable
    },
    # CHILL: Relaxed, not overly happy or sad, low energy
    # Research: valence 0.4-0.7, energy < 0.6, danceability < 0.6
    "chill": {
        "energy_max": 0.5,         # Low intensity, relaxed
        "valence_min": 0.3,        # Not too sad
        "valence_max": 0.7,        # Not overly euphoric
        "danceability_max": 0.6,   # Not high-energy dance tracks
    },
    # PARTY: High energy, high danceability, positive/euphoric mood
    # Research: valence > 0.7, energy > 0.7, danceability > 0.6-0.7
    "party": {
        "energy_min": 0.7,         # High intensity
        "danceability_min": 0.6,   # Suitable for dancing
        "valence_min": 0.6,        # Cheerful, euphoric
    },
    # INTENSE: Very high energy, darker mood (metal, aggressive EDM, workout)
    # High energy + low valence = aggressive/intense
    "intense": {
        "energy_min": 0.75,        # Very high intensity
        "valence_max": 0.5,        # Darker, not cheerful
    }
}

def fetch_unique_tracks(sp, playlist_ids_list):
    all_tracks = []
    seen_track_uris = set()
    
    for pid in playlist_ids_list:
        current_source_tracks = []
        
        # Determine source type: Liked Songs or regular playlist
        if pid == 'liked':
            print("Fetching Liked Songs...")
            results = sp.current_user_saved_tracks(limit=50)
            current_source_tracks.extend(results['items'])
            while results['next']:
                results = sp.next(results)
                current_source_tracks.extend(results['items'])
        else:
            try:
                print(f"Fetching playlist {pid}...")
                results = sp.playlist_items(pid, additional_types=['track'])
                current_source_tracks.extend(results['items'])
                while results['next']:
                    results = sp.next(results)
                    current_source_tracks.extend(results['items'])
            except Exception as e:
                print(f"Error fetching playlist {pid}: {e}")
                continue

        # Add unique tracks to master list
        for item in current_source_tracks:
            if not item or not item.get('track'):
                continue
            track = item['track']
            if track['uri'] not in seen_track_uris:
                seen_track_uris.add(track['uri'])
                all_tracks.append(item)
    return all_tracks

def fetch_audio_features_map(sp, track_ids):
    """
    Fetches audio features from ReccoBeats API (Spotify endpoint is deprecated).
    Uses: GET https://api.reccobeats.com/v1/audio-features?ids=...
    """
    import requests
    
    audio_features_map = {}
    RECCOBEATS_BASE = "https://api.reccobeats.com/v1/audio-features"
    
    # ReccoBeats batch limit is 40
    for i in range(0, len(track_ids), 40):
        batch = track_ids[i:i+40]
        if not batch: 
            continue
        try:
            ids_param = ",".join(batch)
            response = requests.get(f"{RECCOBEATS_BASE}?ids={ids_param}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                # ReccoBeats returns { "content": [...] }
                features_list = data.get("content", [])
                # Match features to track IDs by position (ReccoBeats returns UUIDs, not Spotify IDs)
                for idx, feat in enumerate(features_list):
                    if feat and idx < len(batch):
                        spotify_track_id = batch[idx]
                        audio_features_map[spotify_track_id] = feat
            else:
                print(f"ReccoBeats API returned {response.status_code}: {response.text[:100]}")
        except Exception as e:
            print(f"Error fetching audio features from ReccoBeats: {e}")
    
    return audio_features_map


@app.get("/api/analyze")
def analyze_playlists(playlist_ids: str, request: Request):
    """
    Analyzes one or more playlists (comma-separated IDs).
    Supports 'liked' as a special ID.
    Merges tracks from all sources and removes duplicates.
    """
    sp = get_spotify_client(request=request)
    if not sp:
        raise HTTPException(status_code=401, detail="Not authenticated")

    ids = playlist_ids.split(',')
    print(f"Analyzing playlists: {ids}")
    
    all_tracks = fetch_unique_tracks(sp, ids)


    # Extract Artists & Genres (Same logic as before, but on merged list)
    artist_ids = set()
    track_data = [] 
    
    for item in all_tracks:
        track = item['track']
        if track.get('artists'):
            current_track_artist_names = []
            current_track_artist_ids = []
            
            for artist in track['artists']:
                if artist.get('id'):
                    artist_ids.add(artist['id'])
                    current_track_artist_ids.append(artist['id'])
                current_track_artist_names.append(artist['name'])
            
            track_model = {
                "id": track['id'],
                "uri": track['uri'],
                "name": track['name'],
                "artists": current_track_artist_names,
                "artist_ids": current_track_artist_ids,
                "image": track['album']['images'][0]['url'] if track['album']['images'] else None,
                "genres": []
            }
            track_data.append(track_model)

    # Batch fetch artists
    artist_ids_list = list(artist_ids)
    artist_genres = {}
    
    for i in range(0, len(artist_ids_list), 50):
        batch = artist_ids_list[i:i+50]
        if not batch: continue
        artists_info = sp.artists(batch)
        for artist in artists_info['artists']:
            if artist:
                artist_genres[artist['id']] = artist['genres']

    # Map genres
    genre_counts = {}
    
    for track in track_data:
        t_genres = set()
        for aid in track['artist_ids']:
            if aid in artist_genres:
                t_genres.update(artist_genres[aid])
        
        track['genres'] = list(t_genres)
        
        for g in t_genres:
            genre_counts[g] = genre_counts.get(g, 0) + 1

    # Sort genres
    sorted_genres = dict(sorted(genre_counts.items(), key=lambda item: item[1], reverse=True))

    # Fetch Audio Features
    track_ids_for_features = [t['id'] for t in track_data if t.get('id')]
    audio_features_map = fetch_audio_features_map(sp, track_ids_for_features)

    # Attach features to tracks and calculate aggregates
    total_energy = 0
    total_valence = 0
    total_danceability = 0
    total_tempo = 0
    total_acousticness = 0
    total_instrumentalness = 0
    count_with_features = 0

    for track in track_data:
        tid = track.get('id')
        if tid in audio_features_map:
            feat = audio_features_map[tid]
            track['audio_features'] = {
                'energy': feat.get('energy', 0),
                'valence': feat.get('valence', 0),
                'danceability': feat.get('danceability', 0),
                'tempo': feat.get('tempo', 0),
                'instrumentalness': feat.get('instrumentalness', 0),
                'acousticness': feat.get('acousticness', 0)
            }
            total_energy += feat.get('energy', 0)
            total_valence += feat.get('valence', 0)
            total_danceability += feat.get('danceability', 0)
            total_tempo += feat.get('tempo', 0)
            total_acousticness += feat.get('acousticness', 0)
            total_instrumentalness += feat.get('instrumentalness', 0)
            count_with_features += 1
        else:
            track['audio_features'] = None

    avg_energy = total_energy / count_with_features if count_with_features > 0 else 0
    avg_valence = total_valence / count_with_features if count_with_features > 0 else 0
    avg_danceability = total_danceability / count_with_features if count_with_features > 0 else 0
    avg_tempo = total_tempo / count_with_features if count_with_features > 0 else 0
    avg_acousticness = total_acousticness / count_with_features if count_with_features > 0 else 0
    avg_instrumentalness = total_instrumentalness / count_with_features if count_with_features > 0 else 0

    return {
        "metrics": {
            "total_tracks": len(track_data),
            "unique_artists": len(artist_ids),
            "total_genres": len(sorted_genres),
            "tracks_with_features": count_with_features,
            "avg_energy": round(avg_energy, 2),
            "avg_valence": round(avg_valence, 2),
            "avg_danceability": round(avg_danceability, 2),
            "avg_tempo": round(avg_tempo, 1),
            "avg_acousticness": round(avg_acousticness, 2),
            "avg_instrumentalness": round(avg_instrumentalness, 2)
        },
        "genre_counts": sorted_genres,
        "tracks": track_data
    }

@app.post("/api/create_playlist")
def create_playlist(data: CreatePlaylistRequest, request: Request):
    sp = get_spotify_client(request=request)
    if not sp:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user_id = sp.current_user()['id']
    
    # 1. Check if playlist already exists
    user_playlists = sp.current_user_playlists(limit=50)
    target_playlist = None
    
    # Iterate to find existing playlist by name
    for pl in user_playlists['items']:
        if pl['name'] == data.name:
            target_playlist = pl
            break
            
    if not target_playlist:
        print(f"Creating new playlist: {data.name}")
        target_playlist = sp.user_playlist_create(
            user=user_id, 
            name=data.name, 
            public=False, 
            description="Created by Spotify Sorter"
        )
    else:
        print(f"Found existing playlist: {data.name} ({target_playlist['id']})")

    # 2. Deduplication check: Fetch existing tracks to avoid duplicates
    existing_track_uris = set()
    results = sp.playlist_items(target_playlist['id'], additional_types=['track'])
    for item in results['items']:
        if item.get('track'):
            existing_track_uris.add(item['track']['uri'])
            
    while results['next']:
        results = sp.next(results)
        for item in results['items']:
            if item.get('track'):
                existing_track_uris.add(item['track']['uri'])

    # Filter out tracks that are already in the playlist
    uris_to_add = [uri for uri in data.track_uris if uri not in existing_track_uris]

    # 3. Add tracks in batches of 100
    if uris_to_add:
        print(f"Adding {len(uris_to_add)} new tracks to {data.name}...")
        for i in range(0, len(uris_to_add), 100):
            batch = uris_to_add[i:i+100]
            sp.playlist_add_items(target_playlist['id'], batch)
            
        return {
            "status": "success", 
            "message": f"Added {len(uris_to_add)} new tracks to '{data.name}'.",
            "playlist_id": target_playlist['id'],
            "playlist_url": target_playlist['external_urls']['spotify']
        }
    else:
        return {
            "status": "success", 
            "message": "All tracks already exist in the playlist.",
            "playlist_id": target_playlist['id'],
            "playlist_url": target_playlist['external_urls']['spotify']
        }

@app.post("/api/create_vibe_playlist")
def create_vibe_playlist(data: CreateVibePlaylistRequest, request: Request):
    sp = get_spotify_client(request=request)
    if not sp:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user_id = sp.current_user()['id']
    
    # 1. Fetch Tracks
    playlist_ids = data.source_playlist_ids.split(',')
    all_tracks = fetch_unique_tracks(sp, playlist_ids)
    
    # 2. Extract IDs for audio features
    track_ids = [t['track']['id'] for t in all_tracks if t.get('track') and t['track'].get('id')]
    
    # 3. Fetch Audio Features
    features_map = fetch_audio_features_map(sp, track_ids)
    
    # 4. Filter Logic
    vibe_criteria = VIBE_DEFINITIONS.get(data.vibe)
    if not vibe_criteria:
        raise HTTPException(status_code=400, detail=f"Unknown vibe: {data.vibe}")
        
    filtered_uris = []
    
    for t in all_tracks:
        track = t.get('track')
        if not track: continue
        tid = track.get('id')
        if not tid or tid not in features_map:
            continue
            
        feat = features_map[tid]
        match = True
        
        # Check all criteria (e.g. min_energy, max_valence)
        for key, limit in vibe_criteria.items():
            # key is like 'energy_min', 'valence_max'
            metric = key.split('_')[0] # energy, valence, danceability
            op = key.split('_')[1]     # min/max
            
            val = feat.get(metric)
            if val is None:
                match = False
                break
                
            if op == 'min' and val < limit:
                match = False
                break
            if op == 'max' and val > limit:
                match = False
                break
        
        if match:
            filtered_uris.append(track['uri'])

    if not filtered_uris:
        return {
            "status": "error",
            "message": f"No tracks found matching vibe '{data.vibe}'",
            "count": 0
        }

    # 5. Create Playlist
    try:
        new_playlist = sp.user_playlist_create(
            user=user_id,
            name=data.name,
            public=False,
            description=f"Generated {data.vibe} playlist by Spotify Sorter"
        )
        
        # 6. Add tracks in batches
        for i in range(0, len(filtered_uris), 100):
            batch = filtered_uris[i:i+100]
            sp.playlist_add_items(new_playlist['id'], batch)
            
        return {
            "status": "success", 
            "message": f"Created playlist '{data.name}' with {len(filtered_uris)} tracks.",
            "playlist_id": new_playlist['id'],
            "playlist_url": new_playlist['external_urls']['spotify'],
            "track_count": len(filtered_uris)
        }
    except Exception as e:
        print(f"Error creating playlist: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating playlist: {str(e)}")
