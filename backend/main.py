"""Campus Customs API.

Serves catalogue + inventory data from data/campus_customs.db, the product
images from data/products, user sign-up/login, and the PydanticAI shop chatbot.

Run from the backend/ folder:
    uvicorn main:app --reload --port 8000
"""

import hashlib
import hmac
import json
import re
import secrets
import sqlite3
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from models import (
    ChatHistoryMessage,
    ChatRequest,
    ChatResponse,
    Customer,
    Product,
    SizeStock,
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DATA_DIR / "campus_customs.db"
SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]

# Password hashing: PBKDF2-HMAC-SHA256 with a random per-user salt.
# Stored as "pbkdf2_sha256$<iterations>$<salt>$<hex hash>" so the iteration
# count can be raised later without breaking existing accounts.
PBKDF2_ITERATIONS = 600_000
MIN_PASSWORD_LENGTH = 10

app = FastAPI(title="Campus Customs API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# image_file_path in the db is relative to data/ (e.g. "products/x.jpg"),
# so mounting data/ at /media gives /media/products/x.jpg.
app.mount("/media", StaticFiles(directory=DATA_DIR), name="media")


class SignupRequest(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str
    confirm_password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class User(BaseModel):
    id: int
    first_name: str
    last_name: str
    name: str
    email: str
    created_at: str


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def load_inventory(conn: sqlite3.Connection) -> dict[str, list[SizeStock]]:
    rows = conn.execute("SELECT product_id, size, quantity FROM inventory").fetchall()
    by_product: dict[str, list[SizeStock]] = {}
    for r in rows:
        by_product.setdefault(r["product_id"], []).append(
            SizeStock(size=r["size"], quantity=r["quantity"])
        )
    for sizes in by_product.values():
        sizes.sort(key=lambda s: SIZE_ORDER.index(s.size) if s.size in SIZE_ORDER else 99)
    return by_product


def row_to_product(row: sqlite3.Row, inventory: list[SizeStock]) -> Product:
    return Product(
        product_id=row["product_id"],
        name=row["name"],
        garment_type=row["garment_type"],
        description=row["description"],
        colors=json.loads(row["colors"]),
        search_tags=json.loads(row["search_tags"]),
        image_file_path=row["image_file_path"],
        image_url=f"/media/{row['image_file_path']}",
        price=row["price"],
        inventory=inventory,
        total_stock=sum(s.quantity for s in inventory),
    )


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), PBKDF2_ITERATIONS
    ).hex()
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt}${digest}"


# Accounts seeded into the database before this app used a shorter format that
# didn't record the iteration count: "pbkdf2_sha256$<salt>$<hash>". Those seed
# rows were hashed with this many rounds, so we can still verify them.
LEGACY_ITERATIONS = 120_000


def verify_password(password: str, stored: str) -> bool:
    parts = stored.split("$")
    if len(parts) == 4 and parts[0] == "pbkdf2_sha256":
        _, iterations, salt, expected = parts
    elif len(parts) == 3 and parts[0] == "pbkdf2_sha256":
        # Legacy format with no iteration count stored
        _, salt, expected = parts
        iterations = LEGACY_ITERATIONS
    else:
        return False
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), int(iterations)
    ).hex()
    # Constant-time compare so timing doesn't leak how many characters matched
    return hmac.compare_digest(digest, expected)


def password_problems(password: str) -> list[str]:
    problems = []
    if len(password) < MIN_PASSWORD_LENGTH:
        problems.append(f"be at least {MIN_PASSWORD_LENGTH} characters long")
    if not re.search(r"[A-Z]", password):
        problems.append("contain an uppercase letter")
    if not re.search(r"\d", password):
        problems.append("contain a number")
    return problems


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def row_to_user(row: sqlite3.Row) -> User:
    return User(
        id=row["id"],
        first_name=row["first_name"] or "",
        last_name=row["last_name"] or "",
        name=row["name"],
        email=row["email"],
        created_at=row["created_at"],
    )


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/products", response_model=list[Product])
def list_products() -> list[Product]:
    with get_conn() as conn:
        inventory = load_inventory(conn)
        rows = conn.execute("SELECT * FROM catalogue ORDER BY name").fetchall()
    return [row_to_product(r, inventory.get(r["product_id"], [])) for r in rows]


@app.get("/api/products/{product_id}", response_model=Product)
def get_product(product_id: str) -> Product:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM catalogue WHERE product_id = ?", (product_id,)
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Product not found")
        inventory = load_inventory(conn).get(product_id, [])
    return row_to_product(row, inventory)


@app.post("/api/signup", response_model=User, status_code=201)
def signup(req: SignupRequest) -> User:
    first = req.first_name.strip()
    last = req.last_name.strip()
    email = req.email.strip().lower()

    if not first or not last:
        raise HTTPException(status_code=400, detail="First and last name are required.")
    if not EMAIL_RE.match(email):
        raise HTTPException(status_code=400, detail="Please enter a valid email address.")
    if req.password != req.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match.")
    problems = password_problems(req.password)
    if problems:
        raise HTTPException(
            status_code=400, detail="Password must " + ", ".join(problems) + "."
        )

    with get_conn() as conn:
        try:
            cur = conn.execute(
                "INSERT INTO users (name, email, password_hash, first_name, last_name) "
                "VALUES (?, ?, ?, ?, ?)",
                (f"{first} {last}", email, hash_password(req.password), first, last),
            )
        except sqlite3.IntegrityError:
            raise HTTPException(
                status_code=409, detail="An account with this email already exists."
            )
        row = conn.execute("SELECT * FROM users WHERE id = ?", (cur.lastrowid,)).fetchone()
    return row_to_user(row)


@app.post("/api/login", response_model=User)
def login(req: LoginRequest) -> User:
    email = req.email.strip().lower()
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    # Same message whether the email or the password is wrong, so the form
    # can't be used to discover which emails have accounts.
    if row is None or not verify_password(req.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    return row_to_user(row)


def _lookup_customer(user_id: int | None) -> tuple[Customer | None, int | None]:
    """Load the signed-in customer from the users table, if user_id is valid.

    Identity always comes from the database (looked up by id), never from the
    client, so the agent can trust the name and email it sees.
    """
    if user_id is None:
        return None, None
    with get_conn() as conn:
        row = conn.execute(
            "SELECT name, email FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    if row is None:
        return None, None  # unknown id -> treat as guest
    return Customer(name=row["name"], email=row["email"]), user_id


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    # Import lazily so a missing PORTKEY_API_KEY only affects chat, not the
    # rest of the API. The agent itself is built once and cached in agent.py.
    from agent import run_chat

    customer, user_id = _lookup_customer(req.user_id)
    try:
        return await run_chat(
            req.message,
            history=req.history,
            customer=customer,
            user_id=user_id,
            page_product_ids=req.page_product_ids,
        )
    except Exception:  # keep the panel usable if the model call fails
        return ChatResponse(
            reply=(
                "Sorry, I'm having trouble right now and can't answer that. "
                "Please try again in a moment."
            )
        )


@app.get("/api/chat/history", response_model=list[ChatHistoryMessage])
def chat_history(user_id: int) -> list[ChatHistoryMessage]:
    """Return a logged-in customer's saved chat history so the panel can restore it."""
    from tools import load_history_messages

    customer, resolved = _lookup_customer(user_id)
    if resolved is None:
        return []
    return load_history_messages(resolved)
