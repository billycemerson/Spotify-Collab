import os
import json
import pandas as pd

# Path ke file JSON hasil scraping
DATA_PATH = os.path.join("..", "data", "indonesia_top_tracks.json")

# Load JSON
with open(DATA_PATH, "r", encoding="utf-8") as f:
    raw_data = json.load(f)

# Prepare lists
tracks_data = []
albums_data = []
artists_data = {}
track_artists_data = []

# Loop all tracks in JSON
for track_bundle in raw_data:
    track_id = track_bundle.get("track_id")
    if not track_id:
        continue

    # Track info
    album = track_bundle.get("album", {})
    album_id = album.get("id")

    is_collab = len(track_bundle.get("artists", [])) > 1

    tracks_data.append({
        "track_id": track_id,
        "track_name": track_bundle.get("track_name"),
        "duration_ms": track_bundle.get("duration_ms"),
        "popularity": track_bundle.get("track_popularity"),
        "album_id": album_id,
        "is_collab": is_collab,
    })

    # Album info
    if album_id:
        albums_data.append({
            "album_id": album_id,
            "album_name": album.get("name"),
            "album_type": album.get("album_type"),
            "release_date": album.get("release_date"),
            "total_tracks": album.get("total_tracks"),
            "url": album.get("external_urls", {}).get("spotify"),
        })

    # Artists
    for art in track_bundle.get("artists", []):
        artists_data[art["id"]] = {
            "artist_id": art["id"],
            "name": art.get("name"),
            "popularity": art.get("popularity"),
            "followers": art.get("followers", {}).get("total", 0) if "followers" in art else None,
            "genres": ",".join(art.get("genres", [])) if "genres" in art else None,
            "url": art.get("external_urls", {}).get("spotify"),
        }

        track_artists_data.append({
            "track_id": track_id,
            "artist_id": art.get("id")
        })

# Convert to DataFrames
df_tracks = pd.DataFrame(tracks_data).drop_duplicates("track_id")
df_albums = pd.DataFrame(albums_data).drop_duplicates("album_id")
df_artists = pd.DataFrame(list(artists_data.values())).drop_duplicates("artist_id")
df_track_artists = pd.DataFrame(track_artists_data).drop_duplicates()

# Directory for CSVs
output_dir = os.path.join("..", "data")
os.makedirs(output_dir, exist_ok=True)

# Save individual CSVs
df_tracks.to_csv(os.path.join(output_dir, "tracks.csv"), index=False)
df_albums.to_csv(os.path.join(output_dir, "albums.csv"), index=False)
df_artists.to_csv(os.path.join(output_dir, "artists.csv"), index=False)
df_track_artists.to_csv(os.path.join(output_dir, "track_artists.csv"), index=False)

print("✅ Individual CSV files saved!")

# Make one big denormalized table (track + album + artists names)
df_big = df_tracks.merge(df_albums, on="album_id", how="left", suffixes=("", "_album"))
df_big = df_big.merge(df_track_artists, on="track_id", how="left")
df_big = df_big.merge(df_artists[["artist_id", "name"]], on="artist_id", how="left")

# Group multiple artists per track into one string
df_big_grouped = (
    df_big.groupby(["track_id", "track_name", "duration_ms", "popularity", "album_id", "is_collab",
                    "album_name", "album_type", "release_date", "total_tracks", "url"])
    .agg({"name": lambda x: ", ".join(sorted(set(x.dropna())))})
    .reset_index()
    .rename(columns={"name": "artists"})
)

df_big_grouped.to_csv(os.path.join(output_dir, "spotify_big_table.csv"), index=False)
print("✅ Big denormalized table saved!")