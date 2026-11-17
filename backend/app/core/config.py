import os
from dataclasses import dataclass, field
from typing import List

from dotenv import load_dotenv

load_dotenv()


def _csv(name: str, default: str) -> List[str]:
    return [
        item.strip()
        for item in os.getenv(name, default).split(",")
        if item.strip()
    ]


@dataclass(frozen=True)
class Settings:

    # Groq configuration
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_model: str = os.getenv(
        "GROQ_MODEL",
        "llama-3.3-70b-versatile"
    )

    # Pinecone configuration
    pinecone_api_key: str = os.getenv("PINECONE_API_KEY", "")
    pinecone_index: str = os.getenv(
        "PINECONE_INDEX",
        "hr-enterprise-assistant"
    )
    pinecone_namespace: str = os.getenv(
        "PINECONE_NAMESPACE",
        "company-policies"
    )

    # Embedding configuration
    embedding_model: str = os.getenv(
        "EMBEDDING_MODEL",
        "sentence-transformers/all-MiniLM-L6-v2"
    )

    # RAG configuration
    retrieval_k: int = int(
        os.getenv("RETRIEVAL_K", "8")
    )

    max_retries: int = int(
        os.getenv("MAX_RETRIES", "1")
    )

    cors_origins: List[str] = field(default=None)

    def __post_init__(self):
        object.__setattr__(
            self,
            "cors_origins",
            _csv(
                "CORS_ORIGINS",
                "http://localhost:5173"
            )
        )

        # Validate critical keys at startup
        if not self.groq_api_key:
            import warnings
            warnings.warn(
                "GROQ_API_KEY is not set. LLM calls will fail.",
                stacklevel=2,
            )

        if not self.pinecone_api_key:
            import warnings
            warnings.warn(
                "PINECONE_API_KEY is not set. Vector store calls will fail.",
                stacklevel=2,
            )


settings = Settings()
