import { Octokit } from "@octokit/rest";
import yaml from "js-yaml";

const OWNER = process.env.GITHUB_OWNER || "EricsonArt";
const REPO = process.env.GITHUB_REPO || "moje-projekty";
const PREF_PATH = "config/preferences.yaml";
const RATINGS_PATH = "data/ratings.json";

function gh(): Octokit {
  const token = process.env.GITHUB_TOKEN;
  if (!token) throw new Error("GITHUB_TOKEN not set in env");
  return new Octokit({ auth: token });
}

export type Preferences = {
  scripts_per_run: number;
  cta_intensity: number;
  copy_similarity: number;
  effort_level: number;
  target_seconds: number;
  tone: string;
  hashtags?: { count: number; mix?: Record<string, number> };
  multi_platform?: { enabled: boolean; platforms: string[] };
  ratings?: { enabled: boolean; use_history_in_prompts: boolean };
  trending_hooks?: { enabled: boolean; daily_count: number };
  multi_niche?: { enabled: boolean; active_niches: string[] };
};

export const DEFAULT_PREFS: Preferences = {
  scripts_per_run: 3,
  cta_intensity: 30,
  copy_similarity: 40,
  effort_level: 6,
  target_seconds: 45,
  tone: "balanced",
  hashtags: { count: 18, mix: { niche: 0.5, broad: 0.3, branded: 0.2 } },
  multi_platform: { enabled: false, platforms: ["tiktok"] },
  ratings: { enabled: true, use_history_in_prompts: true },
  trending_hooks: { enabled: false, daily_count: 5 },
  multi_niche: { enabled: false, active_niches: ["skala"] },
};

export async function getPreferences(): Promise<{ prefs: Preferences; sha: string | null }> {
  try {
    const r = await gh().repos.getContent({ owner: OWNER, repo: REPO, path: PREF_PATH });
    if (Array.isArray(r.data) || r.data.type !== "file") {
      return { prefs: DEFAULT_PREFS, sha: null };
    }
    const content = Buffer.from(r.data.content, "base64").toString("utf-8");
    const parsed = (yaml.load(content) as Partial<Preferences>) || {};
    return { prefs: { ...DEFAULT_PREFS, ...parsed }, sha: r.data.sha };
  } catch (e: any) {
    if (e.status === 404) return { prefs: DEFAULT_PREFS, sha: null };
    throw e;
  }
}

export async function savePreferences(prefs: Preferences): Promise<void> {
  const { sha } = await getPreferences();
  const header = `# Preferences - sterowniki generatora skryptow.
# Edytowane przez Web Panel: ${new Date().toISOString()}
# Po commitcie pipeline w kolejnym uruchomieniu uzyje nowych wartosci.

`;
  const content = header + yaml.dump(prefs, { lineWidth: 100, sortKeys: false });
  await gh().repos.createOrUpdateFileContents({
    owner: OWNER,
    repo: REPO,
    path: PREF_PATH,
    message: `panel: update preferences ${new Date().toISOString().split("T")[0]}`,
    content: Buffer.from(content, "utf-8").toString("base64"),
    sha: sha || undefined,
  });
}

export async function triggerWorkflow(skipTelegram = false): Promise<void> {
  await gh().actions.createWorkflowDispatch({
    owner: OWNER,
    repo: REPO,
    workflow_id: "daily.yml",
    ref: "main",
    inputs: { skip_telegram: String(skipTelegram) },
  });
}

export async function getLatestRun(): Promise<any> {
  const r = await gh().actions.listWorkflowRuns({
    owner: OWNER,
    repo: REPO,
    workflow_id: "daily.yml",
    per_page: 1,
  });
  return r.data.workflow_runs[0] || null;
}

export type Rating = {
  script_id: string;       // np. "2026-05-18/01-founder_line"
  rating: 1 | -1;
  timestamp: string;
};

export async function getRatings(): Promise<{ ratings: Rating[]; sha: string | null }> {
  try {
    const r = await gh().repos.getContent({ owner: OWNER, repo: REPO, path: RATINGS_PATH });
    if (Array.isArray(r.data) || r.data.type !== "file") {
      return { ratings: [], sha: null };
    }
    const content = Buffer.from(r.data.content, "base64").toString("utf-8");
    return { ratings: JSON.parse(content) as Rating[], sha: r.data.sha };
  } catch (e: any) {
    if (e.status === 404) return { ratings: [], sha: null };
    throw e;
  }
}

export async function addRating(scriptId: string, rating: 1 | -1): Promise<void> {
  const { ratings, sha } = await getRatings();
  ratings.push({ script_id: scriptId, rating, timestamp: new Date().toISOString() });
  await gh().repos.createOrUpdateFileContents({
    owner: OWNER,
    repo: REPO,
    path: RATINGS_PATH,
    message: `panel: rating ${rating > 0 ? "+1" : "-1"} for ${scriptId}`,
    content: Buffer.from(JSON.stringify(ratings, null, 2), "utf-8").toString("base64"),
    sha: sha || undefined,
  });
}

export async function listScripts(daysBack = 7): Promise<{ date: string; files: string[] }[]> {
  try {
    const r = await gh().repos.getContent({ owner: OWNER, repo: REPO, path: "scripts" });
    if (!Array.isArray(r.data)) return [];
    const dirs = r.data
      .filter((x) => x.type === "dir")
      .sort((a, b) => b.name.localeCompare(a.name))
      .slice(0, daysBack);
    const out: { date: string; files: string[] }[] = [];
    for (const dir of dirs) {
      const sub = await gh().repos.getContent({
        owner: OWNER, repo: REPO, path: dir.path,
      });
      if (Array.isArray(sub.data)) {
        out.push({
          date: dir.name,
          files: sub.data.filter((x) => x.name.endsWith(".md")).map((x) => x.name),
        });
      }
    }
    return out;
  } catch (e: any) {
    if (e.status === 404) return [];
    throw e;
  }
}

export async function getScriptContent(date: string, filename: string): Promise<string> {
  const r = await gh().repos.getContent({
    owner: OWNER, repo: REPO, path: `scripts/${date}/${filename}`,
  });
  if (Array.isArray(r.data) || r.data.type !== "file") {
    throw new Error("Not a file");
  }
  return Buffer.from(r.data.content, "base64").toString("utf-8");
}
