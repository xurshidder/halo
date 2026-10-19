import { useEffect, useState } from "react";
import { api, Brand, Brief, BriefDetail, Entry, formatNumber } from "../api";

export default function Briefs({ brand }: { brand: Brand }) {
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
        <h2>New brief</h2>
        <input
          placeholder="Title, e.g. Spring serum launch"
          value={form.title}
          onChange={(e) => setForm({ ...form, title: e.target.value })}
        />
        <textarea
          rows={6}
          placeholder="Describe the creator you need in plain words: who they talk to, what their videos look like, language, budget..."
          value={form.text}
          onChange={(e) => setForm({ ...form, text: e.target.value })}
        />
        <label className="check">
          <input
            type="checkbox"
            checked={form.standing}
            onChange={(e) => setForm({ ...form, standing: e.target.checked })}
          />
          Keep watching: search again every morning and send new matches to Telegram
        </label>
        <button onClick={create}>Find creators</button>

        <h2>Briefs</h2>
        {briefs.length === 0 && <p className="muted">No briefs yet.</p>}
        {briefs.map((b) => (
          <button key={b.id} className={`list-item ${selected === b.id ? "active" : ""}`} onClick={() => setSelected(b.id)}>
            <span>{b.title}</span>
            <span className={`pill ${b.status}`}>{b.status}</span>
          </button>
        ))}
      </aside>
      <section className="panel grow">
        {selected ? <BriefView id={selected} onChange={load} /> : <p className="muted">Pick or create a brief.</p>}
      </section>
    </div>
  );
}

function BriefView({ id, onChange }: { id: number; onChange: () => void }) {
  const [brief, setBrief] = useState<BriefDetail | null>(null);
  const [error, setError] = useState("");

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

  if (!brief) return <p className="muted">Loading…</p>;
  const visible = brief.entries.filter((e) => e.status !== "rejected");

  return (
    <div>
      <div className="row between">
        <div>
          <h1>{brief.title}</h1>
          <p className="muted">{brief.criteria?.summary ?? brief.text}</p>
          {brief.criteria?.topics && (
            <div className="tags">
              {brief.criteria.topics.map((t) => (
                <span key={t} className="tag">
                  {t}
                </span>
              ))}
              {brief.criteria.languages?.map((l) => (
                <span key={l} className="tag lang">
                  {l}
                </span>
              ))}
            </div>
          )}
        </div>
        <button className="ghost" onClick={rerun} disabled={brief.status === "running"}>
          {brief.status === "running" ? "Watching videos…" : "Search again"}
        </button>
      </div>
      {error && <p className="error">{error}</p>}
      {brief.status === "failed" && <p className="error">Run failed: {brief.error}</p>}
      {brief.status === "running" && <div className="progress">Halo is reading the brief and scoring creators…</div>}
      {brief.status === "done" && visible.length === 0 && (
        <p className="muted">No creators matched yet. Add more creators or loosen the brief.</p>
      )}
      <div className="cards">
        {visible.map((entry) => (
          <EntryCard key={entry.id} entry={entry} onChange={load} />
        ))}
      </div>
    </div>
  );
}

function EntryCard({ entry, onChange }: { entry: Entry; onChange: () => void }) {
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
            {c.accounts.map((a) => `${a.platform} ${a.handle} · ${formatNumber(a.followers)}`).join("  |  ")}
            {c.price_uzs ? `  |  ${formatNumber(c.price_uzs)} UZS` : ""}
          </p>
        </div>
        <div className="score" style={{ ["--score" as string]: entry.score }}>
          {entry.score}
        </div>
      </div>
      <ul className="reasons">
        {entry.reasons.split("\n").filter(Boolean).map((r) => (
          <li key={r}>{r}</li>
        ))}
      </ul>
      {entry.risks && (
        <ul className="risks">
          {entry.risks.split("\n").filter(Boolean).map((r) => (
            <li key={r}>{r}</li>
          ))}
        </ul>
      )}
      <label className="small">
        Outreach draft ({entry.outreach_language ?? "uz"})
        <textarea rows={4} value={message} onChange={(e) => setMessage(e.target.value)} onBlur={saveMessage} />
      </label>
      <div className="row">
        <button className="ghost" onClick={copy}>
          {copied ? "Copied" : "Copy message"}
        </button>
        <button className="ghost" onClick={() => setStatus(entry.status === "starred" ? "suggested" : "starred")}>
          {entry.status === "starred" ? "Unstar" : "Star"}
        </button>
        <button className="ghost" onClick={() => setStatus("contacted")}>
          Mark contacted
        </button>
        <button className="ghost danger" onClick={() => setStatus("rejected")}>
          Not a fit
        </button>
      </div>
    </article>
  );
}
