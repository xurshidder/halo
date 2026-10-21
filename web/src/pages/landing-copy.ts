import { Lang } from "../i18n";

// The landing page's words. Creator videos on the cards keep their own language; everything
// Collab says is in the reader's.
type Copy = {
  nav: { brands: string; creators: string; how: string; faq: string; login: string; start: string };
  hero: { line1: string; line2: string; sub: string; brief: string; creator: string };
  hook: string;
  cardTags: [string, string, string, string, string];
  how: { title: string; steps: [string, string][] };
  evidence: {
    title: string;
    text: string;
    points: string[];
    example: string;
    meta: string;
    reasons: string[];
    risk: string;
    draftLabel: string;
  };
  brands: { title: string; points: string[]; cta: string };
  creators: { title: string; points: string[] };
  facts: string[];
  faq: { title: string; items: [string, string][] };
  final: { title: string; sub: string; cta: string };
  footer: { rights: string };
};

export const COPY: Record<Lang, Copy> = {
  uz: {
    nav: { brands: "Brendlar uchun", creators: "Blogerlar uchun", how: "Qanday ishlaydi", faq: "Savollar", login: "Kirish", start: "Boshlash" },
    hero: {
      line1: "Biz koʻramiz.",
      line2: "Siz tanlaysiz.",
      sub: "Collab Instagram, YouTube va Telegramdagi blogerlarning videolarini koʻrib chiqadi va brendingizga mos kelganlarini tanlab beradi — sabablari va oʻzbek yoki rus tilidagi birinchi xabari bilan.",
      brief: "Brif yozish",
      creator: "Men blogerman",
    },
    hook: "Hook",
    cardTags: ["teri parvarishi", "taomlar", "parvarish", "texnika sharhi", "sayohat"],
    how: {
      title: "Qanday ishlaydi",
      steps: [
        ["Brif yozing", "Qanday bloger kerakligini oddiy soʻzlar bilan yozing: kimga gapiradi, videolari qanday, qaysi tilda, byudjet."],
        ["Collab videolarni koʻradi", "Har bir blogerning soʻnggi videolaridan kadrlar olib, hook, ohang, til, sifat va brend xavfsizligini baholaydi."],
        ["Roʻyxat va xabarlar", "Mos blogerlar baho va sabablari bilan saralanadi, har biriga birinchi xabar tayyor. Yangi mos blogerlar Telegramga keladi."],
      ],
    },
    evidence: {
      title: "Har bir tanlov — dalil bilan",
      text: "Collab obunachilar soniga emas, videolarga qaraydi. Har bir sabab aniq videoga ishora qiladi, xavflar ham ochiq aytiladi.",
      points: [
        "Sabablar videolarga tayanadi",
        "Spirtli ichimlik, qimor va siyosat kabi xavflar belgilanadi",
        "Xabar loyihasi blogerning tilida: oʻzbek yoki rus",
      ],
      example: "Namuna",
      meta: "instagram · 18\u00a0400\u00a0obunachi · 900\u00a0000\u00a0soʻm",
      reasons: [
        "Video 2, 3 va 4 — uyda, tabiiy yorugʻlikda olingan ertalabki parvarish rutinasi.",
        "Hook narxga eʼtibor beradi: «bu krem 90\u00a0000\u00a0soʻmga arziydimi?»",
      ],
      risk: "Videolarda hali SPF yoʻq: formatni sinab koʻrish kerak.",
      draftLabel: "Xabar loyihasi · oʻzbekcha",
    },
    brands: {
      title: "Brendlar uchun",
      points: [
        "Brifdan roʻyxatgacha bir necha daqiqa",
        "Jamoangiz qarorlari saqlanadi: tanlangan, rad etilgan, bogʻlanilgan",
        "Har kuni ertalab yangi mos blogerlar Telegramda",
        "Oʻzbek, rus va ingliz tillarida",
      ],
      cta: "Brif yozish",
    },
    creators: {
      title: "Blogerlar uchun",
      points: [
        "Telegram botimizga /join deb yozing va akkauntlaringizni yuboring",
        "Instagram akkauntingizni ulang yoki videolaringizni botga yuboring",
        "Sizga mos brendlar oʻzlari bogʻlanadi",
      ],
    },
    facts: ["Oʻzbek · Rus · Ingliz", "Narxlar soʻmda", "Instagram · YouTube · Telegram", "Xabarnomalar Telegramda"],
    faq: {
      title: "Savollar",
      items: [
        ["Collab videolarni qanday koʻradi?", "Har bir videodan 8 ta kadr oladi (3 tasi birinchi uch soniyadan — hook shu yerda), izohni va mavjud boʻlsa nutqni oʻqiydi va sunʼiy intellekt yordamida tahlil qiladi: nima boʻlyapti, kimga moʻljallangan, sifat, samimiylik va brend xavfsizligi."],
        ["Qaysi platformalar?", "Instagram (bloger akkauntini ulaganda), YouTube va Telegram botimizga yuborilgan videolar. TikTok Oʻzbekistonda bloklangan, shuning uchun u yoʻq."],
        ["Qaysi tillarda ishlaydi?", "Ilova oʻzbek, rus va ingliz tillarida. Xabar loyihalari blogerning tilida — oʻzbek (lotin) yoki rus tilida yoziladi."],
        ["Blogerga xabarni kim yuboradi?", "Siz. Collab xabar loyihasini tayyorlaydi, siz uni tahrirlab Telegram yoki Instagramda yuborasiz."],
      ],
    },
    final: { title: "Birinchi brifingizni yozing", sub: "Qanday bloger kerakligini yozing — qolganini Collab koʻradi.", cta: "Boshlash" },
    footer: { rights: "© 2026 Collab" },
  },
  ru: {
    nav: { brands: "Брендам", creators: "Блогерам", how: "Как это работает", faq: "Вопросы", login: "Войти", start: "Начать" },
    hero: {
      line1: "Мы смотрим.",
      line2: "Вы выбираете.",
      sub: "Collab смотрит видео блогеров в Instagram, YouTube и Telegram и подбирает тех, кто подходит вашему бренду, — с причинами и первым сообщением на узбекском или русском.",
      brief: "Написать бриф",
      creator: "Я блогер",
    },
    hook: "Хук",
    cardTags: ["уход за кожей", "еда", "уход", "обзоры техники", "путешествия"],
    how: {
      title: "Как это работает",
      steps: [
        ["Напишите бриф", "Опишите простыми словами, какой блогер нужен: для кого он снимает, какие у него видео, язык, бюджет."],
        ["Collab смотрит видео", "Берёт кадры из последних видео каждого блогера и оценивает хук, тон, язык, качество и безопасность для бренда."],
        ["Список и сообщения", "Подходящие блогеры ранжируются с оценкой и причинами, для каждого готово первое сообщение. Новые совпадения приходят в Telegram."],
      ],
    },
    evidence: {
      title: "Каждый выбор — с доказательствами",
      text: "Collab смотрит на видео, а не на число подписчиков. Каждая причина ссылается на конкретное видео, а риски названы прямо.",
      points: [
        "Причины опираются на видео",
        "Отмечает риски: алкоголь, азартные игры, политика",
        "Черновик сообщения — на языке блогера: узбекском или русском",
      ],
      example: "Пример",
      meta: "instagram · 18\u00a0400\u00a0подписчиков · 900\u00a0000\u00a0сум",
      reasons: [
        "Видео 2, 3 и 4 — утренний уход дома при естественном свете.",
        "Хук про цену: «стоит ли этот крем 90\u00a0000\u00a0сум?»",
      ],
      risk: "В видео пока нет SPF: формат нужно проверить.",
      draftLabel: "Черновик сообщения · узбекский",
    },
    brands: {
      title: "Брендам",
      points: [
        "От брифа до списка — за несколько минут",
        "Решения команды сохраняются: избранные, отклонённые, с кем связались",
        "Каждое утро — новые подходящие блогеры в Telegram",
        "На узбекском, русском и английском",
      ],
      cta: "Написать бриф",
    },
    creators: {
      title: "Блогерам",
      points: [
        "Напишите /join нашему Telegram-боту и отправьте свои аккаунты",
        "Подключите Instagram или присылайте видео боту",
        "Подходящие бренды свяжутся с вами сами",
      ],
    },
    facts: ["Узбекский · Русский · Английский", "Цены в сумах", "Instagram · YouTube · Telegram", "Уведомления в Telegram"],
    faq: {
      title: "Вопросы",
      items: [
        ["Как Collab смотрит видео?", "Берёт из каждого видео 8 кадров (3 — из первых трёх секунд, где хук), читает подпись и, если есть, речь и анализирует их с помощью ИИ: что происходит, для кого видео, качество, искренность и безопасность для бренда."],
        ["Какие платформы?", "Instagram (когда блогер подключает аккаунт), YouTube и видео, отправленные нашему Telegram-боту. TikTok в Узбекистане заблокирован, поэтому его нет."],
        ["На каких языках?", "Приложение — на узбекском, русском и английском. Черновики сообщений пишутся на языке блогера: узбекском (латиница) или русском."],
        ["Кто отправляет сообщение блогеру?", "Вы. Collab готовит черновик, вы правите его и отправляете в Telegram или Instagram."],
      ],
    },
    final: { title: "Напишите первый бриф", sub: "Опишите, какой блогер нужен, — остальное Collab посмотрит сам.", cta: "Начать" },
    footer: { rights: "© 2026 Collab" },
  },
  en: {
    nav: { brands: "For brands", creators: "For creators", how: "How it works", faq: "FAQ", login: "Log in", start: "Get started" },
    hero: {
      line1: "We watch.",
      line2: "You choose.",
      sub: "Collab watches creators' videos on Instagram, YouTube and Telegram and picks the ones who fit your brand, with reasons and a first message in Uzbek or Russian.",
      brief: "Write a brief",
      creator: "I'm a creator",
    },
    hook: "Hook",
    cardTags: ["skincare", "food", "skincare", "tech reviews", "travel"],
    how: {
      title: "How it works",
      steps: [
        ["Write a brief", "Describe the creator you need in plain words: who they talk to, what their videos look like, language, budget."],
        ["Collab watches the videos", "It samples frames from each creator's recent videos and rates the hook, tone, language, quality and brand safety."],
        ["Shortlist and messages", "Creators who fit are ranked with a score and reasons, each with a first message ready. New matches arrive in Telegram."],
      ],
    },
    evidence: {
      title: "Every pick comes with evidence",
      text: "Collab looks at videos, not follower counts. Every reason points to a specific video, and risks are named plainly.",
      points: [
        "Reasons are based on videos",
        "Flags risks like alcohol, gambling and politics",
        "Drafts in the creator's language: Uzbek or Russian",
      ],
      example: "Example",
      meta: "instagram · 18,400\u00a0followers · 900,000\u00a0soʻm",
      reasons: [
        "Videos 2, 3 and 4 are morning routines filmed at home in natural light.",
        "The hook is about price: “is this cream worth 90,000\u00a0soʻm?”",
      ],
      risk: "No SPF in her videos yet: test the format first.",
      draftLabel: "Outreach draft · Uzbek",
    },
    brands: {
      title: "For brands",
      points: [
        "From brief to shortlist in a few minutes",
        "Your team's decisions are kept: starred, rejected, contacted",
        "New matches in Telegram every morning",
        "In Uzbek, Russian and English",
      ],
      cta: "Write a brief",
    },
    creators: {
      title: "For creators",
      points: [
        "Send /join to our Telegram bot with your accounts",
        "Connect Instagram, or send your videos to the bot",
        "Brands that fit will contact you",
      ],
    },
    facts: ["Uzbek · Russian · English", "Prices in soʻm", "Instagram · YouTube · Telegram", "Alerts in Telegram"],
    faq: {
      title: "Questions",
      items: [
        ["How does Collab watch videos?", "It takes 8 frames from each video (3 from the first three seconds, where the hook is), reads the caption and, where available, the speech, and analyzes them with AI: what happens, who it's for, quality, authenticity and brand safety."],
        ["Which platforms?", "Instagram (once a creator connects their account), YouTube, and videos sent to our Telegram bot. TikTok is blocked in Uzbekistan, so it isn't included."],
        ["Which languages?", "The app is in Uzbek, Russian and English. Outreach drafts are written in the creator's language: Uzbek (Latin script) or Russian."],
        ["Who sends the message to the creator?", "You do. Collab drafts it; you edit it and send it on Telegram or Instagram."],
      ],
    },
    final: { title: "Write your first brief", sub: "Describe the creator you need. Collab watches the rest.", cta: "Get started" },
    footer: { rights: "© 2026 Collab" },
  },
};
