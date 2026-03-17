"""effects.py

Comprehensive artistic image effects using OpenCV and NumPy.

Edge Detection Effects:
- canny_edge: Canny edge detection with Gaussian blur
- adaptive_sketch: Adaptive threshold for sketch-like output
- sobel_edge: Sobel gradient-based edge detection
- laplacian_edge: Laplacian operator edge detection

Sketch & Pencil Effects:
- pencil_sketch: Pencil sketch using color dodge blending
- pencil_color: Colored pencil with reduced saturation
- sketch_effect: Legacy sketch effect (color dodge variant)
- pencil_color_effect: Legacy colored pencil variant
"""

from typing import Optional

import cv2
import numpy as np


# ============================================================================
# BASIC EDGE EFFECTS
# ============================================================================


def canny_edge(
    image: np.ndarray, low_threshold: int = 100, high_threshold: int = 200
) -> Optional[np.ndarray]:
    """Detect edges using Canny edge detection.

    Steps:
    1. Convert to grayscale
    2. Apply Gaussian blur to reduce noise
    3. Apply Canny edge detection
    4. Return binary edge image

    Parameters:
    - image: Input BGR image as NumPy array
    - low_threshold: Lower threshold for Canny hysteresis
    - high_threshold: Upper threshold for Canny hysteresis

    Returns: Binary edge image (uint8) or None if invalid input
    """
    if image is None:
        return None

    try:
        # 1. convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 2. apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # 3. apply Canny edge detection
        edges = cv2.Canny(
            blurred, max(1, int(low_threshold)), max(1, int(high_threshold))
        )

        # 4. return edge image
        return edges
    except Exception:
        return None


def adaptive_sketch(image: np.ndarray) -> Optional[np.ndarray]:
    """Create sketch-like image using adaptive thresholding.

    Steps:
    1. Convert to grayscale
    2. Apply median blur to reduce noise
    3. Apply adaptive threshold (THRESH_BINARY)
    4. Return black & white sketch image

    Parameters:
    - image: Input BGR image as NumPy array

    Returns: Binary sketch image (uint8) or None if invalid input
    """
    if image is None:
        return None

    try:
        # 1. convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 2. apply median blur to reduce noise
        blurred = cv2.medianBlur(gray, 5)

        # 3. apply adaptive threshold for sketch effect
        sketch = cv2.adaptiveThreshold(
            blurred,
            255,
            cv2.ADAPTIVE_THRESH_MEAN_C,
            cv2.THRESH_BINARY,
            9,
            2,
        )

        # 4. return sketch image
        return sketch
    except Exception:
        return None


def sobel_edge(image: np.ndarray) -> Optional[np.ndarray]:
    """Detect edges using Sobel operator.

    Steps:
    1. Convert to grayscale
    2. Compute Sobel gradient in X direction
    3. Compute Sobel gradient in Y direction
    4. Compute magnitude of combined gradients
    5. Normalize result to 0-255 range
    6. Return edge image

    Parameters:
    - image: Input BGR image as NumPy array

    Returns: Edge magnitude image (uint8) or None if invalid input
    """
    if image is None:
        return None

    try:
        # 1. convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 2. Sobel X gradient
        sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)

        # 3. Sobel Y gradient
        sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)

        # 4. compute magnitude of gradients
        magnitude = np.sqrt(sobel_x**2 + sobel_y**2)

        # 5. normalize to 0-255
        magnitude = (magnitude / magnitude.max() * 255).astype(np.uint8)

        # 6. return edge image
        return magnitude
    except Exception:
        return None


