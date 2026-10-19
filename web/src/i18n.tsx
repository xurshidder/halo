import { createContext, ReactNode, useContext, useEffect, useState } from "react";
import { api } from "./api";

export type Lang = "uz" | "ru" | "en";

// Shown in this order in the picker; Uzbek is the default.
export const LANGS: { code: Lang; label: string }[] = [
  { code: "uz", label: "Oʻzbekcha" },
  { code: "ru", label: "Русский" },
  { code: "en", label: "English" },
];

const en = {
  tab_briefs: "Briefs",
  tab_creators: "Creators",
  tab_brand: "Brand",
  add_brand_short: "+ Brand",
  brand_name_prompt: "Brand name",
  empty_title: "Start by adding your brand",
  empty_text: "Halo uses your brand's pillars, no-go topics and tone in every search and draft.",
  add_brand: "Add brand",
  language: "Language",
  loading: "Loading…",
  translating: "Translating…",
  translate_failed: "Couldn't translate, showing the original English.",

  new_brief: "New brief",
  brief_title_ph: "Title, e.g. Spring serum launch",
  brief_text_ph:
    "Describe the creator you need in plain words: who they talk to, what their videos look like, language, budget...",
  keep_watching: "Keep watching: search again every morning and send new matches to Telegram",
  find_creators: "Find creators",
  briefs: "Briefs",
  no_briefs: "No briefs yet.",
  pick_brief: "Pick or create a brief.",
  watching_videos: "Watching videos…",
  running_progress: "Halo is reading the brief and scoring creators…",
  search_again: "Search again",
  run_failed: "Run failed: {error}",
  no_matches: "No creators matched yet. Add more creators or loosen the brief.",
  outreach_draft: "Outreach draft ({language})",
  copied: "Copied",
  copy_message: "Copy message",
  star: "Star",
  unstar: "Unstar",
  mark_contacted: "Mark contacted",
  not_a_fit: "Not a fit",
  currency: "UZS",

  creators: "Creators",
  cancel: "Cancel",
  add: "+ Add",
  search_ph: "Search name or content…",
  topic_ph: "Topic",
  any_language: "Any language",
  pick_creator: "Pick a creator. Creators can also join through the Telegram bot with /join.",
  name_ph: "Name",
  city_ph: "City",
  price_ph: "Price per video, UZS",
  instagram_ph: "Instagram handle",
  youtube_ph: "YouTube handle, e.g. @channel",
  save_creator: "Save creator",
  refresh_videos: "Refresh videos",
  uploading: "Uploading…",
  upload_video: "Upload video",
  more_like_this: "More like this",
  quality: "Quality",
  hook: "Hook",
  brand_safety: "Brand safety",
  followers: "{count} followers",
  lookalikes: "Look-alikes",
  no_similar: "No similar creators yet.",
  videos_watched: "Videos Halo watched",
  no_videos: "No videos yet.",
  video: "Video {id}",
  hook_score: "Hook ({score}/10):",
  pacing: "{pace} pacing",
  quality_score: "quality {score}/10",
  authenticity_score: "authenticity {score}/10",

  brand_context: "Brand context",
  brand_context_note: "Loaded once. Every search, score and outreach draft runs against it.",
  brand_name: "Name",
  brand_sells: "What the brand sells, and to whom",
  pillars: "Pillars (one per line)",
  no_go: "No-go topics (one per line)",
  tone: "Tone of voice",
  tone_ph: "warm, simple, a bit playful",
  customer_languages: "Customer languages",
  past_campaigns: "Past campaigns: what worked, what didn't",
  save: "Save",
  saved: "Saved",
  telegram_alerts: "Telegram alerts",
  telegram_connected: "Connected. Halo posts new creator matches to your Telegram chat.",
  telegram_before: "Get new matches in Telegram: ",
  telegram_link: "open this link",
  telegram_after: " in the chat or group where your team works.",
};

type Key = keyof typeof en;

