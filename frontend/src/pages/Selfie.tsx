import { useCallback, useEffect, useRef, useState, type ChangeEvent } from "react";
import { Page } from "../components/Layout";
import { Button, InfoNote, ErrorState, Loading, MicroLabel, SceneImage, SectionTitle } from "../components/ui";
import { CameraCapture, cameraSupported } from "../components/CameraCapture";
import { api, ApiError } from "../lib/api";
import { photoFileProblem } from "../lib/camera";
import { titleForMessage } from "../lib/errors";
import { PhotoPrepError, prepareSelfie } from "../lib/imagePrep";
import { useRemote } from "../lib/useRemote";
import { useApp } from "../state/AppState";


// Each demo profile is shown as a "skin story" with a texture image, never a face.
const STORY_IMAGE: Record<string, "gel_coral" | "drops" | "cream_swirl" | "hero_still"> = {
  "uneven-tone": "gel_coral",
  "shine-prone": "drops",
  "dry-sensitive": "cream_swirl",
  balanced: "hero_still",
};

const CameraIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
    <rect x="3" y="6" width="18" height="14" rx="3" />
    <circle cx="12" cy="13" r="3.5" />
    <path d="M8 6l1.5-2h5L16 6" />
  </svg>
);

/**
 * "Take a selfie" opens the in-app camera (permission is asked only on that tap); browsers without a camera API fall
 * back to the system camera via a file input. "Choose an existing photo" opens the file picker. Every photo, however
 * it was made, passes the same type and size checks and becomes a local preview only; it is uploaded only if the
 * customer later agrees to live analysis.
 */
function PhotoActions({ hasPhoto }: { hasPhoto: boolean }) {
  const { setPhoto } = useApp();
  const [error, setError] = useState<string | null>(null);
  const [cameraOpen, setCameraOpen] = useState(false);
  const library = useRef<HTMLInputElement>(null);
  const systemCamera = useRef<HTMLInputElement>(null);
  const selfieButton = useRef<HTMLButtonElement>(null);

  function acceptPhoto(file: File) {
    const problem = photoFileProblem(file);
    setError(problem);
    if (!problem) setPhoto(file); // local object URL only
  }
  function onFile(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (file) acceptPhoto(file);
  }
  function takeSelfie() {
    setError(null);
    if (cameraSupported()) setCameraOpen(true);
    else systemCamera.current?.click();
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="grid gap-2 sm:grid-cols-2">
        <Button ref={selfieButton} variant="dark" size="lg" onClick={takeSelfie} className="px-5">
          <CameraIcon />
          {hasPhoto ? "Retake selfie" : "Take a selfie"}
        </Button>
        <Button variant="outline" size="lg" onClick={() => library.current?.click()} className="px-5">
          {hasPhoto ? "Choose another photo" : "Choose an existing photo"}
        </Button>
      </div>
      <input ref={library} type="file" accept="image/jpeg,image/png" onChange={onFile} className="sr-only" tabIndex={-1} aria-hidden="true" />
      <input ref={systemCamera} type="file" accept="image/jpeg,image/png" capture="user" onChange={onFile} className="sr-only" tabIndex={-1} aria-hidden="true" />
      {error && (
        <p role="alert" className="text-sm text-terra-ink">
          {error}
        </p>
      )}
      {cameraOpen && (
        <CameraCapture
          returnFocus={selfieButton}
          onClose={() => setCameraOpen(false)}
          onAccept={(file) => {
            setCameraOpen(false);
            acceptPhoto(file);
          }}
          onChoosePhoto={() => {
            setCameraOpen(false);
            library.current?.click();
          }}
        />
      )}
    </div>
  );
}

// ------------------------------------------------------------------------------------------ live analysis
type Phase = "idle" | "preparing" | "sending" | "analysing" | "error";
interface LiveError {
  title?: string;
  message: string;
  retake: boolean;
  retryable: boolean;
}

const POLL_MS = 3000;
const GIVE_UP_MS = 4 * 60 * 1000;
const PHOTO_CODES = new Set(["image_too_small", "image_shape", "invalid_image", "image_too_large"]);
const PHASE_TEXT: Record<Phase, string> = {
  idle: "",
  preparing: "Preparing your photo on this device…",
  sending: "Sending your photo securely…",
  analysing: "Analysing nine skin attributes. This can take up to a minute.",
  error: "",
};
const RETAKE_TIPS = [
  "Face a window or a soft, even light",
  "Hold the camera at eye level so your face fills most of the frame",
  "Look straight ahead with your mouth closed and eyes open",
  "Remove glasses and keep hair off your forehead",
];
const GENERIC_ERROR: LiveError = {
  message: "Something went wrong analysing your photo. Please try again, or choose a sample profile.",
  retake: false,
  retryable: true,
};

