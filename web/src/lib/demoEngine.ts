/* Shared timeline primitives for the Demo section's scripted acts
 * (views/demo/*). A pause has to actually stall progress rather than just
 * hide the UI, so both helpers poll a `isPaused()` getter in small chunks
 * instead of firing one long setTimeout - the eventual resume picks up
 * exactly where it left off, not from the top of whatever step it was on. */

export interface RunCtl {
  isStale: () => boolean;
  isPaused: () => boolean;
}

const POLL_MS = 80;

/* Session-wide playback speed, read live by every rawSleep call. A module-
 * level multiplier (not per-act state) so one control in the Demo toolbar
 * speeds up whichever act happens to be running, without threading a prop
 * through three components and every sleep()/typeInto() call site. */
let speedMultiplier = 1;

export function setSpeed(multiplier: number) {
  speedMultiplier = multiplier;
}

export function getSpeed() {
  return speedMultiplier;
}

function rawSleep(ms: number) {
  return new Promise<void>((resolve) => setTimeout(resolve, ms / speedMultiplier));
}

export async function sleep(ms: number, ctl: RunCtl): Promise<void> {
  let remaining = ms;
  while (remaining > 0) {
    if (ctl.isStale()) return;
    if (ctl.isPaused()) {
      await rawSleep(POLL_MS);
      continue;
    }
    const chunk = Math.min(POLL_MS, remaining);
    await rawSleep(chunk);
    remaining -= chunk;
  }
}

export async function typeInto(
  setter: (v: string) => void,
  text: string,
  ctl: RunCtl,
  charMs = 14,
): Promise<void> {
  for (let i = 1; i <= text.length; i++) {
    if (ctl.isStale()) return;
    while (ctl.isPaused()) {
      if (ctl.isStale()) return;
      await rawSleep(POLL_MS);
    }
    setter(text.slice(0, i));
    await rawSleep(charMs);
  }
}