const uz: Record<Key, string> = {
  tab_briefs: "Briflar",
  tab_creators: "Blogerlar",
  tab_brand: "Brend",
  add_brand_short: "+ Brend",
  brand_name_prompt: "Brend nomi",
  empty_title: "Avval brendingizni qoʻshing",
  empty_text: "Halo har bir qidiruv va xabar loyihasida brendingiz tamoyillari, taqiqlangan mavzular va ohangiga tayanadi.",
  add_brand: "Brend qoʻshish",
  language: "Til",
  loading: "Yuklanmoqda…",
  translating: "Tarjima qilinmoqda…",
  translate_failed: "Tarjima qilib boʻlmadi, inglizcha asl matn koʻrsatilmoqda.",

  new_brief: "Yangi brif",
  brief_title_ph: "Nomi, masalan: Bahorgi serum taqdimoti",
  brief_text_ph:
    "Qanday bloger kerakligini oddiy soʻzlar bilan yozing: kimga gapiradi, videolari qanday, qaysi tilda, byudjet...",
  keep_watching: "Kuzatib borish: har kuni ertalab qayta qidirib, yangi mos blogerlarni Telegramga yuborish",
  find_creators: "Blogerlarni topish",
  briefs: "Briflar",
  no_briefs: "Hozircha brif yoʻq.",
  pick_brief: "Brifni tanlang yoki yangisini yarating.",
  watching_videos: "Videolar koʻrilmoqda…",
  running_progress: "Halo brifni oʻqib, blogerlarni baholamoqda…",
  search_again: "Qayta qidirish",
  run_failed: "Qidiruv xato bilan tugadi: {error}",
  no_matches: "Hozircha mos bloger topilmadi. Koʻproq bloger qoʻshing yoki brif shartlarini yumshating.",
  outreach_draft: "Xabar loyihasi ({language})",
  copied: "Nusxalandi",
  copy_message: "Xabarni nusxalash",
  star: "Belgilash",
  unstar: "Belgini olib tashlash",
  mark_contacted: "Bogʻlandik",
  not_a_fit: "Mos emas",
  currency: "soʻm",

  creators: "Blogerlar",
  cancel: "Bekor qilish",
  add: "+ Qoʻshish",
  search_ph: "Ism yoki kontent boʻyicha qidirish…",
  topic_ph: "Mavzu",
  any_language: "Istalgan til",
  pick_creator: "Blogerni tanlang. Blogerlar Telegram botga /join yozib oʻzlari ham qoʻshilishi mumkin.",
  name_ph: "Ism",
  city_ph: "Shahar",
  price_ph: "Bitta video narxi, soʻm",
  instagram_ph: "Instagram akkaunti",
  youtube_ph: "YouTube kanali, masalan: @kanal",
  save_creator: "Blogerni saqlash",
  refresh_videos: "Videolarni yangilash",
  uploading: "Yuklanmoqda…",
  upload_video: "Video yuklash",
  more_like_this: "Shunga oʻxshashlar",
  quality: "Sifat",
  hook: "Hook",
  brand_safety: "Brend xavfsizligi",
  followers: "{count} obunachi",
  lookalikes: "Oʻxshash blogerlar",
  no_similar: "Hozircha oʻxshash bloger yoʻq.",
  videos_watched: "Halo koʻrgan videolar",
  no_videos: "Hozircha video yoʻq.",
  video: "Video {id}",
  hook_score: "Hook ({score}/10):",
  pacing: "temp: {pace}",
  quality_score: "sifat {score}/10",
  authenticity_score: "samimiylik {score}/10",

  brand_context: "Brend haqida",
  brand_context_note: "Har bir qidiruv, baho va xabar loyihasi shu maʼlumotlarga tayanadi.",
  brand_name: "Nomi",
  brand_sells: "Brend nima sotadi va kimga",
  pillars: "Asosiy tamoyillar (har biri yangi qatorda)",
  no_go: "Taqiqlangan mavzular (har biri yangi qatorda)",
  tone: "Muloqot ohangi",
  tone_ph: "iliq, sodda, biroz oʻyinqaroq",
  customer_languages: "Mijozlar tillari",
  past_campaigns: "Oldingi kampaniyalar: nima ishladi, nima ishlamadi",
  save: "Saqlash",
  saved: "Saqlandi",
  telegram_alerts: "Telegram xabarnomalari",
  telegram_connected: "Ulangan. Halo yangi mos blogerlarni Telegram chatingizga yuboradi.",
  telegram_before: "Yangi mos blogerlarni Telegramda olish uchun ",
  telegram_link: "shu havolani",
  telegram_after: " jamoangiz ishlaydigan chat yoki guruhda oching.",
};