def laplacian_edge(image: np.ndarray) -> Optional[np.ndarray]:
    """Detect edges using Laplacian operator.

    Steps:
    1. Convert to grayscale
    2. Apply Laplacian operator for edge detection
    3. Convert to absolute values
    4. Normalize result to 0-255 range
    5. Return edge image

    Parameters:
    - image: Input BGR image as NumPy array

    Returns: Edge image (uint8) or None if invalid input
    """
    if image is None:
        return None

    try:
        # 1. convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 2. apply Laplacian operator
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)

        # 3. convert to absolute values
        laplacian = np.absolute(laplacian)

        # 4. normalize to 0-255
        laplacian = (laplacian / laplacian.max() * 255).astype(np.uint8)

        # 5. return edge image
        return laplacian
    except Exception:
        return None


# ============================================================================
# SKETCH EFFECT
# ============================================================================


def pencil_sketch(image: np.ndarray, blur_ksize: int = 21) -> Optional[np.ndarray]:
    """Create pencil sketch effect using color dodge blending.

    Steps:
    1. Convert to grayscale
    2. Invert grayscale image
    3. Apply Gaussian blur to inverted image
    4. Divide grayscale by inverted blurred (color dodge)
    5. Adjust contrast using cv2.normalize
    6. Return pencil sketch image

    Parameters:
    - image: Input BGR image as NumPy array
    - blur_ksize: Kernel size for Gaussian blur (must be odd)

    Returns: Grayscale sketch image (uint8) or None if invalid input
    """
    if image is None:
        return None

    try:
        # ensure blur_ksize is odd
        ksize = int(blur_ksize)
        if ksize % 2 == 0:
            ksize += 1
        if ksize < 3:
            ksize = 3

        # 1. convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 2. invert grayscale image
        inv_gray = 255 - gray

        # 3. apply Gaussian blur to inverted image
        blurred = cv2.GaussianBlur(inv_gray, (ksize, ksize), 0)

        # 4. color dodge: divide gray by (255 - blurred)
        gray_f = gray.astype(np.float32)
        blurred_f = blurred.astype(np.float32)
        denominator = 255.0 - blurred_f
        denominator = np.maximum(denominator, 1.0)
        sketch = (gray_f / denominator * 255.0).astype(np.uint8)

        # 5. adjust contrast using normalize
        sketch = cv2.normalize(sketch, None, 0, 255, cv2.NORM_MINMAX)

        # 6. return sketch image
        return sketch
    except Exception:
        return None


# ============================================================================
# COLORED PENCIL EFFECT
# ============================================================================


def pencil_color(
    image: np.ndarray, blur_ksize: int = 21, color_strength: float = 0.3
) -> Optional[np.ndarray]:
    """Create colored pencil effect with reduced saturation.

    Steps:
    1. Create sketch outline using pencil_sketch()
    2. Convert original image to HSV
    3. Reduce saturation (multiply S channel by color_strength)
    4. Convert back to BGR
    5. Blend colored image with sketch outline
    6. Return colored pencil image

    Parameters:
    - image: Input BGR image as NumPy array
    - blur_ksize: Kernel size for sketch blur (must be odd)
    - color_strength: Saturation multiplier (0.0-1.0 for muted colors)

    Returns: Colored pencil image (uint8) or None if invalid input
    """
    if image is None:
        return None

    try:
        # ensure blur_ksize is odd
        ksize = int(blur_ksize)
        if ksize % 2 == 0:
            ksize += 1
        if ksize < 3:
            ksize = 3

        # 1. create sketch outline
        sketch = pencil_sketch(image, blur_ksize=ksize)
        if sketch is None:
            return None

        # 2. convert original to HSV
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # 3. reduce saturation
        color_str = float(color_strength)
        hsv[:, :, 1] = cv2.multiply(hsv[:, :, 1], color_str)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1], 0, 255).astype(np.uint8)

        # 4. convert back to BGR
        desaturated = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

        # 5. blend with sketch outline
        # invert sketch so edges are dark (strengthen them)
        sketch_inv = 255 - sketch
        sketch_f = sketch_inv.astype(np.float32) / 255.0

        # darken where sketch is present
        result = (
            desaturated.astype(np.float32) * sketch_f[:, :, np.newaxis]
        ).astype(np.uint8)

        # 6. return colored pencil image
        return result
    except Exception:
        return None

