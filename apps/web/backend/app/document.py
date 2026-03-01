"""Document/writing background removal using Otsu + morphological background estimation."""

import numpy as np
from PIL import Image


def _box_min_filter(img: np.ndarray, radius: int) -> np.ndarray:
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


def _morphological_open(img: np.ndarray, radius: int) -> np.ndarray:
    eroded = _box_min_filter(img, radius)
    dilated = _box_max_filter(eroded, radius)
    return dilated


def _otsu_threshold(gray: np.ndarray) -> float:
    """Compute Otsu's optimal threshold to separate ink from background."""
    hist = np.bincount(gray.astype(np.uint8).ravel(), minlength=256).astype(np.float64)
    total = gray.size
    sum_total = np.dot(np.arange(256, dtype=np.float64), hist)

    sum_bg = 0.0
    weight_bg = 0.0
    max_variance = 0.0
    best_thresh = 0.0

    for t in range(256):
        weight_bg += hist[t]
        if weight_bg == 0:
            continue
        weight_fg = total - weight_bg
        if weight_fg == 0:
            break
        sum_bg += t * hist[t]
        mean_bg = sum_bg / weight_bg
        mean_fg = (sum_total - sum_bg) / weight_fg
        variance = weight_bg * weight_fg * (mean_bg - mean_fg) ** 2
        if variance > max_variance:
            max_variance = variance
            best_thresh = t

    return best_thresh


def _estimate_background(gray: np.ndarray, radius: int) -> np.ndarray:
    dilated = _box_max_filter(gray, radius)
    closed = _box_min_filter(dilated, radius)
    return closed


def remove_background_document(
    input_image: Image.Image,
    ink_threshold: float = 25.0,
    bg_radius: int = 30,
    denoise: bool = True,
) -> Image.Image:
    """
    Remove background from document/writing images.

    Uses three complementary ink detection conditions (all must pass):
      1. Otsu's global threshold — finds the natural intensity valley between
         dark ink and light background/lines. Cleanly eliminates any grid/ruled
         lines because they live in the bright cluster with the paper.
      2. Relative condition — pixel must be at least `ink_threshold` gray levels
         darker than its morphologically estimated local background. Handles
         uneven lighting and colored/shadowed paper.
      3. Absolute percentile gate — pixel must be darker than (85th percentile
         of background minus ink_threshold). Extra safety net.

    Args:
        input_image:   Input PIL image.
        ink_threshold: Minimum gray-level gap for relative condition. Default 25.
        bg_radius:     Radius for morphological background estimation. Default 30.
        denoise:       Remove isolated noise pixels after thresholding.

    Returns:
        RGBA PIL image — ink opaque on transparent background.
    """
    img = input_image.convert("RGB")
    data = np.array(img, dtype=np.uint8)
    gray = np.dot(data[..., :3], [0.299, 0.587, 0.114]).astype(np.float32)

    otsu_thresh = _otsu_threshold(gray)

    background = _estimate_background(gray, bg_radius)
    diff = background - gray

    paper_brightness = float(np.percentile(background, 85))
    abs_gate = paper_brightness - ink_threshold

    ink_mask = (
        (gray <= otsu_thresh)
        & (diff >= ink_threshold)
        & (gray <= abs_gate)
    )

    if denoise:
        ink_u8 = ink_mask.astype(np.uint8) * 255
        ink_u8 = _morphological_open(ink_u8, 1).astype(np.uint8)
        ink_mask = ink_u8 > 0

    ink_range = max(float(otsu_thresh) - float(np.percentile(gray[ink_mask], 5)) if ink_mask.any() else 1.0, 1.0)
    soft_alpha = np.clip((otsu_thresh - gray) / ink_range, 0.0, 1.0)
    alpha = np.where(ink_mask, (soft_alpha * 255).astype(np.uint8), 0).astype(np.uint8)

    rgba = np.dstack([data, alpha])
    return Image.fromarray(rgba, "RGBA")
