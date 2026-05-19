import { NextRequest, NextResponse } from "next/server";
import { isAuthed } from "@/lib/auth";
import { listScripts, getScriptContent } from "@/lib/github";

export const dynamic = "force-dynamic";

export async function GET(req: NextRequest) {
  if (!(await isAuthed())) {
    return NextResponse.json({ ok: false, error: "unauthorized" }, { status: 401 });
  }
  try {
    const date = req.nextUrl.searchParams.get("date");
    const file = req.nextUrl.searchParams.get("file");
    if (date && file) {
      const content = await getScriptContent(date, file);
      return NextResponse.json({ ok: true, content });
    }
    const days = await listScripts(7);
    return NextResponse.json({ ok: true, days });
  } catch (e: any) {
    if (e.message?.includes("GITHUB_TOKEN")) {
      return NextResponse.json({ ok: true, days: [], noToken: true });
    }
    return NextResponse.json({ ok: false, error: e.message }, { status: 500 });
  }
}
