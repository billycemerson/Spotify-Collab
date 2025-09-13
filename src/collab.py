import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import os

# === Load Data ===
df = pd.read_csv("../data/spotify_big_table.csv")
os.makedirs("../results", exist_ok=True)

# === 1. Build Collaboration Network ===
# Split artists string into list
df["artist_list"] = df["artists"].apply(lambda x: [a.strip() for a in x.split(",")])

# Create graph
G = nx.Graph()

for _, row in df.iterrows():
    artists = row["artist_list"]
    if len(artists) > 1:
        # Add edges for each pair of collaborating artists
        for i in range(len(artists)):
            for j in range(i+1, len(artists)):
                if G.has_edge(artists[i], artists[j]):
                    G[artists[i]][artists[j]]["weight"] += 1
                else:
                    G.add_edge(artists[i], artists[j], weight=1)

# === 2. Compute Network Metrics ===
degree_centrality = nx.degree_centrality(G)
betweenness = nx.betweenness_centrality(G)

# Try eigenvector centrality with safe fallback
try:
    eigenvector = nx.eigenvector_centrality(G, max_iter=1000)
except nx.PowerIterationFailedConvergence:
    print("⚠️ Eigenvector centrality did not converge, using numpy backend instead...")
    try:
        eigenvector = nx.eigenvector_centrality_numpy(G)
    except Exception:
        print("❌ Eigenvector centrality failed, assigning None values")
        eigenvector = {n: None for n in G.nodes()}

# Save metrics to CSV
metrics_df = pd.DataFrame({
    "artist": list(degree_centrality.keys()),
    "degree_centrality": list(degree_centrality.values()),
    "betweenness": list(betweenness.values()),
    "eigenvector": list(eigenvector.values())
})
metrics_df.to_csv("../results/artist_network_metrics.csv", index=False)

# === 3. Popularity vs Centrality ===
# Map track popularity to each artist
artist_popularity = {}
for _, row in df.iterrows():
    for artist in row["artist_list"]:
        # Collect popularity values for each artist across all tracks
        artist_popularity.setdefault(artist, []).append(row["popularity"])

# Compute average popularity for each artist
avg_popularity = {
    artist: sum(pops)/len(pops)
    for artist, pops in artist_popularity.items()
}

# Add average popularity to metrics_df
metrics_df["avg_popularity"] = metrics_df["artist"].map(avg_popularity)
nx.set_node_attributes(G, avg_popularity, "avg_popularity")

# Save metrics to CSV
metrics_df.to_csv("../results/artist_network_with_popularity.csv", index=False)


# === 4. Visualization: Collaboration Network ===
plt.figure(figsize=(12, 8))
pos = nx.spring_layout(G, k=0.3, seed=42)
node_sizes = [
    G.nodes[n]["avg_popularity"] * 10
    for n in G.nodes()
]

# Draw edges (faded for clarity)
nx.draw_networkx_edges(G, pos, alpha=0.2, arrows=True, arrowsize=20)

# Draw nodes with size = popularity
nx.draw_networkx_nodes(
    G, pos,
    node_size=node_sizes,
    node_color="skyblue",
    alpha=0.7,
    linewidths=0.5,
    edgecolors="gray"
)

# Show labels only for artists above a popularity threshold
label_threshold = 50
labels = {
    n: n  # use artist name directly as label
    for n in G.nodes()
    if G.nodes[n]["avg_popularity"] >= label_threshold
}

nx.draw_networkx_labels(
    G, pos,
    labels,
    font_size=8,
    font_color="black"
)

# Add title and formatting
plt.title("Collaboration Network (Node size = Avg Popularity)", fontsize=14)
plt.axis("off")
plt.tight_layout()
plt.savefig("../results/collaboration_network_labeled.png", dpi=300)
plt.close()

# === 5. Community Detection / Connected Components (Big vs Small) ===
import os

# Create folders for results
base_dir = "../results/community"
big_dir = os.path.join(base_dir, "big")
small_dir = os.path.join(base_dir, "small")
os.makedirs(big_dir, exist_ok=True)
os.makedirs(small_dir, exist_ok=True)

# Detect connected components (each disconnected subgraph = 1 community)
components = list(nx.connected_components(G))
print(f"Detected {len(components)} communities")

# Define threshold for big vs small communities
threshold = 10

for i, comp in enumerate(components, start=1):
    subG = G.subgraph(comp)

    # Compute positions for this community
    pos = nx.spring_layout(subG, k=0.3, seed=42)

    # Scale node size by avg popularity
    node_sizes = [
        metrics_df.loc[metrics_df["artist"] == n, "avg_popularity"].values[0] * 10
        for n in subG.nodes()
    ]

    plt.figure(figsize=(8, 6))

    # Draw edges
    nx.draw_networkx_edges(subG, pos, alpha=0.3, arrows=True, arrowsize=20)

    # Draw nodes (size = popularity)
    nx.draw_networkx_nodes(
        subG, pos,
        node_size=node_sizes,
        node_color="skyblue",
        alpha=0.8,
        edgecolors="gray",
        linewidths=0.5,
    )

    # Draw all artist labels (since communities are smaller than full graph)
    nx.draw_networkx_labels(
        subG, pos,
        labels={n: n for n in subG.nodes()},
        font_size=7,
        font_color="black"
    )

    # Decide save folder (big or small)
    if len(subG.nodes()) >= threshold:
        save_path = os.path.join(big_dir, f"community_{i}.png")
    else:
        save_path = os.path.join(small_dir, f"community_{i}.png")

    plt.title(f"Community {i} (size={len(subG.nodes())})", fontsize=12)
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()

print("✅ Analysis complete! Results saved in '../results' folder.")