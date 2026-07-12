# AI-First CRM — HCP Module: Log Interaction Screen

## 1. Domain framing

Field reps in life sciences log HCP interactions for three reasons that don't apply to a
generic CRM: **compliance** (every interaction is auditable under regulations like the PhRMA
Code and, where applicable, Sunshine Act reporting), **pharmacovigilance** (any hint of an
adverse event mentioned by an HCP must be captured and routed, not lost in free-text notes),
and **field effectiveness** (next-best-action and sentiment feed territory planning and MSL
follow-up). The design below treats these as first-class, not afterthoughts.

## 2. Why two logging modes

Reps are usually logging an interaction from a car or hallway between visits. A structured
form is fast when they already know exactly what to fill in; a chat interface is faster when
they'd rather just talk through what happened and let the assistant do the data-entry work.
Both modes write to the **same `Interaction` record shape**, so downstream reporting doesn't
care which path was used — `source` just records provenance.

## 3. System architecture

```
┌─────────────────────────────┐        ┌──────────────────────────────┐
│  React + Redux (Vite)       │  REST  │  FastAPI                     │
│  - StructuredForm           │◄──────►│  /api/interactions (CRUD)    │
│  - ChatInterface            │        │  /api/chat/turn              │
│  - Redux slices: form, chat │        │  /api/chat/{id}/confirm      │
└─────────────────────────────┘        └───────────┬───────────────────┘
                                                     │
                                          ┌──────────▼───────────┐
                                          │  LangGraph agent      │
                                          │  extract_slots →      │
                                          │  route → compliance_  │
                                          │  gate                 │
                                          └──────────┬───────────┘
                                                     │ Groq API
                                          ┌──────────▼───────────┐
                                          │ gemma2-9b-it (primary)│
                                          │ llama-3.3-70b (fallback,
                                          │ used on malformed JSON│
                                          │ or primary failure)   │
                                          └───────────────────────┘
                                                     │
                                          ┌──────────▼───────────┐
                                          │ Postgres / MySQL      │
                                          │ hcps, field_reps,     │
                                          │ interactions          │
                                          └───────────────────────┘
```

## 4. LangGraph flow (the core of Task requirement)

State carried across turns: `messages`, `slots` (partially filled interaction fields),
`adverse_event_flag`, `off_label_flag`, `is_ready_to_confirm`.

1. **`extract_slots`** — sends the running transcript + previously-known slots to Groq
   (`gemma2-9b-it`). The model returns strict JSON: updated slots, a natural-language reply
   (either a clarifying question or a summary), and two safety flags. If the primary model
   returns malformed JSON or errors, the graph transparently retries on
   `llama-3.3-70b-versatile` — this is the practical reason the brief calls out a second model.
2. **`route_after_extraction`** (conditional edge) — if `adverse_event_flag` is set OR the
   slots are complete, go to `compliance_gate`; otherwise end the turn and let the rep answer
   the assistant's follow-up question.
3. **`compliance_gate`** — a deterministic (non-LLM) node. This is intentional: whether an
   adverse-event mention triggers an escalation notice should not depend on model sampling.
   It appends a fixed compliance notice to the assistant's message.
4. Turn ends, response returns to the frontend. Once `is_ready_to_confirm` is true, the UI
   shows a "Confirm & Save" banner — **the rep always has final sign-off before anything is
   persisted**, which matters for a regulated audit trail.

This graph is intentionally small and mostly linear rather than a large multi-agent swarm —
for a single-form-filling task, a wide graph adds latency and failure surface without adding
capability. The one branch that matters (adverse event routing) is real and enforced outside
the LLM's discretion.

## 5. Data model highlights

- `Interaction.adverse_event_flag` / `adverse_event_summary` — captured but deliberately
  *not* interpreted by the AI (no diagnosis, no severity grading). The agent's prompt
  explicitly instructs it to only capture facts and never advise, keeping the AI out of
  clinical judgment territory.
- `Interaction.raw_transcript` — the full chat is preserved when that mode is used, so an
  auditor can always see what was actually said versus what was extracted.
- `Interaction.ai_confidence` — surfaced so a compliance reviewer can prioritize
  low-confidence AI-logged records for manual review.
- `HCP.tier` — informs call-frequency/next-best-action logic in later iterations of the
  module (not built out here, but the schema anticipates it).

## 6. Frontend notes

- Redux holds two independent slices (`interaction` for the form, `chat` for the
  conversation) so switching modes doesn't lose either draft.
- The mode switch is deliberately colored: teal for the structured (deterministic) path,
  violet for anything AI-touched — so a rep glancing at the screen always knows when an AI
  is involved, per typical enterprise-AI transparency expectations in regulated industries.
- Google Inter is used throughout; a monospace face is reserved for IDs/lot numbers, which
  benefit from fixed-width legibility.

## 7. What's out of scope / assumptions

- Auth, RBAC, and Sunshine Act export reporting are not implemented — flagged as a
  fast-follow, not because they're unimportant.
- The chat session store is in-memory for the demo; production would use LangGraph's
  Postgres checkpointer or Redis so sessions survive server restarts.
- MySQL is supported by swapping the SQLAlchemy URL/driver; Postgres was chosen for the
  reference implementation for its native JSON column support (used for
  `topics_discussed`, `samples_dropped`, etc.).
