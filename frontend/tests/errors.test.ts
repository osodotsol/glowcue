import assert from "node:assert/strict";
import { test } from "node:test";
import {
  CONNECTION_ERROR,
  friendlyForHttpFailure,
  GENERIC_ERROR,
  isServiceUnavailableStatus,
  SERVICE_ERROR,
  titleForMessage,
} from "../src/lib/errors.ts";

const ALL = [CONNECTION_ERROR, SERVICE_ERROR, GENERIC_ERROR];

test("connection wording is exactly the approved copy", () => {
  assert.equal(CONNECTION_ERROR.title, "We're having trouble connecting.");
  assert.equal(CONNECTION_ERROR.message, "Check your internet connection or move somewhere with a stronger network, then try again.");
});

test("no customer-facing error text uses developer words", () => {
  for (const { title, message } of ALL) {
    assert.doesNotMatch(`${title} ${message}`, /backend|server|\bapi\b|localhost|running|http|status|\b[45]\d\d\b/i);
  }
});

test("gateway failures are reported as the service being unavailable, not as an internet problem", () => {
  for (const status of [502, 503, 504]) {
    assert.equal(isServiceUnavailableStatus(status), true);
    assert.equal(friendlyForHttpFailure(status), SERVICE_ERROR);
  }
  assert.notEqual(SERVICE_ERROR.message, CONNECTION_ERROR.message);
  assert.doesNotMatch(SERVICE_ERROR.message, /internet|network/i);
});

test("other failures without a message get the generic wording, never the connection wording", () => {
  for (const status of [400, 404, 409, 422, 429, 500]) {
    assert.equal(isServiceUnavailableStatus(status), false);
    assert.equal(friendlyForHttpFailure(status), GENERIC_ERROR);
  }
});

test("titles follow the message; unknown messages keep the default title", () => {
  assert.equal(titleForMessage(CONNECTION_ERROR.message), CONNECTION_ERROR.title);
  assert.equal(titleForMessage(SERVICE_ERROR.message), SERVICE_ERROR.title);
  assert.equal(titleForMessage(GENERIC_ERROR.message), GENERIC_ERROR.title);
  assert.equal(titleForMessage("That photo is over 10 MB. Please choose a smaller one."), GENERIC_ERROR.title);
});
