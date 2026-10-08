"""Run exact-decision, DeepEval, and Ragas checks on synthetic golden cases.

The runner calls the local API and writes only synthetic claims and aggregate
evaluation results. It never reads the raw BPJS files.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

import requests
from datasets import Dataset


ROOT = Path(__file__).resolve().parents[1]
GOLDEN_PATH = ROOT / "evaluation" / "golden_cases.json"
BACKEND_URL = os.getenv("GARDA_BACKEND_URL", "http://127.0.0.1:8000")


def call_backend(claim: dict[str, Any]) -> dict[str, Any]:
    response = requests.post(f"{BACKEND_URL}/api/v1/adjudicate", json=claim, timeout=180)
    response.raise_for_status()
    return response.json()


def exact_report(cases: list[dict[str, Any]], responses: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for case, result in zip(cases, responses):
        detail = result.get("response", {})
        decision = detail.get("decision") or detail.get("adjudication_result")
        severity = detail.get("severity_level")
        rows.append({
            "id": case["id"],
            "expected_decision": case["expected_decision"],
            "actual_decision": decision,
            "decision_correct": decision == case["expected_decision"],
            "expected_severity": case["expected_severity"],
            "actual_severity": severity,
            "severity_correct": severity == case["expected_severity"],
        })
    return {
        "decision_accuracy": sum(row["decision_correct"] for row in rows) / len(rows),
        "severity_accuracy": sum(row["severity_correct"] for row in rows) / len(rows),
        "rows": rows,
    }


def run_deepeval(cases: list[dict[str, Any]], responses: list[dict[str, Any]]) -> dict[str, Any]:
    from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric, GEval
    from deepeval.test_case import LLMTestCase, LLMTestCaseParams

    os.environ["OPENAI_API_KEY"] = os.getenv("AIML_API_KEY", os.getenv("OPENAI_API_KEY", ""))
    os.environ.setdefault("OPENAI_BASE_URL", "https://api.aimlapi.com/v1")
    model = os.getenv("DEEPEVAL_MODEL", "deepseek/deepseek-chat")
    metrics = [
        AnswerRelevancyMetric(threshold=0.7, model=model, async_mode=False),
        FaithfulnessMetric(threshold=0.7, model=model, async_mode=False),
        GEval(
            name="Decision Correctness",
            criteria="Evaluate whether the adjudication explicitly matches the expected decision and severity.",
            evaluation_steps=[
                "Compare the actual adjudication reason with the expected decision and severity.",
                "Do not treat confidence, cost, or a plausible narrative as evidence of correctness.",
            ],
            evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],
            model=model,
            threshold=0.7,
            async_mode=False,
        ),
    ]
    report = []
    for case, result in zip(cases, responses):
        detail = result.get("response", {})
        test_case = LLMTestCase(
            input=(f"Evaluasi klaim {case['id']} dengan diagnosis {case['claim'].get('diag_awal')}."),
            actual_output=detail.get("adjudication_reason", ""),
            expected_output=(f"Decision={case['expected_decision']}; Severity={case['expected_severity']}"),
            retrieval_context=[detail.get("rag_context", "")],
        )
        row = {"id": case["id"]}
        for metric in metrics:
            try:
                metric.measure(test_case)
                row[metric.__class__.__name__] = {
                    "score": metric.score,
                    "success": metric.is_successful(),
                    "reason": metric.reason,
                }
            except Exception as exc:
                row[metric.__class__.__name__] = {"error": str(exc)}
        report.append(row)
    return {"model": model, "cases": report}


def run_ragas(cases: list[dict[str, Any]], responses: list[dict[str, Any]]) -> dict[str, Any]:
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
    from ragas import evaluate
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from ragas.llms import LangchainLLMWrapper
    from ragas.metrics import answer_relevancy, context_precision, context_recall, faithfulness

    api_key = os.getenv("AIML_API_KEY", os.getenv("OPENAI_API_KEY", ""))
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.aimlapi.com/v1")
    model = os.getenv("RAGAS_MODEL", "deepseek/deepseek-chat")
    llm = ChatOpenAI(api_key=api_key, base_url=base_url, model=model, temperature=0)
    embeddings = OpenAIEmbeddings(
        api_key=api_key,
        base_url=base_url,
        model=os.getenv("RAGAS_EMBEDDING_MODEL", "openai/text-embedding-3-small"),
    )
    rows = []
    for case, result in zip(cases, responses):
        detail = result.get("response", {})
        rows.append({
            "user_input": f"Evaluasi klaim {case['id']} dengan diagnosis {case['claim'].get('diag_awal')}.",
            "response": detail.get("adjudication_reason", ""),
            "retrieved_contexts": [detail.get("rag_context", "")],
            "reference": f"Decision={case['expected_decision']}; Severity={case['expected_severity']}",
        })
    dataset = Dataset.from_list(rows)
    result = evaluate(
        dataset,
        metrics=[faithfulness, context_precision, context_recall, answer_relevancy],
        llm=LangchainLLMWrapper(llm),
        embeddings=LangchainEmbeddingsWrapper(embeddings),
        raise_exceptions=False,
    )
    return {"model": model, "metrics": result.to_pandas().to_dict(orient="records")}


def main() -> None:
    cases = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    responses = [call_backend(case["claim"]) for case in cases]
    report: dict[str, Any] = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "backend_url": BACKEND_URL,
        "case_count": len(cases),
        "exact": exact_report(cases, responses),
    }
    try:
        report["deepeval"] = run_deepeval(cases, responses)
    except Exception as exc:
        report["deepeval"] = {"error": str(exc)}
    try:
        report["ragas"] = run_ragas(cases, responses)
    except Exception as exc:
        report["ragas"] = {"error": str(exc)}

    output_dir = ROOT / "evaluation" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "full_evaluation_latest.json"
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False, default=str))
    print(f"Report: {output_path}")


if __name__ == "__main__":
    main()
