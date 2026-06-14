# QuickCommerce India

An AI commerce assistant for Indian users that **aggregates, normalizes, and
compares** food (Swiggy, Zomato) and grocery (Blinkit, Zepto, Swiggy Instamart,
BigBasket, Flipkart Minutes, Amazon Fresh) options across 8 apps, then
recommends a best choice **plus** alternatives — transparently, with auditable
reasoning.

This is a **runnable vertical slice** built on the 11-module harness pattern
(see [CLAUDE.md](CLAUDE.md) for the binding standard). Platform data is
**simulated** — the real apps have no public API. Real adapters drop in behind
`app/connectors/base.py` without touching the rest of the app.

## What it does
- Probes all 8 platforms' serviceability **in parallel** at startup.
- Searches across platforms, normalizes to an **all-in true price**
  (item + tax + delivery + surge − membership benefit), keeping money in `Decimal`.
- Ranks **cheapest / fastest / best-rated** and a confidence-weighted **best overall**.
- Emits explanation-first output: **`[BECAUSE]` / `[EVIDENCE]` / `[CONFIDENCE]`**,
  citing timestamped, source-attributed facts from a **Claim Graph**.
- **Abstains** instead of guessing when confidence is below threshold.
- Routes order placement through a **human-in-the-loop** gate with an idempotency
  key — never autonomous, never double-orders.
- Narrates with **Claude** when `QC_ANTHROPIC_API_KEY` is set; otherwise falls
  back to clearly-labelled rule-based explanations (no crash).

## Prerequisites
- Python 3.11+

## Run (Windows)
```bat
run.bat
```
First run creates `.venv`, installs deps, copies `.env.example` → `.env`, and
starts the server at <http://127.0.0.1:8000>.

## Run (manual / cross-platform)
```bash
python -m venv .venv
. .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # optional; add your key to enable Claude
uvicorn app.main:app --reload
```

## Enable Claude (optional)
Add your key to `.env` (never commit it — `.env` is gitignored):
```
QC_ANTHROPIC_API_KEY=sk-ant-...
```
Without it the app runs fully on deterministic reasoning.

## Try it
Open the UI and search `Amul milk`, `Aashirvaad atta`, `Tata salt`, `onion`,
`paneer butter masala`, `masala dosa`, or `chicken biryani`. Toggle **Veg only**
and the **Swiggy One / Zomato Gold** memberships to watch effective prices change.

## Tests
```bash
pip install pytest
pytest -q
```

## API
| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Web UI |
| GET | `/healthz` | Liveness + LLM/connector status |
| POST | `/api/compare` | Run a comparison query |
| POST | `/api/order/prepare` | HITL gate — prepares an order, never places it |

## Module map (`app/`)
`config` · `models` · `bootstrap` (profile, registry, parallel snapshot) ·
`connectors` (base interface, mock data, mock connector) · `memory` (claim graph)
· `engine` (normalize, compare, recommend) · `llm` (Claude client + prompts) ·
`security` (HITL gate) · `coordination` (orchestrator) · `web` (UI).

## Not in this slice (intentionally)
`messaging` durability, `routing` cost-governance, `observability` ledger, and
`evaluation` regression suite are scoped out of the first pass. The interfaces
are structured so they can be added without rework. Real platform connectors
require credentials and raise ToS considerations — out of scope here.
