import { useEffect, useState } from "react";
import { api, Brand } from "../api";
import { useI18n } from "../i18n";

const toLines = (items: string[]) => items.join("\n");
const fromLines = (text: string) =>
  text
    .split(/[\n,]/)
    .map((s) => s.trim())
    .filter(Boolean);

export default function BrandSettings({ brand, onSaved }: { brand: Brand; onSaved: () => void }) {
  const { t } = useI18n();
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
      <h1>{t("brand_context")}</h1>
      <p className="muted">{t("brand_context_note")}</p>
      <label>
        {t("brand_name")}
        <input value={form.name} onChange={set("name")} />
      </label>
      <label>
        {t("brand_sells")}
        <textarea rows={3} value={form.description} onChange={set("description")} />
      </label>
      <div className="two-col">
        <label>
          {t("pillars")}
          <textarea rows={4} value={form.pillars} onChange={set("pillars")} />
        </label>
        <label>
          {t("no_go")}
          <textarea rows={4} value={form.no_go_topics} onChange={set("no_go_topics")} />
        </label>
      </div>
      <label>
        {t("tone")}
        <input value={form.tone} onChange={set("tone")} placeholder={t("tone_ph")} />
      </label>
      <label>
        {t("customer_languages")}
        <input value={form.languages} onChange={set("languages")} placeholder="uz, ru" />
      </label>
      <label>
        {t("past_campaigns")}
        <textarea rows={3} value={form.past_campaigns} onChange={set("past_campaigns")} />
      </label>
      <div className="row">
        <button onClick={save}>{t("save")}</button>
        {saved && <span className="muted">{t("saved")}</span>}
      </div>

      <h2>{t("telegram_alerts")}</h2>
      {link?.connected ? (
        <p>{t("telegram_connected")}</p>
      ) : (
        <p>
          {t("telegram_before")}
          <a href={link?.url} target="_blank" rel="noreferrer">
            {t("telegram_link")}
          </a>
          {t("telegram_after")}
        </p>
      )}
    </section>
  );
}
