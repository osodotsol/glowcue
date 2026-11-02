import { useCallback, useEffect, useRef, useState, type RefObject } from "react";
import { createPortal } from "react-dom";
import { CAMERA_PROBLEM_TEXT, cameraProblem, MIN_SHORT_SIDE, selfieCrop, type CameraProblem } from "../lib/camera";
import { useDialog } from "../lib/useDialog";
import { Button, MicroLabel } from "./ui";

type Stage = "starting" | "live" | "review" | "problem";

interface Props {
  /** Receives the captured photo (a JPEG File) when the customer accepts it. */
  onAccept: (photo: File) => void;
  /** Closes the camera and opens the ordinary photo picker instead. */
  onChoosePhoto: () => void;
  onClose: () => void;
  returnFocus: RefObject<HTMLElement | null>;
}

/** True when this browser can show a live camera preview (needs a secure context: https or localhost). */
export function cameraSupported(): boolean {
  return typeof navigator !== "undefined" && typeof navigator.mediaDevices?.getUserMedia === "function";
}

/**
 * In-app selfie camera. It is mounted only after the customer taps "Take a selfie", so permission is asked only
 * then. Privacy: the preview is a local stream that is never recorded or sent; a single frame is drawn to a canvas
 * only when the customer taps the shutter, every camera track is stopped as soon as that frame is taken (and on
 * close, unmount or page hide), and the photo is uploaded only later, after consent, by the live-analysis card.
 */
