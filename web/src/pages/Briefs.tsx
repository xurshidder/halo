import { useEffect, useState } from "react";
import { api, Brand, Brief, BriefDetail, Entry } from "../api";
import { AiTextStatus, useAiText, useI18n } from "../i18n";

const lines = (text: string) => text.split("\n").filter(Boolean);

export default function Briefs({ brand }: { brand: Brand }) {
  const { t, tv } = useI18n();
  const [briefs, setBriefs] = useState<Brief[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [form, setForm] = useState({ title: "", text: "", standing: false });

  const load = () => api.briefs(brand.id).then(setBriefs);
  useEffect(() => {
    setSelected(null);
    load();
  }, [brand.id]);

  const create = async () => {
    if (!form.title || !form.text) return;
    const brief = await api.createBrief(brand.id, form);
    await api.runBrief(brief.id);
    setForm({ title: "", text: "", standing: false });
    await load();
    setSelected(brief.id);
  };

  return (
    <div className="split">
      <aside className="panel list">
        <h2>{t("new_brief")}</h2>
        <input
          placeholder={t("brief_title_ph")}
          value={form.title}
          onChange={(e) => setForm({ ...form, title: e.target.value })}
        />
        <textarea
          rows={6}
          placeholder={t("brief_text_ph")}
          value={form.text}
          onChange={(e) => setForm({ ...form, text: e.target.value })}
        />
        <label className="check">
          <input
            type="checkbox"
            checked={form.standing}
            onChange={(e) => setForm({ ...form, standing: e.target.checked })}
          />
          {t("keep_watching")}
        </label>
        <button onClick={create}>{t("find_creators")}</button>

        <h2>{t("briefs")}</h2>
        {briefs.length === 0 && <p className="muted">{t("no_briefs")}</p>}
        {briefs.map((b) => (
          <button key={b.id} className={`list-item ${selected === b.id ? "active" : ""}`} onClick={() => setSelected(b.id)}>
            <span>{b.title}</span>
            <span className={`pill ${b.status}`}>{tv("status", b.status)}</span>
          </button>
        ))}
      </aside>
      <section className="panel grow">
        {selected ? <BriefView id={selected} onChange={load} /> : <p className="muted">{t("pick_brief")}</p>}
      </section>
    </div>
  );
}

function BriefView({ id, onChange }: { id: number; onChange: () => void }) {
  const { t, tv } = useI18n();
  const [brief, setBrief] = useState<BriefDetail | null>(null);
  const [error, setError] = useState("");
  const { tr, translating, failed } = useAiText([
    brief?.criteria?.summary,
    ...(brief?.criteria?.topics ?? []),
    ...(brief?.entries ?? [])
      .filter((e) => e.status !== "rejected") // hidden, so not worth translating
      .flatMap((e) => [...lines(e.reasons), ...lines(e.risks)]),
  ]);

  const load = () => api.brief(id).then(setBrief).catch((e) => setError(String(e)));
  useEffect(() => {
    load();
  }, [id]);
  useEffect(() => {
    if (brief?.status !== "running") return;
    const timer = setInterval(async () => {
      const fresh = await api.brief(id);
      setBrief(fresh);
      if (fresh.status !== "running") onChange();
    }, 3000);
    return () => clearInterval(timer);
  }, [brief?.status, id]);

  const rerun = async () => {
    await api.runBrief(id).catch((e) => setError(String(e)));
    await load();
    onChange();
  };

  if (!brief) return <p className="muted">{t("loading")}</p>;
  const visible = brief.entries.filter((e) => e.status !== "rejected");

  return (
    <div>
      <div className="row between">
        <div>
          <h1>{brief.title}</h1>
          <p className="muted">{brief.criteria?.summary ? tr(brief.criteria.summary) : brief.text}</p>
          {brief.criteria?.topics && (
            <div className="tags">
              {brief.criteria.topics.map((topic) => (
                <span key={topic} className="tag">
                  {tr(topic)}
                </span>
              ))}
              {brief.criteria.languages?.map((l) => (
                <span key={l} className="tag lang">
                  {tv("lang", l)}
                </span>
              ))}
            </div>
          )}
          <AiTextStatus translating={translating} failed={failed} />
        </div>
        <button className="ghost" onClick={rerun} disabled={brief.status === "running"}>
          {brief.status === "running" ? t("watching_videos") : t("search_again")}
        </button>
      </div>
      {error && <p className="error">{error}</p>}
      {brief.status === "failed" && <p className="error">{t("run_failed", { error: brief.error ?? "" })}</p>}
      {brief.status === "running" && <div className="progress">{t("running_progress")}</div>}
      {brief.status === "done" && visible.length === 0 && <p className="muted">{t("no_matches")}</p>}
      <div className="cards">
        {visible.map((entry) => (
          <EntryCard key={entry.id} entry={entry} tr={tr} onChange={load} />
        ))}
      </div>
    </div>
  );
}

function EntryCard({ entry, tr, onChange }: { entry: Entry; tr: (text: string) => string; onChange: () => void }) {
  const { t, tv, num } = useI18n();
  const [message, setMessage] = useState(entry.outreach_message ?? "");
  const [copied, setCopied] = useState(false);
  const c = entry.creator;

  const setStatus = async (status: Entry["status"]) => {
    await api.updateEntry(entry.id, { status });
    onChange();
  };
  const saveMessage = () => api.updateEntry(entry.id, { outreach_message: message });
  const copy = async () => {
    await navigator.clipboard.writeText(message);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <article className={`card ${entry.status}`}>
      <div className="row between">
        <div>
          <h3>
            {c.display_name} {entry.status === "starred" && "★"}
          </h3>
          <p className="muted small">
            {c.accounts.map((a) => `${a.platform} ${a.handle} · ${num(a.followers)}`).join("  |  ")}
            {c.price_uzs ? `  |  ${num(c.price_uzs)} ${t("currency")}` : ""}
          </p>
        </div>
        <div className="score" style={{ ["--score" as string]: entry.score }}>
          {entry.score}
        </div>
      </div>
      <ul className="reasons">
        {lines(entry.reasons).map((r) => (
          <li key={r}>{tr(r)}</li>
        ))}
      </ul>
      {entry.risks && (
        <ul className="risks">
          {lines(entry.risks).map((r) => (
            <li key={r}>{tr(r)}</li>
          ))}
        </ul>
      )}
      <label className="small">
        {t("outreach_draft", { language: tv("lang", entry.outreach_language ?? "uz") })}
        <textarea rows={4} value={message} onChange={(e) => setMessage(e.target.value)} onBlur={saveMessage} />
      </label>
      <div className="row">
        <button className="ghost" onClick={copy}>
          {copied ? t("copied") : t("copy_message")}
        </button>
        <button className="ghost" onClick={() => setStatus(entry.status === "starred" ? "suggested" : "starred")}>
          {entry.status === "starred" ? t("unstar") : t("star")}
        </button>
        <button className="ghost" onClick={() => setStatus("contacted")}>
          {t("mark_contacted")}
        </button>
        <button className="ghost danger" onClick={() => setStatus("rejected")}>
          {t("not_a_fit")}
        </button>
      </div>
    </article>
  );
}
