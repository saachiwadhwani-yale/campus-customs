"""Structured types shared by the API (main.py) and the chat agent.

Split into three groups:
  * Catalogue types  — how a product is served over the API.
  * Chat agent types — the agent's structured output and the product cards it
    shows the customer.
  * Request/response types — the shapes the frontend sends and receives.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

# --------------------------------------------------------------------------
# Catalogue types
# --------------------------------------------------------------------------


class SizeStock(BaseModel):
    size: str
    quantity: int


class Product(BaseModel):
    """A full catalogue record, used by the /api/products endpoints."""

    product_id: str
    name: str
    garment_type: str
    description: str
    colors: list[str]
    search_tags: list[str]
    image_file_path: str
    image_url: str
    price: float
    inventory: list[SizeStock]
    total_stock: int


# --------------------------------------------------------------------------
# Chat agent types
# --------------------------------------------------------------------------


class ProductCard(BaseModel):
    """A compact product summary the chatbot can show alongside its reply.

    Built from authoritative database rows (never invented by the model) so the
    price, image and stock are always correct.
    """

    product_id: str
    name: str
    price: float
    garment_type: str
    image_url: str
    description: str
    colors: list[str]
    available_sizes: list[str] = Field(
        default_factory=list, description="Sizes currently in stock"
    )
    stock_by_size: dict[str, int] = Field(
        default_factory=dict,
        description="Exact units per size (0 = sold out); lets the agent answer "
        "'how many' questions from a search result without a separate stock call.",
    )
    in_stock: bool = True


class StockLevel(BaseModel):
    """How many units of one size of a product are in stock."""

    size: str
    quantity: int
    in_stock: bool


class ProductStock(BaseModel):
    """Full, authoritative stock information for one product.

    Returned by the `check_stock` tool so the agent can tell a customer exactly
    what is available and what is sold out — always from the database, never
    guessed.
    """

    product_id: str
    name: str
    price: float
    total_stock: int
    in_stock: bool
    sizes: list[StockLevel] = Field(default_factory=list)
    available_sizes: list[str] = Field(
        default_factory=list, description="Sizes with quantity > 0"
    )
    out_of_stock_sizes: list[str] = Field(
        default_factory=list, description="Sizes that are currently sold out"
    )


class ChatReply(BaseModel):
    """The agent's structured output.

    The agent writes the customer-facing text and names any products it wants
    to show by id; the ids are turned into ProductCards from the database
    afterwards, so the model can't get product details wrong.
    """

    reply: str = Field(description="The friendly message shown to the customer")
    product_ids: list[str] = Field(
        default_factory=list,
        description="product_id values of items to show as cards, in display order",
    )


# --------------------------------------------------------------------------
# Request / response types (frontend <-> FastAPI)
# --------------------------------------------------------------------------


class Customer(BaseModel):
    """The signed-in customer's identity, made available to the agent."""

    name: str
    email: str


class ChatTurn(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatTurn] = Field(default_factory=list)
    # Present when the customer is logged in; used to load/save their history and
    # to tell the agent who it's talking to. None/absent for guests.
    user_id: int | None = None
    # product_ids currently shown on the customer's screen (search results or the
    # product they're viewing), so the agent can answer follow-up questions.
    page_product_ids: list[str] = Field(default_factory=list)


class ChatResponse(BaseModel):
    reply: str
    products: list[ProductCard] = Field(default_factory=list)


class ChatHistoryMessage(BaseModel):
    """One stored message returned when a logged-in customer reopens the chat."""

    role: str
    content: str
    products: list[ProductCard] = Field(default_factory=list)
