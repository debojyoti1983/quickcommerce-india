# CLAUDE.md — QuickCommerce India Aggregator

AI commerce assistant: helps Indian users discover, compare, and order food (Swiggy, Zomato) and
groceries (Blinkit, Zepto, Flipkart Minutes, Amazon Fresh, BigBasket, Instamart) across 8 apps.

Full module specs + the binding engineering/security standard live in
`~/Downloads/HARNESS-SPEC-You-are-an-intelligent-commerc.md`. Read it for any detail this file
summarizes — those rules are non-negotiable. Do not load it wholesale (281KB); open the relevant section.

## The product
Compare options across the 8 apps on: availability, **true price** (item + taxes + delivery + surge,
net of membership), ETA, offers/memberships (Swiggy One, Zomato Gold, BB Star), and user preferences.

Flow: aggregate → normalize (price/qty/units/time) → compare trade-offs (cheapest / fastest /
best-rated) → recommend a best choice **plus** alternatives → state assumptions & missing data →
adapt to India (veg/non-veg, regional cuisine, price sensitivity).

Optimize for: **clarity > verbosity, relevance > completeness, actionable recommendations > raw data.**

## First, before any code (YOU MUST)
Your first response is a clarifying-questions message — a numbered list, each item with a proposed
default in `[brackets]` so the user can accept in one word. Cover: runtime target, compliance
jurisdiction + PII handling, secrets mechanism, observability sink, model + fallback gateway,
per-platform endpoints/auth/rate-limits, HITL approval path + SLA, deploy cadence. Then restate
scope in 3–5 bullets and wait. Don't ask about naming/style — pick a default and note it in a comment.

## Architecture: 11 modules under `app/<module>/`
Build in order, each gated by its acceptance tests (full specs in the harness doc). These are
modules, not "layers", and not a reusable framework — build only this app.

`bootstrap` (cold-start: lat/lng→pincode + parallel serviceability probes → immutable
`ContextSnapshot`) → `prompt` (system prompt, token budget, cache boundaries) → `memory` (episodic/
semantic/procedural/working + timestamped, source-attributed **Claim Graph**) → `messaging`
(durable stage-checkpointed pipeline, idempotent orders) → `security` → `tools` (platform APIs +
checkout state machine) → `execution` (resilient loop, structured output, hallucination remediation)
→ `routing` (semantic intent → cheapest viable model, budget gateway) → `observability`
(tamper-evident decision ledger) → `evaluation` (LLM-judge + regression) → `coordination`
(specialist sub-agents: parallel fetch, normalize, synthesize).

## Domain rules (override generic instincts)
- **Authority tiers** — T1: live cart/checkout API · T2: catalog/listing API · T3: cached/scraped/
  user-recalled (suspect; never present as confirmed).
- **Recency decay** — stamp `captured_at`, decay confidence: eta ~5m · availability ~10m ·
  serviceability ~30m · offers ~1h · price ~2h. Stale → re-fetch or flag, never show as current.
- **Abstain, don't hallucinate** — below ~0.55 confidence, say "I can't confirm this is in stock".
  NEVER invent prices, ETAs, dishes, stock, offers, store IDs, or coupon validity. Every comparison
  fact traces to a Claim Graph entry (source + value + timestamp).
- **HITL — always explicit human approval, never autonomous:** `place_order`, `apply_paid_coupon`,
  `modify_subscription` (Swiggy One / Zomato Gold / BB Star), `payment_method_change`. Show data +
  recommendation + evidence; log the human's decision.
- **Idempotent orders** — a retry never creates two carts or double-charges; use idempotency keys;
  checkpoint each pipeline stage so an interrupted session resumes without re-fetch/re-order.
- **Explanation-first output** — every recommendation carries `[BECAUSE]` (why) / `[EVIDENCE]`
  (sourced, timestamped) / `[CONFIDENCE]` (level + caveats). Show which platforms agree vs conflict.
- **Money & India** — `Decimal` only, never float; currency INR; veg/non-veg + regional cuisine
  respected by default; probe all 8 platforms in parallel (`asyncio.gather`); an unreachable
  platform degrades gracefully and never crashes boot.

## Non-negotiables
- **NEVER hardcode a secret** (key/token/password/cookie/conn-string) anywhere — source, tests,
  comments, commits, or `.env.example`. Source it from a secrets manager (default) → gitignored
  `.env` (+ committed `.env.example` of names only) → encrypted local (dev only, marked
  `# TODO: migrate`). Never log secrets; scrub `Authorization`/`Cookie` headers. If the user pastes
  one in chat: refuse to store it and tell them to rotate it.
- **NEVER let unvalidated external input** reach a DB/shell/filesystem/external API — allowlist-validate at the boundary.
- No silent error swallowing. No deploy without env-based config. No price/diet/payment path without a validation layer.

## Engineering deltas worth stating (rest = the spec's standard + ordinary good practice)
- Timeout every external call; exponential backoff + jitter (1s → cap ~60s, 3–5 retries) for
  transient failures; circuit breakers + graceful degradation per platform.
- **SSRF is a top risk** (many outbound platform calls): allowlist URLs, block private IP ranges.
  Treat platform responses and user text as untrusted (prompt injection).
- Typed boundaries (Pydantic / TS strict); config validated at startup, fail-fast on missing values.
- LLM: real current model IDs only; validate tool-call args before executing; cap agentic-loop
  iterations + token budget; validate structured output against a schema; LLM-jury cross-checks
  price/diet/availability; log token usage + cost per request.
- Structured JSON logs (no secrets); per-model token/cost/latency metrics; specific progress
  indicators for >2s ops ("Comparing 6 of 8 apps — fetching Zepto ETA"), never "Loading…".

## Communication
- Lead with the answer/action; trade-offs as brief comparisons, not essays. After implementing,
  summarize what changed and what needs attention.
- **Push back** on security risks / anti-patterns / wrong-tool choices in one paragraph: "This will
  cause [problem] because [reason]. I'd recommend [alternative]. Proceed, or do you have context I'm
  missing?" Not on taste, naming, or clearly-temporary prototype shortcuts.
- **Impact briefing** before material changes (schema, infra, deps, architecture, cost-, or
  security-affecting, LLM model/prompt/tool): CHANGE → WHAT IT DOES → POSITIVE → TRADE-OFFS → COST →
  SECURITY → ROLLBACK → RECOMMENDATION. Scale to impact; trivial changes need none.

## Definition of Done
- [ ] Input validated at boundaries; authn + resource-level authz
- [ ] No hardcoded secrets; structured logs without sensitive data
- [ ] Errors meaningful, none swallowed; timeouts on all external calls
- [ ] Tests: happy path + primary failures; DB queries parameterized
- [ ] Config via env/secrets manager; API responses carry a request ID
- [ ] Dependencies vuln-audited; docs updated
- [ ] LLM: token limits checked, structured output validated, cost tracked
- [ ] Price/diet/payment: validation layer + HITL on irreversible actions
- [ ] Money in `Decimal` + audit trail; material change → impact briefing given
- [ ] Progress indicators on long operations
