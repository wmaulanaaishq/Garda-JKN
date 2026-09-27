# Handoff Report: Codebase & Environment Survey — GARDA-JKN

**Survey Agent**: Explorer Survey 1  
**Project Root**: `/home/wmaulanaaishq/projects/bpjs_2025`  
**Date**: 2026-09-27  

---

## 1. Observation

### 1.1 Repository Structure & File Layout
A comprehensive filesystem scan reveals the following layout:

```text
/home/wmaulanaaishq/projects/bpjs_2025/
├── .env                                       # Configuration & API keys (AIML_API_KEY, HF_TOKEN, Qdrant configs)
├── .gitignore                                 # Standard Python gitignore
├── Dockerfile                                 # Container build definition for Streamlit app
├── ORIGINAL_REQUEST.md                        # User specifications for Stage 3 (RAG) & Stage 4 (LangGraph)
├── requirements.txt                           # Pinned Python package dependencies
├── app.py                                     # Streamlit GUI for GARDA-JKN claim adjudication
├── download_pnpk.py                           # Web scraper for Ministry of Health (Kemenkes) PNPK documents
├── ingest_pnpk.py                             # Script to parse PDFs and push embeddings to Qdrant
├── app/
│   ├── agents/
│   │   ├── nodes.py                           # LangGraph agent nodes (intake, ml_scoring, rag_reasoning, arbiter)
│   │   ├── state.py                           # ClaimState TypedDict definition
│   │   └── workflow.py                        # LangGraph StateGraph pipeline builder
│   ├── api/                                   # Empty directory (no __init__.py, no FastAPI routes)
│   ├── core/
│   │   ├── llm.py                             # ChatOpenAI client configured for DeepSeek-R1 via AIML API
│   │   ├── ml_engine.py                       # MLEngine class loading XGBoost model & feature meta
│   │   └── vector_db.py                       # MedicalKnowledgeBase class wrapping Qdrant & embeddings
│   └── ui/                                    # Empty directory
├── artifacts/
│   ├── garda_features_meta.json               # JSON listing 8 feature column names
│   ├── garda_xgb_model.json                   # Trained XGBoost classifier model JSON
│   └── sample_vclaim_simulation.json          # 50 simulated BPJS claims with raw features & risk scores
├── Data RAG/
│   ├── PNPK_Diabetes.pdf                      # 3.0 MB PNPK PDF
│   ├── PNPK_Epilepsi.pdf                      # 4.0 MB PNPK PDF
│   ├── PNPK_Leukemia.pdf                      # 2.5 MB PNPK PDF
│   ├── PNPK_Sindrom_Koroner.pdf               # 1.8 MB PNPK PDF
│   ├── PNPK_Tata_Laksana_Stroke_2026.pdf      # 2.9 MB PNPK PDF
│   ├── Aturan Standar Severity Level INA-CBG/ # Empty folder
│   ├── Buku Petunjuk Teknis Verifikasi Klaim BPJS/ # Empty folder
│   └── Pedoman Nasional Pelayanan Kedokteran (PNPK)  Panduan Praktik Klinis (PPK/ # Contains 5 Zone.Identifier files
├── knowledge_base/                            # Target for Qdrant storage (currently empty, no DB created yet)
└── venv/                                      # Python 3.12.3 virtual environment
```

### 1.2 Virtual Environment & Dependency Inspection
Direct execution of `./venv/bin/pip list` and module import tests yielded:
- **Python version**: `Python 3.12.3`
- **Installed packages in `./venv`**: Only `anyio 4.15.1`, `cffi 2.1.1`, `fsspec 2026.9.0`, `google-genai 2.25.0`, `hf-xet 1.6.0`, `hpack 4.2.0`, `httpcore2 2.13.1`, `httptools 0.8.0`, `hyperframe 6.1.0`, `jiter 0.17.0`, `jsonpointer 3.1.1`, `langchain-groq 1.1.3`, `langgraph-checkpoint 4.2.0`, `langgraph-sdk 0.4.5`, `mdurl 0.1.2`, `nvidia-cuda-nvrtc 13.0.88`, `nvidia-cusolver 12.0.4.66`, `pandas 3.0.6`, `pip 24.0`, `Pygments 2.21.0`, `python-dateutil 2.9.0.post0`, `rpds-py 2026.6.3`, `starlette 1.7.0`, `streamlit 1.64.0`.
- **Missing critical packages**:
  ```text
  fastapi: ERROR (No module named 'fastapi')
  uvicorn: ERROR (No module named 'click')
  xgboost: ERROR (No module named 'xgboost')
  shap: ERROR (No module named 'shap')
  qdrant_client: ERROR (No module named 'qdrant_client')
  langchain: ERROR (No module named 'langchain')
  langchain_openai: ERROR (No module named 'langchain_openai')
  sentence_transformers: ERROR (No module named 'sentence_transformers')
  pydantic: ERROR (No module named 'pydantic')
  dotenv: ERROR (No module named 'dotenv')
  pypdf: ERROR (No module named 'pypdf')
  ```
- **Distutils issue**: `distutils-precedence.pth` emits `ModuleNotFoundError: No module named '_distutils_hack'` upon interpreter startup.

