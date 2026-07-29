"""AI provider abstraction + adapters (DOMAIN-013 §10). The domain depends ONLY on
AIProvider — never on a vendor/model. Switch via AI_PROVIDER config, no code change.

  - SandboxAIProvider: default, deterministic (seeded by input hash) — reproducible
    structured outputs + confidence for full local/CI testing without any credentials.
  - LLMProvider: production adapter (Emergent Universal LLM key, gpt-5.4-mini by default)
    returning strict-JSON structured output. Advisory only.
Providers return normalized dicts; the application maps them to immutable AI analyses.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from abc import ABC, abstractmethod

log = logging.getLogger("ai.provider")

_BRANDS = ["Nike", "Adidas", "Levi's", "The North Face", "Carhartt", "Stone Island"]
_CATS = ["footwear", "outerwear", "tops", "bottoms", "accessories"]


class AIProvider(ABC):
    name: str

    @abstractmethod
    async def analyze_listing(self, *, title: str, description: str) -> dict: ...

    @abstractmethod
    async def score_fraud(self, *, title: str, description: str, price: int) -> dict: ...


class SandboxAIProvider(AIProvider):
    """No-network, deterministic. Same input -> same output (reproducible tests)."""
    name = "sandbox"
    model = "sandbox-v1"

    def _seed(self, *parts) -> int:
        h = hashlib.sha256("|".join(parts).encode()).hexdigest()
        return int(h[:8], 16)

    async def analyze_listing(self, *, title, description):
        s = self._seed(title, description)
        text = f"{title} {description}".lower()
        brand = next((b for b in _BRANDS if b.lower() in text), _BRANDS[s % len(_BRANDS)])
        category = next((c for c in _CATS if c in text), _CATS[s % len(_CATS)])
        length = len(description or "")
        quality = max(20, min(95, 40 + length // 4 + (10 if len(title or "") > 15 else 0)))
        recs = []
        if len(title or "") < 15:
            recs.append({"kind": "improve_title", "message": "Add brand, size and condition to the title.", "confidence": 0.9})
        if length < 80:
            recs.append({"kind": "improve_description", "message": "Describe fit, flaws and measurements for buyer trust.", "confidence": 0.85})
        recs.append({"kind": "add_photos", "message": "Add photos of tags, soles and any wear.", "confidence": 0.7})
        return {
            "brand": {"value": brand, "confidence": 0.8},
            "category": {"value": category, "confidence": 0.75},
            "quality_score": {"value": quality, "confidence": 0.7},
            "attributes": [{"kind": "condition_estimate",
                            "value": "good" if quality > 60 else "fair", "confidence": 0.6}],
            "recommendations": recs,
        }

    async def score_fraud(self, *, title, description, price):
        text = f"{title} {description}".lower()
        flags = []
        score = 0.05
        for kw, w in (("replica", 0.6), ("fake", 0.6), ("mirror", 0.4), ("aaa", 0.3),
                      ("wire transfer", 0.5), ("gift card", 0.5), ("off-platform", 0.5),
                      ("whatsapp", 0.3), ("telegram", 0.3)):
            if kw in text:
                flags.append(kw)
                score += w
        if price is not None and price < 500:            # suspiciously cheap (<₴5)
            flags.append("price_too_low")
            score += 0.3
        score = min(1.0, round(score, 2))
        return {"risk_score": score, "flags": flags,
                "reason": "Sandbox heuristic risk assessment"}


class LLMProvider(AIProvider):
    """Production adapter via emergentintegrations. Structured JSON, advisory only."""
    name = "llm"

    def __init__(self, *, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    async def _json(self, objective: str, user_text: str) -> dict:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        from .prompts import active_version, prompt
        pv = active_version(objective)
        chat = LlmChat(api_key=self.api_key, session_id=f"ai-{objective}",
                       system_message=prompt(objective, pv)["system"]).with_model("openai", self.model)
        resp = await chat.send_message(UserMessage(text=user_text))
        raw = resp if isinstance(resp, str) else getattr(resp, "content", str(resp))
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        return json.loads(m.group(0) if m else raw)

    async def analyze_listing(self, *, title, description):
        return await self._json("listing_enrichment",
                                f"Title: {title}\nDescription: {description}")

    async def score_fraud(self, *, title, description, price):
        return await self._json("fraud_analysis",
                                f"Title: {title}\nDescription: {description}\nPrice(minor units): {price}")


def build_ai_provider() -> AIProvider:
    choice = os.environ.get("AI_PROVIDER", "sandbox").lower()
    if choice == "llm":
        key = os.environ.get("EMERGENT_LLM_KEY")
        if not key:
            raise RuntimeError("AI_PROVIDER=llm but EMERGENT_LLM_KEY is not configured")
        return LLMProvider(api_key=key, model=os.environ.get("AI_MODEL", "gpt-5.4-mini"))
    return SandboxAIProvider()
