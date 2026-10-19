import { useEffect, useState } from "react";
import { api, Creator, CreatorDetail } from "../api";
import { AiTextStatus, LANGS, useAiText, useI18n } from "../i18n";

export default function Creators() {
  const { t, tv } = useI18n();
  const [creators, setCreators] = useState<Creator[]>([]);
  const [filters, setFilters] = useState({ q: "", tag: "", language: "" });
  const [selected, setSelected] = useState<number | null>(null);
  const [adding, setAdding] = useState(false);
  const { tr } = useAiText(creators.flatMap((c) => c.niche_tags.slice(0, 3)));

  const load = () => api.creators(filters).then(setCreators);
  useEffect(() => {
    load();
  }, [filters.tag, filters.language]);

  return (
    <div className="split">
      <aside className="panel list">
        <div className="row between">
          <h2>{t("creators")}</h2>
          <button className="ghost" onClick={() => setAdding(!adding)}>
            {adding ? t("cancel") : t("add")}
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
          placeholder={t("search_ph")}
          value={filters.q}
          onChange={(e) => setFilters({ ...filters, q: e.target.value })}
          onKeyDown={(e) => e.key === "Enter" && load()}
        />
        <div className="row">
          <input placeholder={t("topic_ph")} value={filters.tag} onChange={(e) => setFilters({ ...filters, tag: e.target.value })} />
          <select value={filters.language} onChange={(e) => setFilters({ ...filters, language: e.target.value })}>
            <option value="">{t("any_language")}</option>
            {LANGS.map((l) => (
              <option key={l.code} value={l.code}>
                {tv("lang", l.code)}
              </option>
            ))}
          </select>
        </div>
        {creators.map((c) => (
          <button key={c.id} className={`list-item ${selected === c.id ? "active" : ""}`} onClick={() => setSelected(c.id)}>
            <span>
              {c.display_name}
              <span className="muted small"> {c.niche_tags.slice(0, 3).map(tr).join(", ")}</span>
            </span>
            {c.avg_quality != null && <span className="pill">{c.avg_quality.toFixed(1)}</span>}
          </button>
        ))}
      </aside>
      <section className="panel grow">
        {selected ? <CreatorView id={selected} onSelect={setSelected} /> : <p className="muted">{t("pick_creator")}</p>}
      </section>
    </div>
  );
}

function AddCreator({ onAdded }: { onAdded: (c: Creator) => void }) {
  const { t } = useI18n();
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
      <input placeholder={t("name_ph")} value={form.display_name} onChange={set("display_name")} />
      <input placeholder={t("city_ph")} value={form.city} onChange={set("city")} />
      <input placeholder={t("price_ph")} value={form.price_uzs} onChange={set("price_uzs")} />
      <input placeholder={t("instagram_ph")} value={form.instagram} onChange={set("instagram")} />
      <input placeholder={t("youtube_ph")} value={form.youtube} onChange={set("youtube")} />
      <button onClick={save} disabled={!form.display_name}>
        {t("save_creator")}
      </button>
    </div>
  );
}

function CreatorView({ id, onSelect }: { id: number; onSelect: (id: number) => void }) {
  const { t, tv, num } = useI18n();
  const [creator, setCreator] = useState<CreatorDetail | null>(null);
  const [similar, setSimilar] = useState<{ creator: Creator; similarity: number }[] | null>(null);
  const [uploading, setUploading] = useState(false);
  const { tr, translating, failed } = useAiText([
    creator?.summary,
    ...(creator?.niche_tags ?? []),
    ...(creator?.videos ?? []).flatMap((v) =>
      v.analysis ? [v.analysis.summary, v.analysis.hook, v.analysis.setting, ...v.analysis.brand_safety_flags] : [],
    ),
  ]);

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

  if (!creator) return <p className="muted">{t("loading")}</p>;

  return (
    <div>
      <div className="row between">
        <div>
          <h1>{creator.display_name}</h1>
          <p className="muted">
            {[creator.city, creator.languages.map((l) => tv("lang", l)).join(", "), creator.contact]
              .filter(Boolean)
              .join(" · ")}
          </p>
        </div>
        <div className="row">
          <button className="ghost" onClick={() => api.refreshCreator(id).then(load)}>
            {t("refresh_videos")}
          </button>
          <label className="button ghost">
            {uploading ? t("uploading") : t("upload_video")}
            <input type="file" accept="video/*" hidden onChange={upload} />
          </label>
          <button onClick={() => api.lookalikes(id).then(setSimilar)}>{t("more_like_this")}</button>
        </div>
      </div>
      <AiTextStatus translating={translating} failed={failed} />
      {creator.summary && <p>{tr(creator.summary)}</p>}
      <div className="stats">
        <Stat label={t("quality")} value={creator.avg_quality?.toFixed(1)} />
        <Stat label={t("hook")} value={creator.avg_hook_strength?.toFixed(1)} />
        <Stat label={t("brand_safety")} value={tv("risk", creator.brand_safety_risk)} />
        {creator.accounts.map((a) => (
          <Stat key={a.id} label={`${a.platform} ${a.handle}`} value={t("followers", { count: num(a.followers) })} />
        ))}
      </div>
      <div className="tags">
        {creator.niche_tags.map((tag) => (
          <span key={tag} className="tag">
            {tr(tag)}
          </span>
        ))}
      </div>

      {similar && (
        <>
          <h2>{t("lookalikes")}</h2>
          {similar.length === 0 && <p className="muted">{t("no_similar")}</p>}
          <div className="row wrap">
            {similar.map((s) => (
              <button key={s.creator.id} className="ghost" onClick={() => onSelect(s.creator.id)}>
                {s.creator.display_name} · {Math.round(s.similarity * 100)}%
              </button>
            ))}
          </div>
        </>
      )}

      <h2>{t("videos_watched")}</h2>
      {creator.videos.length === 0 && <p className="muted">{t("no_videos")}</p>}
      <div className="cards">
        {creator.videos.map((v) => (
          <article key={v.id} className="card">
            <div className="row between">
              <a href={v.url || undefined} target="_blank" rel="noreferrer">
                {t("video", { id: v.id })} · {tv("platform", v.platform)}
              </a>
              <span className={`pill ${v.status}`}>{tv("status", v.status)}</span>
            </div>
            {v.error && <p className="error small">{v.error}</p>}
            {v.analysis && (
              <>
                <p>{tr(v.analysis.summary)}</p>
                <p className="small">
                  <b>{t("hook_score", { score: v.analysis.hook_strength })}</b> {tr(v.analysis.hook)}
                </p>
                <p className="small muted">
                  {[
                    tr(v.analysis.setting),
                    t("pacing", { pace: tv("pace", v.analysis.pacing) }),
                    tv("energy", v.analysis.energy),
                    t("quality_score", { score: v.analysis.production_quality }),
                    t("authenticity_score", { score: v.analysis.authenticity }),
                  ].join(" · ")}
                </p>
                {v.analysis.brand_safety_flags.length > 0 && (
                  <p className="small risk">⚠ {v.analysis.brand_safety_flags.map(tr).join(", ")}</p>
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
