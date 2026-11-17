"""Reranker module for scoring and reordering retrieved candidate documents."""

from functools import lru_cache
from typing import List

from sentence_transformers import CrossEncoder

from langchain_core.documents import Document


MODEL_NAME = "BAAI/bge-reranker-base"


@lru_cache(maxsize=1)
def _get_reranker():
    """Returns a singleton CrossEncoder reranker."""

    return CrossEncoder(
        MODEL_NAME,
        device="cpu"
    )


def rerank_documents(
    question: str,
    documents: List[Document],
    top_k: int = 4
) -> List[Document]:
    """Reranks retrieved policy snippets based on relevance to query.

    Args:
        question: The user's HR policy question.
        documents: Candidate documents from the retriever.
        top_k: Maximum number of top documents to return.

    Returns:
        Reranked list of documents, capped at top_k.
    """

    if not documents:
        return []

    model = _get_reranker()

    pairs = [
        [question, document.page_content]
        for document in documents
    ]

    scores = model.predict(pairs)

    ranked_documents = sorted(
        zip(documents, scores),
        key=lambda item: float(item[1]),
        reverse=True
    )

    return [
        document
        for document, _score in ranked_documents[:top_k]
    ]
