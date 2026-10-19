import { useEffect, useState } from "react";
import { api, Brand } from "./api";
import BrandSettings from "./pages/BrandSettings";
import Briefs from "./pages/Briefs";
import Creators from "./pages/Creators";

type Tab = "briefs" | "creators" | "brand";

export default function App() {
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
    const name = prompt("Brand name");
    if (!name) return;
    const brand = await api.createBrand({ name });
    await loadBrands(brand.id);
    setTab("brand");
  };

  const brand = brands.find((b) => b.id === brandId) ?? null;

  return (
    <div className="app">
      <header className="topbar">
        <div className="logo">
          <span className="halo-ring" /> Halo
        </div>
        <nav>
          {(["briefs", "creators", "brand"] as Tab[]).map((t) => (
            <button key={t} className={tab === t ? "tab active" : "tab"} onClick={() => setTab(t)}>
              {t === "brand" ? "Brand" : t[0].toUpperCase() + t.slice(1)}
            </button>
          ))}
        </nav>
        <div className="brand-picker">
          <select value={brandId ?? ""} onChange={(e) => setBrandId(Number(e.target.value))}>
            {brands.map((b) => (
              <option key={b.id} value={b.id}>
                {b.name}
              </option>
            ))}
          </select>
          <button className="ghost" onClick={createBrand}>
            + Brand
          </button>
        </div>
      </header>
      <main>
        {error && <p className="error">{error}</p>}
        {!brand && tab !== "creators" ? (
          <div className="empty">
            <h2>Start by adding your brand</h2>
            <p>Halo uses your brand's pillars, no-go topics and tone in every search and draft.</p>
            <button onClick={createBrand}>Add brand</button>
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
