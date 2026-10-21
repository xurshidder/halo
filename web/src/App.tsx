import { useEffect, useState } from "react";
import { api, Brand } from "./api";
import { Lang, LANGS, useI18n } from "./i18n";
import BrandSettings from "./pages/BrandSettings";
import Briefs from "./pages/Briefs";
import Creators from "./pages/Creators";

type Tab = "briefs" | "creators" | "brand";
const TAB_LABELS = { briefs: "tab_briefs", creators: "tab_creators", brand: "tab_brand" } as const;

export default function App() {
  const { t, lang, setLang } = useI18n();
  const [brands, setBrands] = useState<Brand[]>([]);
  const [brandId, setBrandId] = useState<number | null>(null);
  const [tab, setTab] = useState<Tab>("briefs");
  const [error, setError] = useState("");

  const loadBrands = async (select?: number) => {
    try {
      const list = await api.brands();
      setBrands(list);
      setBrandId(select ?? brandId ?? list[0]?.id ?? null);
    } catch (e) {
      setError(String(e));
    }
  };

  useEffect(() => {
    loadBrands();
  }, []);

  const createBrand = async () => {
    const name = prompt(t("brand_name_prompt"));
    if (!name) return;
    const brand = await api.createBrand({ name });
    await loadBrands(brand.id);
    setTab("brand");
  };

  const brand = brands.find((b) => b.id === brandId) ?? null;

  return (
    <div className="app">
      <header className="topbar">
        <a className="logo" href="/" aria-label="Collab">
          <picture>
            <source srcSet="/collab-wordmark-on-dark.svg" media="(prefers-color-scheme: dark)" />
            <img src="/collab-wordmark.svg" alt="Collab" />
          </picture>
        </a>
        <nav>
          {(["briefs", "creators", "brand"] as Tab[]).map((tb) => (
            <button key={tb} className={tab === tb ? "tab active" : "tab"} onClick={() => setTab(tb)}>
              {t(TAB_LABELS[tb])}
            </button>
          ))}
        </nav>
        <div className="brand-picker">
          <select
            className="lang-picker"
            aria-label={t("language")}
            value={lang}
            onChange={(e) => setLang(e.target.value as Lang)}
          >
            {LANGS.map((l) => (
              <option key={l.code} value={l.code}>
                {l.label}
              </option>
            ))}
          </select>
          <select value={brandId ?? ""} onChange={(e) => setBrandId(Number(e.target.value))}>
            {brands.map((b) => (
              <option key={b.id} value={b.id}>
                {b.name}
              </option>
            ))}
          </select>
          <button className="ghost" onClick={createBrand}>
            {t("add_brand_short")}
          </button>
        </div>
      </header>
      <main>
        {error && <p className="error">{error}</p>}
        {!brand && tab !== "creators" ? (
          <div className="empty">
            <h2>{t("empty_title")}</h2>
            <p>{t("empty_text")}</p>
            <button onClick={createBrand}>{t("add_brand")}</button>
          </div>
        ) : tab === "briefs" ? (
          <Briefs brand={brand!} />
        ) : tab === "creators" ? (
          <Creators />
        ) : (
          <BrandSettings key={brand!.id} brand={brand!} onSaved={() => loadBrands(brand!.id)} />
        )}
      </main>
    </div>
  );
}
