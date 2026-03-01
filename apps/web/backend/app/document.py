"""Document/writing background removal using adaptive thresholding."""

import numpy as np
from PIL import Image


def _adaptive_threshold(gray: np.ndarray, block_size: int, c: float) -> np.ndarray:
    """Compute adaptive Gaussian threshold without OpenCV dependency."""
    from scipy.ndimage import uniform_filter

    half = block_size // 2
    local_mean = uniform_filter(gray.astype(np.float32), size=block_size)
    thresh = local_mean - c
    binary = (gray < thresh).astype(np.uint8) * 255
    return binary


def _adaptive_threshold_manual(gray: np.ndarray, block_size: int, c: float) -> np.ndarray:
    """Pure numpy adaptive threshold using sliding window approximation via integral image."""
    h, w = gray.shape
    padded = np.pad(gray.astype(np.float64), block_size // 2, mode='reflect')
    integral = np.cumsum(np.cumsum(padded, axis=0), axis=1)

    def box_sum(r1, c1, r2, c2):
        s = integral[r2 + 1, c2 + 1]
        if r1 > 0:
            s -= integral[r1, c2 + 1]
        if c1 > 0:
            s -= integral[r2 + 1, c1]
        if r1 > 0 and c1 > 0:
            s += integral[r1, c1]
        return s

    half = block_size // 2
    area = block_size * block_size

    rows = np.arange(h)
    cols = np.arange(w)
    r1 = rows
    r2 = rows + block_size
    c1 = cols
    c2 = cols + block_size

    local_mean = np.zeros((h, w), dtype=np.float64)
    for i in range(h):
        row_sum = integral[i + block_size + 1, block_size:block_size + w] - \
                  integral[i + block_size + 1, :w] - \
                  integral[i, block_size:block_size + w] + \
                  integral[i, :w]
        local_mean[i] = row_sum / area

    thresh = local_mean - c
    binary = (gray.astype(np.float64) < thresh).astype(np.uint8) * 255
    return binary


def remove_background_document(
    input_image: Image.Image,
    block_size: int = 15,
    c: float = 10.0,
    denoise: bool = True,
) -> Image.Image:
    """
    Remove background from document/writing images using adaptive thresholding.

    Works well for handwritten notes, typed text, drawings on paper with or
    without ruled lines, uneven lighting, and varying paper colors.

    Args:
        input_image: Input PIL image
        block_size: Local neighborhood size for threshold computation (odd number).
                    Increase for thicker/bolder text (e.g. 21, 31).
        c: Constant subtracted from the mean. Higher removes more faint marks.
        denoise: Whether to apply morphological opening to reduce noise.

    Returns:
        RGBA PIL image with background made transparent.
    """
    img = input_image.convert("RGB")
    data = np.array(img)

    gray = np.dot(data[..., :3], [0.299, 0.587, 0.114]).astype(np.uint8)

    if block_size % 2 == 0:
        block_size += 1

    h, w = gray.shape
    half = block_size // 2
    padded = np.pad(gray.astype(np.float64), half, mode='reflect')

    integral = np.cumsum(np.cumsum(padded, axis=0), axis=1)

    r = np.arange(h)
    area = block_size * block_size

    local_mean = (
        integral[r[:, None] + block_size, np.arange(w)[None, :] + block_size]
        - integral[r[:, None] + block_size, np.arange(w)[None, :]]
        - integral[r[:, None], np.arange(w)[None, :] + block_size]
        + integral[r[:, None], np.arange(w)[None, :]]
    ) / area

    alpha = (gray.astype(np.float64) < (local_mean - c)).astype(np.uint8) * 255

    if denoise:
        kernel = np.ones((2, 2), dtype=np.uint8)
        alpha = _morphological_open(alpha, kernel)

    rgba = np.dstack([data, alpha])
    return Image.fromarray(rgba.astype(np.uint8), "RGBA")


def _morphological_open(img: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    """Apply morphological opening (erosion then dilation) to remove noise specks."""
    eroded = _erode(img, kernel)
    dilated = _dilate(eroded, kernel)
    return dilated


def _erode(img: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    kh, kw = kernel.shape
    ph, pw = kh // 2, kw // 2
    padded = np.pad(img, ((ph, ph), (pw, pw)), mode='constant', constant_values=255)
    h, w = img.shape
    out = np.full_like(img, 255)
    for i in range(kh):
        for j in range(kw):
            if kernel[i, j]:
                out = np.minimum(out, padded[i:i + h, j:j + w])
    return out


def _dilate(img: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    kh, kw = kernel.shape
    ph, pw = kh // 2, kw // 2
    padded = np.pad(img, ((ph, ph), (pw, pw)), mode='constant', constant_values=0)
    h, w = img.shape
    out = np.zeros_like(img)
    for i in range(kh):
        for j in range(kw):
            if kernel[i, j]:
                out = np.maximum(out, padded[i:i + h, j:j + w])
    return out
