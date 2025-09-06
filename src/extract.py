import os
import requests
import json
from dotenv import load_dotenv
from tqdm import tqdm
import time

# Load Spotify API credentials from .env file
load_dotenv("env", override=True)
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

def get_access_token():
    """Get a new access token using Client Credentials flow"""
    url = "https://accounts.spotify.com/api/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {"grant_type": "client_credentials"}
    resp = requests.post(url, headers=headers, data=data, auth=(CLIENT_ID, CLIENT_SECRET))
    resp.raise_for_status()
    return resp.json()["access_token"]

def spotify_get(url, token, params=None):
    """Generic GET request to Spotify Web API with rate limit handling"""
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers, params=params)
    if resp.status_code == 429:  # Handle rate limit
        retry_after = int(resp.headers.get("Retry-After", 1))
        print(f"Rate limited. Waiting {retry_after} seconds...")
        time.sleep(retry_after)
        return spotify_get(url, token, params)
    resp.raise_for_status()
    return resp.json()

def get_playlist_tracks(playlist_id, token, limit=100):
    """Fetch all tracks from a given playlist"""
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    results = []
    offset = 0
    while True:
        params = {"limit": limit, "offset": offset}
        data = spotify_get(url, token, params)
        items = data.get("items", [])
        if not items:
            break
        results.extend(items)
        offset += limit
        if offset >= data["total"]:
            break
    return results

def get_artist_info(artist_id, token):
    """Fetch detailed information about an artist"""
    url = f"https://api.spotify.com/v1/artists/{artist_id}"
    return spotify_get(url, token)

def get_album_info(album_id, token):
    """Fetch detailed information about an album"""
    url = f"https://api.spotify.com/v1/albums/{album_id}"
    return spotify_get(url, token)

if __name__ == "__main__":
    token = get_access_token()

    # Spotify playlist
    playlist_id = "7KHJBz12xG3fPKErBd41K9" #Top 50 Terbaik & Terpopuler 2025

    # Create data folder
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(data_dir, exist_ok=True)

    # Step 1: Fetch all playlist tracks
    playlist_tracks = get_playlist_tracks(playlist_id, token)
    print(f"✅ {len(playlist_tracks)} tracks found in playlist")

    all_data = []
    artist_cache, album_cache = {}, {}

    for item in tqdm(playlist_tracks, desc="Processing tracks"):
        track = item["track"]
        if not track:
            continue

        track_id = track["id"]
        track_name = track["name"]
        track_popularity = track.get("popularity", None)
        duration_ms = track.get("duration_ms", None)

        # Collect artist information
        artists_info = []
        artist_names = []
        for artist in track.get("artists", []):
            aid = artist["id"]
            if aid not in artist_cache:
                try:
                    artist_cache[aid] = get_artist_info(aid, token)
                except Exception as e:
                    print(f"⚠️ Error fetching artist {aid}: {e}")
                    artist_cache[aid] = {}
                    continue
            artists_info.append(artist_cache[aid])
            artist_names.append(artist_cache[aid].get("name", "Unknown"))

        # Collect album information
        album_id = track["album"]["id"]
        if album_id not in album_cache:
            try:
                album_cache[album_id] = get_album_info(album_id, token)
            except Exception as e:
                print(f"⚠️ Error fetching album {album_id}: {e}")
                album_cache[album_id] = {}
        album_info = album_cache[album_id]

        # Collaboration check
        is_collab = len(artist_names) > 1
        collab_with = {}
        if is_collab:
            # Map each artist to the others they collaborated with
            for i, name in enumerate(artist_names):
                collab_with[name] = [n for j, n in enumerate(artist_names) if j != i]

        all_data.append({
            "track_id": track_id,
            "track_name": track_name,
            "track_popularity": track_popularity,
            "duration_ms": duration_ms,
            "is_collab": is_collab,
            "artists": artists_info,
            "album": album_info,
            "collab_with": collab_with
        })

        # Small delay to avoid hitting rate limit
        time.sleep(0.1)

    # Step 2: Save results to JSON file
    output_file = os.path.join(data_dir, "indonesia_top_tracks.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print(f"🎉 Data for {len(all_data)} tracks saved to {output_file}")