### 1.3 External API Connectivity Verification
- **AIML API Key**: Verified active and authorized via `curl -s -H "Authorization: Bearer 7ee8b8083b76c9971a8cdd58778c609b" https://api.aimlapi.com/v1/models`.
- **DeepSeek-R1 Availability**: `deepseek/deepseek-r1` is present in the AIML API model catalog and successfully returned completions (`BPJS adalah Badan Penyelenggara Jaminan Sosial...`).
- **AIML Embedding Endpoint**: Successfully tested with `openai/text-embedding-3-small` via AIML API endpoint (`https://api.aimlapi.com/v1/embeddings`), returning 1536-dimensional float vectors.

### 1.4 Code Inspection Observations & Defects Found

#### Observation A: Fatal bug in `app/agents/nodes.py` (Line 10 & Line 33)
```python
# app/agents/nodes.py:10
ml_engine = MLEngine()  # CRASH: MLEngine.__init__() requires model_path and meta_path!

# app/agents/nodes.py:33
is_anomaly, risk_score, shap_explanation = ml_engine.predict_fraud(claim_data)  # CRASH: Method is predict_risk, returns dict!
```
Versus actual definition in `app/core/ml_engine.py`:
```python
# app/core/ml_engine.py:7
def __init__(self, model_path: str, meta_path: str): ...
# app/core/ml_engine.py:15
def predict_risk(self, claim_data: dict) -> dict: ...
```

#### Observation B: Type schema mismatch between `app/agents/state.py`, `app/agents/nodes.py`, and `app.py`
- `app/agents/state.py` defines:
  ```python
  class ClaimState(TypedDict):
      claim_id: str
      patient_data: Dict[str, Any]
      clinical_data: Dict[str, Any]
      billing_data: Dict[str, Any]
      ml_risk_score: float
      ml_is_anomaly: bool
      rag_references: List[str]
      medical_validation_notes: str
      is_upcoding_detected: bool
      revised_severity_level: Optional[int]
      final_adjudication_letter: str
      status: str
  ```
- But `app/agents/nodes.py` uses:
  - `state["claim_data"]` (Not in ClaimState)
  - `state["is_anomalous"]` (State has `ml_is_anomaly`)
  - `state["ml_explanation"]` (Not in ClaimState)
  - `state["rag_context"]` (State has `rag_references`)
  - returns `final_status` and `adjudication_reason` (State has `status` and `final_adjudication_letter`)
- And `app.py` (Lines 38, 51, 60, 64, 66, 67, 72, 77) accesses:
  `claim_data`, `final_status`, `adjudication_reason`, `is_anomalous`, `ml_risk_score`, `ml_explanation`, `rag_context`.

#### Observation C: DeepSeek-R1 output format vs naive JSON parsing in `arbiter_node`
In `app/agents/nodes.py` lines 80-87:
```python
clean_json = response.content.replace('```json', '').replace('```', '').strip()
decision = json.loads(clean_json)
```
DeepSeek-R1 outputs extensive reasoning tokens wrapped in `<think> ... </think>` blocks before the final answer. Naive string replacement fails on `<think>` tags, triggering the fallback `except` block every time.

#### Observation D: Missing Test Suites & Ingestion Status
- Neither `test_rag.py` nor `test_langgraph.py` exists in the repository.
- `knowledge_base/` has 0 files (vector DB has not been ingested/built yet).
- `download_pnpk.py` line 12 contains a hardcoded wrong path:
  `out_dir = "/home/wmaulanaaishq/projects/bpjs_2025/project Garda-JKN/Data RAG"`.

---

## 2. Logic Chain

1. **Premise 1**: The user request and acceptance criteria mandate working `test_rag.py` demonstrating Qdrant ingestion and semantic retrieval, and `test_langgraph.py` running an end-to-end multi-agent adjudication workflow with `final_status` and `adjudication_reason`.
2. **Premise 2**: Running any Python script currently fails because `./venv` is missing core packages (`qdrant-client`, `langchain`, `xgboost`, `shap`, `pydantic`, `pypdf`, `sentence-transformers`, `fastapi`, `uvicorn`).
3. **Premise 3**: In `app/agents/nodes.py`, `ml_engine = MLEngine()` fails with `TypeError`, and `ml_engine.predict_fraud()` fails with `AttributeError`. Therefore, the LangGraph workflow cannot execute even if packages are installed.
4. **Premise 4**: In `app/agents/state.py`, the schema mismatch prevents clean state passing between `intake`, `ml_scoring`, `rag_reasoning`, and `arbiter`, and breaks compatibility with `app.py` and `ORIGINAL_REQUEST.md`.
5. **Premise 5**: In `app/core/vector_db.py`, embeddings default to `GoogleGenerativeAIEmbeddings` using `GEMINI_API_KEY` (which is not configured in `.env`), falling back to `all-MiniLM-L6-v2`. However, AIML API key (`AIML_API_KEY`) is active and verified to support both `deepseek/deepseek-r1` and `openai/text-embedding-3-small`, while local embeddings (FastEmbed / SentenceTransformers) are also feasible offline.
6. **Conclusion**:
   - To achieve Acceptance Criteria R1, R2, and R3, dependencies must be restored in the environment.
   - `ClaimState` and `nodes.py` must be reconciled and refactored with proper typing.
   - `ml_engine.py` singleton usage must be corrected.
   - DeepSeek-R1 response parsing must strip `<think>` tags.
   - `test_rag.py` and `test_langgraph.py` must be created.

