"""Document/writing background removal using top-hat background estimation."""

import numpy as np
from PIL import Image


def _box_min_filter(img: np.ndarray, radius: int) -> np.ndarray:
    """Approximate morphological erosion via sliding-window minimum using 1D decomposition."""
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
    """Approximate morphological dilation via sliding-window maximum using 1D decomposition."""
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
    Estimate the paper background brightness at each pixel using morphological closing.

    Closing = dilation then erosion. On a document, this fills in the dark ink
    strokes and leaves only the slowly-varying paper brightness — including any
    shadows, colored paper, or faint grid lines.
    """
    dilated = _box_max_filter(gray, radius)
    closed = _box_min_filter(dilated, radius)
    return closed


def _integral_image(arr: np.ndarray) -> np.ndarray:
    return np.cumsum(np.cumsum(arr.astype(np.float64), axis=0), axis=1)


def _box_mean(integral: np.ndarray, h: int, w: int, half: int) -> np.ndarray:
    block = 2 * half + 1
    area = block * block
    padded_i = np.pad(
        np.cumsum(np.cumsum(np.ones((h, w), dtype=np.float64), axis=0), axis=1),
        half, mode='reflect'
    )
    r = np.arange(h)
    c = np.arange(w)
    return (
        integral[r[:, None] + block, c[None, :] + block]
        - integral[r[:, None] + block, c[None, :]]
        - integral[r[:, None], c[None, :] + block]
        + integral[r[:, None], c[None, :]]
    ) / area


def _morphological_open(img: np.ndarray, radius: int) -> np.ndarray:
    """Remove isolated noise pixels (opening = erosion then dilation)."""
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

    Uses morphological background estimation (closing) to determine the true
    paper brightness at each pixel, then marks a pixel as ink if it is
    significantly darker than the estimated background. This correctly handles:

    - Lined / grid paper (lines are much closer to paper brightness than ink)
    - Uneven lighting and shadows
    - Colored or yellowed paper
    - Both light and dark ink on any paper color

    Args:
        input_image: Input PIL image.
        ink_threshold: How many gray levels darker than the estimated background
                       a pixel must be to count as ink. Lower = more sensitive
                       (picks up lighter ink but may retain faint lines).
                       Higher = less sensitive (clean removal of faint lines
                       but may drop light pencil strokes). Default 25 works
                       well for most pens on lined/grid paper.
        bg_radius:    Radius (pixels) of the morphological closing used to
                      estimate background. Should be larger than the widest
                      stroke but smaller than large blank areas. Default 30.
        denoise:      Remove isolated single-pixel noise after thresholding.

    Returns:
        RGBA PIL image with background transparent and ink fully opaque.
    """
    img = input_image.convert("RGB")
    data = np.array(img, dtype=np.uint8)

    gray = np.dot(data[..., :3], [0.299, 0.587, 0.114]).astype(np.float32)

    background = _estimate_background(gray, bg_radius)

    diff = background - gray
    alpha = np.clip(diff * (255.0 / max(ink_threshold, 1.0)), 0, 255).astype(np.uint8)

    hard_alpha = (diff >= ink_threshold).astype(np.uint8) * 255

    if denoise:
        hard_alpha = _morphological_open(hard_alpha, 1).astype(np.uint8)

    rgba = np.dstack([data, hard_alpha])
    return Image.fromarray(rgba, "RGBA")