export function CameraCapture({ onAccept, onChoosePhoto, onClose, returnFocus }: Props) {
  const { panel, initialFocus, onKeyDown } = useDialog<HTMLElement, HTMLButtonElement>(true, onClose, returnFocus);
  const video = useRef<HTMLVideoElement>(null);
  const stream = useRef<MediaStream | null>(null);
  const [session, setSession] = useState(0);
  const [stage, setStage] = useState<Stage>(() => (cameraSupported() ? "starting" : "problem"));
  const [problem, setProblem] = useState<CameraProblem | "too_small">(() => (cameraSupported() ? "failed" : "unavailable"));
  const [shot, setShot] = useState<{ file: File; url: string } | null>(null);

  const stopCamera = useCallback(() => {
    stream.current?.getTracks().forEach((track) => track.stop());
    stream.current = null;
    if (video.current) video.current.srcObject = null;
  }, []);

  // Each session asks for one camera stream; "Retake" and "Try again" start a new session. The stream is requested
  // inside the effect so that every exit (retake, close, unmount, page hide) runs the same cleanup.
  useEffect(() => {
    if (!cameraSupported()) return; // the initial state already explains this
    let cancelled = false;
    navigator.mediaDevices
      .getUserMedia({ audio: false, video: { facingMode: "user", width: { ideal: 1280 }, height: { ideal: 1280 } } })
      .then((media) => {
        if (cancelled) {
          media.getTracks().forEach((track) => track.stop()); // closed while the permission prompt was open
          return;
        }
        stream.current = media;
        const el = video.current;
        if (el) {
          el.srcObject = media;
          el.play().catch(() => undefined); // a muted inline stream may autoplay
        }
        setStage("live");
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        setProblem(cameraProblem(error));
        setStage("problem");
      });
    const onHide = () => {
      cancelled = true;
      stopCamera();
    };
    window.addEventListener("pagehide", onHide);
    return () => {
      cancelled = true;
      window.removeEventListener("pagehide", onHide);
      stopCamera();
    };
  }, [session, stopCamera]);

  // The review image is a local object URL; release it when it is replaced or the camera closes.
  useEffect(
    () => () => {
      if (shot) URL.revokeObjectURL(shot.url);
    },
    [shot],
  );

  async function capture() {
    const el = video.current;
    if (!el || stage !== "live") return;
    const crop = selfieCrop(el.videoWidth, el.videoHeight);
    if (!crop) {
      stopCamera();
      setProblem("too_small");
      setStage("problem");
      return;
    }
    const canvas = document.createElement("canvas");
    canvas.width = crop.width;
    canvas.height = crop.height;
    canvas.getContext("2d")?.drawImage(el, crop.sx, crop.sy, crop.width, crop.height, 0, 0, crop.width, crop.height);
    stopCamera(); // one frame is all we need: the camera light goes off now
    const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, "image/jpeg", 0.92));
    canvas.width = 0; // drop the frame buffer
    if (!blob) {
      setProblem("failed");
      setStage("problem");
      return;
    }
    const file = new File([blob], "glowcue-selfie.jpg", { type: "image/jpeg" });
    setShot({ file, url: URL.createObjectURL(blob) });
    setStage("review");
  }

  function restart() {
    setShot(null);
    setStage("starting");
    setSession((n) => n + 1);
  }

  const problemText =
    problem === "too_small"
      ? {
          title: "This camera's picture is too small",
          body: `Skin analysis needs a photo at least ${MIN_SHORT_SIDE} pixels on its shorter side. Try your phone's camera, or choose a photo you already have.`,
        }
      : CAMERA_PROBLEM_TEXT[problem];

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-stretch justify-center sm:items-center sm:p-6">
      <div className="absolute inset-0 bg-ink/70 animate-fade" onClick={onClose} aria-hidden="true" />
      <section
        ref={panel}
        role="dialog"
        aria-modal="true"
        aria-labelledby="camera-title"
        onKeyDown={onKeyDown}
        className="relative flex max-h-full w-full flex-col gap-4 overflow-y-auto bg-ink p-4 text-surface sm:max-w-[440px] sm:rounded-[28px] sm:p-6 animate-fade"
      >
        <header className="flex items-center justify-between gap-3">
          <div>
            <MicroLabel className="text-peach">Selfie camera</MicroLabel>
            <h2 id="camera-title" className="display text-[28px] leading-tight">
              {stage === "review" ? (
                <>
                  Happy with <span className="italic text-peach">this one?</span>
                </>
              ) : (
                <>
                  Face the light, <span className="italic text-peach">fill the oval.</span>
                </>
              )}
            </h2>
          </div>
          <button
            ref={initialFocus}
            type="button"
            onClick={onClose}
            aria-label="Close camera"
            className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-surface/30 hover:bg-surface hover:text-ink"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <path d="M6 6l12 12M18 6L6 18" />
            </svg>
          </button>
        </header>

        <div className="relative mx-auto aspect-[4/5] w-full max-w-[400px] overflow-hidden rounded-[22px] bg-ink-soft">
          {/* the live preview is mirrored, like a mirror; the saved photo is not */}
          <video
            ref={video}
            muted
            playsInline
            aria-label="Live camera preview"
            className={`h-full w-full -scale-x-100 object-cover ${stage === "live" ? "" : "invisible"}`}
          />
          {stage === "review" && shot && (
            <img src={shot.url} alt="The selfie you just took" className="absolute inset-0 h-full w-full object-cover" />
          )}
          {stage === "live" && (
            <svg viewBox="0 0 290 360" preserveAspectRatio="none" className="pointer-events-none absolute inset-0 h-full w-full" aria-hidden="true">
              <path d="M18 58V18h40M232 18h40v40M272 302v40h-40M58 342H18v-40" fill="none" stroke="var(--color-peach)" strokeWidth="3" strokeLinecap="round" opacity="0.9" />
              <ellipse cx="145" cy="168" rx="92" ry="122" fill="none" stroke="var(--color-surface)" strokeWidth="2" strokeDasharray="5 8" opacity="0.75" />
            </svg>
          )}
          {stage === "starting" && (
            <div role="status" aria-live="polite" className="absolute inset-0 flex flex-col items-center justify-center gap-3 px-8 text-center text-sm text-peach">
              <span className="h-6 w-6 animate-spin rounded-full border-2 border-surface/25 border-t-peach" aria-hidden="true" />
              Waiting for your camera. If your browser asks, allow camera access.
            </div>
          )}
          {stage === "problem" && (
            <div role="alert" className="absolute inset-0 flex flex-col items-center justify-center gap-2 px-7 text-center">
              <p className="display text-[24px] leading-tight">{problemText.title}</p>
              <p className="text-sm leading-relaxed text-peach">{problemText.body}</p>
            </div>
          )}
        </div>

        {stage === "live" && (
          <p className="text-center text-xs leading-relaxed text-peach">Soft daylight · eyes level with the lens · glasses off, hair back</p>
        )}

        <div className="flex flex-col gap-2">
          {stage === "live" && (
            <button
              type="button"
              onClick={capture}
              className="mx-auto inline-flex min-h-14 items-center gap-3 rounded-full bg-surface py-2 pr-7 pl-2 font-semibold text-ink transition-transform active:scale-[0.97]"
            >
              <span className="inline-flex h-10 w-10 items-center justify-center rounded-full border-2 border-ink" aria-hidden="true">
                <span className="h-7 w-7 rounded-full bg-terra-deep" />
              </span>
              Take photo
            </button>
          )}
          {stage === "review" && shot && (
            <div className="grid grid-cols-2 gap-2">
              <Button variant="light" size="lg" onClick={restart} className="bg-transparent text-surface ring-1 ring-surface/40 hover:bg-surface hover:text-ink">
                Retake
              </Button>
              <Button size="lg" onClick={() => onAccept(shot.file)}>
                Use this photo
              </Button>
            </div>
          )}
          {stage === "problem" && (
            <div className="grid gap-2 sm:grid-cols-2">
              <Button size="lg" onClick={onChoosePhoto}>
                Choose a photo instead
              </Button>
              {problem !== "unavailable" && problem !== "too_small" && (
                <Button variant="light" size="lg" onClick={restart}>
                  Try again
                </Button>
              )}
            </div>
          )}
        </div>

        <p className="flex gap-2 text-xs leading-relaxed text-peach/90">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true" className="mt-0.5 shrink-0">
            <rect x="5" y="11" width="14" height="10" rx="2" />
            <path d="M8 11V8a4 4 0 0 1 8 0v3" />
          </svg>
          <span>The preview stays on this device. Nothing is recorded, and your photo is never sent anywhere unless you later agree to an analysis.</span>
        </p>
      </section>
    </div>,
    document.body,
  );
}
