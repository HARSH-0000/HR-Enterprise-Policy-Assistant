"""Vector store management for policy indexing and retrieval."""

from functools import lru_cache

from pinecone import Pinecone, ServerlessSpec

from langchain_pinecone import PineconeVectorStore

from app.core.config import settings
from app.rag.embeddings import get_embedding_model


@lru_cache(maxsize=1)
def get_vectorstore():
    """Initializes and returns the Pinecone vector store singleton."""

    if not settings.pinecone_api_key:
        raise ValueError("PINECONE_API_KEY is missing.")

    if not settings.pinecone_index:
        raise ValueError("PINECONE_INDEX is missing.")

    pc = Pinecone(
        api_key=settings.pinecone_api_key
    )

    existing_indexes = pc.list_indexes().names()

    if settings.pinecone_index not in existing_indexes:

        pc.create_index(
            name=settings.pinecone_index,
            dimension=384,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )

        raise RuntimeError(
            "Pinecone index created. Wait until it is ready, "
            "then restart the application."
        )

    index = pc.Index(settings.pinecone_index)

    return PineconeVectorStore(
        index=index,
        embedding=get_embedding_model(),
        namespace=settings.pinecone_namespace,
        text_key="text"  # Specify the text field key
    )


def get_retriever():
    """Returns a similarity-search retriever over the vector store."""

    vectorstore = get_vectorstore()

    return vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={
            "k": settings.retrieval_k
        }
    )
