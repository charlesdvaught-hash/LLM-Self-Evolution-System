"""
ASSAY Visualization Module

Produces Plotly figures for activation contrast analysis:
- Heatmap: quality class performance across layers
- Constellation: PCA-reduced layer activation space with co-activation clusters
"""

import numpy as np
import plotly.graph_objects as go
from typing import Dict, Optional


def make_heatmap(
    layer_stats: Dict[int, Dict[str, float]],
    topic: str,
    winning_strategy: str
) -> go.Figure:
    """
    Create a heatmap showing activation contrast across layers and quality classes.

    Args:
        layer_stats: Dict mapping layer index to quality metrics.
                    Keys: "great", "acceptable", "wrong", "hallucinated", "contrast"
        topic: Analysis topic for title
        winning_strategy: Probe strategy used (e.g., "binary", "multiclass")

    Returns:
        Plotly Figure with dark theme
    """
    # Sort layers by index
    layer_indices = sorted(layer_stats.keys())
    quality_classes = ["great", "acceptable", "wrong", "hallucinated"]

    # Build heatmap data: rows=layers, cols=classes, values=contrast
    heatmap_data = []
    for layer_idx in layer_indices:
        row = [layer_stats[layer_idx].get(cls, 0.0) for cls in quality_classes]
        heatmap_data.append(row)

    heatmap_array = np.array(heatmap_data)

    # Find top 3 layers by max contrast
    contrast_scores = [layer_stats[idx].get("contrast", 0.0) for idx in layer_indices]
    top_3_indices = sorted(
        range(len(contrast_scores)),
        key=lambda i: contrast_scores[i],
        reverse=True
    )[:3]

    # Create heatmap figure
    fig = go.Figure(
        data=go.Heatmap(
            z=heatmap_array,
            x=quality_classes,
            y=layer_indices,
            colorscale="RdYlGn",
            colorbar=dict(title="Contrast", thickness=15, len=0.7),
            hovertemplate="Layer %{y}<br>%{x}<br>Contrast: %{z:.3f}<extra></extra>",
        )
    )

    # Annotate top 3 layers with star markers
    for row_idx in top_3_indices:
        layer_num = layer_indices[row_idx]
        # Place star at the middle of the layer row (between classes)
        fig.add_annotation(
            x=1.5,  # middle of x range
            y=layer_num,
            text="★",
            showarrow=False,
            font=dict(size=20, color="gold"),
            xref="x",
            yref="y",
        )

    # Configure layout with dark theme
    fig.update_layout(
        title=f"ASSAY — {topic} ({winning_strategy} probes)",
        xaxis_title="Quality Class",
        yaxis_title="Layer Index",
        plot_bgcolor="#0d1117",
        paper_bgcolor="#0d1117",
        font=dict(color="white", size=11),
        height=400 + max(0, len(layer_indices) - 20) * 3,  # Scale height for many layers
        hovermode="closest",
        xaxis=dict(side="bottom", showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="#30363d"),
    )

    return fig


def make_constellation(
    layer_stats: Dict[int, Dict[str, float]],
    layer_vectors: Optional[Dict[int, np.ndarray]],
    topic: str
) -> go.Figure:
    """
    Create a 2D constellation plot of layers in PCA-reduced activation space.

    Args:
        layer_stats: Dict mapping layer index to quality metrics (used for contrast scores)
        layer_vectors: Dict mapping layer index to activation vectors [hidden_dim].
                      If None/empty, render layers in a circle
        topic: Analysis topic for title

    Returns:
        Plotly Figure with nodes (layers), edges (co-activations), dark theme
    """
    layer_indices = sorted(layer_stats.keys())
    contrast_scores = np.array([layer_stats[idx].get("contrast", 0.0) for idx in layer_indices])

    # Compute 2D positions via PCA (SVD)
    if layer_vectors and len(layer_vectors) > 0:
        # Stack activation vectors
        vectors = np.array([layer_vectors[idx] for idx in layer_indices])

        # Center data
        vectors_centered = vectors - vectors.mean(axis=0)

        # SVD to get first 2 principal components
        if vectors_centered.shape[0] >= 2:
            U, S, Vt = np.linalg.svd(vectors_centered, full_matrices=False)
            # Project onto first 2 components
            positions_2d = U[:, :2] * S[:2]
        else:
            # Fallback for very few layers
            positions_2d = np.array([[i, 0.0] for i in range(len(layer_indices))])
    else:
        # Render in a circle if no vectors provided
        angles = np.linspace(0, 2 * np.pi, len(layer_indices), endpoint=False)
        radius = max(1.0, len(layer_indices) / 10)
        positions_2d = radius * np.array([[np.cos(a), np.sin(a)] for a in angles])

    # Normalize positions for better visualization
    if len(layer_indices) > 1:
        positions_2d = (positions_2d - positions_2d.mean(axis=0)) / (positions_2d.std(axis=0) + 1e-8)

    # Build edges based on cosine similarity > 0.85
    edge_x, edge_y = [], []
    if layer_vectors and len(layer_vectors) > 1:
        vectors_norm = np.array([layer_vectors[idx] / (np.linalg.norm(layer_vectors[idx]) + 1e-8)
                                 for idx in layer_indices])

        for i in range(len(layer_indices)):
            for j in range(i + 1, len(layer_indices)):
                similarity = np.dot(vectors_norm[i], vectors_norm[j])
                if similarity > 0.85:
                    edge_x.extend([positions_2d[i, 0], positions_2d[j, 0], None])
                    edge_y.extend([positions_2d[i, 1], positions_2d[j, 1], None])

    # Node sizes: scale contrast scores to 8-24px range
    if contrast_scores.max() > contrast_scores.min():
        node_sizes = 8 + 16 * (contrast_scores - contrast_scores.min()) / (contrast_scores.max() - contrast_scores.min())
    else:
        node_sizes = np.ones_like(contrast_scores) * 16

    # Create figure
    fig = go.Figure()

    # Add edges first (so they appear behind nodes)
    if edge_x:
        fig.add_trace(
            go.Scatter(
                x=edge_x,
                y=edge_y,
                mode="lines",
                line=dict(width=1, color="#30363d"),
                hoverinfo="none",
                showlegend=False,
            )
        )

    # Add nodes
    fig.add_trace(
        go.Scatter(
            x=positions_2d[:, 0],
            y=positions_2d[:, 1],
            mode="markers+text",
            marker=dict(
                size=node_sizes,
                color=contrast_scores,
                colorscale="RdYlGn",
                showscale=True,
                colorbar=dict(title="Contrast", thickness=15, len=0.7),
                line=dict(width=1, color="#30363d"),
            ),
            text=[str(idx) for idx in layer_indices],
            textposition="middle center",
            textfont=dict(size=10, color="white"),
            hovertemplate="Layer %{text}<br>Contrast: %{marker.color:.3f}<extra></extra>",
            showlegend=False,
        )
    )

    # Configure layout
    fig.update_layout(
        title=f"ASSAY Constellation — {topic}",
        showlegend=False,
        hovermode="closest",
        plot_bgcolor="#0d1117",
        paper_bgcolor="#0d1117",
        font=dict(color="white", size=11),
        height=600,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    )

    return fig
