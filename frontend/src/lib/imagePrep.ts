// Client-side photo preparation before a live analysis (the server checks and cleans the photo again).
// The photo is drawn upright onto a canvas and re-encoded as JPEG: the result carries no EXIF, GPS or other
// metadata. The long side is capped at 2048 px; YouCam's SD analysis needs at least 480 px on the short side.

const MIN_SHORT_SIDE = 480;
const MAX_LONG_SIDE = 2048;

export class PhotoPrepError extends Error {}

/** `photoUrl` is the local object URL of the chosen file (it never leaves the device in this step). */
export async function prepareSelfie(photoUrl: string): Promise<Blob> {
  let bitmap: ImageBitmap;
  try {
    const img = new Image();
    img.src = photoUrl;
    await img.decode(); // browsers apply the EXIF orientation when decoding into an <img>
    bitmap = await createImageBitmap(img);
  } catch {
    throw new PhotoPrepError("We couldn't read this photo. Please try a different JPEG or PNG.");
  }
  try {
    const { width, height } = bitmap;
    if (Math.min(width, height) < MIN_SHORT_SIDE) {
      throw new PhotoPrepError("This photo is too small. Use one at least 480 pixels on its shorter side.");
    }
    const scale = Math.min(1, MAX_LONG_SIDE / Math.max(width, height));
    const w = Math.round(width * scale);
    const h = Math.round(height * scale);
    if (Math.min(w, h) < MIN_SHORT_SIDE) {
      throw new PhotoPrepError("This photo is very long and narrow. Try an upright photo of your face.");
    }
    const canvas = document.createElement("canvas");
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext("2d");
    if (!ctx) throw new PhotoPrepError("Your browser couldn't prepare this photo. Please try another browser.");
    ctx.drawImage(bitmap, 0, 0, w, h);
    const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, "image/jpeg", 0.9));
    if (!blob) throw new PhotoPrepError("Your browser couldn't prepare this photo. Please try another browser.");
    return blob;
  } finally {
    bitmap.close();
  }
}
