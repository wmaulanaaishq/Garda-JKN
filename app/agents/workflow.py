"""GARDA-JKN LangGraph State Machine Workflow.

Orchestrates multi-agent claim adjudication pipeline:
Intake -> ML Scoring -> RAG Retrieval -> Validator ("Pengecek") -> Executor ("Pengeksekusi") -> END
"""

from langgraph.graph import END, StateGraph
from app.agents.nodes import (
    executor_node,
    intake_node,
    ml_scoring_node,
    rag_retrieval_node,
    validator_node,
)
from app.agents.state import ClaimState


def check_security(state: ClaimState) -> str:
    """Conditional routing based on security check."""
    if state.get("security_flags"):
        return "end"
    return "ml_scoring"


def build_garda_workflow():
    """Constructs and compiles the LangGraph StateGraph pipeline for GARDA-JKN."""
    workflow = StateGraph(ClaimState)

    # 1. Register Agent Nodes
    from app.agents.nodes import security_guardrail_node
    workflow.add_node("intake", intake_node)
    workflow.add_node("security_guardrail", security_guardrail_node)
    workflow.add_node("ml_scoring", ml_scoring_node)
    workflow.add_node("rag_retrieval", rag_retrieval_node)
    workflow.add_node("validator", validator_node)
    workflow.add_node("executor", executor_node)

    # 2. Define Linear Multi-Agent Adjudication Flow
    workflow.set_entry_point("intake")
    workflow.add_edge("intake", "security_guardrail")
    workflow.add_conditional_edges("security_guardrail", check_security, {"end": END, "ml_scoring": "ml_scoring"})
    workflow.add_edge("ml_scoring", "rag_retrieval")
    workflow.add_edge("rag_retrieval", "validator")
    workflow.add_edge("validator", "executor")
    workflow.add_edge("executor", END)

    # 3. Compile Graph Application
    return workflow.compile()


# Global Compiled LangGraph Application
garda_app = build_garda_workflow()
