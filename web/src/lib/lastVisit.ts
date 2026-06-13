// "New since your last visit" with no accounts (BUILD_SPEC §6.3).
// We read the stored timestamp on load, compute the diff, and only AFTER the
// user has seen the result do we write `now()` back (App handles the write).

const KEY = "pnw.lastVisit";

export function readLastVisit(): Date | null {
  const raw = localStorage.getItem(KEY);
  if (!raw) return null;
  const t = Date.parse(raw);
  return Number.isNaN(t) ? null : new Date(t);
}

export function writeLastVisit(when: Date = new Date()): void {
  localStorage.setItem(KEY, when.toISOString());
}

export function isNewSince(firstSeen: string, since: Date | null): boolean {
  if (!since) return false; // first-ever visit: nothing is "new" yet
  return Date.parse(firstSeen) > since.getTime();
}
