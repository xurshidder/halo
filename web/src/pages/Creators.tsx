import { useEffect, useState } from "react";
import { api, Creator, CreatorDetail, formatNumber } from "../api";

export default function Creators() {
  const [creators, setCreators] = useState<Creator[]>([]);
  const [filters, setFilters] = useState({ q: "", tag: "", language: "" });
  const [selected, setSelected] = useState<number | null>(null);
  const [adding, setAdding] = useState(false);

  const load = () => api.creators(filters).then(setCreators);
  useEffect(() => {
    load();
  }, [filters.tag, filters.language]);

  return (
    <div className="split">
      <aside className="panel list">
        <div className="row between">
          <h2>Creators</h2>
          <button className="ghost" onClick={() => setAdding(!adding)}>
            {adding ? "Cancel" : "+ Add"}
          </button>
        </div>
        {adding && (
          <AddCreator
            onAdded={(c) => {
              setAdding(false);
              load();
              setSelected(c.id);
            }}
          />
        )}
        <input
          placeholder="Search name or content…"
          value={filters.q}
          onChange={(e) => setFilters({ ...filters, q: e.target.value })}
          onKeyDown={(e) => e.key === "Enter" && load()}
        />
        <div className="row">
          <input placeholder="Topic" value={filters.tag} onChange={(e) => setFilters({ ...filters, tag: e.target.value })} />
          <select value={filters.language} onChange={(e) => setFilters({ ...filters, language: e.target.value })}>
            <option value="">Any language</option>
            <option value="uz">Uzbek</option>
            <option value="ru">Russian</option>
            <option value="en">English</option>
          </select>
        </div>
        {creators.map((c) => (
          <button key={c.id} className={`list-item ${selected === c.id ? "active" : ""}`} onClick={() => setSelected(c.id)}>
            <span>
              {c.display_name}
              <span className="muted small"> {c.niche_tags.slice(0, 3).join(", ")}</span>
            </span>
            {c.avg_quality != null && <span className="pill">{c.avg_quality.toFixed(1)}</span>}
          </button>
        ))}
      </aside>
      <section className="panel grow">
        {selected ? (
          <CreatorView id={selected} onSelect={setSelected} />
        ) : (
          <p className="muted">Pick a creator. Creators can also join through the Telegram bot with /join.</p>
        )}
      </section>
    </div>
  );
}

function AddCreator({ onAdded }: { onAdded: (c: Creator) => void }) {
  const [form, setForm] = useState({ display_name: "", city: "", price_uzs: "", instagram: "", youtube: "" });
  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) => setForm({ ...form, [k]: e.target.value });

  const save = async () => {
    const accounts = [
      form.instagram && { platform: "instagram", handle: form.instagram.replace(/^@/, "") },
      form.youtube && { platform: "youtube", handle: form.youtube },
    ].filter(Boolean);
    const creator = await api.createCreator({
      display_name: form.display_name,
      city: form.city,
      price_uzs: form.price_uzs ? Number(form.price_uzs) : null,
      accounts,
    });
    if (accounts.length) await api.refreshCreator(creator.id);
    onAdded(creator);
  };

  return (
    <div className="subform">
      <input placeholder="Name" value={form.display_name} onChange={set("display_name")} />
      <input placeholder="City" value={form.city} onChange={set("city")} />
      <input placeholder="Price per video, UZS" value={form.price_uzs} onChange={set("price_uzs")} />
      <input placeholder="Instagram handle" value={form.instagram} onChange={set("instagram")} />
      <input placeholder="YouTube handle, e.g. @channel" value={form.youtube} onChange={set("youtube")} />
      <button onClick={save} disabled={!form.display_name}>
        Save creator
      </button>
    </div>
  );
}

function CreatorView({ id, onSelect }: { id: number; onSelect: (id: number) => void }) {
  const [creator, setCreator] = useState<CreatorDetail | null>(null);
  const [similar, setSimilar] = useState<{ creator: Creator; similarity: number }[] | null>(null);
  const [uploading, setUploading] = useState(false);

  const load = () => api.creator(id).then(setCreator);
  useEffect(() => {
    setSimilar(null);
    load();
  }, [id]);
  useEffect(() => {
    if (!creator?.videos.some((v) => v.status === "pending" || v.status === "analyzing")) return;
    const timer = setInterval(load, 4000);
    return () => clearInterval(timer);
  }, [creator]);

  const upload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    await api.uploadVideo(id, file, "").finally(() => setUploading(false));
    load();
  };

  if (!creator) return <p className="muted">Loading…</p>;

  return (
    <div>
      <div className="row between">
        <div>
          <h1>{creator.display_name}</h1>
          <p className="muted">
            {[creator.city, creator.languages.join(", "), creator.contact].filter(Boolean).join(" · ")}
          </p>
        </div>
        <div className="row">
          <button className="ghost" onClick={() => api.refreshCreator(id).then(load)}>
            Refresh videos
          </button>
          <label className="button ghost">
            {uploading ? "Uploading…" : "Upload video"}
            <input type="file" accept="video/*" hidden onChange={upload} />
          </label>
          <button onClick={() => api.lookalikes(id).then(setSimilar)}>More like this</button>
        </div>
      </div>
      {creator.summary && <p>{creator.summary}</p>}
      <div className="stats">
        <Stat label="Quality" value={creator.avg_quality?.toFixed(1)} />
        <Stat label="Hook" value={creator.avg_hook_strength?.toFixed(1)} />
        <Stat label="Brand safety" value={creator.brand_safety_risk} />
        {creator.accounts.map((a) => (
          <Stat key={a.id} label={`${a.platform} ${a.handle}`} value={`${formatNumber(a.followers)} followers`} />
        ))}
      </div>
      <div className="tags">
        {creator.niche_tags.map((t) => (
          <span key={t} className="tag">
            {t}
          </span>
        ))}
      </div>

      {similar && (
        <>
          <h2>Look-alikes</h2>
          {similar.length === 0 && <p className="muted">No similar creators yet.</p>}
          <div className="row wrap">
            {similar.map((s) => (
              <button key={s.creator.id} className="ghost" onClick={() => onSelect(s.creator.id)}>
                {s.creator.display_name} · {Math.round(s.similarity * 100)}%
              </button>
            ))}
          </div>
        </>
      )}

      <h2>Videos Halo watched</h2>
      {creator.videos.length === 0 && <p className="muted">No videos yet.</p>}
      <div className="cards">
        {creator.videos.map((v) => (
          <article key={v.id} className="card">
            <div className="row between">
              <a href={v.url || undefined} target="_blank" rel="noreferrer">
                Video {v.id} · {v.platform}
              </a>
              <span className={`pill ${v.status}`}>{v.status}</span>
            </div>
            {v.error && <p className="error small">{v.error}</p>}
            {v.analysis && (
              <>
                <p>{v.analysis.summary}</p>
                <p className="small">
                  <b>Hook ({v.analysis.hook_strength}/10):</b> {v.analysis.hook}
                </p>
                <p className="small muted">
                  {v.analysis.setting} · {v.analysis.pacing} pacing · {v.analysis.energy} · quality{" "}
                  {v.analysis.production_quality}/10 · authenticity {v.analysis.authenticity}/10
                </p>
                {v.analysis.brand_safety_flags.length > 0 && (
                  <p className="small risk">⚠ {v.analysis.brand_safety_flags.join(", ")}</p>
                )}
              </>
            )}
          </article>
        ))}
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value?: string }) {
  return (
    <div className="stat">
      <span className="muted small">{label}</span>
      <b>{value ?? "—"}</b>
    </div>
  );
}
