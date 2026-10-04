"""Helpers and agent tools for the Campus Customs chatbot.

Everything the agent needs to read the shop's data lives here:
  * loading the shared Portkey key and the system prompt,
  * reading products and stock from the SQLite database,
  * the tool functions the agent can call while answering a customer.

The database is the single source of truth — the model is never trusted to
remember prices or stock, it asks these tools instead.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from models import ChatHistoryMessage, ChatTurn, ProductCard, ProductStock, StockLevel

ROOT = Path(__file__).resolve().parent
PROMPT_PATH = ROOT / "prompts" / "prompt.md"
DATA_DIR = ROOT.parent / "data"
DB_PATH = DATA_DIR / "campus_customs.db"
# Append-only audit trail of agent activity (JSON Lines). Never truncated or rewritten.
AUDIT_PATH = ROOT.parent / "output" / "audit_trail.json"

SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]
# Words on almost every product, so they carry no signal when searching.
STOP_WORDS = {"yale", "the", "a", "an", "of", "and", "with", "for", "do", "you", "have"}


# --------------------------------------------------------------------------
# Environment + prompt
# --------------------------------------------------------------------------


def load_env() -> None:
    """Load env vars from the first .env found, later paths overriding earlier.

    Checks the shared ai_class/.env, then hw4/.env (the one described in the
    README / .env.example), then backend/.env.
    """
    for env_path in (ROOT.parent.parent / ".env", ROOT.parent / ".env", ROOT / ".env"):
        if not env_path.exists():
            continue
        for raw_line in env_path.read_text().splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ[key.strip()] = value.strip().strip("\"'")


def load_prompt() -> str:
    """Return the full system prompt text from prompts/prompt.md."""
    return PROMPT_PATH.read_text().strip()


def model_name() -> str:
    return os.environ.get("PORTKEY_MODEL", "gpt-4o-mini")


# --------------------------------------------------------------------------
# Database access
# --------------------------------------------------------------------------


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _ordered_stock(sizes: list[sqlite3.Row]) -> list[tuple[str, int]]:
    ordered = sorted(
        sizes, key=lambda s: SIZE_ORDER.index(s["size"]) if s["size"] in SIZE_ORDER else 99
    )
    return [(s["size"], s["quantity"]) for s in ordered]


def _row_to_card(row: sqlite3.Row, sizes: list[sqlite3.Row]) -> ProductCard:
    stock = _ordered_stock(sizes)
    in_stock_sizes = [size for size, qty in stock if qty > 0]
    return ProductCard(
        product_id=row["product_id"],
        name=row["name"],
        price=row["price"],
        garment_type=row["garment_type"],
        image_url=f"/media/{row['image_file_path']}",
        description=row["description"],
        colors=json.loads(row["colors"]),
        available_sizes=in_stock_sizes,
        stock_by_size=dict(stock),
        in_stock=bool(in_stock_sizes),
    )


def _load_cards(where: str = "", params: tuple = ()) -> list[ProductCard]:
    with _get_conn() as conn:
        rows = conn.execute(f"SELECT * FROM catalogue {where}", params).fetchall()
        inv: dict[str, list[sqlite3.Row]] = {}
        for s in conn.execute("SELECT product_id, size, quantity FROM inventory"):
            inv.setdefault(s["product_id"], []).append(s)
    return [_row_to_card(r, inv.get(r["product_id"], [])) for r in rows]


def get_product_card(product_id: str) -> ProductCard | None:
    cards = _load_cards("WHERE product_id = ?", (product_id,))
    return cards[0] if cards else None


def cards_for_ids(product_ids: list[str]) -> list[ProductCard]:
    """Resolve the ids the agent chose into ProductCards, preserving order."""
    by_id = {c.product_id: c for c in _load_cards()}
    return [by_id[pid] for pid in product_ids if pid in by_id]


# --------------------------------------------------------------------------
# Customer memory (chat history)
# --------------------------------------------------------------------------


def save_message(
    user_id: int, role: str, content: str, products: list[ProductCard] | None = None
) -> None:
    """Persist one chat message for a logged-in user in the chat_messages table."""
    products_json = (
        json.dumps([p.model_dump() for p in products]) if products else None
    )
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content, products_json) "
            "VALUES (?, ?, ?, ?)",
            (user_id, role, content, products_json),
        )


def load_history_turns(user_id: int, limit: int = 12) -> list[ChatTurn]:
    """Return a user's most recent turns (oldest first) for conversation context."""
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT role, content FROM chat_messages WHERE user_id = ? "
            "ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    return [ChatTurn(role=r["role"], content=r["content"]) for r in reversed(rows)]


