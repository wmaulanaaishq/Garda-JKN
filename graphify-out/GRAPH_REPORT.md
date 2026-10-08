# Graph Report - bpjs_2025  (2026-09-29)

## Corpus Check
- Large corpus: 133 files · ~602,095 words. Semantic extraction will be expensive (many Claude tokens). Consider running on a subfolder.

## Summary
- 788 nodes · 1049 edges · 93 communities (34 shown, 59 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 75 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- LangGraph Agents
- RAG and Evaluation
- Data Loading
- Fraud Classifier
- Qdrant RAG
- Next.js Frontend
- FastAPI Backend
- API Test Suite
- PDF Ingestion
- Embedding Fallbacks
- E2E Browser Tests
- Concurrency Tests
- Clinical Guidelines
- Vector Search Core
- TypeScript Config
- Clinical Features
- LangGraph E2E Tests
- Adversarial Testing
- ML XAI Requirements
- Environment Audit
- Clinical Incoherence
- Integrity Audit
- Leukemia Guidelines
- Audit Findings
- Reliability Results
- Architecture Layers
- Adjudication Workflow
- ML Engine
- Epilepsy Guidelines
- Concurrency Reliability
- Acceptance Milestones
- LLM Executor Validator
- Embedding Providers
- Clinical Rule Tests
- Deployment Surfaces
- Supporting Evidence 35
- Supporting Evidence 36
- Supporting Evidence 37
- Supporting Evidence 38
- Supporting Evidence 39
- Supporting Evidence 40
- Supporting Evidence 41
- Supporting Evidence 42
- Supporting Evidence 43
- Supporting Evidence 44
- Supporting Evidence 45
- Supporting Evidence 46
- Supporting Evidence 47
- Supporting Evidence 48
- Supporting Evidence 49
- Supporting Evidence 50
- Supporting Evidence 51
- Supporting Evidence 52
- Supporting Evidence 53
- Supporting Evidence 54
- Supporting Evidence 55
- Supporting Evidence 56
- Supporting Evidence 57
- Supporting Evidence 58
- Supporting Evidence 59
- Frontend Configuration 60
- Frontend Configuration 61
- Frontend Configuration 62
- Deployment Scripts 63
- Deployment Scripts 64
- Supporting Evidence 65
- Supporting Evidence 66
- Supporting Evidence 67
- Supporting Evidence 68
- Supporting Evidence 69
- Supporting Evidence 70
- Supporting Evidence 71
- Supporting Evidence 72
- Supporting Evidence 73
- Supporting Evidence 74
- Supporting Evidence 75
- Supporting Evidence 76
- Supporting Evidence 77
- Supporting Evidence 78
- Supporting Evidence 79
- Supporting Evidence 80
- Supporting Evidence 81
- Supporting Evidence 82
- Supporting Evidence 83
- Supporting Evidence 84
- Supporting Evidence 85
- Supporting Evidence 86
- Supporting Evidence 87
- Supporting Evidence 89
- Supporting Evidence 90
- Supporting Evidence 91

## God Nodes (most connected - your core abstractions)
1. `MedicalKnowledgeBase` - 25 edges
2. `BalancedBaggingXGBoost` - 22 edges
3. `compilerOptions` - 16 edges
4. `ClaimState` - 14 edges
5. `assert_adjudication_contract()` - 13 edges
6. `StratifiedIsolationForest` - 12 edges
7. `ShapAuditorReasonCodeGenerator` - 12 edges
8. `FastLocalHashEmbeddings` - 11 edges
9. `run_full_pipeline()` - 11 edges
10. `TestMedicalRAGPipeline` - 11 edges

## Surprising Connections (you probably didn't know these)
- `Qdrant RAG Layer` --semantically_similar_to--> `MedicalKnowledgeBase Implementation`  [INFERRED] [semantically similar]
  README.md → .agents/teamwork/worker_m1_v3/handoff.md
- `INA-CBG Severity Rules` --semantically_similar_to--> `Severity Level I-III`  [INFERRED] [semantically similar]
  .agents/teamwork/worker_m1_v3/handoff.md → Data RAG/Aturan_INA_CBG_BPJS.md
- `execute_single_http_adjudication()` --uses--> `EvaluationResponse`  [INFERRED]
  tests/test_concurrency_stress.py → api.py
- `TestMedicalRAGPipeline` --uses--> `MedicalKnowledgeBase`  [INFERRED]
  test_rag.py → app/core/vector_db.py
- `execute_single_qdrant_query()` --uses--> `MedicalKnowledgeBase`  [INFERRED]
  tests/test_concurrency_stress.py → app/core/vector_db.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Enterprise Fraud Detection Requirements** — _agents_teamwork_original_request_stratified_isolation_forest, _agents_teamwork_original_request_clinical_incoherence_features, _agents_teamwork_original_request_balanced_bagging_xgboost, _agents_teamwork_original_request_shap_auditor_reason_codes [EXTRACTED 1.00]
- **Authentic Adjudication Pipeline** — _agents_teamwork_auditor_1_handoff_xgboost_shap_inference, _agents_teamwork_auditor_1_handoff_genuine_qdrant_search, _agents_teamwork_auditor_1_handoff_deepseek_chatopenai [EXTRACTED 1.00]
- **Concurrency Reliability and Determinism Results** — _agents_teamwork_challenger_2_replacement_handoff_28_qps_zero_errors, _agents_teamwork_challenger_2_replacement_handoff_in_memory_qdrant_fallback, _agents_teamwork_challenger_2_replacement_handoff_mean_llm_latency_3_37s, _agents_teamwork_challenger_2_replacement_handoff_five_of_five_rag_runs, _agents_teamwork_challenger_2_replacement_handoff_three_of_three_langgraph_runs [EXTRACTED 1.00]
- **GARDA-JKN Four-Layer Architecture** — _agents_teamwork_orchestrator_2_project_lapis_1_ml_risk_engine, _agents_teamwork_orchestrator_2_project_lapis_2_knowledge_base_rag, _agents_teamwork_orchestrator_2_project_lapis_3_multi_agent_stategraph, _agents_teamwork_orchestrator_2_project_lapis_4_e2e_xai [EXTRACTED 1.00]
- **Claim Validation and Execution Flow** — _agents_teamwork_spec_miner_survey_1_handoff_claimstate, _agents_teamwork_spec_miner_survey_1_handoff_validator_node, _agents_teamwork_spec_miner_survey_1_handoff_executor_node [EXTRACTED 1.00]
- **R1 R2 R3 Acceptance Review** — _agents_teamwork_reviewer_1_handoff_r1_qdrant_rag_pass, _agents_teamwork_reviewer_1_handoff_r2_langgraph_pass, _agents_teamwork_reviewer_1_handoff_r3_xai_pass [EXTRACTED 1.00]
- **RAG Pipeline Components** — agents_teamwork_worker_m1_briefing_local_qdrant_embedded_mode, agents_teamwork_worker_m1_briefing_medical_metadata_chunking, agents_teamwork_worker_m1_briefing_search_rules, agents_teamwork_worker_m1_v3_handoff_medical_knowledge_base [INFERRED 0.95]
- **GARDA-JKN Adjudication Layers** — readme_xgboost_screening, readme_qdrant_rag_layer, readme_langgraph_clinical_arbiter [EXTRACTED 1.00]
- **BPJS Claim Data Flow** — data_rag_aturan_ina_cbg_bpjs_vclaim, data_rag_aturan_ina_cbg_bpjs_icd10, data_rag_aturan_ina_cbg_bpjs_ina_cbg, data_rag_aturan_ina_cbg_bpjs_severity_level [EXTRACTED 1.00]

## Communities (93 total, 59 thin omitted)

### Community 0 - "LangGraph Agents"
Cohesion: 0.06
Nodes (61): LangGraph Multi-Agent Orchestration, GARDA-JKN Agents Module., executor_node(), get_kb(), intake_node(), ml_scoring_node(), Any, rag_retrieval_node() (+53 more)

### Community 1 - "RAG and Evaluation"
Cohesion: 0.06
Nodes (41): Qdrant Vector Database RAG Enhancement, deepeval_evaluate, deepeval_metrics, deepeval_test_case, OperationalEvaluator, Any, GARDA-JKN Advanced Data Science Pipeline for BPJS Kesehatan Fraud Detection.…, Translates ensemble TreeSHAP feature contributions into structured,… (+33 more)

### Community 2 - "Data Loading"
Cohesion: 0.06
Nodes (29): BaseEstimator, DataFrame, BPJSDataLoader, generate_semi_supervised_labels(), Manages robust loading of BPJS Stata (.dta) files with automatic path…, Finds the first existing candidate path., Loads FKRTL and Secondary Diagnosis tables. Falls back to realistic synthetic…, Generates realistic synthetic BPJS claim data adhering strictly to BPJS 2025… (+21 more)

### Community 3 - "Fraud Classifier"
Cohesion: 0.05
Nodes (24): ClassifierMixin, BalancedBaggingXGBoost, Ensemble of Balanced Bagging XGBoost Classifiers. Addresses extreme fraud class…, Stress testing BalancedBaggingXGBoost and strict compliance checks., Verify zero presence or importation of SMOTE, ADASYN, or imblearn., Stress test BalancedBaggingXGBoost on extreme class imbalance (98% neg, 2% pos)., Ensure BalancedBaggingXGBoost safely raises ValueError when no positive…, TestBalancedBaggingAndIntegrityChallenger (+16 more)

### Community 4 - "Qdrant RAG"
Cohesion: 0.05
Nodes (42): Local Qdrant Embedded Mode, M1 Qdrant Vector Database RAG Enhancement, Medical Metadata Chunking, search_rules, test_rag.py Verification, RAG Implementation Plan, Structured Clinical Metadata, MedicalKnowledgeBase (+34 more)

### Community 5 - "Next.js Frontend"
Cohesion: 0.05
Nodes (36): eslintConfig, nextConfig, dependencies, next, react, react-dom, devDependencies, eslint (+28 more)

### Community 6 - "FastAPI Backend"
Cohesion: 0.06
Nodes (36): adjudicate_claim(), ClaimData, EvaluationDetail, EvaluationResponse, health_check(), read_root(), dummy_gpu(), BaseModel (+28 more)

### Community 7 - "API Test Suite"
Cohesion: 0.07
Nodes (35): fastapi_testclient, assert_adjudication_contract(), client(), fixture, Comprehensive automated test suite for GARDA-JKN Claim Adjudication API.…, Test Case 1: Stroke with severe AKI KDIGO comorbidity. Scenario: - Primary:…, Test Case 2: Sepsis/Shock with 0 ICU days (Incoherence Anomaly). Scenario: -…, Test Case 3: STEMI with Cardiogenic Shock and Primary PCI. Scenario: - Primary:… (+27 more)

### Community 8 - "PDF Ingestion"
Cohesion: 0.11
Nodes (19): PNPK PDF Ingestion, argparse, dotenv, hashlib, huggingface_hub, extract_pages_from_pdf(), Any, Extract text from PDF pages with page number tracking. (+11 more)

### Community 9 - "Embedding Fallbacks"
Cohesion: 0.09
Nodes (12): FastLocalHashEmbeddings, Initialize AIML API embeddings with automatic local fallback., Fast, deterministic, zero-dependency embedding fallback. Produces unit-…, Embeddings, Uji penarikan aturan medis spesifik untuk Stroke Iskemik & Trombolisis rTPA., Uji penarikan pedoman intervensi koroner perkutan (PCI) dan waktu door-to-…, Uji aturan debridement bedah versus perawatan bangsal pada ulkus kaki diabetes., Uji aturan deteksi upcoding dan kriteria ventilator pada Severity Level III… (+4 more)

### Community 10 - "E2E Browser Tests"
Cohesion: 0.10
Nodes (21): Browser, Page, playwright_sync_api, pytest, requests, subprocess, browser_instance(), browser_page() (+13 more)

### Community 11 - "Concurrency Tests"
Cohesion: 0.13
Nodes (24): Client, concurrent_futures, execute_single_http_adjudication(), execute_single_ml_prediction(), execute_single_qdrant_query(), get_process_rss_mb(), live_server(), main() (+16 more)

### Community 12 - "Clinical Guidelines"
Cohesion: 0.08
Nodes (25): Cardiovascular Risk, Diabetes Diagnosis, PNPK Diabetes, Insulin Therapy, Lifestyle Intervention, Metformin, Microvascular Complications, Type 2 Diabetes Mellitus (+17 more)

### Community 13 - "Vector Search Core"
Cohesion: 0.09
Nodes (14): Any, Connects to embedded Qdrant or in-memory instance and initializes collection., Splits text content into semantic chunks and ingests into Qdrant. Preserves…, Subclass of list holding search result dictionaries: [{"text": str, "source":…, Ingests pre-constructed Document objects., Performs semantic similarity search against indexed clinical guidelines.…, Helper to format search result dictionaries into string., Returns collection metadata and point count. (+6 more)

### Community 14 - "TypeScript Config"
Cohesion: 0.11
Nodes (18): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+10 more)

### Community 15 - "Clinical Features"
Cohesion: 0.12
Nodes (10): ClinicalFeatureExtractor, Extracts features adhering strictly to BPJS 2025 specifications. Fixes baseline…, Transforms raw BPJS FKRTL dataframe and secondary diagnosis into feature matrix., Adversarial stress tests for ClinicalFeatureExtractor., Verify negative LOS is clipped to 0 and cost per day never divides by 0., Verify behavior when primary diagnosis is None/NaN and secondary table is empty…, Stress test with a claim containing 100 secondary diagnoses., Verify clinical validity: Sepsis + short stay + Meninggal != Fraud; Sepsis +… (+2 more)

### Community 16 - "LangGraph E2E Tests"
Cohesion: 0.18
Nodes (6): Test Scenario 2: STEMI with cardiogenic shock and verified emergency PCI ->…, Test Scenario 3: Refractory Epilepsy with unattached EEG traces at Type C…, Test Scenario 4: Batch Simulation with records from…, End-to-End Test Suite for GARDA-JKN LangGraph Adjudication Engine., Test Scenario 1: Stroke Iskemik with unsubstantiated AKI comorbidity ->…, TestGardaMultiAgentAdjudication

### Community 17 - "Adversarial Testing"
Cohesion: 0.22
Nodes (10): Adversarial Stress Testing, Challenger 1 Briefing, Malformed Payload Resilience, Null Billing TypeError, Reject Verdict, String Severity ValueError, Defensive Type Casting, Adversarial Challenge Handoff (+2 more)

### Community 18 - "ML XAI Requirements"
Cohesion: 0.25
Nodes (9): Three of Three LangGraph Runs Passed, Stratified Isolation Forest Analysis, Balanced Bagging XGBoost, Complex Claim Payload Processing, Original User Request, Explainable AI Evaluation, SHAP Auditor Reason Codes, Stratified Isolation Forest (+1 more)

### Community 19 - "Environment Audit"
Cohesion: 0.25
Nodes (9): Active AIML API, ClaimState Schema Mismatch, Codebase Environment Survey Handoff, Missing Critical Dependencies, Missing Test Suites, MLEngine API Mismatch, Module Encapsulation Plan, Naive DeepSeek JSON Parsing (+1 more)

### Community 20 - "Clinical Incoherence"
Cohesion: 0.28
Nodes (9): Clinical Incoherence Indicators, Explorer Survey 2 Briefing, Clinical Feature Extraction Interface, Hierarchical Fallback Strategy, Sample Strata Statistics, Suspect ICD Codes E43 J96, True LOS Columns FKL04 FKL03, True Severity Columns FKL23 FKL19 (+1 more)

### Community 21 - "Integrity Audit"
Cohesion: 0.29
Nodes (8): DeepSeek ChatOpenAI Executor, Forensic Integrity Audit Report, Genuine Qdrant Search, No Mock Bypasses, Qdrant File Locking, XGBoost SHAP Inference, LangGraph Multi-Agent Orchestration, Qdrant Semantic RAG

### Community 22 - "Leukemia Guidelines"
Cohesion: 0.25
Nodes (8): Acute Lymphoblastic Leukemia, CNS Prophylaxis, Consolidation Therapy, PNPK Leukemia, Induction Therapy, Maintenance Therapy, Minimal Residual Disease, Tumor Lysis Syndrome

### Community 23 - "Audit Findings"
Cohesion: 0.29
Nodes (7): Clean Audit Verdict, Auditor 1 Briefing, Forensic Integrity Audit, Live DeepSeek Calls, Live Qdrant Search, Severity Level Casting Vulnerability, Severity Level ValueError

### Community 24 - "Reliability Results"
Cohesion: 0.33
Nodes (7): 28 QPS With Zero Errors, Approve Verdict, Concurrency Latency Handoff, Five of Five RAG Runs Passed, In-Memory Qdrant Fallback, Mean LLM Latency 3.37 Seconds, Remote Embedding Rate Limits

### Community 25 - "Architecture Layers"
Cohesion: 0.29
Nodes (7): ClaimState, Lapis 1 ML Risk Engine, Lapis 2 Knowledge Base and RAG, Lapis 3 Multi-Agent StateGraph, Lapis 4 E2E Verification and XAI, Persistent Qdrant Collection, Workflow Entry Exit Contract

### Community 26 - "Adjudication Workflow"
Cohesion: 0.33
Nodes (7): APPROVED DOWNGRADED ESCALATED Statuses, ClaimState, DeepSeek Chat Model, Executor Escalation Fallback, Executor Node, Formal Indonesian Adjudication Phrasing, Validator Node

### Community 28 - "Epilepsy Guidelines"
Cohesion: 0.29
Nodes (7): Antiseizure Medication, Brain MRI, Drug-Resistant Epilepsy, Electroencephalography, Epileptic Seizure, PNPK Epilepsy, Status Epilepticus

### Community 29 - "Concurrency Reliability"
Cohesion: 0.40
Nodes (5): Concurrent Vector Search, DeepSeek Latency SLA, Deterministic Test Suites, Disk Lock Fallback, Challenger 2 Replacement Briefing

### Community 30 - "Acceptance Milestones"
Cohesion: 0.40
Nodes (5): Direct Iteration Workflow, GARDA-JKN Healthkathon BPJS 2026, R1 Qdrant RAG, R2 LangGraph Multi-Agent, R3 E2E Verification

### Community 31 - "LLM Executor Validator"
Cohesion: 0.50
Nodes (4): DeepSeek AIML API, Executor Pengeksekusi, Formal Indonesian Medical Terminology, Validator Pengecek

### Community 32 - "Embedding Providers"
Cohesion: 0.50
Nodes (4): AIML API Embeddings, FastEmbed or SentenceTransformers Fallback, FastLocalHashEmbeddings, sentence-transformers Dependency

### Community 33 - "Clinical Rule Tests"
Cohesion: 0.67
Nodes (3): Status Epilepticus EEG Rule, STEMI Primary PCI Rule, Stroke KDIGO AKI Rule

### Community 34 - "Deployment Surfaces"
Cohesion: 0.67
Nodes (3): End-to-End Comprehensive Testing, FastAPI Railway Backend, Next.js Vercel Frontend

## Knowledge Gaps
- **212 isolated node(s):** `eslintConfig`, `nextConfig`, `name`, `version`, `private` (+207 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 444 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **59 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `MedicalKnowledgeBase` connect `Qdrant RAG` to `PDF Ingestion`?**
  _High betweenness centrality (0.061) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `MedicalKnowledgeBase` (e.g. with `execute_single_search()` and `TestMedicalRAGPipeline`) actually correct?**
  _`MedicalKnowledgeBase` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `BalancedBaggingXGBoost` (e.g. with `TestBalancedBaggingAndIntegrityChallenger` and `TestShapAuditorReasonCodeGeneratorChallenger`) actually correct?**
  _`BalancedBaggingXGBoost` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `ClaimState` (e.g. with `executor_node()` and `intake_node()`) actually correct?**
  _`ClaimState` has 7 INFERRED edges - model-reasoned connections that need verification._
- **What connects `eslintConfig`, `nextConfig`, `name` to the rest of the system?**
  _212 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `LangGraph Agents` be split into smaller, more focused modules?**
  _Cohesion score 0.05674044265593561 - nodes in this community are weakly interconnected._
- **Should `RAG and Evaluation` be split into smaller, more focused modules?**
  _Cohesion score 0.05701754385964912 - nodes in this community are weakly interconnected._