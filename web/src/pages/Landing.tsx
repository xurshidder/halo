import { Lang, LANGS, useI18n } from "../i18n";
import ScoreRing from "../ScoreRing";
import { COPY } from "./landing-copy";
import "./landing.css";

// What Collab reads from a video, as the hero's cards show it. The hooks are the creators' own
// words, so they keep their language; the tags follow the reader's.
const VIDEOS = [
  { hook: "Bu krem 90\u00a0000\u00a0soʻmga arziydimi?", score: 8, lang: "uz", tone: "lojuvard" },
  { hook: "5 daqiqada qozon kabob", score: 7, lang: "uz", tone: "nur" },
  { hook: "Утренний уход за 3 шага", score: 7, lang: "ru", tone: "paxta" },
  { hook: "Uzumdagi eng arzon quloqchin", score: 8, lang: "uz", tone: "firuza" },
  { hook: "Samarqandda bir kun", score: 9, lang: "uz", tone: "tun" },
];

const DRAFT =
  "Assalomu alaykum, Malika! Uydagi ertalabki parvarishingiz juda samimiy chiqqan. Noyabrda yangi SPF kremimiz uchun 2 ta Reels taklif qilmoqchimiz. Qiziqasizmi?";

function Wordmark({ onDark = false }: { onDark?: boolean }) {
  if (onDark) return <img src="/collab-wordmark-on-dark.svg" alt="Collab" />;
  return (
    <picture>
      <source srcSet="/collab-wordmark-on-dark.svg" media="(prefers-color-scheme: dark)" />
      <img src="/collab-wordmark.svg" alt="Collab" />
    </picture>
  );
}

function VideoCard({ video, tag, hookLabel }: { video: (typeof VIDEOS)[number]; tag: string; hookLabel: string }) {
  return (
    <div className={`l-vcard tone-${video.tone}`}>
      <span className="l-vchip">
        {hookLabel} {video.score}/10
      </span>
      <p className="l-vhook" lang={video.lang}>
        {video.hook}
      </p>
      <div className="l-vfoot">
        <span className="l-vtag">
          {tag} · {video.lang.toUpperCase()}
        </span>
        {/* the 8 frames Collab samples; the first 3 cover the hook */}
        <span className="l-frames" aria-hidden="true">
          {Array.from({ length: 8 }, (_, i) => (
            <i key={i} className={i < 3 ? "hi" : undefined} />
          ))}
        </span>
      </div>
    </div>
  );
}

export default function Landing() {
  const { lang, setLang, t } = useI18n();
  const c = COPY[lang];
  const e = c.evidence;

  return (
    <div className="landing">
      <header className="l-nav-wrap">
        <nav className="l-nav" aria-label="Collab">
          <a href="/" className="l-logo" aria-label="Collab">
            <Wordmark />
          </a>
          <div className="l-links">
            <a href="#brands">{c.nav.brands}</a>
            <a href="#creators">{c.nav.creators}</a>
            <a href="#how">{c.nav.how}</a>
            <a href="#faq">{c.nav.faq}</a>
          </div>
          <div className="l-actions">
            <select className="l-lang" aria-label={t("language")} value={lang} onChange={(ev) => setLang(ev.target.value as Lang)}>
              {LANGS.map((l) => (
                <option key={l.code} value={l.code}>
                  {l.label}
                </option>
              ))}
            </select>
            <a href="/app" className="l-login">
              {c.nav.login}
            </a>
            <a href="/app" className="button l-start">
              {c.nav.start}
            </a>
          </div>
        </nav>
      </header>

      <section className="l-hero">
        <h1 className="l-title">
          <span>{c.hero.line1}</span>
          <span>{c.hero.line2}</span>
        </h1>
        <p className="l-sub">{c.hero.sub}</p>
        <div className="l-ctas">
          <a className="button l-btn" href="/app">
            {c.hero.brief}
          </a>
          <a className="button l-btn outline" href="#creators">
            {c.hero.creator}
          </a>
        </div>
        <div className="l-videos">
          {VIDEOS.map((v, i) => (
            <VideoCard key={v.hook} video={v} tag={c.cardTags[i]} hookLabel={c.hook} />
          ))}
        </div>
      </section>

      <section id="how" className="l-section">
        <h2 className="l-h2">{c.how.title}</h2>
        <ol className="l-steps">
          {c.how.steps.map(([title, text], i) => (
            <li key={title}>
              <span className="l-step-num">{i + 1}</span>
              <h3>{title}</h3>
              <p>{text}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="l-section l-evidence">
        <div>
          <h2 className="l-h2">{e.title}</h2>
          <p className="l-lead">{e.text}</p>
          <ul className="l-checks">
            {e.points.map((p) => (
              <li key={p}>{p}</li>
            ))}
          </ul>
        </div>
        <article className="card starred l-sample">
          <div className="row between">
            <div>
              <h3>Malika ★</h3>
              <p className="muted small">{e.meta}</p>
            </div>
            <ScoreRing score={91} top />
          </div>
          <div className="row">
            <span className="pill l-example">{e.example}</span>
          </div>
          <ul className="reasons">
            {e.reasons.map((r) => (
              <li key={r}>{r}</li>
            ))}
          </ul>
          <ul className="risks">
            <li>{e.risk}</li>
          </ul>
          <span className="l-draft-label">{e.draftLabel}</span>
          <p className="l-draft" lang="uz">
            {DRAFT}
          </p>
        </article>
      </section>

      <section className="l-section l-audiences">
        <article id="brands" className="l-aud l-aud-brands">
          <h2 className="l-h2">{c.brands.title}</h2>
          <ul className="l-checks">
            {c.brands.points.map((p) => (
              <li key={p}>{p}</li>
            ))}
          </ul>
          <a className="button l-btn" href="/app">
            {c.brands.cta}
          </a>
        </article>
        <article id="creators" className="l-aud">
          <h2 className="l-h2">{c.creators.title}</h2>
          <ul className="l-checks">
            {c.creators.points.map((p) => (
              <li key={p}>{p}</li>
            ))}
          </ul>
        </article>
      </section>

      <section className="l-section">
        <ul className="l-facts">
          {c.facts.map((f) => (
            <li key={f}>{f}</li>
          ))}
        </ul>
      </section>

      <section id="faq" className="l-section l-faq">
        <h2 className="l-h2">{c.faq.title}</h2>
        {c.faq.items.map(([q, a]) => (
          <details key={q}>
            <summary>{q}</summary>
            <p>{a}</p>
          </details>
        ))}
      </section>

      <section className="l-final">
        <svg className="l-final-rings" viewBox="0 0 400 400" aria-hidden="true">
          <circle cx="200" cy="200" r="90" />
          <circle cx="200" cy="200" r="140" />
          <circle cx="200" cy="200" r="190" />
          <circle className="point" cx="299" cy="101" r="16" />
        </svg>
        <h2 className="l-h2">{c.final.title}</h2>
        <p>{c.final.sub}</p>
        <a className="button l-btn" href="/app">
          {c.final.cta}
        </a>
      </section>

      <footer className="l-footer">
        <div className="l-footer-inner">
          <div>
            <Wordmark onDark />
            <p>Biz koʻramiz. Siz tanlaysiz.</p>
          </div>
          <div className="l-footer-links">
            <a href="#how">{c.nav.how}</a>
            <a href="#faq">{c.nav.faq}</a>
            <a href="/app">{c.nav.login}</a>
          </div>
          <p className="l-rights">{c.footer.rights}</p>
        </div>
      </footer>
    </div>
  );
}
