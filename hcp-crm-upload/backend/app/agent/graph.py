"""
LangGraph workflow that powers the conversational "Log Interaction" chat mode.

Flow:
  START -> extract_slots -> route
      route -> (needs_more_info)  -> END (returns clarifying question to user)
      route -> (ready_to_confirm) -> compliance_gate -> END
      route -> (adverse_event)    -> escalate -> END

The graph is re-invoked on every user turn with the running conversation history and the
slots extracted so far (LangGraph's checkpointer / state carries this between turns).
"""
import json
from typing import TypedDict, List, Optional, Annotated
import operator

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END

from app.config import settings
from app.agent.prompts import SYSTEM_EXTRACTION_PROMPT


class AgentState(TypedDict):
    messages: Annotated[List[dict], operator.add]   # running chat transcript
    slots: dict
    adverse_event_flag: bool
    adverse_event_summary: Optional[str]
    off_label_flag: bool
    is_ready_to_confirm: bool
    assistant_message: str
    confidence: float


def _get_llm(model_name: str, temperature: float = 0.1):
    return ChatGroq(
        api_key=settings.groq_api_key,
        model=model_name,
        temperature=temperature,
    )


def extract_slots_node(state: AgentState) -> AgentState:
    """Calls the Groq LLM to extract/update structured slots from the conversation so far."""
    llm = _get_llm(settings.groq_model)

    history_text = "\n".join(
        f"{m['role'].upper()}: {m['content']}" for m in state["messages"]
    )
    prior_slots = json.dumps(state.get("slots", {}))

    prompt = [
        SystemMessage(content=SYSTEM_EXTRACTION_PROMPT),
        HumanMessage(
            content=(
                f"Conversation so far:\n{history_text}\n\n"
                f"Previously extracted slots (merge/update, don't discard known values):\n{prior_slots}"
            )
        ),
    ]

    try:
        response = llm.invoke(prompt)
        parsed = json.loads(response.content)
    except (json.JSONDecodeError, Exception):
        # Fall back to the larger model if gemma2-9b-it produces malformed JSON
        # or the primary call fails for any reason.
        llm_fallback = _get_llm(settings.groq_fallback_model)
        response = llm_fallback.invoke(prompt)
        parsed = json.loads(response.content)

    merged_slots = {**state.get("slots", {}), **{
        k: v for k, v in parsed["slots"].items() if v not in (None, [], "")
    }}

    return {
        "messages": [{"role": "assistant", "content": parsed["assistant_message"]}],
        "slots": merged_slots,
        "adverse_event_flag": parsed.get("adverse_event_flag", False),
        "adverse_event_summary": parsed.get("adverse_event_summary"),
        "off_label_flag": parsed.get("off_label_flag", False),
        "is_ready_to_confirm": parsed.get("is_ready_to_confirm", False),
        "assistant_message": parsed["assistant_message"],
        "confidence": parsed.get("confidence", 0.5),
    }


def compliance_gate_node(state: AgentState) -> AgentState:
    """Terminal safety check: adverse events always short-circuit straight-through auto-save."""
    if state.get("adverse_event_flag"):
        note = (
            "\n\n⚠️ This interaction mentions a potential adverse event. It will be routed to "
            "Pharmacovigilance/Medical Affairs for review in addition to being logged here."
        )
        return {"assistant_message": state["assistant_message"] + note}
    return {}


def route_after_extraction(state: AgentState) -> str:
    if state.get("adverse_event_flag"):
        return "compliance_gate"
    if state.get("is_ready_to_confirm"):
        return "compliance_gate"
    return "end_turn"


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("extract_slots", extract_slots_node)
    graph.add_node("compliance_gate", compliance_gate_node)

    graph.set_entry_point("extract_slots")
    graph.add_conditional_edges(
        "extract_slots",
        route_after_extraction,
        {
            "compliance_gate": "compliance_gate",
            "end_turn": END,
        },
    )
    graph.add_edge("compliance_gate", END)

    return graph.compile()


# Singleton compiled graph reused across requests
interaction_agent = build_graph()
