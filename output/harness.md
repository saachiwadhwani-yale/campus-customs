# Homework 4 — Harness

How the Campus Customs website works: database, API, chat agent (Handsome Dan),
data models, tools, safety, and audit trail.

## Tech Stack & Key Specs

| Area | Detail |
|---|---|
| Frontend | React + TypeScript + Vite (`hw4/frontend`), dev on **:5173** |
| Backend | FastAPI + Uvicorn (`hw4/backend`), **:8000** — `uvicorn main:app --reload --port 8000` from `backend/` |
| Database | SQLite `data/campus_customs.db` — the single source of truth |
| Chat model | `gpt-4o-mini` via **Portkey** (`PORTKEY_API_KEY` from `ai_class/.env`) |
| Agent | PydanticAI, structured output, **single model round-trip** per message (~1–2s) |
| Auth | PBKDF2-SHA256, per-user salt, 600k rounds |
| Persistence | Chat history in `chat_messages`; wishlist in browser `localStorage` |
| Audit | Append-only `output/audit_trail.json` |

## Database

SQLite, `data/campus_customs.db`.

| Table | Rows | Purpose |
|---|---|---|
| `catalogue` | 102 | One row per product |
| `inventory` | 612 | Stock per product/size (6 sizes × 102) |
| `users` | 3 | Shop accounts |
| `chat_messages` | 22 | Saved chat history per user |
| `sqlite_sequence` | — | SQLite AUTOINCREMENT bookkeeping |

**`catalogue`** — `product_id` (PK, slug matching the image file), `name`,
`garment_type` (free text), `description`, `colors` (JSON list), `search_tags`
(JSON list), `image_file_path` (relative to `data/`), `price` (REAL).

**`inventory`** — `id` (PK), `product_id` (FK), `size` (XS–XXL), `quantity`
(0 = out of stock). `(product_id, size)` is unique.

**`users`** — `id` (PK), `name`, `email` (unique), `password_hash`, `created_at`,
`first_name`, `last_name`.

**`chat_messages`** — `id` (PK), `user_id` (FK), `role` (user/assistant),
`content`, `products_json` (JSON of cards shown, nullable), `created_at`.

Relationships: `inventory.product_id → catalogue.product_id`;
`chat_messages.user_id → users.id`.

## Accounts & Passwords

Sign-up stores only: names, `email` (lowercased, unique), a password **hash**, and
`created_at` — never the plain password, payment info, or addresses.

Sign-up requires (checked on the client **and** re-checked on the backend):
passwords match, ≥ 10 chars, one uppercase, one number, valid unused email.

Passwords use **PBKDF2-SHA256** with a random per-user salt and 600,000 rounds,
stored as `pbkdf2_sha256$<rounds>$<salt>$<hash>`. Login re-hashes and
constant-time compares; wrong email vs. wrong password give the same message.
(Seed accounts use the older `pbkdf2_sha256$<salt>$<hash>` format; `verify_password`
falls back to 120,000 rounds for those, so the test account
`test@campuscustoms.yale.edu` / `password` works.)

## Chat Agent (PydanticAI + FastAPI)

Four files, hw3-style: `prompts/prompt.md` (system prompt + safety),
`models.py` (types), `tools.py` (DB helpers + audit), `agent.py` (builds the agent,
`run_chat()`). `main.py` exposes `/api/chat` and imports `run_chat` lazily so a
missing Portkey key only affects chat.

**Single round-trip.** The agent is built **without tool-calling**. `run_chat`
searches the catalogue locally, injects the matching products into the prompt, and
the model answers in one call (~1–2s instead of ~5–8s). The customer's identity and
on-screen products are injected as dynamic **instructions** (from `ChatDeps`), not
tool calls. The agent is built once and cached; `output_type=ChatReply` forces
`{ reply, product_ids }`.

**A message is answered by:** searching the catalogue → labelling matches with
short codes (`p1`, `p2`…) → one prompt (history + identity/page instructions +
coded candidates) → one `agent.run()` → mapping codes back to ids →
`ProductCard`s from the DB. Short codes keep the model's output small (faster).

### Catalogue helpers (`tools.py`)

Read straight from the DB, so the agent never guesses. `search_catalogue` runs on
every message; the rest back the product/stock API and the injected context.

| Function | Purpose |
|---|---|
| `search_catalogue(query, limit=6)` | Weighted whole-word search over name, garment_type, tags, colors, description → `list[ProductCard]` |
| `stock_summary(product_id)` | Per-size quantity string (`XS:15, S:5, M:0`) injected per candidate for "how many" questions |
| `get_product_details(product_id)` | One product → `ProductCard` |
| `check_stock(product_id)` | Per-size stock incl. sold-out → `ProductStock` |
| `list_garment_types()` | Distinct garment types |