class LiveFailure extends Error {
  readonly detail: LiveError;
  constructor(detail: LiveError) {
    super(detail.message);
    this.detail = detail;
  }
}

function toLiveError(e: unknown): LiveError {
  if (e instanceof LiveFailure) return e.detail;
  if (e instanceof PhotoPrepError) return { message: e.message, retake: true, retryable: false };
  if (e instanceof ApiError) {
    const connection = e.code === "network" || e.code === "unavailable";
    return {
      title: connection ? titleForMessage(e.message) : undefined,
      message: e.message,
      retake: PHOTO_CODES.has(e.code),
      retryable: e.retryable,
    };
  }
  return GENERIC_ERROR;
}

/** Shown only when the server reports live analysis as switched on. The photo is sent only after consent. */
function LiveAnalysisCard({ onUseDemo }: { onUseDemo: () => void }) {
  const { photoUrl, setPhoto, setAnalysis, go } = useApp();
  const [consent, setConsent] = useState(false);
  const [phase, setPhase] = useState<Phase>("idle");
  const [error, setError] = useState<LiveError | null>(null);
  const [seconds, setSeconds] = useState(0);
  const alive = useRef(true);
  const busy = phase === "preparing" || phase === "sending" || phase === "analysing";

  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
    };
  }, []);
  useEffect(() => {
    if (phase !== "analysing") return;
    const timer = setInterval(() => setSeconds((n) => n + 1), 1000);
    return () => clearInterval(timer);
  }, [phase]);

  async function analyse() {
    if (!photoUrl || !consent || busy) return;
    setError(null);
    setSeconds(0);
    setPhase("preparing");
    try {
      const jpeg = await prepareSelfie(photoUrl); // cleaned on this device before anything is sent
      setPhase("sending");
      let job = await api.startLiveAnalysis(jpeg);
      setPhase("analysing");
      const started = Date.now();
      while (job.status === "running") {
        if (Date.now() - started > GIVE_UP_MS) {
          throw new LiveFailure({ message: "The analysis is taking too long. Please try again in a moment.", retake: false, retryable: true });
        }
        await new Promise((resolve) => setTimeout(resolve, POLL_MS));
        if (!alive.current) return;
        job = await api.liveAnalysis(job.analysis_id);
      }
      if (!alive.current) return;
      if (job.status === "success" && job.analysis && !job.analysis.is_demo) {
        setAnalysis(job.analysis);
        go("results");
        return;
      }
      throw new LiveFailure(job.error ?? GENERIC_ERROR);
    } catch (e) {
      if (!alive.current) return;
      setError(toLiveError(e));
      setPhase("error");
    }
  }

  return (
    <section aria-labelledby="live-title" className="flex flex-col gap-4 rounded-[28px] bg-surface p-4 sm:p-6">
      <MicroLabel className="text-sage">Live analysis · YouCam</MicroLabel>
      <h2 id="live-title" className="display text-[2rem] sm:text-[2.6rem]">
        Analyse <span className="italic text-terra-deep">my photo</span>
      </h2>
      <p className="text-sm leading-relaxed text-ink-soft">
        GlowCue sends your photo to Perfect Corp&rsquo;s YouCam service for a <strong>cosmetic</strong> analysis of nine skin
        attributes. Results depend on the light and the photo, and are not medical advice.
      </p>
      <div className="flex flex-col gap-2">
        <label className="flex min-h-11 cursor-pointer items-start gap-3 rounded-2xl bg-bg p-3 text-sm leading-relaxed">
          <input
            type="checkbox"
            checked={consent}
            disabled={busy}
            onChange={(e) => setConsent(e.target.checked)}
            aria-describedby="consent-note"
            className="mt-0.5 h-5 w-5 shrink-0 accent-terra-deep"
          />
          <span>I agree to send this photo to Perfect Corp (YouCam) for automated skin analysis.</span>
        </label>
        <p id="consent-note" className="px-3 text-[13px] leading-relaxed text-ink-soft">
          Your photo is processed temporarily and is not stored by GlowCue after processing. We request that YouCam deletes its
          copy after analysis. We cannot independently verify deletion by YouCam.
        </p>
      </div>

      {busy && (
        <div role="status" aria-live="polite" className="flex items-center gap-3 rounded-2xl bg-bg p-3 text-sm text-ink-soft">
          <span className="h-5 w-5 shrink-0 animate-spin rounded-full border-2 border-line border-t-terra-deep" aria-hidden="true" />
          <span>
            {PHASE_TEXT[phase]}
            {phase === "analysing" && seconds > 0 && <span className="tabular-nums text-muted"> {seconds}s</span>}
          </span>
        </div>
      )}

      {error && (
        <div role="alert" className="flex flex-col gap-3 rounded-2xl bg-terra-soft p-4 text-sm text-terra-ink">
          {error.title && <p className="font-semibold">{error.title}</p>}
          <p className={error.title ? undefined : "font-semibold"}>{error.message}</p>
          {error.retake && (
            <ul className="flex list-disc flex-col gap-1 pl-5 leading-relaxed">
              {RETAKE_TIPS.map((tip) => (
                <li key={tip}>{tip}</li>
              ))}
            </ul>
          )}
          <div className="flex flex-wrap gap-2">
            {error.retake && (
              <Button
                variant="outline"
                onClick={() => {
                  setPhoto(null);
                  setError(null);
                  setPhase("idle");
                }}
              >
                Try another photo
              </Button>
            )}
            {error.retryable && !error.retake && (
              <Button variant="outline" onClick={analyse}>
                Try again
              </Button>
            )}
            <Button variant="ghost" className="underline" onClick={onUseDemo}>
              Use a sample profile instead
            </Button>
          </div>
        </div>
      )}

      <Button size="lg" onClick={analyse} disabled={!photoUrl || !consent || busy}>
        {busy ? "Analysing…" : photoUrl ? "Analyse my photo" : "Add a photo to analyse it"}
      </Button>
    </section>
  );
}

