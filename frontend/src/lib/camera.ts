// Pure helpers for the in-app selfie camera and the photo picker (no DOM access, so they are unit-tested in Node).
// The camera itself lives in components/CameraCapture.tsx.

export const ACCEPTED_PHOTO_TYPES = ["image/jpeg", "image/png"];
export const MAX_PHOTO_BYTES = 10 * 1024 * 1024;
/** YouCam's SD analysis needs at least this many pixels on the photo's short side (same rule as imagePrep). */
export const MIN_SHORT_SIDE = 480;

/** The checks every photo passes before it becomes the preview, whether chosen from files or taken with the camera. */
export function photoFileProblem(file: { type: string; size: number }): string | null {
  if (!ACCEPTED_PHOTO_TYPES.includes(file.type)) return "Please choose a JPEG or PNG photo.";
  if (file.size > MAX_PHOTO_BYTES) return "That photo is over 10 MB. Please choose a smaller one.";
  return null;
}

export type CameraProblem = "denied" | "unavailable" | "busy" | "failed";

/** Maps a getUserMedia failure (a DOMException name) to what we tell the customer. */
export function cameraProblem(error: unknown): CameraProblem {
  const name = typeof error === "object" && error !== null && "name" in error ? String((error as { name: unknown }).name) : "";
  if (name === "NotAllowedError" || name === "SecurityError" || name === "PermissionDeniedError") return "denied";
  if (name === "NotFoundError" || name === "OverconstrainedError" || name === "DevicesNotFoundError") return "unavailable";
  if (name === "NotReadableError" || name === "TrackStartError" || name === "AbortError") return "busy";
  return "failed";
}

export const CAMERA_PROBLEM_TEXT: Record<CameraProblem, { title: string; body: string }> = {
  denied: {
    title: "Camera access is off",
    body: "GlowCue can't use your camera because permission was declined. You can allow it in your browser's site settings, or choose a photo you already have.",
  },
  unavailable: {
    title: "No camera found",
    body: "We couldn't find a camera on this device. You can choose a photo you already have instead.",
  },
  busy: {
    title: "Your camera is busy",
    body: "Another app or tab may be using your camera. Close it and try again, or choose a photo you already have.",
  },
  failed: {
    title: "The camera didn't start",
    body: "Something stopped the camera from starting. Try again, or choose a photo you already have.",
  },
};

export interface Crop {
  sx: number;
  sy: number;
  width: number;
  height: number;
}

/**
 * The part of a camera frame to keep: a centred 4:5 portrait (what the preview shows) when that is still large enough
 * for analysis, otherwise the widest centred crop that keeps MIN_SHORT_SIDE, otherwise the whole frame. Returns null
 * when the frame itself is too small to analyse.
 */
export function selfieCrop(frameWidth: number, frameHeight: number): Crop | null {
  if (Math.min(frameWidth, frameHeight) < MIN_SHORT_SIDE) return null;
  let width = Math.min(frameWidth, Math.round((frameHeight * 4) / 5));
  let height = Math.min(frameHeight, Math.round((width * 5) / 4));
  if (Math.min(width, height) < MIN_SHORT_SIDE) {
    width = Math.min(frameWidth, Math.max(width, MIN_SHORT_SIDE));
    height = frameHeight;
  }
  return { sx: Math.round((frameWidth - width) / 2), sy: Math.round((frameHeight - height) / 2), width, height };
}
