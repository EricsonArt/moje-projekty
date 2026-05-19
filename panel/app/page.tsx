"use client";

import { useEffect, useState } from "react";

type Preferences = {
  scripts_per_run: number;
  cta_intensity: number;
  copy_similarity: number;
  effort_level: number;
  target_seconds: number;
  tone: string;
};

const TONES = [
  { v: "balanced", label: "Balanced (AI sam wybiera)" },
  { v: "anti_guru", label: "Anti-guru (kontrarian, bezposredni)" },
  { v: "hormozi", label: "Hormozi PL (agitate->solve->CTA)" },
  { v: "storyteller", label: "Storyteller (osobiste historie)" },
  { v: "kontrarian", label: "Kontrarian (hot takes)" },
];

function describeCta(v: number) {
  if (v < 20) return "Pure value, zero sprzedazy";
  if (v < 50) return "Wartosc + soft CTA";
  if (v < 80) return "Mocna promocja Skali";
  return "Hard sell - kazde zdanie sprzedaje";
}
function describeCopy(v: number) {
  if (v < 30) return "Pure original (viral to tylko temat)";
  if (v < 60) return "Subtelna inspiracja wzorca";
  if (v < 85) return "Mocna inspiracja (podobna struktura)";
  return "Klon (1:1, tylko zmieniamy slowa)";
}
function describeEffort(v: number) {
  if (v <= 4) return "Fast - 1 iter, szybko";
  if (v <= 7) return "Standard - 3 iter, balans";
  return "Thorough - 5 iter + multi-attempt, max jakosc";
}