def load_history_messages(user_id: int, limit: int = 40) -> list[ChatHistoryMessage]:
    """Return a user's saved messages (oldest first) for restoring the chat panel."""
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT role, content, products_json FROM chat_messages WHERE user_id = ? "
            "ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    messages: list[ChatHistoryMessage] = []
    for r in reversed(rows):
        products: list[ProductCard] = []
        if r["products_json"]:
            try:
                # Parse defensively: older seeded rows use a richer product shape;
                # ProductCard ignores extra fields and fills in defaults.
                products = [
                    ProductCard.model_validate(p) for p in json.loads(r["products_json"])
                ]
            except Exception:
                products = []
        messages.append(
            ChatHistoryMessage(role=r["role"], content=r["content"], products=products)
        )
    return messages


# --------------------------------------------------------------------------
# Append-only audit trail
# --------------------------------------------------------------------------


def audit_append(record: dict) -> None:
    """Append one agent-activity record to the audit trail as valid JSON.

    The file is always a valid JSON array: `[\\n<obj>\\n...<obj>\\n]\\n`, one object
    per line. The writer always ends the file with the exact 3 bytes `\\n]\\n`, so an
    append just truncates those 3 bytes and writes `,\\n<obj>\\n]\\n`. This never
    scans the content for brackets (tool results may contain `}`/`]`), and never
    wipes existing entries — the trail is permanent. Each entry records the time,
    the tool/step name(s) with their args and results, and the stop reason.
    """
    entry = {"time": datetime.now(timezone.utc).isoformat(), **record}
    line = json.dumps(entry, ensure_ascii=False)
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # First entry (or empty file): start a fresh array.
    if not AUDIT_PATH.exists() or AUDIT_PATH.stat().st_size == 0:
        AUDIT_PATH.write_text(f"[\n{line}\n]\n", encoding="utf-8")
        return

    with open(AUDIT_PATH, "rb+") as f:
        size = f.seek(0, os.SEEK_END)
        f.seek(max(0, size - 3))
        if f.read() == b"\n]\n":
            # Normal case: drop the trailing "\n]\n" and append the new object.
            f.seek(size - 3)
            f.truncate()
            f.write(f",\n{line}\n]\n".encode("utf-8"))
            return

    # Unexpected format (older JSONL, or a file corrupted by an earlier writer):
    # rebuild a clean, valid array from whatever entries can be recovered.
    existing = _parse_legacy_entries(AUDIT_PATH)
    existing.append(entry)
    body = ",\n".join(json.dumps(e, ensure_ascii=False) for e in existing)
    AUDIT_PATH.write_text(f"[\n{body}\n]\n", encoding="utf-8")


def _parse_legacy_entries(path: Path) -> list[dict]:
    """Recover entries from an older JSON-Lines audit file."""
    entries: list[dict] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        s = raw.strip().rstrip(",")
        if not s or s in ("[", "]"):
            continue
        try:
            entries.append(json.loads(s))
        except Exception:
            pass
    return entries


# --------------------------------------------------------------------------
# Agent tools
# --------------------------------------------------------------------------


# Field weights: a customer's words usually name the *kind* of garment first
# ("crewneck", "hoodie", "t-shirt"), so garment_type and name matter most; color
# and tags next; the long description last. This is what stops a color word alone
# ("blue") from outranking a clear garment-type match ("crewneck").
FIELD_WEIGHTS = {"garment_type": 6, "name": 4, "search_tags": 3, "colors": 3, "description": 1}

# Colors customers say vs. how the catalogue writes them (Yale items are "navy",
# but shoppers ask for "blue"; "gray" is spelled both ways).
COLOR_SYNONYMS = {
    "blue": ["blue", "navy"],
    "navy": ["navy", "blue"],
    "gray": ["gray", "grey"],
    "grey": ["grey", "gray"],
    "maroon": ["maroon", "burgundy"],
    "burgundy": ["burgundy", "maroon"],
}

# Multi-word / alternate spellings normalized to a single token BEFORE tokenizing,
# so "t-shirt", "tee", "crew neck" and "quarter zip" match the catalogue wording.
_QUERY_NORMALIZERS = [
    (re.compile(r"\bt[\s-]?shirts?\b"), " tshirt "),
    (re.compile(r"\btees?\b"), " tshirt "),
    (re.compile(r"\bcrew[\s-]?necks?\b"), " crewneck "),
    (re.compile(r"\bquarter[\s-]?zips?\b|\b1/4[\s-]?zips?\b|\bqtr[\s-]?zips?\b"), " quarterzip "),
    (re.compile(r"\bhood(?:ies|y)?\b"), " hoodie "),
    (re.compile(r"\bsweat\s?shirts?\b"), " sweatshirt "),
]

