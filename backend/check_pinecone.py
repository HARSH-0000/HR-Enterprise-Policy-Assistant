from pinecone import Pinecone
from app.core.config import settings

pc = Pinecone(api_key=settings.pinecone_api_key)
index = pc.Index(settings.pinecone_index)
stats = index.describe_index_stats()

print(f"Index: {settings.pinecone_index}")
print(f"Total vectors: {stats.total_vector_count}")
print(f"Namespace: {settings.pinecone_namespace}")

ns_stats = stats.namespaces.get(settings.pinecone_namespace, {})
ns_count = ns_stats.get('vector_count', 0)
print(f"Namespace vectors: {ns_count}")

if ns_count == 0:
    print("\nERROR: No vectors in namespace! Need to run ingestion.")
else:
    print(f"\nOK: {ns_count} vectors found in namespace.")
