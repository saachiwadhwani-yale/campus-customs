"""The Campus Customs chat agent, built with PydanticAI.

The agent is created once, at import time, and routed through Portkey using
PORTKEY_API_KEY from the shared ai_class .env (same pattern as hw3). It has a
structured output (`ChatReply`), a set of catalogue tools, and dependencies
(`ChatDeps`) that carry who the customer is and what products are on their
screen. `run_chat` is the single entry point main.py calls per message.
"""

from __future__ import annotations

import os

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

from dataclasses import dataclass, field

from openai import AsyncOpenAI
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from models import ChatReply, ChatResponse, ChatTurn, Customer, ProductCard
from tools import (
    audit_append,
    cards_for_ids,
    load_env,
    load_history_turns,
    load_prompt,
    model_name,
    save_message,
    search_catalogue,
    stock_summary,
)


@dataclass
class ChatDeps:
    """Per-request dependencies handed to the agent.

    * `customer` — the signed-in customer, or None for a guest.
    * `page_products` — the products currently shown on the customer's screen
      (their latest search results or the product they're viewing).
    """

    customer: Customer | None = None
    page_products: list[ProductCard] = field(default_factory=list)


def build_agent() -> Agent[ChatDeps, ChatReply]:
    """Create the Portkey-backed chat agent with its tools and deps registered."""
    load_env()

    portkey_key = os.environ.get("PORTKEY_API_KEY")
    if not portkey_key:
        raise RuntimeError(
            "PORTKEY_API_KEY is required. Add it to the .env in the ai_class folder."
        )

    client = AsyncOpenAI(
        api_key=portkey_key,
        base_url="https://api.portkey.ai/v1",
        default_headers={"x-portkey-api-key": portkey_key},
    )
    # No tool-calling: searching the catalogue is done locally (see run_chat) and
    # the matching products are injected into the prompt. This keeps the whole
    # exchange to a SINGLE model round-trip (~1-2s) instead of the two the model
    # needs when it has to call a search tool and then answer.
    agent: Agent[ChatDeps, ChatReply] = Agent(
        OpenAIChatModel(model_name(), provider=OpenAIProvider(openai_client=client)),
        deps_type=ChatDeps,
        output_type=ChatReply,
        system_prompt=load_prompt(),
    )

    # Dependency-driven context, injected into the system prompt each run so the
    # agent knows who it's talking to and what's on their screen — no tool call.

    @agent.instructions
    def customer_identity(ctx: RunContext[ChatDeps]) -> str:
        c = ctx.deps.customer
        if c is None:
            return "The customer is browsing as a guest (not logged in)."
        first = c.name.split()[0] if c.name else "there"
        return (
            f"The signed-in customer is {c.name} (email: {c.email}). "
            f"You may greet them warmly by their first name ({first}). "
            "Do not read their email address back to them unless they ask."
        )

    @agent.instructions
    def page_context(ctx: RunContext[ChatDeps]) -> str:
        products = ctx.deps.page_products
        if not products:
            return ""
        listing = "\n".join(f"  - {_describe(p)}" for p in products)
        return (
            "The customer is currently looking at these products on the page:\n"
            f"{listing}\n"
            "If they ask a follow-up such as 'which is cheapest', 'the first one', "
            "or 'is that in my size', assume they mean these items."
        )

    return agent


def _price(p: ProductCard) -> str:
    return f"${p.price:.2f}"


def _describe(p: ProductCard) -> str:
    """A compact one-line product summary for the model to read.

    Includes everything needed to answer catalogue questions — name, type, price,
    colors, per-size stock levels (0 = sold out) and a short description — so the
    agent can respond in one pass without any extra lookups.
    """
    colors = ", ".join(p.colors) if p.colors else "n/a"
    stock = stock_summary(p.product_id)
    desc = p.description.split(". ")[0].rstrip(".")
    return (
        f"{p.name} — {p.garment_type}, {_price(p)}, colors: {colors}; "
        f"stock by size: {stock} (id: {p.product_id}). {desc}."
    )


# Built once and reused for every request.
agent = build_agent()


