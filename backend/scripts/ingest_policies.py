"""Script to parse and ingest HR policy documents into Pinecone."""

import json
import hashlib
import uuid
import time
import sys
import logging

from pathlib import Path

from pinecone import Pinecone, ServerlessSpec

from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader
)

from langchain_text_splitters import RecursiveCharacterTextSplitter

# Add parent dir to sys.path so `app` is importable when running
# this script directly: python scripts/ingest_policies.py
sys.path.insert(
    0, str(Path(__file__).resolve().parents[1])
)

from app.core.config import settings               # noqa: E402
from app.rag.embeddings import get_embedding_model  # noqa: E402


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
)
logger = logging.getLogger(__name__)


# -----------------------------------------------------------
# Constants
# -----------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]

POLICY_DIR = BASE_DIR / "data" / "hr_policies"

MANIFEST_PATH = POLICY_DIR / "policy_manifest.json"

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150

SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".txt",
    ".md"
}

BATCH_SIZE = 50

# Pinecone index readiness wait (seconds)
INDEX_READY_WAIT = 15


# -----------------------------------------------------------
# Helpers
# -----------------------------------------------------------

def load_manifest():
    """Load the policy manifest (filename -> metadata)."""

    if not MANIFEST_PATH.exists():
        logger.warning("No manifest at %s — metadata will be defaults.", MANIFEST_PATH)
        return {}

    with open(
        MANIFEST_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


def load_document(file_path: Path):
    """Load a single file into LangChain Document objects."""

    extension = file_path.suffix.lower()

    if extension == ".pdf":

        loader = PyPDFLoader(str(file_path))

    elif extension in {".txt", ".md"}:

        loader = TextLoader(
            str(file_path),
            encoding="utf-8"
        )

    else:
        return []

    return loader.load()


def load_all_policies():
    """Walk the policy directory and load every supported file."""

    documents = []

    manifest = load_manifest()

    for file_path in sorted(POLICY_DIR.rglob("*")):

        if not file_path.is_file():
            continue

        if file_path == MANIFEST_PATH:
            continue

        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        logger.info("Loading: %s", file_path.name)

        try:

            loaded_docs = load_document(file_path)

            if not loaded_docs:
                logger.warning("No text extracted from %s", file_path.name)
                continue

            policy_metadata = manifest.get(
                file_path.name,
                {}
            )

            for document in loaded_docs:

                # Merge manifest metadata onto each page/chunk
                document.metadata.update({

                    "source": file_path.name,

                    "title": policy_metadata.get(
                        "title",
                        file_path.stem
                    ),

                    "policy_id": policy_metadata.get(
                        "policy_id",
                        "UNKNOWN"
                    ),

                    "version": policy_metadata.get(
                        "version",
                        "UNKNOWN"
                    ),

                    "status": policy_metadata.get(
                        "status",
                        "pending_review"
                    ),

                    "effective_date": policy_metadata.get(
                        "effective_date",
                        "UNKNOWN"
                    ),

                    "department": policy_metadata.get(
                        "department",
                        "Human Resources"
                    ),

                    # Keep page as a string for Pinecone metadata
                    "page": str(
                        document.metadata.get(
                            "page",
                            ""
                        )
                    )
                })

                documents.append(document)

            logger.info(
                "Extracted %d pages from %s",
                len(loaded_docs),
                file_path.name,
            )

        except Exception as error:

            logger.error(
                "Failed to load %s: %s",
                file_path.name,
                error,
            )

    return documents


def split_documents(documents):
    """Chunk documents with RecursiveCharacterTextSplitter."""

    splitter = RecursiveCharacterTextSplitter(

        chunk_size=CHUNK_SIZE,

        chunk_overlap=CHUNK_OVERLAP,

        separators=[
            "\n\n",
            "\n",
            ". ",
            " ",
            ""
        ]
    )

    chunks = splitter.split_documents(documents)

    logger.info("Total chunks created: %d", len(chunks))

    return chunks


def generate_ids(chunks):
    """Deterministic IDs: source + page + content hash -> UUID5."""

    ids = []

    for chunk in chunks:

        source = chunk.metadata.get(
            "source",
            "unknown"
        )

        page = chunk.metadata.get(
            "page",
            ""
        )

        content_hash = hashlib.sha256(
            chunk.page_content.encode("utf-8")
        ).hexdigest()

        unique_string = (
            f"{source}|{page}|{content_hash}"
        )

        document_id = str(
            uuid.uuid5(
                uuid.NAMESPACE_URL,
                unique_string
            )
        )

        ids.append(document_id)

    return ids


def initialize_pinecone():
    """Create (or recreate) the Pinecone index."""

    if not settings.pinecone_api_key:
        raise ValueError(
            "PINECONE_API_KEY is missing."
        )

    pc = Pinecone(
        api_key=settings.pinecone_api_key
    )

    existing_indexes = pc.list_indexes().names()

    if settings.pinecone_index in existing_indexes:
        logger.info("Deleting existing index: %s", settings.pinecone_index)
        pc.delete_index(settings.pinecone_index)
        logger.info("Index deleted.")

    logger.info("Creating Pinecone index...")

    pc.create_index(

        name=settings.pinecone_index,

        dimension=384,

        metric="cosine",

        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        )
    )

    logger.info(
        "Index created. Waiting %ds for initialization...",
        INDEX_READY_WAIT,
    )
    time.sleep(INDEX_READY_WAIT)

    return pc.Index(settings.pinecone_index)


