"""Compare HR CRAG with and without relevance grading.

Run from backend/:
    python scripts/evaluate_relevance_grading.py --dataset evaluation/hr_qa_40.csv

The benchmark CSV must contain exactly 40 policy-grounded questions and
reference answers derived from the actual HR policy corpus.
"""
import argparse
import csv
import json
import logging
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from langchain_groq import ChatGroq

from app.core.config import settings
from app.rag.crag import build_hr_crag_graph
from app.rag.reranker import rerank_documents
from app.rag.vectorstore import get_retriever
from app.services.chat_service import answer_question

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("grading-evaluation")

REQUIRED_COLUMNS = {
    "id", "question", "reference_answer", "expected_source", "should_abstain"
}

JUDGE_PROMPT = """You are evaluating an enterprise HR policy assistant.
Compare the assistant response with the reference answer below.

Rules:
- Mark answer_correct true only if the response conveys the materially
  correct policy facts without inventing or contradicting policy details.
- If should_abstain is true, answer_correct is true only when the assistant
  clearly declines to provide an unsupported policy answer and directs the
  employee to HR or an authoritative source.
- If should_abstain is false, a generic refusal is not correct.
- Do not reward confident wording without factual support.
Return ONLY valid JSON with keys:
{"answer_correct": true/false, "reason": "short explanation"}

Question: {question}
Reference answer: {reference_answer}
Should abstain: {should_abstain}
Assistant response: {actual_answer}
Retrieved sources: {sources}
"""


def parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized not in {"true", "false", "yes", "no", "1", "0"}:
        raise ValueError(f"Expected true/false value, got: {value!r}")
    return normalized in {"true", "yes", "1"}


def load_dataset(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Dataset is missing columns: {sorted(missing)}")
        rows = list(reader)

    if len(rows) != 40:
        raise ValueError(f"Expected exactly 40 questions; found {len(rows)}.")

    for row in rows:
        for field in ("question", "reference_answer"):
            if not row[field].strip():
                raise ValueError(
                    f"Question {row.get('id', '?')} has an empty {field}."
                )
        parse_bool(row["should_abstain"])
    return rows


def judge_answer(judge, row, result):
    sources = result.get("sources", [])
    raw = judge.invoke(JUDGE_PROMPT.format(
        question=row["question"],
        reference_answer=row["reference_answer"],
        should_abstain=parse_bool(row["should_abstain"]),
        actual_answer=result.get("answer", ""),
        sources=json.dumps(sources, ensure_ascii=False),
    )).content

    if isinstance(raw, list):
        raw = "".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in raw
        )
    raw = str(raw).strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    try:
        verdict = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Judge returned invalid JSON: {raw}") from exc
    return bool(verdict["answer_correct"]), str(verdict.get("reason", ""))


def run_variant(rows, graph, judge, variant):
    records = []
    for position, row in enumerate(rows, start=1):
        started = time.perf_counter()
        result = answer_question(graph, row["question"])
        latency = time.perf_counter() - started

        correct, reason = judge_answer(judge, row, result)
        sources = result.get("sources", [])
        source_text = " ".join(
            f"{source.get('title', '')} {source.get('policy_id', '')}"
            for source in sources
        ).lower()
        expected_source = row.get("expected_source", "").strip().lower()
        source_hit = (
            bool(expected_source) and expected_source in source_text
        ) if expected_source else None

        record = {
            "id": row["id"],
            "variant": variant,
            "question": row["question"],
            "reference_answer": row["reference_answer"],
            "actual_answer": result.get("answer", ""),
            "answer_correct": correct,
            "judge_reason": reason,
            "grounded": bool(result.get("grounded", False)),
            "status": result.get("status", ""),
            "source_hit": source_hit,
            "sources": json.dumps(sources, ensure_ascii=False),
            "latency_seconds": round(latency, 3),
        }
        records.append(record)
        logger.info(
            "[%s] %02d/40 | correct=%s | grounded=%s | %.2fs",
            variant, position, correct, record["grounded"], latency
        )
    return records


def summarize(records):
    total = len(records)
    return {
        "questions": total,
        "answer_accuracy_percent": round(
            100 * sum(r["answer_correct"] for r in records) / total, 2
        ),
        "grounded_response_percent": round(
            100 * sum(r["grounded"] for r in records) / total, 2
        ),
        "source_hit_percent": (
            round(100 * sum(r["source_hit"] is True for r in records)
                  / sum(r["source_hit"] is not None for r in records), 2)
            if any(r["source_hit"] is not None for r in records) else None
        ),
        "average_latency_seconds": round(
            sum(r["latency_seconds"] for r in records) / total, 3
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset", type=Path,
        default=BASE_DIR / "evaluation" / "hr_qa_40.csv"
    )
    parser.add_argument(
        "--output-dir", type=Path,
        default=BASE_DIR / "evaluation" / "results"
    )
    args = parser.parse_args()

    if not settings.groq_api_key or not settings.pinecone_api_key:
        raise RuntimeError("Set GROQ_API_KEY and PINECONE_API_KEY in backend/.env")

    rows = load_dataset(args.dataset)
    logger.info("Loading embedding model, reranker, and Pinecone retriever...")
    from app.rag.embeddings import get_embedding_model
    get_embedding_model()
    from app.rag.reranker import _get_reranker
    _get_reranker()
    retriever = get_retriever()

    # Keep retrieval and reranking identical; only document relevance grading
    # and its dependent query-rewrite loop are ablated.
    graph_with = build_hr_crag_graph(
        retriever, reranker=rerank_documents, enable_relevance_grading=True
    )
    graph_without = build_hr_crag_graph(
        retriever, reranker=rerank_documents, enable_relevance_grading=False
    )
    judge = ChatGroq(
        model=settings.groq_model,
        api_key=settings.groq_api_key,
        temperature=0,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    all_records = []
    for label, graph in (
        ("with_relevance_grading", graph_with),
        ("without_relevance_grading", graph_without),
    ):
        all_records.extend(run_variant(rows, graph, judge, label))

    detail_path = args.output_dir / "relevance_grading_comparison.csv"
    columns = list(all_records[0].keys())
    with detail_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(all_records)

    summaries = {
        "with_relevance_grading": summarize(
            [r for r in all_records if r["variant"] == "with_relevance_grading"]
        ),
        "without_relevance_grading": summarize(
            [r for r in all_records if r["variant"] == "without_relevance_grading"]
        ),
        "evaluation_notes": [
            "LLM-as-judge scores are estimates; manually review incorrect and borderline cases.",
            "Both variants use the same retriever, reranker, model, policy index, and question set.",
            "The no-grading variant bypasses document relevance grading and query rewriting.",
            "Run both variants against the same unchanged Pinecone namespace.",
        ],
    }
    summary_path = args.output_dir / "relevance_grading_summary.json"
    summary_path.write_text(
        json.dumps(summaries, indent=2), encoding="utf-8"
    )
    print(json.dumps(summaries, indent=2))
    print(f"Detailed results: {detail_path}")
    print(f"Summary: {summary_path}")


if __name__ == "__main__":
    main()
