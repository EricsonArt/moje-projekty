import { cookies } from "next/headers";

const COOKIE = "skala_auth";
const TTL_DAYS = 30;

export async function checkPin(pin: string): Promise<boolean> {
  const required = process.env.PANEL_PIN;
  if (!required) throw new Error("PANEL_PIN not set in env");
  return pin === required;
}

export async function setAuth() {
  const c = await cookies();
  c.set(COOKIE, "1", {
    httpOnly: true,
    secure: true,
    sameSite: "lax",
    maxAge: TTL_DAYS * 24 * 60 * 60,
    path: "/",
  });
}

export async function isAuthed(): Promise<boolean> {
  const c = await cookies();
  return c.get(COOKIE)?.value === "1";
}

export async function clearAuth() {
  const c = await cookies();
  c.delete(COOKIE);
}
