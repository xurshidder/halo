# Halo

Halo is an AI coworker for influencer marketing in Uzbekistan. It watches creators' videos, learns each brand's context, and turns a plain-language brief into a ranked shortlist of creators, each with reasons and an outreach draft written in Uzbek or Russian. New matches are posted to the brand's Telegram chat.

It follows the architecture of [Kuli](https://www.ycombinator.com/companies/kuli) (YC Spring 2026), adapted to the Uzbek market.

## Stack

| Layer | Kuli | Halo | Why the change |
|---|---|---|---|
| Backend | Python, FastAPI | Python 3.13, FastAPI | Same |
| Agent framework | LangGraph | LangGraph | Same |
| Database | PostgreSQL (Supabase) + Redis | PostgreSQL 16 + pgvector + Redis | Supabase is Postgres; point `HALO_DATABASE_URL` at it any time |
| Cloud | Azure | Docker Compose, deploy anywhere | Cloud choice deferred |
| Frontend | TypeScript, React | TypeScript, React (Vite) | Same |
| AI models | OpenAI, Anthropic, Google | Claude via the official Anthropic SDK | One provider, structured outputs everywhere |
| Video sources | TikTok, Instagram | Instagram, YouTube, videos sent to Telegram | TikTok is blocked in Uzbekistan |
| Alerts | Slack | Telegram bot | Uzbek teams work in Telegram |

## How it works

```
creator accounts ──► ingest (Instagram / YouTube / Telegram uploads)
                        │
                        ▼
        video ──► ffmpeg: 8 frames (3 in the first 3 s for the hook) + audio
                        │            └─► speech-to-text (optional)
                        ▼
                Claude: hook, pacing, setting, tone, topics, languages,
                quality, authenticity, brand-safety flags  ──► creator profile

brief ──► scout agent (LangGraph)
          load ─► plan ─► retrieve ─► score ─► rank ─► draft ─► save ─► notify
          Claude   SQL + pgvector     Claude         Claude          Telegram
```

- **Brand context** (pillars, no-go topics, tone, past campaigns) is loaded once and sent in a cached system prompt for every score and draft.
- **Standing briefs** search again every morning (09:00 Tashkent) and push only new matches, like Kuli's "keeps watching".
- **Look-alikes**: star a creator, then "More like this" finds creators with similar content (vector search when Voyage embeddings are on, topic overlap otherwise).
- **Hourly routine** re-syncs creators whose accounts were not synced in the last 24 hours and analyzes new videos.
- Re-running a brief refreshes scores but keeps your team's decisions (starred, rejected, contacted) and edited messages.
- **Languages**: the web app is in Uzbek (default), Russian or English. Halo writes analyses, reasons and risks in English; when someone opens a page in Uzbek or Russian, the API translates that page's AI text with Claude once and keeps it (`translations` table), so later views cost nothing. The first view of a page in a language costs about $0.01–0.05.

## Run it

```bash
cp .env.example .env        # add ANTHROPIC_API_KEY at minimum
docker compose up --build   # web on http://localhost:8080, API on :8000
docker compose --profile bot up -d bot   # once HALO_TELEGRAM_BOT_TOKEN is set
```

Demo data (made-up creators and a finished brief), to explore the UI without keys:

```bash
docker compose exec api python -m scripts.seed_demo
```

### Local development

Needs Python 3.13 with [uv](https://docs.astral.sh/uv/), Node 22, PostgreSQL 16 with pgvector, Redis and ffmpeg.

```bash
cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn halo.api.main:app --reload     # API
uv run arq halo.worker.WorkerSettings         # worker
uv run python -m halo.bot.main                # Telegram bot (optional)
uv run pytest                                 # tests (uses the halo_test database)

cd ../web
npm install
npm run dev                                   # http://localhost:5173, proxies /api to :8000
```

The tests expect a database at `HALO_DATABASE_URL` (default in `tests/conftest.py`: `halo_test` on a local socket, port 5433). They use a stand-in for Claude, so they need no API key.

## Keys and accounts

| Key | Needed for | Required |
|---|---|---|
| `ANTHROPIC_API_KEY` (or `HALO_ANTHROPIC_API_KEY`, which wins if both are set) | Video analysis, brief planning, scoring, outreach drafts | Yes |
| `HALO_YOUTUBE_API_KEY` | Pulling YouTube channels | For YouTube |
| Instagram token per creator | Pulling a creator's own Reels (Instagram API with Instagram Login) | For Instagram |
| `HALO_TELEGRAM_BOT_TOKEN` | Creator sign-up via `/join`, brand alerts | For Telegram |
| `HALO_ELEVENLABS_API_KEY` | Transcribing speech | Optional |
| `HALO_VOYAGE_API_KEY` | Vector search and look-alikes | Optional |

## Costs

Video analysis is the expensive step: about 8 frames plus a transcript per video, about **$0.06 per video** on Claude Opus 5.5 (measured on 13–15 second vertical videos: about 12,700 input and 500–760 output tokens). 1,000 creators × 10 videos is about $600. Scoring a brief costs one call per candidate (40 by default, $0.013–0.028 each), plus one draft (about $0.013) per creator who joins the shortlist; re-runs keep existing drafts instead of writing new ones. Every Claude call logs its token usage (`claude <Step> ... input=… cache_write=… cache_read=… output=…`) in the worker output.

## Things to know before launch

- **Instagram:** a Meta app with `instagram_business_basic` (and `instagram_business_manage_insights` for views) must pass app review. Until then, creators can send videos to the Telegram bot.
- **YouTube:** the API gives no video file, so YouTube videos are judged from the thumbnail and YouTube's three auto-generated stills, plus title and description.
- **Telegram:** bots can download files up to 20 MB.
- **Uzbek speech-to-text** quality varies between providers. Test on real mixed Uzbek/Russian audio before relying on transcripts.
- **Data law:** since the March 2026 amendment, only biometric/genetic data and telecom subscriber data must stay in Uzbekistan. Other personal data can go abroad with safeguards. Check with a lawyer before choosing where to host.
- **Refusal fallbacks** are enabled on every Claude call (`fallbacks: "default"`): if the model declines on a policy category, the API retries on a fallback model inside the same call.

## Layout

```
backend/
  halo/
    ai/          Claude wrapper, video analysis, embeddings
    agent/       scout agent (LangGraph) and its prompts
    api/         FastAPI app and routes
    bot/         Telegram bot, alerts, signed brand links
    media/       ffmpeg frames/audio, downloads, speech-to-text
    services/    ingest, analyze, creator profiles, look-alikes
    sources/     Instagram and YouTube connectors
    models.py    database models     worker.py  background jobs and routines
  migrations/    Alembic
  scripts/       demo data
  tests/
web/             React + TypeScript app
```