const ru: Record<Key, string> = {
  tab_briefs: "Брифы",
  tab_creators: "Блогеры",
  tab_brand: "Бренд",
  add_brand_short: "+ Бренд",
  brand_name_prompt: "Название бренда",
  empty_title: "Начните с добавления бренда",
  empty_text: "Halo учитывает ценности бренда, запретные темы и тон в каждом поиске и каждом черновике.",
  add_brand: "Добавить бренд",
  language: "Язык",
  loading: "Загрузка…",
  translating: "Переводим…",
  translate_failed: "Не удалось перевести, показан английский оригинал.",

  new_brief: "Новый бриф",
  brief_title_ph: "Название, например: Запуск весенней сыворотки",
  brief_text_ph:
    "Опишите простыми словами, какой блогер нужен: для кого он снимает, какие у него видео, язык, бюджет...",
  keep_watching: "Следить дальше: искать заново каждое утро и присылать новых подходящих блогеров в Telegram",
  find_creators: "Найти блогеров",
  briefs: "Брифы",
  no_briefs: "Брифов пока нет.",
  pick_brief: "Выберите бриф или создайте новый.",
  watching_videos: "Смотрим видео…",
  running_progress: "Halo читает бриф и оценивает блогеров…",
  search_again: "Искать заново",
  run_failed: "Поиск завершился с ошибкой: {error}",
  no_matches: "Подходящих блогеров пока нет. Добавьте блогеров или смягчите условия брифа.",
  outreach_draft: "Черновик сообщения ({language})",
  copied: "Скопировано",
  copy_message: "Скопировать сообщение",
  star: "В избранное",
  unstar: "Убрать из избранного",
  mark_contacted: "Связались",
  not_a_fit: "Не подходит",
  currency: "сум",

  creators: "Блогеры",
  cancel: "Отмена",
  add: "+ Добавить",
  search_ph: "Поиск по имени или контенту…",
  topic_ph: "Тема",
  any_language: "Любой язык",
  pick_creator: "Выберите блогера. Блогеры также могут присоединиться сами через Telegram-бота командой /join.",
  name_ph: "Имя",
  city_ph: "Город",
  price_ph: "Цена за видео, сум",
  instagram_ph: "Аккаунт в Instagram",
  youtube_ph: "YouTube-канал, например: @channel",
  save_creator: "Сохранить блогера",
  refresh_videos: "Обновить видео",
  uploading: "Загрузка…",
  upload_video: "Загрузить видео",
  more_like_this: "Похожие блогеры",
  quality: "Качество",
  hook: "Хук",
  brand_safety: "Безопасность для бренда",
  followers: "{count} подписчиков",
  lookalikes: "Похожие блогеры",
  no_similar: "Похожих блогеров пока нет.",
  videos_watched: "Видео, которые посмотрел Halo",
  no_videos: "Видео пока нет.",
  video: "Видео {id}",
  hook_score: "Хук ({score}/10):",
  pacing: "темп: {pace}",
  quality_score: "качество {score}/10",
  authenticity_score: "искренность {score}/10",

  brand_context: "О бренде",
  brand_context_note: "Каждый поиск, оценка и черновик сообщения опирается на эти данные.",
  brand_name: "Название",
  brand_sells: "Что продаёт бренд и кому",
  pillars: "Ценности бренда (каждая с новой строки)",
  no_go: "Запретные темы (каждая с новой строки)",
  tone: "Тон общения",
  tone_ph: "тёплый, простой, немного игривый",
  customer_languages: "Языки клиентов",
  past_campaigns: "Прошлые кампании: что сработало, а что нет",
  save: "Сохранить",
  saved: "Сохранено",
  telegram_alerts: "Уведомления в Telegram",
  telegram_connected: "Подключено. Halo присылает новых подходящих блогеров в ваш Telegram-чат.",
  telegram_before: "Чтобы получать новых подходящих блогеров в Telegram, ",
  telegram_link: "откройте эту ссылку",
  telegram_after: " в чате или группе, где работает ваша команда.",
};

const STRINGS: Record<Lang, Record<Key, string>> = { en, uz, ru };

// Fixed values from the API (statuses, risk levels, pacing...), looked up as "kind.value".
const VALUES: Record<Lang, Record<string, string>> = {
  en: { "lang.uz": "Uzbek", "lang.ru": "Russian", "lang.en": "English", "platform.manual": "uploaded" },
  uz: {
    "status.draft": "qoralama", "status.running": "ishlamoqda", "status.done": "tayyor", "status.failed": "xato",
    "status.pending": "navbatda", "status.analyzing": "tahlil qilinmoqda", "status.analyzed": "tahlil qilindi",
    "risk.low": "past", "risk.medium": "oʻrtacha", "risk.high": "yuqori", "risk.unknown": "nomaʼlum",
    "pace.slow": "sekin", "pace.medium": "oʻrtacha", "pace.fast": "tez",
    "energy.calm": "osoyishta", "energy.warm": "iliq", "energy.upbeat": "quvnoq", "energy.high-energy": "juda energik",
    "lang.uz": "oʻzbekcha", "lang.ru": "ruscha", "lang.en": "inglizcha",
    "platform.manual": "yuklangan",
  },
  ru: {
    "status.draft": "черновик", "status.running": "идёт поиск", "status.done": "готово", "status.failed": "ошибка",
    "status.pending": "в очереди", "status.analyzing": "анализируется", "status.analyzed": "проанализировано",
    "risk.low": "низкий", "risk.medium": "средний", "risk.high": "высокий", "risk.unknown": "неизвестно",
    "pace.slow": "медленный", "pace.medium": "средний", "pace.fast": "быстрый",
    "energy.calm": "спокойный", "energy.warm": "тёплый", "energy.upbeat": "бодрый", "energy.high-energy": "очень энергичный",
    "lang.uz": "узбекский", "lang.ru": "русский", "lang.en": "английский",
    "platform.manual": "загружено",
  },
};
const STORAGE_KEY = "halo.lang";

