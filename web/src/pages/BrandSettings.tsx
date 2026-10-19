import { useEffect, useState } from "react";
import { api, Brand } from "../api";

const toLines = (items: string[]) => items.join("\n");
const fromLines = (text: string) =>
  text
    .split(/[\n,]/)
    .map((s) => s.trim())
    .filter(Boolean);

export default function BrandSettings({ brand, onSaved }: { brand: Brand; onSaved: () => void }) {
  const [form, setForm] = useState({
    name: brand.name,
    description: brand.description,
    pillars: toLines(brand.pillars),
    no_go_topics: toLines(brand.no_go_topics),
    tone: brand.tone,
    languages: brand.languages.join(", "),
    past_campaigns: brand.past_campaigns,
  });
  const [link, setLink] = useState<{ url: string; connected: boolean } | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    api.telegramLink(brand.id).then(setLink);
  }, [brand.id]);

  const set = (key: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
    setForm({ ...form, [key]: e.target.value });

  const save = async () => {
    await api.updateBrand(brand.id, {
      ...form,
      pillars: fromLines(form.pillars),
      no_go_topics: fromLines(form.no_go_topics),
      languages: fromLines(form.languages),
    });
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
    onSaved();
  };

  return (
    <section className="panel narrow">
      <h1>Brand context</h1>
      <p className="muted">Loaded once. Every search, score and outreach draft runs against it.</p>
      <label>
        Name
        <input value={form.name} onChange={set("name")} />
      </label>
      <label>
        What the brand sells, and to whom
        <textarea rows={3} value={form.description} onChange={set("description")} />
      </label>
      <div className="two-col">
        <label>
          Pillars (one per line)
          <textarea rows={4} value={form.pillars} onChange={set("pillars")} />
        </label>
        <label>
          No-go topics (one per line)
          <textarea rows={4} value={form.no_go_topics} onChange={set("no_go_topics")} />
        </label>
      </div>
      <label>
        Tone of voice
        <input value={form.tone} onChange={set("tone")} placeholder="warm, simple, a bit playful" />
      </label>
      <label>
        Customer languages
        <input value={form.languages} onChange={set("languages")} placeholder="uz, ru" />
      </label>
      <label>
        Past campaigns: what worked, what didn't
        <textarea rows={3} value={form.past_campaigns} onChange={set("past_campaigns")} />
      </label>
      <div className="row">
        <button onClick={save}>Save</button>
        {saved && <span className="muted">Saved</span>}
      </div>

      <h2>Telegram alerts</h2>
      {link?.connected ? (
        <p>Connected. Halo posts new creator matches to your Telegram chat.</p>
      ) : (
        <p>
          Get new matches in Telegram:{" "}
          <a href={link?.url} target="_blank" rel="noreferrer">
            open this link
          </a>{" "}
          in the chat or group where your team works.
        </p>
      )}
    </section>
  );
}
