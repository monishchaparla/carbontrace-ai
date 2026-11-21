import "server-only";
import { createHash, timingSafeEqual } from "node:crypto";

// Public deployments set UPLOAD_PASSCODE so visitors can browse but not change data or spend the extraction quota.
export function passcodeOk(given: string | null | undefined): boolean {
  const expected = process.env.UPLOAD_PASSCODE;
  if (!expected) return true;
  const hash = (s: string) => createHash("sha256").update(s).digest();
  return timingSafeEqual(hash(given ?? ""), hash(expected));
}
