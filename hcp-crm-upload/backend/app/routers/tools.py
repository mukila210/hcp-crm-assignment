from fastapi import APIRouter

from app.agent.tools import (
    log_interaction_tool,
    edit_interaction_tool,
    lookup_hcp_tool,
    flag_adverse_event_tool,
    suggest_next_best_action_tool,
)

router = APIRouter(prefix="/api/tools", tags=["agent-tools (demo)"])


@router.post("/log-interaction")
def demo_log_interaction(
    hcp_id: str,
    field_rep_id: str,
    interaction_type: str,
    topics_discussed: list[str],
    hcp_sentiment: str | None = None,
):
    """Tool 1 (mandatory): Log Interaction — creates a new interaction record."""
    return log_interaction_tool.invoke({
        "hcp_id": hcp_id,
        "field_rep_id": field_rep_id,
        "interaction_type": interaction_type,
        "topics_discussed": topics_discussed,
        "hcp_sentiment": hcp_sentiment,
    })


@router.post("/edit-interaction")
def demo_edit_interaction(interaction_id: str, updates: dict):
    """Tool 2 (mandatory): Edit Interaction — modifies fields on an existing record."""
    return edit_interaction_tool.invoke({"interaction_id": interaction_id, "updates": updates})


@router.get("/lookup-hcp")
def demo_lookup_hcp(hcp_id: str):
    """Tool 3: Lookup HCP — pulls profile + recent history for agent context."""
    return lookup_hcp_tool.invoke({"hcp_id": hcp_id})


@router.post("/flag-adverse-event")
def demo_flag_adverse_event(interaction_id: str, summary: str):
    """Tool 4: Flag Adverse Event — compliance/pharmacovigilance escalation."""
    return flag_adverse_event_tool.invoke({"interaction_id": interaction_id, "summary": summary})


@router.post("/suggest-next-best-action")
def demo_suggest_nba(topics_discussed: list[str], hcp_sentiment: str):
    """Tool 5: Suggest Next Best Action — recommends a concrete follow-up."""
    return {"suggestion": suggest_next_best_action_tool.invoke({
        "topics_discussed": topics_discussed,
        "hcp_sentiment": hcp_sentiment,
    })}