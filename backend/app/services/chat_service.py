"""Chat service orchestrating user queries with the CRAG pipeline."""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def answer_question(
    crag_graph,
    question: str
) -> Dict[str, Any]:
    """
    Invoke the CRAG workflow to answer HR policy questions.

    Args:
        crag_graph: The compiled LangGraph CRAG workflow.
        question: User question about HR policies.

    Returns:
        Dictionary with answer, sources, grounded flag, and status.

    Raises:
        Exception: Propagated to the caller (main.py) for
        proper HTTP error handling. No silent swallowing.
    """

    # Initialize state with all required fields
    initial_state = {
        "question": question,
        "search_query": "",
        "documents": [],
        "context": "",
        "answer": "",
        "grounded": False,
        "retry_count": 0,
        "status": "processing"
    }

    # Invoke the CRAG graph
    result = crag_graph.invoke(initial_state)

    # Extract the answer
    answer = result.get(
        "answer",
        "I couldn't find an answer to your question."
    )

    # Build source metadata from surviving documents
    sources: List[Dict[str, Any]] = []
    for doc in result.get("documents", []):
        meta = doc.metadata or {}
        sources.append({
            "title": meta.get("title", "HR Policy"),
            "policy_id": meta.get("policy_id", "UNKNOWN"),
            "page": _safe_int(meta.get("page")),
            "department": meta.get(
                "department", "Human Resources"
            ),
            "status": meta.get("status", "pending_review"),
            "section": meta.get("section"),
            "version": meta.get("version"),
            "effective_date": meta.get("effective_date"),
        })

    return {
        "answer": answer,
        "sources": sources,
        "grounded": result.get("grounded", False),
        "status": result.get("status", "answered"),
    }


def _safe_int(value) -> int:
    """Convert a value to int safely, defaulting to 0."""
    if value is None:
        return 0
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0