# ============================================================================
# LEGACY FUNCTIONS (alternative implementations)
# ============================================================================


def sketch_effect(
    image: np.ndarray, blur_ksize: int = 21, contrast: float = 1.5
) -> Optional[np.ndarray]:
    """Convert image to pencil sketch using color dodge blending.

    The sketch effect is created by:
    1. Converting to grayscale
    2. Inverting the grayscale image
    3. Applying Gaussian blur to the inverted image
    4. Blending using color dodge (dividing original by blurred)
    5. Adjusting contrast

    Parameters:
    - image: Input BGR image as NumPy array
    - blur_ksize: Kernel size for Gaussian blur (must be odd and > 0)
    - contrast: Contrast multiplier (typically 1.0–3.0)

    Returns: Sketch image or None if input is invalid
    """
    if image is None:
        return None

    try:
        # ensure blur_ksize is odd
        ksize = int(blur_ksize)
        if ksize % 2 == 0:
            ksize += 1
        if ksize < 3:
            ksize = 3

        # 1. convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 2. invert grayscale
        inv_gray = 255 - gray

        # 3. apply Gaussian blur to inverted image
        blurred = cv2.GaussianBlur(inv_gray, (ksize, ksize), 0)

        # 4. color dodge blending: result = gray / (255 - blurred) * 255
        # to avoid division by zero, convert to float
        gray_f = gray.astype(np.float32)
        blurred_f = blurred.astype(np.float32)
        denominator = 255.0 - blurred_f
        # avoid division by zero
        denominator = np.maximum(denominator, 1.0)
        sketch = (gray_f / denominator * 255.0).astype(np.uint8)

        # 5. adjust contrast: output = (value - 128) * contrast + 128
        contrast_val = float(contrast)
        sketch_f = sketch.astype(np.float32)
        sketch = ((sketch_f - 128.0) * contrast_val + 128.0).astype(np.uint8)
        sketch = np.clip(sketch, 0, 255).astype(np.uint8)

        # convert single-channel to BGR for consistency with rest of pipeline
        return cv2.cvtColor(sketch, cv2.COLOR_GRAY2BGR)

    except Exception:
        return None


def pencil_color_effect(
    image: np.ndarray, blur_ksize: int = 21, saturation_scale: float = 0.5
) -> Optional[np.ndarray]:
    """Create colored pencil effect by combining sketch with desaturated image.

    The pencil effect is created by:
    1. Extracting sketch edges using sketch_effect
    2. Converting original to HSV and reducing saturation
    3. Extracting edges from desaturated image
    4. Combining sketch and colored edges

    Parameters:
    - image: Input BGR image as NumPy array
    - blur_ksize: Kernel size for sketch blur (must be odd and > 0)
    - saturation_scale: Saturation multiplier (0.0–1.0 for muted; >1.0 for vibrant)

    Returns: Colored pencil image or None if input is invalid
    """
    if image is None:
        return None

    try:
        # ensure blur_ksize is odd
        ksize = int(blur_ksize)
        if ksize % 2 == 0:
            ksize += 1
        if ksize < 3:
            ksize = 3

        # 1. create sketch mask using the sketch_effect function
        sketch = sketch_effect(image, blur_ksize=ksize, contrast=1.5)
        if sketch is None:
            return None
        # extract the grayscale sketch from BGR
        sketch_gray = cv2.cvtColor(sketch, cv2.COLOR_BGR2GRAY)

        # 2. convert to HSV and reduce saturation
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        sat_scale = float(saturation_scale)
        # saturation is in channel index 1
        hsv[:, :, 1] = cv2.multiply(hsv[:, :, 1], sat_scale)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1], 0, 255).astype(np.uint8)
        desaturated = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

        # 3. extract edges from desaturated image (same sketch process)
        edges = sketch_effect(desaturated, blur_ksize=ksize, contrast=1.5)
        if edges is None:
            edges_gray = sketch_gray
        else:
            edges_gray = cv2.cvtColor(edges, cv2.COLOR_BGR2GRAY)

        # 4. combine: use sketch edges to darken the desaturated image
        # invert sketch so edges are black (0) and non-edges are white (255)
        sketch_mask = 255 - sketch_gray
        sketch_mask_f = sketch_mask.astype(np.float32) / 255.0

        # blend: darken colors where sketch is present
        result = (
            desaturated.astype(np.float32) * sketch_mask_f[:, :, np.newaxis]
        ).astype(np.uint8)

        return result

    except Exception:
        return None


