import { NextRequest, NextResponse } from "next/server";
import { isAuthed } from "@/lib/auth";
import { getPreferences, savePreferences, DEFAULT_PREFS, Preferences } from "@/lib/github";

export const dynamic = "force-dynamic";

async function guard() {
  if (!(await isAuthed())) {
    return NextResponse.json({ ok: false, error: "unauthorized" }, { status: 401 });
  }
  return null;
}

export async function GET() {
  const g = await guard();
  if (g) return g;
  try {
    const { prefs } = await getPreferences();
    return NextResponse.json({ ok: true, preferences: prefs });
  } catch (e: any) {
    return NextResponse.json({ ok: false, error: e.message }, { status: 500 });
  }
}

export async function POST(req: NextRequest) {
  const g = await guard();
  if (g) return g;
  try {
    const body = (await req.json()) as Partial<Preferences>;
    const merged: Preferences = { ...DEFAULT_PREFS, ...body };

    // walidacja zakresów
    merged.scripts_per_run = Math.max(1, Math.min(10, merged.scripts_per_run));
    merged.cta_intensity = Math.max(0, Math.min(100, merged.cta_intensity));
    merged.copy_similarity = Math.max(0, Math.min(100, merged.copy_similarity));
    merged.effort_level = Math.max(1, Math.min(10, merged.effort_level));
    merged.target_seconds = Math.max(15, Math.min(90, merged.target_seconds));

    await savePreferences(merged);
    return NextResponse.json({ ok: true, preferences: merged });
  } catch (e: any) {
    return NextResponse.json({ ok: false, error: e.message }, { status: 500 });
  }
}