export default function Home() {
  const [authed, setAuthed] = useState<boolean | null>(null);
  const [pin, setPin] = useState("");
  const [pinError, setPinError] = useState("");
  const [prefs, setPrefs] = useState<Preferences | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState<"idle" | "saved" | "err">("idle");
  const [triggering, setTriggering] = useState(false);
  const [latestRun, setLatestRun] = useState<any>(null);
  const [scripts, setScripts] = useState<{ date: string; files: string[] }[]>([]);
  const [openScript, setOpenScript] = useState<{ date: string; file: string; content: string } | null>(null);
  const [noToken, setNoToken] = useState(false);

  useEffect(() => {
    fetch("/api/auth").then((r) => r.json()).then((d) => setAuthed(d.authed));
  }, []);

  useEffect(() => {
    if (!authed) return;
    fetch("/api/preferences").then((r) => r.json()).then((d) => {
      if (d.ok) setPrefs(d.preferences);
      if (d.noToken) setNoToken(true);
    });
    fetch("/api/trigger").then((r) => r.json()).then((d) => {
      if (d.ok) setLatestRun(d.run);
      if (d.noToken) setNoToken(true);
    });
    fetch("/api/scripts").then((r) => r.json()).then((d) => {
      if (d.ok) setScripts(d.days);
      if (d.noToken) setNoToken(true);
    });
  }, [authed]);

  async function login(e: React.FormEvent) {
    e.preventDefault();
    setPinError("");
    const r = await fetch("/api/auth", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pin }),
    });
    const d = await r.json();
    if (d.ok) setAuthed(true);
    else setPinError(d.error || "Zly PIN");
  }

  async function save() {
    if (!prefs) return;
    setSaving(true);
    setSaved("idle");
    const r = await fetch("/api/preferences", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(prefs),
    });
    const d = await r.json();
    setSaving(false);
    setSaved(d.ok ? "saved" : "err");
    setTimeout(() => setSaved("idle"), 3000);
  }

  async function generateNow() {
    setTriggering(true);
    await fetch("/api/trigger", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    });
    setTimeout(() => {
      fetch("/api/trigger").then((r) => r.json()).then((d) => {
        if (d.ok) setLatestRun(d.run);
        setTriggering(false);
      });
    }, 2000);
  }

  async function openScriptFile(date: string, file: string) {
    const r = await fetch(`/api/scripts?date=${date}&file=${encodeURIComponent(file)}`);
    const d = await r.json();
    if (d.ok) setOpenScript({ date, file, content: d.content });
  }

  if (authed === null) {
    return <div className="p-8 text-neutral-500">Ladowanie...</div>;
  }

  if (!authed) {
    return (
      <div className="min-h-screen flex items-center justify-center p-6">
        <form onSubmit={login} className="w-full max-w-sm bg-card border border-border rounded-2xl p-8 space-y-4">
          <h1 className="text-2xl font-bold">Skala Viral Panel</h1>
          <p className="text-sm text-neutral-400">Podaj PIN żeby zalogować się.</p>
          <input
            type="password"
            inputMode="numeric"
            pattern="[0-9]*"
            autoFocus
            value={pin}
            onChange={(e) => setPin(e.target.value)}
            placeholder="PIN (4 cyfry)"
            className="w-full bg-bg border border-border rounded-lg px-4 py-3 text-lg outline-none focus:border-accent"
          />
          {pinError && <p className="text-red-400 text-sm">{pinError}</p>}
          <button
            type="submit"
            className="w-full bg-accent text-black font-bold py-3 rounded-lg hover:opacity-90"
          >
            Wejdź
          </button>
        </form>
      </div>
    );
  }

  return (
    <main className="max-w-3xl mx-auto p-4 sm:p-8 space-y-6">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl sm:text-3xl font-bold">Skala Viral Panel</h1>
        <button
          onClick={() => fetch("/api/auth", { method: "DELETE" }).then(() => setAuthed(false))}
          className="text-sm text-neutral-500 hover:text-neutral-300"
        >
          Wyloguj
        </button>
      </header>

      {noToken && (
        <section className="bg-amber-950/40 border border-amber-700 rounded-2xl p-4 sm:p-5 text-sm space-y-2">
          <div className="font-bold text-amber-300">⚠️ Tryb podgladu — zmiany sie nie zapisuja</div>
          <p className="text-amber-100/90">
            Zeby panel zapisywal preferencje i triggerowal generowanie, dodaj <code className="bg-black/40 px-1.5 py-0.5 rounded">GITHUB_TOKEN</code> w Vercel env vars.
          </p>
          <ol className="text-amber-100/80 list-decimal pl-5 space-y-1">
            <li>
              <a className="text-amber-300 underline" href="https://github.com/settings/tokens/new?scopes=repo,workflow&description=Skala+Panel" target="_blank" rel="noreferrer">Wygeneruj token w GitHub ↗</a> → kopiuj <code>ghp_...</code>
            </li>
            <li>
              <a className="text-amber-300 underline" href="https://vercel.com/hajduczekeryk-1015s-projects/moje-projekty/settings/environment-variables" target="_blank" rel="noreferrer">Vercel env vars ↗</a> → "Add New" → Key: <code>GITHUB_TOKEN</code>, Value: wklej token
            </li>
            <li>
              <a className="text-amber-300 underline" href="https://vercel.com/hajduczekeryk-1015s-projects/moje-projekty/deployments" target="_blank" rel="noreferrer">Deployments ↗</a> → 3 kropki → "Redeploy"
            </li>
          </ol>
        </section>
      )}

      {/* === Status workflow === */}
      <section className="bg-card border border-border rounded-2xl p-5 sm:p-6 space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="font-bold">Ostatni run</h2>
          {latestRun && (
            <a
              href={latestRun.html_url}
              target="_blank"
              rel="noreferrer"
              className="text-xs text-neutral-500 hover:text-accent"
            >
              Logs ↗
            </a>
          )}
        </div>
        {latestRun ? (
          <div className="text-sm space-y-1">
            <div>
              Status: <span className={
                latestRun.conclusion === "success" ? "text-accent" :
                latestRun.conclusion === "failure" ? "text-red-400" :
                "text-amber-400"
              }>{latestRun.conclusion || latestRun.status}</span>
            </div>
            <div className="text-neutral-500">
              {new Date(latestRun.created_at).toLocaleString("pl-PL")}
            </div>
          </div>
        ) : (
          <p className="text-sm text-neutral-500">Brak runów.</p>
        )}
        <button
          onClick={generateNow}
          disabled={triggering}
          className="w-full bg-accent2 text-black font-bold py-3 rounded-lg hover:opacity-90 disabled:opacity-50"
        >
          {triggering ? "Wystartowano - czekaj 3-5 min..." : "🚀 Wygeneruj teraz"}
        </button>
      </section>

      {/* === Suwaki === */}
      {prefs && (
        <section className="bg-card border border-border rounded-2xl p-5 sm:p-6 space-y-6">
          <h2 className="font-bold">Sterowanie generatorem</h2>

          <Slider
            label="Ilość skryptów"
            value={prefs.scripts_per_run}
            min={1}
            max={10}
            unit=""
            describe={(v) => `${v} skryptów per run`}
            onChange={(v) => setPrefs({ ...prefs, scripts_per_run: v })}
          />

          <Slider
            label="Intensywność CTA"
            value={prefs.cta_intensity}
            min={0}
            max={100}
            unit="%"
            describe={describeCta}
            onChange={(v) => setPrefs({ ...prefs, cta_intensity: v })}
          />

          <Slider
            label="Podobieństwo do inspiracji"
            value={prefs.copy_similarity}
            min={0}
            max={100}
            unit="%"
            describe={describeCopy}
            onChange={(v) => setPrefs({ ...prefs, copy_similarity: v })}
          />

          <Slider
            label="Effort level (jakość vs szybkość)"
            value={prefs.effort_level}
            min={1}
            max={10}
            unit=""
            describe={describeEffort}
            onChange={(v) => setPrefs({ ...prefs, effort_level: v })}
          />

          <Slider
            label="Długość filmu"
            value={prefs.target_seconds}
            min={15}
            max={90}
            unit="s"
            describe={(v) => `${v} sekund mówione`}
            onChange={(v) => setPrefs({ ...prefs, target_seconds: v })}
          />

          <div>
            <label className="block text-sm font-medium mb-2">Ton skryptu</label>
            <select
              value={prefs.tone}
              onChange={(e) => setPrefs({ ...prefs, tone: e.target.value })}
              className="w-full bg-bg border border-border rounded-lg px-4 py-3 outline-none focus:border-accent"
            >
              {TONES.map((t) => (
                <option key={t.v} value={t.v}>{t.label}</option>
              ))}
            </select>
          </div>

          <button
            onClick={save}
            disabled={saving}
            className="w-full bg-accent text-black font-bold py-3 rounded-lg hover:opacity-90 disabled:opacity-50"
          >
            {saving ? "Zapisuje..." : "💾 Zapisz preferencje"}
          </button>
          {saved === "saved" && <p className="text-accent text-sm text-center">✓ Zapisane. Następny run użyje nowych ustawień.</p>}
          {saved === "err" && <p className="text-red-400 text-sm text-center">✗ Błąd zapisu - sprawdź GITHUB_TOKEN.</p>}
        </section>
      )}

      {/* === Skrypty z ostatnich dni === */}
      <section className="bg-card border border-border rounded-2xl p-5 sm:p-6 space-y-3">
        <h2 className="font-bold">Ostatnie skrypty</h2>
        {scripts.length === 0 ? (
          <p className="text-sm text-neutral-500">Brak skryptów. Kliknij "Wygeneruj teraz".</p>
        ) : (
          scripts.map((day) => (
            <div key={day.date} className="border-t border-border pt-3 first:border-t-0 first:pt-0">
              <div className="font-mono text-xs text-neutral-500 mb-1">{day.date}</div>
              <div className="space-y-1">
                {day.files.map((f) => (
                  <button
                    key={f}
                    onClick={() => openScriptFile(day.date, f)}
                    className="block text-sm text-left hover:text-accent w-full"
                  >
                    📝 {f}
                  </button>
                ))}
              </div>
            </div>
          ))
        )}
      </section>

      {/* === Modal podglądu skryptu === */}
      {openScript && (
        <div
          className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4"
          onClick={() => setOpenScript(null)}
        >
          <div
            className="bg-card border border-border rounded-2xl max-w-2xl w-full max-h-[80vh] overflow-auto p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex justify-between items-start mb-4">
              <div className="font-mono text-sm text-neutral-500">
                {openScript.date}/{openScript.file}
              </div>
              <button
                onClick={() => setOpenScript(null)}
                className="text-neutral-400 hover:text-white"
              >
                ✕
              </button>
            </div>
            <pre className="whitespace-pre-wrap text-sm leading-relaxed">{openScript.content}</pre>
          </div>
        </div>
      )}

      <footer className="text-center text-xs text-neutral-600 pb-8">
        Skala Viral Engine · sterowanie systemem viralowych shortów
      </footer>
    </main>
  );
}

function Slider({
  label, value, min, max, unit, describe, onChange,
}: {
  label: string; value: number; min: number; max: number; unit: string;
  describe: (v: number) => string; onChange: (v: number) => void;
}) {
  return (
    <div>
      <div className="flex justify-between items-baseline mb-2">
        <label className="text-sm font-medium">{label}</label>
        <span className="font-mono text-accent text-lg font-bold">{value}{unit}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        value={value}
        onChange={(e) => onChange(parseInt(e.target.value, 10))}
      />
      <p className="text-xs text-neutral-500 mt-2">{describe(value)}</p>
    </div>
  );
}
