"""
Neo4j Graph Visualizer — networkx + matplotlib
Requirements: pip install neo4j networkx matplotlib
"""

from neo4j import GraphDatabase
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# ── Connection ────────────────────────────────────────────────────────────────
URI      = "bolt://localhost:7687"
USER     = "neo4j"
PASSWORD = "secret"

# ── Query ─────────────────────────────────────────────────────────────────────
QUERY = """
MATCH (a)-[r]->(b)
RETURN a, type(r) AS rel, r, b
LIMIT 100
"""

# ── Color map by node label ───────────────────────────────────────────────────
LABEL_COLORS = {
    "Person": "#00e5a0",
    "Movie":  "#5b8dee",
    "Show":   "#f7c948",
    "Genre":  "#f06292",
}
DEFAULT_COLOR = "#94a3b8"

REL_COLOR     = "#475569"
REL_FONT_COLOR = "#94a3b8"
BACKGROUND    = "#0d0f14"
NODE_FONT     = "white"


def get_label(node):
    """Return the first label of a Neo4j node."""
    labels = list(node.labels)
    return labels[0] if labels else "Unknown"


def get_caption(node):
    """Return the best display name for a node."""
    for key in ("name", "title", "id"):
        if key in node:
            return str(node[key])
    return str(node.element_id)


def build_graph(driver):
    G = nx.DiGraph()

    with driver.session() as session:
        results = session.run(QUERY)
        for record in results:
            a, rel_type, r, b = record["a"], record["rel"], record["r"], record["b"]

            # Nodes
            a_id = a.element_id
            b_id = b.element_id

            if a_id not in G.nodes:
                G.add_node(a_id,
                           label=get_label(a),
                           caption=get_caption(a),
                           props=dict(a))

            if b_id not in G.nodes:
                G.add_node(b_id,
                           label=get_label(b),
                           caption=get_caption(b),
                           props=dict(b))

            # Edge (allow multiple rels between same pair)
            G.add_edge(a_id, b_id, rel=rel_type, props=dict(r))

    return G


def draw_graph(G):
    fig, ax = plt.subplots(figsize=(14, 9))
    fig.patch.set_facecolor(BACKGROUND)
    ax.set_facecolor(BACKGROUND)
    ax.axis("off")

    # Layout
    pos = nx.spring_layout(G, seed=42, k=2.5)

    # Node attributes
    node_colors  = [LABEL_COLORS.get(G.nodes[n]["label"], DEFAULT_COLOR) for n in G.nodes]
    node_labels  = {n: G.nodes[n]["caption"] for n in G.nodes}
    node_sizes   = [1800 for _ in G.nodes]

    # Draw edges
    nx.draw_networkx_edges(
        G, pos, ax=ax,
        edge_color=REL_COLOR,
        arrows=True,
        arrowstyle="-|>",
        arrowsize=18,
        width=1.5,
        connectionstyle="arc3,rad=0.1",
        min_source_margin=28,
        min_target_margin=28,
    )

    # Edge labels
    edge_labels = {(u, v): d["rel"] for u, v, d in G.edges(data=True)}
    nx.draw_networkx_edge_labels(
        G, pos, edge_labels=edge_labels, ax=ax,
        font_size=7,
        font_color=REL_FONT_COLOR,
        bbox=dict(boxstyle="round,pad=0.15", fc=BACKGROUND, ec="none", alpha=0.8),
    )

    # Draw nodes
    nx.draw_networkx_nodes(
        G, pos, ax=ax,
        node_color=node_colors,
        node_size=node_sizes,
        alpha=0.95,
    )

    # Node labels
    nx.draw_networkx_labels(
        G, pos, labels=node_labels, ax=ax,
        font_size=8,
        font_color=NODE_FONT,
        font_weight="bold",
    )

    # Legend
    seen_labels = set(nx.get_node_attributes(G, "label").values())
    legend_patches = [
        mpatches.Patch(color=LABEL_COLORS.get(lbl, DEFAULT_COLOR), label=lbl)
        for lbl in sorted(seen_labels)
    ]
    ax.legend(
        handles=legend_patches,
        loc="upper left",
        facecolor="#1e2330",
        edgecolor="#3a4460",
        labelcolor="white",
        fontsize=9,
        framealpha=0.9,
    )

    plt.title("Neo4j Graph", color="white", fontsize=13, pad=16)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    try:
        G = build_graph(driver)
        print(f"Loaded {G.number_of_nodes()} nodes, {G.number_of_edges()} relationships.")
        draw_graph(G)
    finally:
        driver.close()