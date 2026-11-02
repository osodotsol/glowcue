"""Selfie validation and metadata removal (in memory)."""

from __future__ import annotations

import io

import pytest
from PIL import Image
from tests.youcam_fakes import selfie_bytes

from app.errors import AppError
from app.services.image import MAX_LONG_SIDE, MAX_UPLOAD_BYTES, prepare_image


def jpeg_with_metadata(size: tuple[int, int] = (800, 600), orientation: int | None = None) -> bytes:
    exif = Image.Exif()
    exif[0x010F] = "SecretCameraMake"  # Make
    exif[0x0131] = "SecretSoftwareTag"  # Software
    exif[0x8825] = {1: "N", 2: (6.0, 27.0, 0.0), 3: "E", 4: (3.0, 23.0, 0.0)}  # GPSInfo: Lagos-ish
    if orientation:
        exif[0x0112] = orientation
    buf = io.BytesIO()
    Image.new("RGB", size, (200, 150, 130)).save(buf, "JPEG", exif=exif, comment=b"SecretComment")
    return buf.getvalue()


def code_of(data: bytes) -> tuple[str, int]:
    with pytest.raises(AppError) as err:
        prepare_image(data)
    return err.value.code, err.value.status


def test_image_metadata_fixture_really_contains_metadata():
    raw = jpeg_with_metadata()
    assert b"SecretCameraMake" in raw and b"SecretComment" in raw
    assert Image.open(io.BytesIO(raw)).getexif().get_ifd(0x8825)  # GPS present before cleaning


def test_image_prepare_strips_exif_gps_and_comments():
    out = prepare_image(jpeg_with_metadata())
    assert out.content_type == "image/jpeg"
    for marker in (b"Exif", b"SecretCameraMake", b"SecretSoftwareTag", b"SecretComment"):
        assert marker not in out.data
    reopened = Image.open(io.BytesIO(out.data))
    assert reopened.format == "JPEG"
    assert len(reopened.getexif()) == 0
    assert not {"exif", "comment", "xmp"} & set(reopened.info)


def test_image_prepare_applies_orientation_before_dropping_it():
    out = prepare_image(jpeg_with_metadata(size=(800, 600), orientation=6))  # 6 = rotate 90 degrees
    assert (out.width, out.height) == (600, 800)


def test_image_prepare_accepts_png_with_transparency():
    buf = io.BytesIO()
    Image.new("RGBA", (600, 700), (200, 150, 130, 128)).save(buf, "PNG")
    out = prepare_image(buf.getvalue())
    assert Image.open(io.BytesIO(out.data)).mode == "RGB"


def test_image_prepare_checks_the_real_signature_not_the_name():
    assert code_of(b"this is not an image at all") == ("invalid_image", 415)
    gif = io.BytesIO()
    Image.new("RGB", (600, 600)).save(gif, "GIF")
    assert code_of(gif.getvalue()) == ("invalid_image", 415)


def test_image_prepare_rejects_a_truncated_jpeg():
    assert code_of(jpeg_with_metadata()[:200]) == ("invalid_image", 415)


def test_image_prepare_rejects_photos_below_480px_short_side():
    assert code_of(selfie_bytes((470, 900))) == ("image_too_small", 422)


def test_image_prepare_rejects_files_over_10mb():
    assert code_of(b"\xff\xd8\xff" + b"0" * MAX_UPLOAD_BYTES) == ("image_too_large", 413)


def test_image_prepare_scales_the_long_side_down_to_2048():
    out = prepare_image(selfie_bytes((3000, 2400)))
    assert max(out.width, out.height) == MAX_LONG_SIDE and min(out.width, out.height) >= 480


def test_image_prepare_rejects_extreme_strips_after_scaling():
    assert code_of(selfie_bytes((4000, 500))) == ("image_shape", 422)