# ============================================================================
# ENHANCED ARTISTIC EFFECTS
# ============================================================================


def oil_painting_effect(image: np.ndarray, size: int = 7) -> Optional[np.ndarray]:
    """Create an oil painting effect using bilateral filtering.

    Steps:
    1. Apply bilateral filter multiple times for smoothness
    2. Enhance edges slightly
    3. Return the oil painting-like result

    Parameters:
    - image: Input BGR image as NumPy array
    - size: Kernel size for bilateral filter (odd number, default 7)

    Returns: Oil painting effect image or None if invalid input
    """
    if image is None:
        return None

    try:
        # ensure size is odd
        s = int(size)
        if s % 2 == 0:
            s += 1
        if s < 3:
            s = 3

        # apply bilateral filter multiple times for oil painting look
        result = image.copy()
        for _ in range(2):
            result = cv2.bilateralFilter(result, s, 75, 75)

        return result
    except Exception:
        return None


def vintage_sepia_effect(image: np.ndarray, intensity: float = 0.5) -> Optional[np.ndarray]:
    """Create a vintage sepia tone effect.

    Steps:
    1. Convert to sepia using the standard sepia matrix
    2. Blend with original based on intensity
    3. Adjust brightness slightly for aged look

    Parameters:
    - image: Input BGR image as NumPy array
    - intensity: Sepia strength 0.0 (original) to 1.0 (full sepia)

    Returns: Sepia-toned image or None if invalid input
    """
    if image is None:
        return None

    try:
        intensity = max(0.0, min(1.0, float(intensity)))

        # standard sepia kernel (BGR order for OpenCV)
        kernel = np.array(
            [
                [0.272, 0.534, 0.131],
                [0.349, 0.686, 0.168],
                [0.393, 0.769, 0.189],
            ]
        )

        # apply sepia
        sepia = cv2.transform(image, kernel)
        sepia = np.clip(sepia, 0, 255).astype(np.uint8)

        # blend with original
        result = cv2.addWeighted(image, 1 - intensity, sepia, intensity, 0)

        # reduce brightness slightly for aged look
        hsv = cv2.cvtColor(result, cv2.COLOR_BGR2HSV)
        hsv[:, :, 2] = cv2.multiply(hsv[:, :, 2], 0.95)
        result = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

        return result
    except Exception:
        return None


def sharpen_effect(image: np.ndarray, strength: float = 1.0) -> Optional[np.ndarray]:
    """Create a sharpened version of the image using unsharp masking.

    Steps:
    1. Create a blurred version
    2. Subtract blurred from original and scale by strength
    3. Add back to original to create sharp effect

    Parameters:
    - image: Input BGR image as NumPy array
    - strength: Sharpening intensity (0.5 = mild, 1.0 = moderate, 2.0 = strong)

    Returns: Sharpened image or None if invalid input
    """
    if image is None:
        return None

    try:
        strength = max(0.0, float(strength))

        # create blurred version
        blurred = cv2.GaussianBlur(image, (0, 0), 2)

        # unsharp masking: original + (original - blurred) * strength
        sharpened = cv2.addWeighted(
            image.astype(np.float32),
            1 + strength,
            blurred.astype(np.float32),
            -strength,
            0,
        )

        # clip and convert back to uint8
        sharpened = np.clip(sharpened, 0, 255).astype(np.uint8)

        return sharpened
    except Exception:
        return None


