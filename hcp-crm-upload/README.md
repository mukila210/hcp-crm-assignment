# AI-First HCP CRM — Log Interaction Screen

See `docs/ARCHITECTURE.md` for the full design write-up.

## LangGraph AI Agent & Tools

**Role of the agent:** The LangGraph agent manages the conversational half of the Log
Interaction screen. As a field rep describes a visit in plain language, the agent
(built on Groq's `gemma2-9b-it`, with `llama-3.3-70b-versatile` as a fallback for
malformed responses) extracts structured fields turn-by-turn, asks clarifying
questions for anything missing, live-syncs the draft into the structured form UI, and
gates anything safety-relevant through a deterministic compliance check before it can
be saved. See `backend/app/agent/graph.py` for the graph definition.

**The 5 tools** (`backend/app/agent/tools.py`), demoable individually at `/docs` under
"agent-tools (demo)":

1. **Log Interaction** *(mandatory)* — `log_interaction_tool`. Persists a new
   interaction record. In the chat flow, the LLM performs entity extraction
   (interaction type, topics, sentiment, samples) from the rep's free text first;
   once confirmed, this tool writes the structured result to the database.
2. **Edit Interaction** *(mandatory)* — `edit_interaction_tool`. Updates fields on an
   already-logged interaction — used when a rep corrects something mid-conversation
   (e.g. "actually that was a virtual call, not in person").
3. **Lookup HCP** — `lookup_hcp_tool`. Retrieves an HCP's profile and recent
   interaction history for agent context (recognizing returning HCPs, their tier,
   specialty).
4. **Flag Adverse Event** — `flag_adverse_event_tool`. A deliberately deterministic
   (non-LLM-judged) compliance tool that marks an interaction for Pharmacovigilance/
   Medical Affairs review whenever the extraction step detects a safety-relevant
   mention.
5. **Suggest Next Best Action** — `suggest_next_best_action_tool`. Recommends a
   concrete follow-up action based on discussion topics and observed HCP sentiment.

## Run the backend

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then paste your Groq API key from console.groq.com/keys
# create the Postgres DB first, e.g.: createdb hcp_crm
uvicorn app.main:app --reload --port 8000
```

## Run the frontend

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
```

## Try it

- **Structured Form mode**: fill in HCP ID / Field Rep ID (any string works against a fresh
  DB as long as an `HCP` row with that id exists — see below) and submit.
- **Chat mode**: type something like *"Just wrapped up a visit with Dr. Rao, talked through
  the new dosing data for Drug X, left two sample boxes, she seemed pretty receptive"* and
  the assistant will ask for anything missing, then offer a Confirm & Save banner.
- Try mentioning a side effect (e.g. *"she also mentioned a patient had a rash on Drug X"*)
  to see the compliance escalation banner fire.

### Seeding a test HCP row

The API doesn't include an HCP-creation endpoint (out of scope for this task), so for local
testing insert one directly:

```sql
INSERT INTO hcps (id, full_name, npi_id, specialty)
VALUES ('HCP-04213', 'Dr. Ananya Rao', '1234567890', 'Cardiology');

INSERT INTO field_reps (id, name, email)
VALUES ('REP-1029', 'Test Rep', 'rep@example.com');
```

## Project structure

```
backend/
  app/
    agent/         LangGraph graph + prompts (the AI core)
    routers/        interactions.py (form path), chat.py (chat path)
    models.py       SQLAlchemy models
    schemas.py       Pydantic request/response contracts
frontend/
  src/
    components/     LogInteractionScreen, StructuredForm, ChatInterface, ModeToggle
    store/          Redux slices
    api/            axios client
docs/
  ARCHITECTURE.md   Design rationale, LangGraph flow, data model notes
```