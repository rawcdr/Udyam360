"""Image preprocessing utilities for enhancing document OCR accuracy."""

import io
from pathlib import Path
from typing import Tuple, Union
from PIL import Image, ImageEnhance, ImageFilter, ImageOps


def load_image(image_input: Union[bytes, str, Path]) -> Image.Image:
    """Safely load an image from bytes, str path, or Path object into a PIL Image."""
    if isinstance(image_input, bytes):
        img = Image.open(io.BytesIO(image_input))
    elif isinstance(image_input, (str, Path)):
        img = Image.open(Path(image_input))
    else:
        raise ValueError(f"Unsupported image input type: {type(image_input)}")
    
    # Handle EXIF rotation if present
    img = ImageOps.exif_transpose(img)
    return img


def preprocess_document_image(
    image_input: Union[bytes, str, Path],
    enhance_contrast: bool = True,
    sharpen: bool = True,
    target_dpi_scale: bool = True,
) -> Tuple[Image.Image, int, int]:
    """Preprocess document image for optimal character recognition.

    Operations performed:
    1. Grayscale conversion.
    2. Adaptive contrast enhancement.
    3. Edge sharpening.
    4. Size normalization.

    Returns:
        (preprocessed_pil_image, original_width, original_height)
    """
    orig = load_image(image_input)
    width, height = orig.size

    # Convert to RGB if palette/RGBA, then to Grayscale
    if orig.mode != "RGB":
        working = orig.convert("RGB")
    else:
        working = orig.copy()

    # Grayscale
    gray = working.convert("L")

    # Resize if very small (< 1000px on longest side) for better OCR accuracy
    max_dim = max(width, height)
    if target_dpi_scale and max_dim < 1200:
        scale_factor = 1200.0 / max_dim
        new_w = int(width * scale_factor)
        new_h = int(height * scale_factor)
        gray = gray.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # Contrast enhancement
    if enhance_contrast:
        enhancer = ImageEnhance.Contrast(gray)
        gray = enhancer.enhance(1.5)

    # Sharpening
    if sharpen:
        gray = gray.filter(ImageFilter.SHARPEN)

    return gray, width, height

