import pandas as pd
import matplotlib.pyplot as plt
import os

# === Load Data ===
df = pd.read_csv("../data/spotify_big_table.csv")

# Buat folder hasil kalau belum ada
os.makedirs("../results", exist_ok=True)

# === 1. Distribusi Popularity ===
plt.figure(figsize=(8,5))
df["popularity"].hist(bins=20, edgecolor="black")
plt.title("Popularity Distribution")
plt.xlabel("Popularity")
plt.ylabel("Count")
plt.savefig("../results/popularity_distribution.png")
plt.close()

# === 2. Kolaborasi vs Non-Kolaborasi ===
avg_collab = df.groupby("is_collab")["popularity"].mean()
avg_collab.plot(kind="bar", color=["skyblue","orange"])
plt.title("Average Popularity: Collab vs Non-Collab")
plt.ylabel("Avg Popularity")
plt.xticks(rotation=0)
plt.savefig("../results/collab_vs_noncollab.png")
plt.close()

# === 3. Single vs Album ===
avg_album = df.groupby("album_type")["popularity"].mean()
avg_album.plot(kind="bar", color=["green","purple"])
plt.title("Average Popularity: Single vs Album")
plt.ylabel("Avg Popularity")
plt.xticks(rotation=0)
plt.savefig("../results/single_vs_album.png")
plt.close()

# === 4. Top 10 Artists ===
# Ambil nama artis pertama dari list artists
df["main_artist"] = df["artists"].str.split(",").str[0]
top_artists = df.groupby("main_artist")["popularity"].mean().sort_values(ascending=False).head(10)
top_artists.plot(kind="bar", color="teal")
plt.title("Top 10 Artists by Avg Popularity")
plt.ylabel("Avg Popularity")
plt.xticks(rotation=45, ha="right")
plt.savefig("../results/top_artists.png")
plt.close()

# === 5. Popularity by Release Year ===
df["release_year"] = pd.to_datetime(df["release_date"], errors="coerce").dt.year
yearly_pop = df.groupby("release_year")["popularity"].mean().dropna()
yearly_pop.plot(kind="line", marker="o", color="red")
plt.title("Average Popularity by Release Year")
plt.xlabel("Year")
plt.ylabel("Avg Popularity")
plt.savefig("../results/popularity_by_year.png")
plt.close()

# === 6. Duration vs Popularity ===
plt.figure(figsize=(8,5))
plt.scatter(df["duration_ms"]/60000, df["popularity"], alpha=0.5)
plt.title("Duration vs Popularity")
plt.xlabel("Duration (minutes)")
plt.ylabel("Popularity")
plt.savefig("../results/duration_vs_popularity.png")
plt.close()

print("✅ Analysis complete! Results saved in '../results' folder.")