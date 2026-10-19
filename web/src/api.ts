export type Brand = {
  id: number;
  name: string;
  description: string;
  pillars: string[];
  no_go_topics: string[];
  tone: string;
  languages: string[];
  past_campaigns: string;
  telegram_connected: boolean;
};

export type Account = {
  id: number;
  platform: string;
  handle: string;
  followers: number | null;
  avg_views: number | null;
  engagement_rate: number | null;
  last_synced_at: string | null;
};

export type Creator = {
  id: number;
  display_name: string;
  bio: string;
  city: string;
  contact: string;
  price_uzs: number | null;
  summary: string;
  languages: string[];
  niche_tags: string[];
  avg_quality: number | null;
  avg_hook_strength: number | null;
  brand_safety_risk: string;
  accounts: Account[];
};

export type Analysis = {
  summary: string;
  hook: string;
  hook_strength: number;
  pacing: string;
  setting: string;
  energy: string;
  on_screen_tone: string;
  languages: string[];
  niche_tags: string[];
  production_quality: number;
  authenticity: number;
  brand_safety_risk: string;
  brand_safety_flags: string[];
};

export type Video = {
  id: number;
  platform: string;
  url: string;
  caption: string;
  posted_at: string | null;
  views: number | null;
  status: string;
  error: string | null;
  analysis: Analysis | null;
};

export type CreatorDetail = Creator & { videos: Video[] };

export type Entry = {
  id: number;
  creator: Creator;
  score: number;
  reasons: string;
  risks: string;
  evidence_video_ids: number[];
  outreach_language: string | null;
  outreach_message: string | null;
  status: "suggested" | "starred" | "rejected" | "contacted";
};

export type Brief = {
  id: number;
  brand_id: number;
  title: string;
  text: string;
  standing: boolean;
  criteria: { summary?: string; topics?: string[]; languages?: string[] } | null;
  status: "draft" | "running" | "done" | "failed";
  error: string | null;
  created_at: string;
  completed_at: string | null;
};

export type BriefDetail = Brief & { entries: Entry[] };

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = init?.body instanceof FormData ? {} : { "Content-Type": "application/json" };
  const resp = await fetch(`/api${path}`, { ...init, headers });
  if (!resp.ok) {
    const detail = await resp.json().catch(() => ({}));
    throw new Error(detail.detail ?? `${resp.status} ${resp.statusText}`);
  }
  return resp.json();
}

const json = (method: string, body: unknown): RequestInit => ({ method, body: JSON.stringify(body) });

export const api = {
  brands: () => request<Brand[]>("/brands"),
  createBrand: (body: Partial<Brand>) => request<Brand>("/brands", json("POST", body)),
  updateBrand: (id: number, body: Partial<Brand>) => request<Brand>(`/brands/${id}`, json("PATCH", body)),
  telegramLink: (id: number) => request<{ url: string; connected: boolean }>(`/brands/${id}/telegram-link`),

  creators: (params: Record<string, string>) =>
    request<Creator[]>(`/creators?${new URLSearchParams(Object.entries(params).filter(([, v]) => v))}`),
  creator: (id: number) => request<CreatorDetail>(`/creators/${id}`),
  createCreator: (body: unknown) => request<Creator>("/creators", json("POST", body)),
  refreshCreator: (id: number) => request(`/creators/${id}/refresh`, { method: "POST" }),
  uploadVideo: (id: number, file: File, caption: string) => {
    const form = new FormData();
    form.append("file", file);
    form.append("caption", caption);
    return request<Video>(`/creators/${id}/videos`, { method: "POST", body: form });
  },
  lookalikes: (id: number) => request<{ creator: Creator; similarity: number }[]>(`/creators/${id}/lookalikes`),

  briefs: (brandId: number) => request<Brief[]>(`/brands/${brandId}/briefs`),
  brief: (id: number) => request<BriefDetail>(`/briefs/${id}`),
  createBrief: (brandId: number, body: { title: string; text: string; standing: boolean }) =>
    request<Brief>(`/brands/${brandId}/briefs`, json("POST", body)),
  runBrief: (id: number) => request(`/briefs/${id}/run`, { method: "POST" }),
  updateEntry: (id: number, body: Partial<Pick<Entry, "status" | "outreach_message">>) =>
    request<Entry>(`/shortlist/${id}`, json("PATCH", body)),

  translate: (lang: string, texts: string[]) =>
    request<{ texts: string[] }>("/translate", json("POST", { lang, texts })),
};