# ============================================================================
# ENHANCEMENT FILTERS (adjustable controls)
# ============================================================================


def adjust_brightness(image: np.ndarray, factor: float = 1.0) -> Optional[np.ndarray]:
    """Adjust image brightness.

    Parameters:
    - image: Input BGR image
    - factor: Brightness multiplier (0.5 = darker, 1.0 = original, 2.0 = brighter)

    Returns: Brightness-adjusted image or None
    """
    if image is None:
        return None

    try:
        factor = max(0.0, float(factor))
        result = cv2.convertScaleAbs(image, alpha=factor, beta=0)
        return np.clip(result, 0, 255).astype(np.uint8)
    except Exception:
        return None


def adjust_contrast(image: np.ndarray, factor: float = 1.0) -> Optional[np.ndarray]:
    """Adjust image contrast.

    Parameters:
    - image: Input BGR image
    - factor: Contrast multiplier (0.5 = lower, 1.0 = original, 2.0 = higher)

    Returns: Contrast-adjusted image or None
    """
    if image is None:
        return None

    try:
        factor = max(0.0, float(factor))
        # convert to float, apply contrast, clip and convert back
        img_f = image.astype(np.float32) / 255.0
        # adjust around 0.5 (middle gray)
        img_f = (img_f - 0.5) * factor + 0.5
        img_f = np.clip(img_f, 0, 1)
        return (img_f * 255).astype(np.uint8)
    except Exception:
        return None


def adjust_saturation(image: np.ndarray, factor: float = 1.0) -> Optional[np.ndarray]:
    """Adjust color saturation (intensity).

    Parameters:
    - image: Input BGR image
    - factor: Saturation multiplier (0.5 = desaturated, 1.0 = original, 2.0 = vivid)

    Returns: Saturation-adjusted image or None
    """
    if image is None:
        return None

    try:
        factor = max(0.0, float(factor))
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        hsv[:, :, 1] = cv2.multiply(hsv[:, :, 1], factor)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1], 0, 255).astype(np.uint8)
        return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    except Exception:
        return None


def apply_blur(image: np.ndarray, strength: float = 5.0) -> Optional[np.ndarray]:
    """Apply Gaussian blur.

    Parameters:
    - image: Input BGR image
    - strength: Blur strength (1 = very light, 15 = strong)

    Returns: Blurred image or None
    """
    if image is None:
        return None

    try:
        strength = int(max(1, strength))
        # ensure odd kernel size
        if strength % 2 == 0:
            strength += 1
        return cv2.GaussianBlur(image, (strength, strength), 0)
    except Exception:
        return None


# ============================================================================
# WRAPPER FUNCTIONS FOR CARTOON STYLES
# ============================================================================

def cartoonify_classic(image: np.ndarray) -> Optional[np.ndarray]:
    """Apply classic cartoon style (uses bilateral filtering + edge mask).
    
    This is a simplified cartoon effect using bilateral filtering
    for color smoothing combined with edge detection.
    
    Parameters:
    - image: Input BGR image as NumPy array
    
    Returns: Cartoonified image or None if invalid input
    """
    if image is None:
        return None
    
    try:
        # 1. Apply bilateral filter for smooth colors
        smooth = cv2.bilateralFilter(image, 9, 75, 75)
        smooth = cv2.bilateralFilter(smooth, 9, 75, 75)
        
        # 2. Detect edges
        gray = cv2.cvtColor(smooth, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 200)
        
        # 3. Dilate edges to make them more visible
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        edges = cv2.dilate(edges, kernel, iterations=1)
        
        # 4. Invert edges and convert to BGR
        edges_inv = cv2.bitwise_not(edges)
        edges_bgr = cv2.cvtColor(edges_inv, cv2.COLOR_GRAY2BGR)
        
        # 5. Combine smooth colors with black edges
        result = cv2.bitwise_and(smooth, edges_bgr)
        
        return result
    except Exception:
        return None
