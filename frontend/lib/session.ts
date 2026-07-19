import { cookies } from "next/headers";
import { SESSION_COOKIE_NAME } from "@/lib/backend";

/** Reads the httpOnly session cookie (the raw JWT) server-side only. */
export async function getSessionToken(): Promise<string | null> {
  const cookieStore = await cookies();
  return cookieStore.get(SESSION_COOKIE_NAME)?.value ?? null;
}
