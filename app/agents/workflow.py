from langgraph.graph import StateGraph, END
from app.agents.state import ClaimState
from app.agents.nodes import intake_node, ml_scoring_node, rag_reasoning_node, arbiter_node

def build_garda_workflow():
    """
    Membangun arsitektur LangGraph (State Machine) untuk GARDA-JKN.
    Alur: Intake -> ML Scoring -> RAG Reasoning -> Arbiter -> Selesai
    """
    workflow = StateGraph(ClaimState)
    
    # 1. Tambahkan Node (Agen)
    workflow.add_node("intake", intake_node)
    workflow.add_node("ml_scoring", ml_scoring_node)
    workflow.add_node("rag_reasoning", rag_reasoning_node)
    workflow.add_node("arbiter", arbiter_node)
    
    # 2. Definisikan Alur (Edges)
    workflow.set_entry_point("intake")
    workflow.add_edge("intake", "ml_scoring")
    
    # Logika Conditional: Jika ML tidak mendeteksi anomali (Skor rendah), langsung Approve?
    # Untuk MVP Healthkathon ini, kita lewatkan semua klaim ke RAG & Arbiter agar AI bisa "pamer" kemampuan penalarannya.
    workflow.add_edge("ml_scoring", "rag_reasoning")
    workflow.add_edge("rag_reasoning", "arbiter")
    workflow.add_edge("arbiter", END)
    
    # 3. Compile Graf
    return workflow.compile()

# Instansiasi graph untuk bisa di-import langsung
garda_app = build_garda_workflow()
