"""Document/writing background removal using morphological background estimation."""

import numpy as np
from PIL import Image


def _box_min_filter(img: np.ndarray, radius: int) -> np.ndarray:
    """Sliding-window minimum (morphological erosion approximation) via 1D decomposition."""
    size = 2 * radius + 1
    h, w = img.shape

    padded = np.pad(img.astype(np.float32), radius, mode='reflect')
    cummin_h = np.minimum.accumulate(padded, axis=0)
    out = np.empty((h, w), dtype=np.float32)
    for i in range(h):
        out[i] = np.minimum.reduce(cummin_h[i:i + size, radius:radius + w], axis=0)

    padded2 = np.pad(out, ((0, 0), (radius, radius)), mode='reflect')
    cummin_w = np.minimum.accumulate(padded2, axis=1)
    result = np.empty((h, w), dtype=np.float32)
    for j in range(w):
        result[:, j] = np.minimum.reduce(cummin_w[:, j:j + size], axis=1)

    return result


def _box_max_filter(img: np.ndarray, radius: int) -> np.ndarray:
    """Sliding-window maximum (morphological dilation approximation) via 1D decomposition."""
    size = 2 * radius + 1
    h, w = img.shape

    padded = np.pad(img.astype(np.float32), radius, mode='reflect')
    cummax_h = np.maximum.accumulate(padded, axis=0)
    out = np.empty((h, w), dtype=np.float32)
    for i in range(h):
        out[i] = np.maximum.reduce(cummax_h[i:i + size, radius:radius + w], axis=0)

    padded2 = np.pad(out, ((0, 0), (radius, radius)), mode='reflect')
    cummax_w = np.maximum.accumulate(padded2, axis=1)
    result = np.empty((h, w), dtype=np.float32)
    for j in range(w):
        result[:, j] = np.maximum.reduce(cummax_w[:, j:j + size], axis=1)

    return result


def _estimate_background(gray: np.ndarray, radius: int) -> np.ndarray:
    """
    Estimate paper background brightness via morphological closing (dilation then erosion).
    This fills in dark ink strokes while preserving paper color, shadows, and any faint lines.
    """
    dilated = _box_max_filter(gray, radius)
    closed = _box_min_filter(dilated, radius)
    return closed


def _morphological_open(img: np.ndarray, radius: int) -> np.ndarray:
    """Morphological opening (erosion then dilation) to remove isolated noise pixels."""
    eroded = _box_min_filter(img, radius)
    dilated = _box_max_filter(eroded, radius)
    return dilated


def remove_background_document(
    input_image: Image.Image,
    ink_threshold: float = 25.0,
    bg_radius: int = 30,
    denoise: bool = True,
) -> Image.Image:
    """
    Remove background from document/writing images.

    Uses a two-condition ink detection strategy:
      1. Relative condition: pixel must be at least `ink_threshold` gray levels
         darker than the locally estimated paper background (handles colored paper,
         uneven lighting, shadows).
      2. Absolute condition: pixel must be darker than the auto-detected paper
         brightness floor (eliminates faint grid/ruled lines that are close in
         brightness to the paper regardless of local context).

    Both conditions must be satisfied for a pixel to be treated as ink.
    Alpha is soft (smooth ink edges) within the ink region.

    Args:
        input_image:   Input PIL image.
        ink_threshold: Minimum gray-level gap between background estimate and pixel
                       brightness to count as ink. Default 25. Lower = picks up
                       lighter ink; higher = cleaner line removal.
        bg_radius:     Radius for background closing. Default 30. Increase if ink
                       strokes are very wide.
        denoise:       Remove isolated noise pixels after thresholding.

    Returns:
        RGBA PIL image — ink pixels fully opaque, background fully transparent.
    """
    img = input_image.convert("RGB")
    data = np.array(img, dtype=np.uint8)
    gray = np.dot(data[..., :3], [0.299, 0.587, 0.114]).astype(np.float32)

    background = _estimate_background(gray, bg_radius)

    diff = background - gray

    paper_brightness = float(np.percentile(background, 85))
    abs_gate = paper_brightness - ink_threshold

    ink_mask = (diff >= ink_threshold) & (gray <= abs_gate)

    if denoise:
        ink_mask_u8 = ink_mask.astype(np.uint8) * 255
        ink_mask_u8 = _morphological_open(ink_mask_u8, 1).astype(np.uint8)
        ink_mask = ink_mask_u8 > 0

    soft_alpha = np.clip(diff / max(ink_threshold, 1.0), 0.0, 1.0)
    alpha = np.where(ink_mask, (soft_alpha * 255).astype(np.uint8), 0).astype(np.uint8)

    rgba = np.dstack([data, alpha])
    return Image.fromarray(rgba, "RGBA")
