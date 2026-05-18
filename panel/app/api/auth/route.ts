import { NextRequest, NextResponse } from "next/server";
import { checkPin, setAuth, clearAuth, isAuthed } from "@/lib/auth";

export const dynamic = "force-dynamic";

export async function POST(req: NextRequest) {
  const { pin } = await req.json();
  if (!pin || typeof pin !== "string") {
    return NextResponse.json({ ok: false, error: "Missing PIN" }, { status: 400 });
  }
  try {
    const ok = await checkPin(pin);
    if (!ok) return NextResponse.json({ ok: false, error: "Bad PIN" }, { status: 401 });
    await setAuth();
    return NextResponse.json({ ok: true });
  } catch (e: any) {
    return NextResponse.json({ ok: false, error: e.message }, { status: 500 });
  }
}

export async function DELETE() {
  await clearAuth();
  return NextResponse.json({ ok: true });
}

export async function GET() {
  return NextResponse.json({ authed: await isAuthed() });
}
