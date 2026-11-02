"""Selfie validation and clean re-encoding, entirely in memory (never written to disk, temp files or logs).

* The file signature ("magic bytes") must be JPEG or PNG; the filename and declared type are not trusted.
* Limits follow the YouCam docs for SD analysis: under 10 MB, shorter side at least 480 px.
* The photo is rotated upright from its EXIF orientation, then copied pixel-by-pixel into a NEW image and saved
  as JPEG. The copy carries no EXIF, GPS, XMP, comments or other metadata from the original.
* The long side is capped at 2048 px (YouCam resizes anything over 2560 px itself; smaller uploads are faster).
"""

from __future__ import annotations

import io
from dataclasses import dataclass

from PIL import Image, ImageOps, UnidentifiedImageError

from app.errors import AppError

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MIN_SHORT_SIDE = 480
MAX_LONG_SIDE = 2048
MAX_PIXELS = 40_000_000  # refuse decompression bombs before decoding
# At most this many photos are decoded at once (in worker threads, off the event loop); more are told to retry.
MAX_CONCURRENT_PREPARATIONS = 2
_JPEG = b"\xff\xd8\xff"
_PNG = b"\x89PNG\r\n\x1a\n"


@dataclass(frozen=True)
class PreparedImage:
    data: bytes
    width: int
    height: int
    content_type: str = "image/jpeg"


def _reject(code: str, message: str, status: int = 422) -> AppError:
    return AppError(code, message, status=status)


def check_upload(data: bytes) -> None:
    """Cheap checks that never decode the image: size and file signature (same errors as prepare_image)."""
    if len(data) > MAX_UPLOAD_BYTES:
        raise _reject("image_too_large", "That photo is over 10 MB. Please choose a smaller one.", 413)
    if not (data.startswith(_JPEG) or data.startswith(_PNG)):
        raise _reject("invalid_image", "Please choose a JPEG or PNG photo.", 415)


def prepare_image(data: bytes) -> PreparedImage:
    """CPU-heavy (Pillow decode and re-encode): call it from a worker thread, not the event loop."""
    check_upload(data)
    try:
        with Image.open(io.BytesIO(data)) as source:
            if source.format not in ("JPEG", "PNG"):
                raise _reject("invalid_image", "Please choose a JPEG or PNG photo.", 415)
            if source.width * source.height > MAX_PIXELS:
                raise _reject("image_too_large", "That photo has too many pixels. Please choose a smaller one.", 413)
            upright = ImageOps.exif_transpose(source)
            if upright.mode in ("RGBA", "LA", "P"):
                rgba = upright.convert("RGBA")
                flat = Image.new("RGB", rgba.size, (255, 255, 255))
                flat.paste(rgba, mask=rgba.getchannel("A"))
            else:
                flat = upright.convert("RGB")
    except AppError:
        raise
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        raise _reject(
            "invalid_image", "We couldn't read that photo. Please try a different JPEG or PNG.", 415
        ) from None

    if min(flat.size) < MIN_SHORT_SIDE:
        raise _reject("image_too_small", "This photo is too small. Use one at least 480 pixels on its shorter side.")
    if max(flat.size) > MAX_LONG_SIDE:
        flat.thumbnail((MAX_LONG_SIDE, MAX_LONG_SIDE), Image.Resampling.LANCZOS)
        if min(flat.size) < MIN_SHORT_SIDE:
            raise _reject("image_shape", "This photo is very long and narrow. Try an upright photo of your face.")

    clean = Image.new("RGB", flat.size)  # fresh image: no metadata can survive the copy
    clean.paste(flat)
    out = io.BytesIO()
    clean.save(out, format="JPEG", quality=90, optimize=True)
    return PreparedImage(data=out.getvalue(), width=clean.width, height=clean.height)
