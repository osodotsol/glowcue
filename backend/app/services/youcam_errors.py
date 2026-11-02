"""The one table that turns YouCam (and client-side) failure codes into friendly GlowCue errors.

Codes come from the official docs (task-level `data.error` values, request-level `error_code` values) plus the
GlowCue client's own codes (timeout, network, credit_floor, ...). Anything unknown falls back to a generic,
retryable "analysis_failed". Messages are plain, cosmetic and never blame the customer's skin.
"""

from __future__ import annotations

from app.models import ErrorDetail

_RETAKE = "retake"
_SERVICE = "service"

# vendor/client code -> (GlowCue code, message, retryable, kind)
_TABLE: dict[str, tuple[str, str, bool, str]] = {
    # ---- photo problems: the customer can fix these with another photo
    "error_no_face": (
        "no_face",
        "We couldn't find a face in this photo. Use a front-facing selfie with your whole face in view.",
        True,
        _RETAKE,
    ),  # noqa: E501
    "error_src_face_too_small": (
        "face_too_small",
        "Your face looks small in the frame. Move closer so your face fills most of the photo's width.",
        True,
        _RETAKE,
    ),  # noqa: E501
    "error_src_face_out_of_bound": (
        "face_out_of_frame",
        "Part of your face is outside the photo. Centre your face and keep all of it in view.",
        True,
        _RETAKE,
    ),  # noqa: E501
    "error_lighting_dark": (
        "too_dark",
        "This photo is too dark. Face a window or a soft, even light and try again.",
        True,
        _RETAKE,
    ),  # noqa: E501
    "error_pose": ("face_angle", "Look straight at the camera with a relaxed, neutral expression.", True, _RETAKE),
    "error_large_face_angle": (
        "face_angle",
        "Look straight at the camera with a relaxed, neutral expression.",
        True,
        _RETAKE,
    ),  # noqa: E501
    "error_face_parsing": (
        "face_unclear",
        "We couldn't read your skin clearly. Remove glasses, keep hair off your forehead and hold the camera steady.",
        True,
        _RETAKE,
    ),  # noqa: E501
    "error_multiple_people": (
        "multiple_faces",
        "We found more than one person. Use a photo of just you.",
        True,
        _RETAKE,
    ),
    "error_below_min_image_size": (
        "image_too_small",
        "This photo is too small. Use one at least 480 pixels on its shorter side.",
        True,
        _RETAKE,
    ),  # noqa: E501
    "error_exceed_max_image_size": (
        "image_too_large",
        "This photo is too large. Please use a smaller one.",
        True,
        _RETAKE,
    ),
    "exceed_max_filesize": ("image_too_large", "This photo is too large. Please use a smaller one.", True, _RETAKE),
    "error_unsupport_ratio": ("image_shape", "Try an upright (portrait) photo of your face.", True, _RETAKE),
    "error_decode_image": (
        "image_unreadable",
        "We couldn't read this photo. Try a different JPEG or PNG.",
        True,
        _RETAKE,
    ),
    "error_download_image": (
        "image_unreadable",
        "We couldn't read this photo. Try a different JPEG or PNG.",
        True,
        _RETAKE,
    ),  # noqa: E501
    "error_nsfw_content_detected": (
        "image_rejected",
        "This photo can't be analysed. Please use a simple selfie.",
        False,
        _RETAKE,
    ),  # noqa: E501
    # ---- service state: not the customer's photo
    "credit_floor": (
        "live_paused",
        "Live analysis is paused right now. You can choose a sample profile instead.",
        False,
        _SERVICE,
    ),  # noqa: E501
    "CreditInsufficiency": (
        "live_paused",
        "Live analysis is paused right now. You can choose a sample profile instead.",
        False,
        _SERVICE,
    ),  # noqa: E501
    "auth_failed": (
        "live_unavailable",
        "Live analysis isn't available right now. You can choose a sample profile instead.",
        False,
        _SERVICE,
    ),  # noqa: E501
    "credit_unknown": (
        "live_unavailable",
        "Live analysis isn't available right now. You can choose a sample profile instead.",
        False,
        _SERVICE,
    ),  # noqa: E501
    "rate_limited": ("busy", "The analysis service is busy. Please try again in a minute.", True, _SERVICE),
    "timeout": ("analysis_timeout", "The analysis took too long. Please try again in a moment.", True, _SERVICE),
    "InvalidParameters": (
        "analysis_failed",
        "Something went wrong on our side. Please try again later, or choose a sample profile.",
        False,
        _SERVICE,
    ),  # noqa: E501
}

_FALLBACK = (
    "analysis_failed",
    "Something went wrong analysing your photo. Please try again, or choose a sample profile.",
    True,
    _SERVICE,
)


def friendly_error(code: str) -> ErrorDetail:
    """Map a vendor or client failure code to the error shown to the customer."""
    glowcue_code, message, retryable, kind = _TABLE.get(code, _FALLBACK)
    return ErrorDetail(code=glowcue_code, message=message, retryable=retryable, retake=kind == _RETAKE)
