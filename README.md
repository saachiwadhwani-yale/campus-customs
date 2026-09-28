# Campus Customs

A Yale apparel shop with a product catalogue, accounts, a wishlist, and a chat
assistant (**Handsome Dan**) built with PydanticAI + FastAPI and a React + Vite
frontend.

## Project layout

```
hw4/
├── AI_prompts.md
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── frontend/                 # Vite React TypeScript app
├── backend/
│   ├── main.py               # FastAPI app — uvicorn main:app --reload --port 8000
│   ├── agent.py
│   ├── models.py
│   ├── tools.py
│   └── prompts/prompt.md
└── output/                   # harness.md, design.md, usability.md,
                              # app_check.html, app_check_images/, audit_trail.json
```

The database and product images are a **local-only data pack** (not in git):

```
hw4/data/
├── campus_customs.db
└── products/                 # images referenced by the catalogue
```

## Prerequisites

- Python 3.11+
- Node.js 18+ and npm

## 1. Set up the data pack

Place the provided data pack at `hw4/data/` so it contains `campus_customs.db` and
the `products/` image folder (see the layout above). These are git-ignored and must
be added manually.

## 2. Configure your environment

```bash
cp .env.example .env
```

Then edit `.env` and set your Portkey key (used for the chatbot's model calls):

```
PORTKEY_API_KEY=your-portkey-api-key-here
```

## 3. Run the backend (FastAPI)

From `hw4/`:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cd backend
uvicorn main:app --reload --port 8000
```

The API runs at http://localhost:8000 and serves the catalogue, accounts, chat, and
product images.

## 4. Run the frontend (Vite)

In a second terminal, from `hw4/frontend/`:

```bash
npm install
npm run dev
```

Open http://localhost:5173. The dev server proxies `/api` and `/media` to the
backend on port 8000, so both must be running.

## Notes

- **Chat** needs a valid `PORTKEY_API_KEY`. The rest of the site (browsing,
  accounts, wishlist) works without it.
- **Test account:** `test@campuscustoms.yale.edu` / `password`.
- The wishlist is stored in the browser (`localStorage`); chat history for
  logged-in users is stored in the database.
- Design and testing docs live in `output/` (`harness.md`, `design.md`,
  `usability.md`, `app_check.html`), and every chat run is logged to
  `output/audit_trail.json`.
