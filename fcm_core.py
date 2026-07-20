from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent / ".deps"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "work" / "pydeps"))
import numpy as np
from scipy.ndimage import uniform_filter

def fcm(image, mask, n_clusters=3, m=2.0, max_iter=100, tol=1e-5,
        alpha=0.0, window=3, seed=0):
    """FCM; alpha>0 enables transparent spatial membership correction."""
    rng = np.random.default_rng(seed)
    values = image[mask].astype(np.float64)[:, None]
    qs = np.linspace(.12, .88, n_clusters)
    centers = np.quantile(values[:, 0], qs)[:, None]
    centers += rng.normal(0, 1e-4, centers.shape)
    history = []
    last_neighborhood = None
    for _ in range(max_iter):
        dist2 = np.maximum((values - centers.T) ** 2, 1e-12)
        inv = dist2 ** (-1.0 / (m - 1.0))
        membership = inv / inv.sum(axis=1, keepdims=True)
        if alpha > 0:
            maps = np.zeros(image.shape + (n_clusters,), dtype=np.float64)
            maps[mask] = membership
            support = np.stack([
                uniform_filter(maps[..., k], size=window, mode="reflect")
                for k in range(n_clusters)
            ], axis=-1)
            neighborhood = np.maximum(support[mask], 1e-12)
            membership *= neighborhood ** alpha
            membership /= membership.sum(axis=1, keepdims=True)
            last_neighborhood = support
        weights = membership ** m
        new_centers = (weights.T @ values) / (weights.sum(axis=0)[:, None] + 1e-12)
        history.append(float(np.sum(weights * dist2)))
        if np.max(np.abs(new_centers - centers)) < tol:
            centers = new_centers
            break
        centers = new_centers
    order = np.argsort(centers[:, 0])
    membership = membership[:, order]
    centers = centers[order, 0]
    labels = np.full(image.shape, -1, dtype=np.int16)
    labels[mask] = np.argmax(membership, axis=1)
    maps = np.zeros(image.shape + (n_clusters,), dtype=np.float32)
    maps[mask] = membership
    return labels, centers, maps, np.asarray(history), last_neighborhood