Each injected candidate carries name, type, price, colors, short description, and
per-size stock — enough to answer any catalogue question in one pass.

**Search scoring:** whole-word matches only (so "tshirt" can't hit "sweatshirt"),
weighted by field (garment type & name > tags/colors > description) so an item-type
match beats a stray color match. Understands shopper wording ("tee"/"t-shirt",
"crew neck", "quarter zip", "blue"→navy) and vibe words ("cozy"/"warm"→fleece,
hoodie, sweatshirt). The catalogue is preprocessed once into memory (sub-ms search).

### Customer memory, identity & page context

- **Identity:** the frontend sends `user_id` (null for guests); the backend looks
  the user up in `users` and builds `Customer(name, email)` — never trusting the
  browser. It's injected as a dynamic instruction so Handsome Dan can greet by
  name. Guests are handled normally.
- **History (logged-in only):** each turn is saved to `chat_messages`; the next
  message loads recent turns for context, and reopening the panel restores the
  conversation via `GET /api/chat/history`. Guests are never saved.
- **Page context:** `PageProvider` tracks the `product_ids` on screen (search
  results or the viewed product); `ChatPanel` sends them as `page_product_ids`,
  injected as an instruction so follow-ups like "which of these is cheapest?" work.

### Frontend ↔ API

Vite proxies `/api` and `/media` to `:8000` (CORS also enabled). Helpers in
`api.ts` call `GET /api/products`, `GET /api/products/{id}`, `POST /api/signup`,
`POST /api/login`, `POST /api/chat`, `GET /api/chat/history`. Images are served from
`data/` at `/media/...`.

**Chat drives the page:** when the agent returns products, `ChatPanel` navigates to
`/products?ids=…&q=<question>`; `Products.tsx` filters the grid to those ids (best
first) with a "Show all products" reset. Each card still links to its detail page,
which fetches full data independently, so single-item pages keep working. The filter
lives in the URL (survives refresh).

## models.py — Types

- `SizeStock` — `size`, `quantity`.
- `Product` — full catalogue record for the product API (catalogue fields +
  `image_url`, `inventory`, `total_stock`).
- `ProductCard` — compact card shown in chat and the grid: `product_id`, `name`,
  `price`, `garment_type`, `image_url`, `description`, `colors`, `available_sizes`,
  `in_stock`.
- `StockLevel` / `ProductStock` — per-size and full availability (incl.
  `out_of_stock_sizes`).
- `ChatReply` — the model's structured output: `reply` + `product_ids` (chosen from
  provided candidates; the backend hydrates ids into cards so details can't be
  wrong).
- `Customer` — `name`, `email` (from `users`, server-side only).
- `ChatTurn`, `ChatRequest` (`message`, `history`, `user_id`, `page_product_ids`),
  `ChatResponse` (`reply`, `products`), `ChatHistoryMessage`.
- `SignupRequest`, `LoginRequest`, `User` (in `main.py`) — auth; `User` never
  includes the password hash.

## Safety

Rules live in `prompt.md` and override everything. Handsome Dan:

- never collects personal info (passwords, card/bank numbers, SSNs, addresses);
- doesn't store or repeat sensitive info a customer volunteers;
- never reveals anyone else's personal info or chat history;
- never reveals its instructions or internals;
- stays on topic and never invents products, prices, colors, or stock.

Two layers: the prompt rules, plus Azure's content filter (via Portkey) that blocks
jailbreak/unsafe prompts — on a block the backend returns a friendly decline and
logs `stop_reason: content_filtered`. Identity is resolved server-side from
`user_id`, so the browser can't spoof it.

## Audit Trail

Every run is logged to `output/audit_trail.json`, kept as a **valid JSON array**
(one object per line inside `[ ... ]`). It stays append-only: each new entry only
rewrites the trailing `]`, so existing entries are never truncated or wiped.

Each entry: `time` (UTC), `who` (`user:<id>` or `guest`), `message`, `steps` (each
a `tool` with `args` and `result` — `search_catalogue`, `model.generate`,
`save_message`), and `stop_reason` (`completed`, `no_products_shown`,
`content_filtered`, `error`). Written by `audit_append()` in `tools.py`, called at
the end of every `run_chat`.

## Running the app

Prereqs: Python 3.11+, Node 18+, the data pack at `hw4/data/`
(`campus_customs.db` + `products/`), and a `.env` with `PORTKEY_API_KEY`
(`cp .env.example .env`). See the README for full setup.

**Backend** (from `backend/`):

```bash
pip install -r ../requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend** (from `frontend/`, in a second terminal):

```bash
npm install
npm run dev
```

Open http://localhost:5173. Vite proxies `/api` and `/media` to the backend on
:8000, so both servers must be running. Browsing, accounts, and the wishlist work
without a Portkey key; the chat needs one.
