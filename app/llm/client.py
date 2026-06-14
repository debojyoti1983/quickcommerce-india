"""Anthropic client wrapper with graceful deterministic fallback.

Secret consumed: QC_ANTHROPIC_API_KEY (env / secrets manager). Format sk-ant-...
If missing OR the API call fails, we return a deterministic narration built from
the engine's decision and flag source="deterministic" — the app never crashes on
an LLM problem.
"""

from __future__ import annotations

import json
import logging

from app.config import get_settings
from app.engine.recommend import Recommendation
from app.llm.prompts import SYSTEM_PROMPT, USER_TEMPLATE
from app.models import UserContext

logger = logging.getLogger("qcommerce.llm")

# Bound the agentic surface: this is a single, non-tool completion with a cap.
_MAX_TOKENS = 500


def _decision_payload(rec: Recommendation) -> dict:
    """Compact, number-faithful payload the model may restate but not alter."""
    def offer_dict(o):
        return {
            "platform": o.platform,
            "item": o.item_name,
            "unit": o.unit,
            "true_price_inr": str(o.true_price),
            "eta_minutes": o.eta_minutes,
            "rating": o.rating,
            "offer": o.offer_text,
            "veg": o.veg,
        }

    return {
        "abstained": rec.abstained,
        "abstain_reason": rec.abstain_reason,
        "best": offer_dict(rec.best.offer) if rec.best else None,
        "alternatives": [offer_dict(a.offer) for a in rec.alternatives],
        "because": rec.because,
        "confidence": {"value": rec.confidence_value, "label": rec.confidence_label},
        "assumptions": rec.assumptions,
        "missing_data": rec.missing_data,
    }


def _deterministic_narration(rec: Recommendation) -> str:
    if rec.abstained:
        lines = ["I can't confirm a reliable recommendation right now.",
                 f"Reason: {rec.abstain_reason}"]
        if rec.missing_data:
            lines.append("Missing data: " + "; ".join(rec.missing_data))
        return "\n".join(lines)

    b = rec.best.offer
    out = [f"**Best choice: {b.platform} — {b.item_name} at ₹{b.true_price}**"]
    if b.eta_minutes is not None:
        out[-1] += f" · ETA {b.eta_minutes} min"
    if b.rating is not None:
        out[-1] += f" · {b.rating}★"
    out.append("")
    out.extend(f"- {r}" for r in rec.because)
    if rec.alternatives:
        out.append("")
        out.append("Alternatives:")
        for a in rec.alternatives:
            o = a.offer
            eta = f", {o.eta_minutes} min" if o.eta_minutes is not None else ""
            out.append(f"- {o.platform}: ₹{o.true_price}{eta}"
                       + (f" — {o.offer_text}" if o.offer_text else ""))
    return "\n".join(out)


def narrate_recommendation(rec: Recommendation, user: UserContext) -> dict:
    """Return {text, source}. source is 'claude' or 'deterministic'."""
    settings = get_settings()
    if not settings.llm_enabled:
        return {"text": _deterministic_narration(rec), "source": "deterministic"}

    try:
        import anthropic  # imported lazily so the app runs without the dep configured

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        message = client.messages.create(
            model=settings.llm_model,
            max_tokens=_MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": USER_TEMPLATE.format(
                        query=rec.query,
                        user_context=user.model_dump_json(),
                        decision_json=json.dumps(_decision_payload(rec), ensure_ascii=False),
                    ),
                }
            ],
        )
        text = "".join(block.text for block in message.content if block.type == "text")
        return {"text": text.strip(), "source": "claude"}
    except Exception as exc:  # noqa: BLE001 — degrade, never crash on LLM failure
        logger.warning("LLM narration failed (%s); using deterministic fallback", type(exc).__name__)
        return {"text": _deterministic_narration(rec), "source": "deterministic"}