---

## 3. Caveats

- **Virtual Environment Integrity**: The virtual environment at `./venv` has an issue with `distutils-precedence.pth`. A clean `pip install -r requirements.txt` or rebuilding the venv with `--upgrade pip` is required.
- **AIML API Rate Limits**: While AIML API is active, DeepSeek-R1 takes 5–15 seconds per call due to test-time reasoning. Offline mock fallbacks or timeout configs should be considered in test suites.
- **INA-CBG Rule Documents**: While 5 PNPK PDFs are present in `Data RAG/`, the INA-CBG severity level directory is empty. Structured synthetic rules or INA-CBG tariff rules should be injected into Qdrant for complete coverage.

---

## 4. Conclusion & Recommendations

### 4.1 Dependency & Environment Plan
1. Fix or reinstall dependencies into `./venv` using `pip install -r requirements.txt` plus `fastembed` or embedding dependencies.
2. Remove or clean the orphaned `distutils-precedence.pth` file if it causes noise.

### 4.2 Module Encapsulation Architecture
Refactor into cleanly separated, robust modules:
- **`app/__init__.py`**, **`app/agents/__init__.py`**, **`app/core/__init__.py`**: Add explicit `__init__.py` files with clean exports.
- **`app/agents/state.py`**: Align `ClaimState` with real system requirements:
  ```python
  class ClaimState(TypedDict, total=False):
      claim_data: Dict[str, Any]
      is_anomalous: bool
      ml_risk_score: float
      ml_explanation: str
      rag_context: str
      rag_references: List[Dict[str, Any]]
      final_status: str  # "APPROVED" | "DOWNGRADED" | "ESCALATED"
      adjudication_reason: str
      adjudication_letter: str
      validation_notes: str
  ```
- **`app/core/ml_engine.py` & `app/agents/nodes.py`**:
  - Export `ml_engine = MLEngine(MODEL_PATH, META_PATH)` in `ml_engine.py`.
  - Fix `nodes.py` to import `ml_engine` and call `predict_risk(claim_data)`.
  - Add SHAP feature importance extraction or simulation to populate `ml_explanation`.
  - Add mapper function from friendly fields (`usia`, `diag_awal`, `durasi_rawat`, `biaya_tagih`) to ML feature columns (`LOS_HARI`, `BIAYA_TAGIH`, `FKL*`).
- **`app/core/vector_db.py`**:
  - Support dual embedding mode: local `SentenceTransformer` / `FastEmbed` or `AIML API` embeddings (`openai/text-embedding-3-small`) using `AIML_API_KEY`.
  - Ensure collection auto-initialization if `knowledge_base/qdrant_db` does not yet exist.
- **`app/agents/nodes.py` (Arbiter)**:
  - Add robust regex extraction for `{ ... }` JSON and remove `<think>` reasoning tags from DeepSeek-R1 output.

### 4.3 Acceptance Criteria Deliverables Needed
1. **`test_rag.py`**: Script that initializes `MedicalKnowledgeBase`, ingests a document from `Data RAG/` or a dummy medical rule PDF, runs similarity search, and prints retrieved snippets with metadata.
2. **`test_langgraph.py`**: Script that executes `garda_app.invoke({"claim_data": claim})` on multiple simulated claims from `artifacts/sample_vclaim_simulation.json`, asserting that `final_status` is one of `{"APPROVED", "DOWNGRADED", "ESCALATED"}` and `adjudication_reason` is populated without timeout or infinite loops.
3. **`test_evaluation.py`**: Automated end-to-end evaluation script demonstrating Explainable AI metrics (risk score, SHAP drivers, RAG citation sources, AI rationalization log).

---

## 5. Verification Method

To verify these observations independently:
1. **Check missing packages**:
   ```bash
   ./venv/bin/python -c "import qdrant_client, langchain, xgboost, shap, pypdf"
   ```
   *(Expected: ModuleNotFoundError)*
2. **Inspect MLEngine signature defect**:
   ```bash
   grep -n "MLEngine" app/agents/nodes.py app/core/ml_engine.py
   ```
3. **Inspect ClaimState schema mismatch**:
   ```bash
   cat app/agents/state.py
   grep -n "state\[" app/agents/nodes.py
   ```
4. **Test AIML API & DeepSeek-R1 connectivity**:
   ```bash
   curl -s -X POST https://api.aimlapi.com/v1/chat/completions \
     -H "Authorization: Bearer 7ee8b8083b76c9971a8cdd58778c609b" \
     -H "Content-Type: application/json" \
     -d '{"model": "deepseek/deepseek-r1", "messages": [{"role": "user", "content": "ping"}], "max_tokens": 10}'
   ```
