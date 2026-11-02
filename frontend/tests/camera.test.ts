import assert from "node:assert/strict";
import { test } from "node:test";
import { cameraProblem, MAX_PHOTO_BYTES, MIN_SHORT_SIDE, photoFileProblem, selfieCrop } from "../src/lib/camera.ts";

test("photoFileProblem accepts JPEG and PNG up to 10 MB", () => {
  assert.equal(photoFileProblem({ type: "image/jpeg", size: 1000 }), null);
  assert.equal(photoFileProblem({ type: "image/png", size: MAX_PHOTO_BYTES }), null);
});

test("photoFileProblem rejects other types and oversized files", () => {
  assert.match(photoFileProblem({ type: "image/heic", size: 1000 }) ?? "", /JPEG or PNG/);
  assert.match(photoFileProblem({ type: "image/gif", size: 1000 }) ?? "", /JPEG or PNG/);
  assert.match(photoFileProblem({ type: "image/jpeg", size: MAX_PHOTO_BYTES + 1 }) ?? "", /10 MB/);
});

test("cameraProblem maps getUserMedia errors to customer messages", () => {
  assert.equal(cameraProblem({ name: "NotAllowedError" }), "denied");
  assert.equal(cameraProblem({ name: "SecurityError" }), "denied");
  assert.equal(cameraProblem({ name: "NotFoundError" }), "unavailable");
  assert.equal(cameraProblem({ name: "OverconstrainedError" }), "unavailable");
  assert.equal(cameraProblem({ name: "NotReadableError" }), "busy");
  assert.equal(cameraProblem(new Error("boom")), "failed");
  assert.equal(cameraProblem(undefined), "failed");
});

test("selfieCrop keeps a centred 4:5 portrait from a landscape webcam frame", () => {
  assert.deepEqual(selfieCrop(1280, 720), { sx: 352, sy: 0, width: 576, height: 720 });
  assert.deepEqual(selfieCrop(1920, 1080), { sx: 528, sy: 0, width: 864, height: 1080 });
});

test("selfieCrop keeps a 4:5 portrait from a portrait phone frame", () => {
  assert.deepEqual(selfieCrop(720, 1280), { sx: 0, sy: 190, width: 720, height: 900 });
});

test("selfieCrop never goes below the analysis minimum", () => {
  const crop = selfieCrop(640, 480);
  assert.ok(crop);
  assert.ok(Math.min(crop.width, crop.height) >= MIN_SHORT_SIDE);
  assert.equal(selfieCrop(640, 360), null); // a frame too small to analyse at all
});
