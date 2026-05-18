import { NextRequest, NextResponse } from "next/server";
import { addRating } from "@/lib/github";

export const dynamic = "force-dynamic";

function html(title: string, body: string, color = "#10b981") {
  return `<!DOCTYPE html><html lang="pl"><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>${title}</title>
<style>
body{font-family:-apple-system,BlinkMacSystemFont,system-ui,sans-serif;background:#0a0a0a;color:#f5f5f5;margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:2rem;}
.card{background:#141414;border:1px solid #262626;border-radius:1rem;padding:2rem;max-width:24rem;text-align:center;}
.icon{font-size:4rem;line-height:1;margin-bottom:1rem;}
h1{margin:0 0 0.5rem;font-size:1.5rem;color:${color};}
p{margin:0;color:#a3a3a3;font-size:0.95rem;line-height:1.5;}
a{display:inline-block;margin-top:1.5rem;color:#10b981;text-decoration:none;font-weight:600;}
a:hover{text-decoration:underline;}
</style>
</head><body><div class="card">${body}</div></body></html>`;
}

export async function GET(req: NextRequest) {
  const id = req.nextUrl.searchParams.get("id");
  const ratingStr = req.nextUrl.searchParams.get("rating");
  const token = req.nextUrl.searchParams.get("token");

  if (!id || (ratingStr !== "1" && ratingStr !== "-1")) {
    return new NextResponse(
      html("Błąd", `<div class="icon">⚠️</div><h1>Złe parametry</h1><p>Linka nie da się przetworzyć.</p>`, "#f59e0b"),
      { headers: { "Content-Type": "text/html; charset=utf-8" }, status: 400 },
    );
  }
  if (token !== process.env.RATING_TOKEN) {
    return new NextResponse(
      html("Błąd", `<div class="icon">🔒</div><h1>Brak uprawnień</h1><p>Token niepoprawny.</p>`, "#ef4444"),
      { headers: { "Content-Type": "text/html; charset=utf-8" }, status: 403 },
    );
  }

  const rating = ratingStr === "1" ? 1 : -1;
  try {
    await addRating(id, rating as 1 | -1);
  } catch (e: any) {
    return new NextResponse(
      html("Błąd zapisu", `<div class="icon">💥</div><h1>Nie udało się zapisać</h1><p>${e.message}</p>`, "#ef4444"),
      { headers: { "Content-Type": "text/html; charset=utf-8" }, status: 500 },
    );
  }

  const icon = rating > 0 ? "👍" : "👎";
  const title = rating > 0 ? "Dzięki! Świetny" : "Zanotowane. Słaby";
  const subtitle = rating > 0
    ? "System nauczy się, że takie skrypty Ci pasują."
    : "Następne generacje będą inne. Pamięta, czego unikać.";

  return new NextResponse(
    html(
      "Zapisano",
      `<div class="icon">${icon}</div><h1>${title}</h1><p>${subtitle}</p>
      <a href="${process.env.NEXT_PUBLIC_PANEL_URL || ""}">Otwórz panel →</a>`,
    ),
    { headers: { "Content-Type": "text/html; charset=utf-8" } },
  );
}