def _format_history(history: list[ChatTurn]) -> str:
    """Render recent turns as a short transcript for context."""
    lines = []
    for turn in history[-12:]:
        who = "Customer" if turn.role == "user" else "Assistant"
        lines.append(f"{who}: {turn.content}")
    return "\n".join(lines)


async def run_chat(
    message: str,
    history: list[ChatTurn] | None = None,
    customer: Customer | None = None,
    user_id: int | None = None,
    page_product_ids: list[str] | None = None,
) -> ChatResponse:
    """Answer one customer message and return the reply plus product cards.

    For logged-in customers (`user_id` set) the conversation is loaded from and
    saved to the database, giving them persistent chat history. Guests use only
    the history the frontend passes in for the current session.
    """
    page_product_ids = page_product_ids or []

    # Customer memory: logged-in users get their saved history from the database.
    if user_id is not None:
        history = load_history_turns(user_id)
    else:
        history = history or []

    deps = ChatDeps(customer=customer, page_products=cards_for_ids(page_product_ids))

    # Search the catalogue locally (sub-millisecond) and inject the matches, so
    # the model answers in one round-trip instead of calling a search tool first.
    candidates = search_catalogue(message, limit=6)
    # Label candidates with short codes (p1, p2, …) the model echoes back instead
    # of long id slugs — fewer output tokens means a faster response.
    code_to_id = {f"p{i + 1}": c.product_id for i, c in enumerate(candidates)}

    parts: list[str] = []
    if history:
        parts.append("Conversation so far:\n" + _format_history(history))
    if candidates:
        listing = "\n".join(f"  [p{i + 1}] {_describe(c)}" for i, c in enumerate(candidates))
        parts.append(
            "Matching products (the ONLY products you may show — put the best few "
            "CODES like p1, p3 in product_ids, best first):\n" + listing
        )
    parts.append(f"Customer's new message: {message}")
    prompt = "\n\n".join(parts)

    # Each agent run logs its activity to the append-only audit trail.
    who = f"user:{user_id}" if user_id is not None else "guest"
    steps: list[dict] = [
        {
            "tool": "search_catalogue",
            "args": {"query": message, "limit": 6},
            "result": {"product_ids": [c.product_id for c in candidates], "count": len(candidates)},
        }
    ]

    try:
        result = await agent.run(prompt, deps=deps)
    except Exception as exc:
        steps.append({"tool": "model.generate", "args": {"model": model_name()}, "result": {"error": str(exc)}})
        # Azure's content filter blocks jailbreak / unsafe prompts before the model
        # replies. Treat that as a graceful safety decline, not a crash.
        if "content_filter" in str(exc).lower() or "content management policy" in str(exc).lower():
            audit_append({"who": who, "message": message, "steps": steps, "stop_reason": "content_filtered"})
            return ChatResponse(
                reply=(
                    "I can only help with Campus Customs products and your shopping — "
                    "is there something I can help you find? Woof!"
                )
            )
        audit_append({"who": who, "message": message, "steps": steps, "stop_reason": "error"})
        raise

    reply: ChatReply = result.output
    # Map short codes back to real ids (tolerate the model returning a real id).
    resolved_ids = [code_to_id.get(pid, pid) for pid in reply.product_ids]
    products = cards_for_ids(resolved_ids)

    steps.append(
        {
            "tool": "model.generate",
            "args": {
                "model": model_name(),
                "candidates": len(candidates),
                "has_history": bool(history),
                "page_products": len(deps.page_products),
                "logged_in": customer is not None,
            },
            "result": {"reply": reply.reply, "product_ids": resolved_ids},
        }
    )

    # Save this turn for logged-in customers.
    if user_id is not None:
        save_message(user_id, "user", message)
        save_message(user_id, "assistant", reply.reply, products)
        steps.append({"tool": "save_message", "args": {"user_id": user_id}, "result": {"saved": 2}})

    audit_append(
        {
            "who": who,
            "message": message,
            "steps": steps,
            "stop_reason": "completed" if products or not candidates else "no_products_shown",
        }
    )

    return ChatResponse(reply=reply.reply, products=products)