def _sanitize_metadata(metadata: dict) -> dict:
    """Ensure all metadata values are Pinecone-safe types
    (str, int, float, bool, or list of str)."""

    clean = {}
    for key, value in metadata.items():
        if value is None:
            continue
        if isinstance(value, (str, int, float, bool)):
            clean[key] = value
        elif isinstance(value, list):
            clean[key] = [str(v) for v in value]
        else:
            clean[key] = str(value)
    return clean


def store_documents(chunks):
    """Embed chunks and upsert into Pinecone in batches."""

    if not chunks:
        logger.warning("No chunks available for ingestion.")
        return

    index = initialize_pinecone()

    if index is None:
        return

    embeddings = get_embedding_model()

    ids = generate_ids(chunks)

    total_uploaded = 0

    for start in range(0, len(chunks), BATCH_SIZE):

        batch_chunks = chunks[
            start:start + BATCH_SIZE
        ]

        batch_ids = ids[
            start:start + BATCH_SIZE
        ]

        # Generate embeddings for this batch
        texts = [
            chunk.page_content for chunk in batch_chunks
        ]

        embeddings_list = embeddings.embed_documents(texts)

        # Prepare vectors for upsert with sanitized metadata
        vectors_to_upsert = []

        for vec_id, embedding, chunk in zip(
            batch_ids, embeddings_list, batch_chunks
        ):
            # Add text content to metadata
            metadata = _sanitize_metadata(chunk.metadata)
            metadata['text'] = chunk.page_content  # Store the actual text
            
            vectors_to_upsert.append((
                vec_id,
                embedding,
                metadata
            ))

        # Upsert to Pinecone
        try:
            index.upsert(
                vectors=vectors_to_upsert,
                namespace=settings.pinecone_namespace
            )
            total_uploaded += len(batch_chunks)
            logger.info(
                "Uploaded batch: %d chunks (total: %d/%d)",
                len(batch_chunks),
                total_uploaded,
                len(chunks),
            )
        except Exception as e:
            logger.error("Error upserting batch at offset %d: %s", start, e)
            raise

    logger.info("Ingestion completed successfully. %d chunks stored.", total_uploaded)


# -----------------------------------------------------------
# Main
# -----------------------------------------------------------

def main():

    logger.info("=" * 50)
    logger.info("HR POLICY INGESTION PIPELINE")
    logger.info("=" * 50)

    if not POLICY_DIR.exists():

        raise FileNotFoundError(
            f"Policy directory not found: {POLICY_DIR}"
        )

    # Step 1: Load documents
    documents = load_all_policies()

    if not documents:

        logger.warning("No supported documents found in %s", POLICY_DIR)
        return

    logger.info("Loaded %d document pages total.", len(documents))

    # Step 2: Split documents
    chunks = split_documents(documents)

    # Step 3: Upload to Pinecone
    store_documents(chunks)


if __name__ == "__main__":

    main()
