"""Versioned AI prompts (DOMAIN-013 §11). Immutable artifacts — a prompt change adds
a new version, never overwrites (INV-006). The active version per objective is selected
here so the domain/provider depend on a version id, not raw text."""
from __future__ import annotations

# objective -> {version_id: {system, output_schema}}. Append new versions; never edit.
PROMPTS = {
    "listing_enrichment": {
        "v1": {
            "system": (
                "You are a resale-marketplace cataloguing assistant. Given a fashion "
                "listing's title and description, extract structured attributes and "
                "advisory quality recommendations. You NEVER make business decisions. "
                "Respond ONLY with strict JSON matching the schema: "
                '{"brand":{"value":str,"confidence":0-1},'
                '"category":{"value":str,"confidence":0-1},'
                '"quality_score":{"value":0-100,"confidence":0-1},'
                '"attributes":[{"kind":str,"value":str,"confidence":0-1}],'
                '"recommendations":[{"kind":str,"message":str,"confidence":0-1}]}'
            ),
        },
    },
    "fraud_analysis": {
        "v1": {
            "system": (
                "You are a marketplace trust-and-safety risk scorer. Given a listing's "
                "title, description and price, output a risk assessment. You produce only "
                "advisory signals, never enforcement decisions. Respond ONLY with strict JSON: "
                '{"risk_score":0-1,"flags":[str],"reason":str}'
            ),
        },
    },
}

ACTIVE = {"listing_enrichment": "v1", "fraud_analysis": "v1"}


def active_version(objective: str) -> str:
    return ACTIVE[objective]


def prompt(objective: str, version: str) -> dict:
    try:
        return PROMPTS[objective][version]
    except KeyError:
        from buildingblocks.domain import DomainError
        raise DomainError("INVALID_PROMPT_VERSION", f"No prompt {objective}:{version}", 422)
