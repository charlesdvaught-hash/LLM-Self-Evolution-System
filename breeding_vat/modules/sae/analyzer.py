import torch
import torch.nn as nn
import os

class MiniSAE(nn.Module):
    """
    Sparse Autoencoder for layer feature analysis.
    """
    def __init__(self, d_model, d_sae):
        super().__init__()
        self.encoder = nn.Linear(d_model, d_sae)
        self.decoder = nn.Linear(d_sae, d_model)
        self.relu = nn.ReLU()

    def forward(self, x):
        encoded = self.relu(self.encoder(x))
        decoded = self.decoder(encoded)
        return decoded, encoded

class SAEAnalyzer:
    def __init__(self, model_path):
        self.model_path = model_path

    def analyze_layer(self, layer_index, weight_tensor: torch.Tensor):
        """
        Performs real analysis on layer weights to detect potential.
        """
        # Calculate weight entropy and sparsity as a proxy for "geometric shape" complexity
        sparsity = (weight_tensor.abs() < 1e-4).float().mean().item()
        variance = weight_tensor.var().item()
        kurtosis = ((weight_tensor - weight_tensor.mean())**4).mean() / (variance**2)

        # Determine "Geometric Shape" based on distribution properties
        if kurtosis > 6:
            shape = "High-kurtosis Star-cluster"
        elif sparsity > 0.5:
            shape = "Sparse Manifold"
        else:
            shape = "Dense Gaussian Hypersphere"

        return {
            "feature_description": f"Layer {layer_index} showing {sparsity:.2%} sparsity and {variance:.4f} variance.",
            "geometric_shape": shape,
            "importance_score": min(1.0, variance * 100) # Simple importance heuristic
        }

    def identify_mergable_layers(self, state_dict):
        """
        Scans all layers in the state_dict to find those with the most distinct features.
        """
        discoveries = []
        for key, tensor in state_dict.items():
            if "layers" in key and "weight" in key:
                # Extract layer index from key like 'model.layers.12.self_attn.q_proj.weight'
                parts = key.split(".")
                if len(parts) > 2 and parts[2].isdigit():
                    layer_idx = int(parts[2])
                    analysis = self.analyze_layer(layer_idx, tensor)
                    discoveries.append({
                        "layer": layer_idx,
                        "key": key,
                        **analysis
                    })

        # Sort by importance
        discoveries.sort(key=lambda x: x["importance_score"], reverse=True)
        return discoveries[:10] # Return top 10 most "interesting" layers