function savedLang(): Lang {
  try {
    const value = localStorage.getItem(STORAGE_KEY);
    if (value === "uz" || value === "ru" || value === "en") return value;
  } catch {
    // Storage can be blocked (private mode); fall back to the default.
  }
  return "uz";
}

type I18n = {
  lang: Lang;
  setLang: (lang: Lang) => void;
  t: (key: Key, vars?: Record<string, string | number>) => string;
  tv: (kind: string, value: string) => string;
  num: (n: number | null | undefined) => string;
};

const I18nContext = createContext<I18n | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(savedLang);

  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);

  const setLang = (next: Lang) => {
    setLangState(next);
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch {
      // Not remembered across visits, but the switch still works.
    }
  };
  const t = (key: Key, vars: Record<string, string | number> = {}) =>
    STRINGS[lang][key].replace(/\{(\w+)\}/g, (match, name) => (name in vars ? String(vars[name]) : match));
  const tv = (kind: string, value: string) => VALUES[lang][`${kind}.${value}`] ?? value;
  const num = (n: number | null | undefined) =>
    n == null ? "—" : new Intl.NumberFormat(lang, { notation: "compact" }).format(n);

  return <I18nContext.Provider value={{ lang, setLang, t, tv, num }}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18n {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useI18n must be used inside I18nProvider");
  return ctx;
}

// AI-written text (summaries, reasons, risks, tags) is stored in English. In Uzbek or Russian,
// each page asks the API to translate what it shows; the API translates every text once and
// keeps it, and this cache saves asking again while the app is open.
const translations = new Map<string, string>();
const inFlight = new Map<string, Promise<void>>();
const cacheKey = (lang: Lang, text: string) => `${lang}\u0000${text}`;
const CHUNK = 200;

function fetchTranslations(lang: Lang, texts: string[]): Promise<void> {
  const todo = texts.filter((text) => !translations.has(cacheKey(lang, text)) && !inFlight.has(cacheKey(lang, text)));
  for (let i = 0; i < todo.length; i += CHUNK) {
    const chunk = todo.slice(i, i + CHUNK);
    const request = api
      .translate(lang, chunk)
      .then(({ texts: out }) => out.forEach((result, j) => translations.set(cacheKey(lang, chunk[j]), result)))
      .finally(() => chunk.forEach((text) => inFlight.delete(cacheKey(lang, text))));
    chunk.forEach((text) => inFlight.set(cacheKey(lang, text), request));
  }
  const waiting = texts.map((text) => inFlight.get(cacheKey(lang, text))).filter((p): p is Promise<void> => !!p);
  return Promise.all(waiting).then(() => undefined);
}

export function useAiText(texts: (string | null | undefined)[]) {
  const { lang } = useI18n();
  const [status, setStatus] = useState<"idle" | "loading" | "failed">("idle");
  const [, setVersion] = useState(0);

  const wanted =
    lang === "en"
      ? []
      : [...new Set(texts.filter((t): t is string => !!t && t.trim() !== ""))].filter(
          (t) => !translations.has(cacheKey(lang, t)),
        );
  const signature = wanted.join("\u0001");

  useEffect(() => {
    if (wanted.length === 0) {
      setStatus("idle");
      return;
    }
    let live = true;
    setStatus("loading");
    fetchTranslations(lang, wanted)
      .then(() => {
        if (!live) return;
        setStatus("idle");
        setVersion((v) => v + 1);
      })
      .catch(() => live && setStatus("failed"));
    return () => {
      live = false;
    };
  }, [lang, signature]);

  const tr = (text: string) => (lang === "en" ? text : translations.get(cacheKey(lang, text)) ?? text);
  return { tr, translating: status === "loading", failed: status === "failed" };
}

export function AiTextStatus({ translating, failed }: { translating: boolean; failed: boolean }) {
  const { t } = useI18n();
  if (translating) return <p className="muted small">{t("translating")}</p>;
  if (failed) return <p className="muted small">{t("translate_failed")}</p>;
  return null;
}