# Query tokens whose catalogue wording differs, matched against the collapsed
# (punctuation-stripped) field text so e.g. "tshirt" matches "t-shirt".
_TOKEN_SYNONYMS = {
    "tshirt": ["tshirt", "t-shirt", "tee"],
    "crewneck": ["crewneck", "crew neck"],
    "quarterzip": ["quarterzip", "quarter-zip", "quarter zip", "1/4 zip"],
    "hoodie": ["hoodie", "hooded", "hood"],
    # "Vibe" words shoppers use → the warm layers they usually mean, so
    # descriptive searches ("something cozy", "warm for a tailgate") still match.
    "cozy": ["sweatshirt", "hoodie", "fleece", "crewneck"],
    "comfy": ["sweatshirt", "hoodie", "fleece", "crewneck"],
    "warm": ["fleece", "jacket", "hoodie", "sweatshirt"],
    "cold": ["fleece", "jacket", "hoodie", "sweatshirt"],
    "tailgate": ["hoodie", "sweatshirt", "fleece", "jacket"],
    "layer": ["fleece", "quarter", "sweatshirt", "jacket"],
}


# Cached, preprocessed catalogue for search — built once, reused every request.
_SEARCH_CORPUS: list[dict] | None = None


def _search_corpus() -> list[dict]:
    global _SEARCH_CORPUS
    if _SEARCH_CORPUS is not None:
        return _SEARCH_CORPUS

    with _get_conn() as conn:
        rows = conn.execute("SELECT * FROM catalogue").fetchall()
        inv: dict[str, list[sqlite3.Row]] = {}
        for s in conn.execute("SELECT product_id, size, quantity FROM inventory"):
            inv.setdefault(s["product_id"], []).append(s)

    corpus: list[dict] = []
    for order, r in enumerate(rows):
        sizes = inv.get(r["product_id"], [])
        ordered = sorted(
            sizes, key=lambda s: SIZE_ORDER.index(s["size"]) if s["size"] in SIZE_ORDER else 99
        )
        stock = [(s["size"], s["quantity"]) for s in ordered]
        in_stock = [s["size"] for s in sizes if s["quantity"] > 0]
        in_stock.sort(key=lambda s: SIZE_ORDER.index(s) if s in SIZE_ORDER else 99)
        colors = json.loads(r["colors"])
        tags = json.loads(r["search_tags"])
        fields = {
            "garment_type": r["garment_type"],
            "name": r["name"],
            "search_tags": " ".join(tags),
            "colors": " ".join(colors),
            "description": r["description"],
        }
        corpus.append(
            {
                "order": order,
                "card": ProductCard(
                    product_id=r["product_id"],
                    name=r["name"],
                    price=r["price"],
                    garment_type=r["garment_type"],
                    image_url=f"/media/{r['image_file_path']}",
                    description=r["description"],
                    colors=colors,
                    available_sizes=in_stock,
                    stock_by_size=dict(stock),
                    in_stock=bool(in_stock),
                ),
                # Precomputed per weighted field: the set of whole words used for
                # matching (no substrings, so "tshirt" can't hit "sweatshirt").
                "words": {f: set(re.findall(r"[a-z0-9]+", v.lower())) for f, v in fields.items()},
                # Exact per-size quantities, so the chat can report inventory levels.
                "stock": stock,
            }
        )
    _SEARCH_CORPUS = corpus
    return _SEARCH_CORPUS


def stock_summary(product_id: str) -> str:
    """Compact per-size inventory string, e.g. 'XS:15, S:5, M:0, L:8'."""
    for entry in _search_corpus():
        if entry["card"].product_id == product_id:
            return ", ".join(f"{size}:{qty}" for size, qty in entry["stock"]) or "no sizes"
    return "unknown"


def _term_variants(token: str) -> list[str]:
    """All strings a query token should match on (singular, synonyms, colors)."""
    variants = {token}
    if len(token) > 3 and token.endswith("s"):
        variants.add(token[:-1])
    for base in list(variants):
        variants.update(_TOKEN_SYNONYMS.get(base, []))
        variants.update(COLOR_SYNONYMS.get(base, []))
    return list(variants)


def _normalize_query(query: str) -> list[str]:
    q = query.lower()
    for pattern, replacement in _QUERY_NORMALIZERS:
        q = pattern.sub(replacement, q)
    return [w for w in re.findall(r"[a-z0-9]+", q) if w not in STOP_WORDS]


