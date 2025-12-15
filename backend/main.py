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
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:5173")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
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
    token_str = request.cookies.get("spotify_token")
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
            # Note: We can't update the cookie here easily without a Response object.
            # In a full conversion, we'd handle this middleware-style. 
            # For now, we'll return the new token info so the endpoint can set the cookie if needed, 
            # or just use it for this request.
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
    response.set_cookie(
        key="spotify_token", 
        value=token_str, 
        httponly=True, 
        max_age=3600*24*7, # 1 week
        samesite="lax",
        secure=False # Set to True in production (HTTPS)
    )
    return response

@app.get("/api/playlists")
def get_playlists(request: Request):
    sp = get_spotify_client(request=request)
    if not sp:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
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
    
    all_tracks = []
    seen_track_uris = set()
    
    for pid in ids:
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

    return {
        "metrics": {
            "total_tracks": len(track_data),
            "unique_artists": len(artist_ids),
            "total_genres": len(sorted_genres)
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
        if pl['name'] == request.name:
            target_playlist = pl
            break
            
    if not target_playlist:
        print(f"Creating new playlist: {request.name}")
        target_playlist = sp.user_playlist_create(
            user=user_id, 
            name=request.name, 
            public=False, 
            description="Created by Spotify Sorter"
        )
    else:
        print(f"Found existing playlist: {request.name} ({target_playlist['id']})")

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
    uris_to_add = [uri for uri in request.track_uris if uri not in existing_track_uris]

    # 3. Add tracks in batches of 100
    if uris_to_add:
        print(f"Adding {len(uris_to_add)} new tracks to {request.name}...")
        for i in range(0, len(uris_to_add), 100):
            batch = uris_to_add[i:i+100]
            sp.playlist_add_items(target_playlist['id'], batch)
            
        return {
            "status": "success", 
            "message": f"Added {len(uris_to_add)} new tracks to '{request.name}'.",
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
