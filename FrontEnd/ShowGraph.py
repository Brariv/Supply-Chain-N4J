"""
Backorder Graph Visualizer — networkx + matplotlib
Displays each Manufacturer at the hub, with its ON_BACKORDER Car nodes
fanned out in a circle around it. Car nodes are colored by body type.
"""

import os
import math
from neo4j import GraphDatabase
from dotenv import load_dotenv
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

load_dotenv(override=True)

URI      = os.getenv("URI")
USER     = os.getenv("USER")
PASSWORD = os.getenv("PASSWORD")
DATABASE = os.getenv("DATABASE")

QUERY = """
MATCH (m:Manufacturer)-[:ON_BACKORDER]->(c:Car)
WITH m, collect(c)[..25] AS cars
UNWIND cars AS c
RETURN m, c
"""

MANUFACTURER_COLOR = "#e8c57a"
CAR_COLORS = {
    "Sedan":  "#5b9bd5",
    "SUV":    "#70ad47",
    "Pickup": "#ed7d31",
}
DEFAULT_CAR_COLOR  = "#5bc8f5"
BACKGROUND         = "#0d0f14"
REL_COLOR          = "#475569"
NODE_FONT          = "white"


def _car_color(node):
    for body in ("Sedan", "SUV", "Pickup"):
        if body in node.labels:
            return CAR_COLORS[body]
    return DEFAULT_CAR_COLOR


def build_graph(driver):
    G         = nx.DiGraph()
    mfr_nodes = set()
    car_mfr   = {}   # car element_id → manufacturer element_id

    with driver.session(database=DATABASE) as session:
        for record in session.run(QUERY):
            m, c = record["m"], record["c"]  # r removed — not returned by query
            m_id, c_id = m.element_id, c.element_id

            if m_id not in G.nodes:
                G.add_node(m_id,
                           kind="manufacturer",
                           caption=m.get("Brand", str(m.get("manufacturerId", "Mfr"))),
                           color=MANUFACTURER_COLOR)
                mfr_nodes.add(m_id)

            if c_id not in G.nodes:
                caption = f"{c.get('Brand', '')}\n{c.get('Model', '')}".strip()
                G.add_node(c_id,
                           kind="car",
                           caption=caption,
                           color=_car_color(c))
                car_mfr[c_id] = m_id

            G.add_edge(m_id, c_id, rel="ON_BACKORDER")

    return G, mfr_nodes, car_mfr


def _radial_layout(mfr_nodes, car_mfr):
    """Manufacturers on a horizontal axis; cars in a circle around each.
    Spacing between clusters is computed dynamically so they never overlap."""
    pos      = {}
    mfr_list = list(mfr_nodes)

    # Radius large enough that adjacent car nodes don't touch within a cluster
    # arc_spacing ≈ 2π*r/n  ≥  min_gap  →  r ≥ n*min_gap / (2π)
    MIN_ARC_GAP = 2.8
    radii = {}
    for m_id in mfr_list:
        n = sum(1 for _, m in car_mfr.items() if m == m_id)
        radii[m_id] = max(3.5, n * MIN_ARC_GAP / (2 * math.pi))

    # Cumulative x-placement: separate cluster edges by GAP
    GAP = 2.0
    xs  = []
    x   = 0.0
    for i, m_id in enumerate(mfr_list):
        if i > 0:
            x += radii[mfr_list[i - 1]] + radii[m_id] + GAP
        xs.append(x)

    mid = xs[-1] / 2.0 if xs else 0.0

    for i, m_id in enumerate(mfr_list):
        mx = xs[i] - mid
        pos[m_id] = (mx, 0.0)

        cars   = [c for c, m in car_mfr.items() if m == m_id]
        n_cars = len(cars)
        r      = radii[m_id]

        for j, c_id in enumerate(cars):
            angle     = 2 * math.pi * j / max(n_cars, 1)
            pos[c_id] = (mx + r * math.cos(angle),
                         r * math.sin(angle))

    return pos


def draw_graph(G, mfr_nodes, car_mfr):
    pos = _radial_layout(mfr_nodes, car_mfr)

    # Size the figure to match the actual data span so clusters aren't squished
    if pos:
        all_x = [p[0] for p in pos.values()]
        all_y = [p[1] for p in pos.values()]
        fig_w = max(18, (max(all_x) - min(all_x)) * 0.85)
        fig_h = max(10, (max(all_y) - min(all_y)) * 0.85)
    else:
        fig_w, fig_h = 18, 10

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    fig.patch.set_facecolor(BACKGROUND)
    ax.set_facecolor(BACKGROUND)
    ax.axis("off")

    node_colors = [G.nodes[n]["color"] for n in G.nodes]
    node_sizes  = [4000 if G.nodes[n]["kind"] == "manufacturer" else 1600
                   for n in G.nodes]
    node_labels = {n: G.nodes[n]["caption"] for n in G.nodes}

    nx.draw_networkx_edges(
        G, pos, ax=ax,
        edge_color=REL_COLOR,
        arrows=True,
        arrowstyle="-|>",
        arrowsize=14,
        width=1.2,
        min_source_margin=40,
        min_target_margin=22,
    )

    nx.draw_networkx_nodes(
        G, pos, ax=ax,
        node_color=node_colors,
        node_size=node_sizes,
        alpha=0.95,
    )

    nx.draw_networkx_labels(
        G, pos, labels=node_labels, ax=ax,
        font_size=7,
        font_color=NODE_FONT,
        font_weight="bold",
    )

    legend = [
        mpatches.Patch(color=MANUFACTURER_COLOR,   label="Manufacturer"),
        mpatches.Patch(color=CAR_COLORS["Sedan"],  label="Sedan"),
        mpatches.Patch(color=CAR_COLORS["SUV"],    label="SUV"),
        mpatches.Patch(color=CAR_COLORS["Pickup"], label="Pickup"),
        mpatches.Patch(color=DEFAULT_CAR_COLOR,    label="Car (other)"),
    ]
    ax.legend(handles=legend, loc="upper left",
              facecolor="#1e2330", edgecolor="#3a4460",
              labelcolor="white", fontsize=9, framealpha=0.9)

    total_cars = sum(1 for n in G.nodes if G.nodes[n]["kind"] == "car")
    plt.title(f"Backorder by Manufacturer  —  {total_cars} cars pending",
              color="white", fontsize=13, pad=16)
    plt.tight_layout()
    plt.show()


drv = GraphDatabase.driver(URI, auth=(USER, PASSWORD))  # type: ignore[arg-type]
try:
    G, mfr_nodes, car_mfr = build_graph(drv)
    print(f"{G.number_of_nodes()} nodes · {G.number_of_edges()} backorder relationships")
    draw_graph(G, mfr_nodes, car_mfr)
finally:
    drv.close()