def _word_in(word: str, words: set[str]) -> bool:
    """Whole-word match tolerant of simple singular/plural differences."""
    if word in words:
        return True
    if len(word) > 3 and word.endswith("s") and word[:-1] in words:
        return True
    if (word + "s") in words:
        return True
    return False


def _variant_matches_field(variant: str, words: set[str]) -> bool:
    """Does a query-term variant match one product field?

    Everything is matched on WHOLE words, never substrings, so "tshirt" can't hit
    "swea-tshirt" and "tee" can't hit "canteen". Multi-word variants (e.g.
    "t-shirt", "crew neck", "quarter-zip") match only when every part appears as a
    word, which is how catalogue types like "short-sleeve t-shirt" are written.
    """
    parts = [p for p in re.split(r"[\s-]+", variant.lower()) if p]
    if not parts:
        return False
    if len(parts) > 1:
        return all(_word_in(p, words) for p in parts)
    return _word_in(parts[0], words)


def search_catalogue(query: str, limit: int = 6) -> list[ProductCard]:
    """Search the shop's catalogue for products matching a customer's request.

    Scores each product by how well the customer's words match its garment type,
    name, tags, colors and description — with garment type and name weighted most
    heavily — so a clear item-type match ("crewneck") beats a stray color match
    ("blue"). Understands common shopper wording: "tee"/"t-shirt", "crew neck",
    "quarter zip", and "blue" for navy. Use this whenever a customer asks what you
    sell or looks for something specific (e.g. "navy hoodies", "blue crew necks",
    "baseball shirts").
    """
    corpus = _search_corpus()
    tokens = _normalize_query(query)
    if not tokens:
        return [entry["card"] for entry in corpus[:limit]]

    token_variants = [_term_variants(t) for t in tokens]

    scored: list[tuple[int, int, ProductCard]] = []
    for entry in corpus:
        score = 0
        for variants in token_variants:
            for field, weight in FIELD_WEIGHTS.items():
                words = entry["words"][field]
                if any(_variant_matches_field(v, words) for v in variants):
                    score += weight
                    break  # count each field at most once per token
        if score:
            scored.append((score, entry["order"], entry["card"]))

    # Highest score first; ties keep catalogue order for stable results.
    scored.sort(key=lambda t: (-t[0], t[1]))
    return [card for _, _, card in scored[:limit]]


def get_product_details(product_id: str) -> ProductCard | str:
    """Get full details for one product by its product_id.

    Use this after `search_catalogue` when a customer asks about a specific
    item's price, colors or which sizes are in stock.
    """
    card = get_product_card(product_id)
    if card is None:
        return f"No product found with id '{product_id}'."
    return card


def check_stock(product_id: str) -> ProductStock | str:
    """Get exact, up-to-date stock for one product, size by size.

    Looks the product up by its `product_id` and reads its `inventory` rows
    from the database. Use this whenever a customer asks whether an item — or a
    specific size — is available. Returns each size with its quantity and
    whether it's in stock, plus lists of the in-stock and sold-out sizes, so
    you can tell the customer exactly what they can buy. Never state stock you
    did not get from this tool.
    """
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT product_id, name, price FROM catalogue WHERE product_id = ?",
            (product_id,),
        ).fetchone()
        if row is None:
            return f"No product found with id '{product_id}'."
        size_rows = conn.execute(
            "SELECT size, quantity FROM inventory WHERE product_id = ?", (product_id,)
        ).fetchall()

    ordered = sorted(
        size_rows,
        key=lambda s: SIZE_ORDER.index(s["size"]) if s["size"] in SIZE_ORDER else 99,
    )
    sizes = [
        StockLevel(size=s["size"], quantity=s["quantity"], in_stock=s["quantity"] > 0)
        for s in ordered
    ]
    available = [s.size for s in sizes if s.in_stock]
    sold_out = [s.size for s in sizes if not s.in_stock]
    return ProductStock(
        product_id=row["product_id"],
        name=row["name"],
        price=row["price"],
        total_stock=sum(s.quantity for s in sizes),
        in_stock=bool(available),
        sizes=sizes,
        available_sizes=available,
        out_of_stock_sizes=sold_out,
    )


def list_garment_types() -> list[str]:
    """List the kinds of garments the shop carries (hoodies, tees, etc.).

    Use this when a customer asks broadly what types of clothing are available.
    """
    with _get_conn() as conn:
        rows = conn.execute("SELECT DISTINCT garment_type FROM catalogue").fetchall()
    return sorted({r["garment_type"].lower() for r in rows})
