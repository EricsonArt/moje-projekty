import { NextRequest, NextResponse } from "next/server";
import { isAuthed } from "@/lib/auth";
import { addRating, getRatings } from "@/lib/github";

export const dynamic = "force-dynamic";

export async function GET() {
  if (!(await isAuthed())) {
    return NextResponse.json({ ok: false, error: "unauthorized" }, { status: 401 });
  }
  try {
    const { ratings } = await getRatings();
    return NextResponse.json({ ok: true, ratings });
  } catch (e: any) {
    return NextResponse.json({ ok: false, error: e.message }, { status: 500 });
  }
}

export async function POST(req: NextRequest) {
  // POST nie wymaga auth - bo wolany z Telegram bot callback (publiczny)
  // Wymaga jednak `token` matching env var
  const token = req.nextUrl.searchParams.get("token");
  if (token !== process.env.RATING_TOKEN) {
    return NextResponse.json({ ok: false, error: "bad token" }, { status: 403 });
  }
  try {
    const { script_id, rating } = await req.json();
    if (!script_id || (rating !== 1 && rating !== -1)) {
      return NextResponse.json({ ok: false, error: "bad input" }, { status: 400 });
    }
    await addRating(script_id, rating);
    return NextResponse.json({ ok: true });
  } catch (e: any) {
    return NextResponse.json({ ok: false, error: e.message }, { status: 500 });
  }
}
