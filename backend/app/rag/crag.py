"""Corrective RAG (CRAG) pipeline implementation using LangGraph.

Evaluates retrieved documents, rewrites queries when documents are
irrelevant, verifies answer grounding, and synthesizes the final response.
"""

import logging
from typing import TypedDict, List, Optional

from langchain_groq import ChatGroq
from langchain_core.documents import Document
from langgraph.graph import StateGraph, START, END

from app.core.config import settings

from app.rag.prompts import (
    ANSWER_PROMPT,
    REWRITE_PROMPT,
    RELEVANCE_PROMPT,
    GROUNDING_PROMPT
)


logger = logging.getLogger(__name__)


class HRState(TypedDict):

    question: str
    search_query: str
    documents: List[Document]
    context: str
    answer: str
    grounded: Optional[bool]
    verify_grounding: bool
    retry_count: int
    status: str


def build_hr_crag_graph(
    retriever,
    reranker=None
):
    """Build and compile the CRAG LangGraph workflow.

    Args:
        retriever: A LangChain retriever for HR policy documents.
        reranker: Optional callable(question, documents, top_k) for reranking.

    Returns:
        A compiled LangGraph that accepts HRState and produces an answer.
    """

    llm = ChatGroq(
        model=settings.groq_model,
        api_key=settings.groq_api_key,
        temperature=0
    )

    # --------------------------------
    # Node 1: Retrieve HR Documents
    # --------------------------------

    def retrieve(state: HRState):

        query = state.get(
            "search_query"
        ) or state["question"]

        logger.info("Retrieving documents for: %s", query[:100])

        documents = retriever.invoke(query)

        if reranker and documents:
            documents = reranker(
                state["question"],
                documents,
                top_k=4
            )

        # Only approved documents are eligible.
        approved_documents = [
            doc
            for doc in documents
            if (
                doc.metadata or {}
            ).get("status") == "approved"
        ]

        logger.info(
            "Retrieved %d docs, %d approved",
            len(documents),
            len(approved_documents),
        )

        return {
            "documents": approved_documents,
            "context": "\n\n".join(
                doc.page_content
                for doc in approved_documents
            )
        }

    # --------------------------------
    # Node 2: Grade Document Relevance
    # --------------------------------

    def grade_documents(state: HRState):

        relevant_documents = []

        for document in state["documents"]:

            response = llm.invoke(
                RELEVANCE_PROMPT.format(
                    question=state["question"],
                    document=document.page_content
                )
            )

            grade = response.content.strip().lower()

            if "relevant" in grade and "irrelevant" not in grade:
                relevant_documents.append(document)

        logger.info(
            "Graded %d -> %d relevant",
            len(state["documents"]),
            len(relevant_documents),
        )

        return {
            "documents": relevant_documents,
            "context": "\n\n".join(
                doc.page_content
                for doc in relevant_documents
            )
        }

    # --------------------------------
    # Node 3: Rewrite Search Query
    # --------------------------------

    def rewrite_query(state: HRState):

        response = llm.invoke(
            REWRITE_PROMPT.format(
                question=state["question"]
            )
        )

        new_query = response.content.strip()
        logger.info("Rewrote query to: %s", new_query[:100])

        return {
            "search_query": new_query,
            "retry_count": state.get("retry_count", 0) + 1
        }

    # --------------------------------
    # Node 4: Generate Answer
    # --------------------------------

    def generate_answer(state: HRState):

        if not state["documents"]:
            return {
                "answer": (
                    "I could not find an approved HR policy "
                    "that answers your question. Please "
                    "contact the HR department."
                ),
                "grounded": False,
                "status": "insufficient_evidence"
            }

        response = llm.invoke(
            ANSWER_PROMPT.format(
                context=state["context"],
                question=state["question"]
            )
        )

        return {
            "answer": response.content,
            "status": "generated"
        }

    # --------------------------------
    # Node 5: Verify Answer Grounding
    # --------------------------------

    def verify_answer(state: HRState):

        # Skip verification for fallback answers
        if state.get("status") == "insufficient_evidence":
            return {
                "grounded": False,
                "status": "insufficient_evidence"
            }

        if not state.get("verify_grounding", True):
            logger.info("Grounding verification disabled for this request.")
            return {
                "grounded": None,
                "status": "verification_skipped"
            }

        response = llm.invoke(
            GROUNDING_PROMPT.format(
                context=state["context"],
                answer=state["answer"]
            )
        )

        grounded = (
            "grounded" in response.content.strip().lower()
            and "not_grounded" not in response.content.strip().lower()
        )

        if not grounded:

            return {
                "grounded": False,
                "status": "ungrounded",
                "answer": (
                    "I could not verify this answer "
                    "against the approved HR policies. "
                    "Please contact HR for confirmation."
                )
            }

        return {
            "grounded": True,
            "status": "answered"
        }

    # --------------------------------
    # Node 6: Conditional Routing
    # --------------------------------

    def route_after_grading(state: HRState):

        if state["documents"]:
            return "generate"

        if state.get("retry_count", 0) < settings.max_retries:
            return "rewrite"

        return "generate"

    # --------------------------------
    # Build LangGraph
    # --------------------------------

    workflow = StateGraph(HRState)

    workflow.add_node("retrieve", retrieve)
    workflow.add_node("grade", grade_documents)
    workflow.add_node("rewrite", rewrite_query)
    workflow.add_node("generate", generate_answer)
    workflow.add_node("verify", verify_answer)

    workflow.add_edge(START, "retrieve")

    workflow.add_edge("retrieve", "grade")

    workflow.add_conditional_edges(
        "grade",
        route_after_grading,
        {
            "generate": "generate",
            "rewrite": "rewrite"
        }
    )

    workflow.add_edge("rewrite", "retrieve")

    workflow.add_edge("generate", "verify")

    workflow.add_edge("verify", END)

    return workflow.compile()