export function Selfie() {
  const { photoUrl, setPhoto, setAnalysis, analysis, go, config } = useApp();
  const liveOn = config?.live_enabled === true;
  const [profileId, setProfileId] = useState<string>(analysis?.profile_id ?? "uneven-tone");
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);
  const loadProfiles = useCallback(() => api.demoProfiles(), []);
  const profiles = useRemote(`profiles-${attempt}`, loadProfiles);

  async function continueToResults() {
    setSubmitting(true);
    setSubmitError(null);
    try {
      setAnalysis(await api.demoAnalysis(profileId)); // sends the profile id only, never the photo
      go("results");
    } catch (e) {
      setSubmitError((e as Error).message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Page wide>
      <SectionTitle eyebrow="Selfie · optional" title={<>Add a <span className="italic text-terra-deep">clear</span> selfie.</>}>
        Face the light, fill the frame, hair off your forehead.{" "}
        {liveOn ? "Your photo stays on this device unless you choose live analysis." : "Your photo stays on this device."}
      </SectionTitle>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
        {/* photo */}
        <section aria-label="Your photo" className="flex flex-col gap-4 rounded-[28px] bg-surface p-4 sm:p-6">
          <div className="relative flex aspect-[4/5] max-h-[460px] items-center justify-center overflow-hidden rounded-[22px] bg-bg">
            {photoUrl ? (
              <>
                <img src={photoUrl} alt="Your selfie preview" className="h-full w-full object-cover animate-fade" />
                <span className="absolute top-3 left-3 inline-flex items-center gap-1.5 rounded-full bg-surface/92 px-3 py-2 text-xs font-semibold">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="var(--color-sage)" strokeWidth="2.6" aria-hidden="true">
                    <path d="M5 12l4 4 10-10" />
                  </svg>
                  {liveOn ? "On this device until you analyse it" : "On this device only"}
                </span>
              </>
            ) : (
              <>
                <svg viewBox="0 0 290 330" className="absolute inset-6 h-[calc(100%-3rem)] w-[calc(100%-3rem)]" aria-hidden="true" preserveAspectRatio="xMidYMid meet">
                  <path d="M14 54V14h40M236 14h40v40M276 276v40h-40M54 316H14v-40" fill="none" stroke="var(--color-terra-deep)" strokeWidth="3" strokeLinecap="round" />
                  <ellipse cx="145" cy="160" rx="82" ry="108" fill="none" stroke="var(--color-line-strong)" strokeWidth="2" strokeDasharray="4 7" />
                </svg>
                <span className="relative max-w-[180px] text-center text-[13px] leading-relaxed text-muted">
                  Face the light and fill the oval.
                </span>
              </>
            )}
          </div>
          {!photoUrl && (
            <ul className="grid grid-cols-3 gap-2 text-center text-[11px] text-ink-soft">
              <li className="rounded-xl bg-bg px-2 py-2.5">Soft daylight</li>
              <li className="rounded-xl bg-bg px-2 py-2.5">No glasses</li>
              <li className="rounded-xl bg-bg px-2 py-2.5">Bare skin</li>
            </ul>
          )}
          <PhotoActions hasPhoto={photoUrl !== null} />
          {photoUrl && (
            <Button variant="ghost" onClick={() => setPhoto(null)} className="self-start underline">
              Remove photo
            </Button>
          )}
          <p className="flex gap-2 text-xs leading-relaxed text-ink-soft">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--color-sage)" strokeWidth="2" aria-hidden="true" className="mt-0.5 shrink-0">
              <rect x="5" y="11" width="14" height="10" rx="2" />
              <path d="M8 11V8a4 4 0 0 1 8 0v3" />
            </svg>
            {liveOn ? (
              <span>
                Your photo is uploaded <strong>only if you agree</strong> and choose live analysis. Otherwise it never leaves this
                device, and it&rsquo;s cleared when you start over or close the tab.
              </span>
            ) : (
              <span>
                Live analysis is switched off right now, so your photo is <strong>never uploaded or analysed</strong>. It&rsquo;s
                cleared when you start over or close the tab.
              </span>
            )}
          </p>
        </section>

        {/* live analysis (only when switched on), then the demo profiles */}
        <div className="flex min-w-0 flex-col gap-6">
        {liveOn && <LiveAnalysisCard onUseDemo={() => document.getElementById("stories")?.scrollIntoView({ block: "start" })} />}
        <section aria-labelledby="stories" className="flex scroll-mt-24 flex-col gap-4">
          <InfoNote>
            {liveOn ? (
              <>
                <strong className="text-ink">Prefer not to upload?</strong> Choose the sample profile closest to your skin. Its
                report is marked as a sample, not an analysis of you.
              </>
            ) : (
              <>
                <strong className="text-ink">Sample profiles.</strong> Choose the one closest to your skin. Its report is marked as
                a sample, not an analysis of you.
              </>
            )}
          </InfoNote>
          <h2 id="stories" className="display text-[2rem] sm:text-[2.6rem]">
            {liveOn ? (
              <>
                Or start from a <span className="italic text-terra-deep">sample</span> profile
              </>
            ) : (
              <>
                Start from a <span className="italic text-terra-deep">sample</span> profile
              </>
            )}
          </h2>
          {profiles.loading && !profiles.data && <Loading label="Loading profiles…" />}
          {profiles.error && <ErrorState message={profiles.error} onRetry={() => setAttempt((n) => n + 1)} />}
          {profiles.data && (
            <div role="radiogroup" aria-label="Sample profile" className="grid grid-cols-2 gap-3">
              {profiles.data.map((profile) => {
                const on = profileId === profile.id;
                return (
                  <label
                    key={profile.id}
                    className={`group cursor-pointer overflow-hidden rounded-[22px] bg-surface transition-[border-color,transform] duration-200 has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-offset-2 has-[:focus-visible]:outline-terra-deep ${
                      on ? "border-2 border-ink" : "border border-line-strong hover:border-ink"
                    }`}
                  >
                    <input type="radio" name="skin-story" value={profile.id} checked={on} onChange={() => setProfileId(profile.id)} className="sr-only" />
                    <div className="h-28 overflow-hidden sm:h-36">
                      <SceneImage name={STORY_IMAGE[profile.id] ?? "drops"} alt="" className="transition-transform duration-500 group-hover:scale-105" />
                    </div>
                    <div className="flex flex-col gap-1 p-3 sm:p-4">
                      <span className="flex items-center justify-between gap-2">
                        <strong className="text-sm">{profile.name}</strong>
                        {on && <MicroLabel className="text-terra-deep">Chosen</MicroLabel>}
                      </span>
                      <span className="text-xs leading-relaxed text-muted">{profile.summary}</span>
                    </div>
                  </label>
                );
              })}
            </div>
          )}
          {submitError && <ErrorState message={submitError} />}
          <div className="sticky bottom-0 -mx-4 mt-2 flex gap-3 border-t border-line bg-bg/95 px-4 py-4 backdrop-blur lg:static lg:mx-0 lg:border-0 lg:bg-transparent lg:px-0">
            <button
              type="button"
              onClick={() => go("about", 4)}
              aria-label="Back to the consultation"
              className="inline-flex h-14 w-14 shrink-0 items-center justify-center rounded-full border border-ink hover:bg-ink hover:text-surface"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                <path d="M15 6l-6 6 6 6" />
              </svg>
            </button>
            <Button size="lg" onClick={continueToResults} disabled={submitting || !profiles.data} className="flex-1">
              {submitting
                ? "Preparing your report…"
                : liveOn
                  ? "See a sample report"
                  : photoUrl
                    ? "See my sample report"
                    : "Continue without a photo"}
            </Button>
          </div>
        </section>
        </div>
      </div>
    </Page>
  );
}
