"""Test to verify content is plain text before and after Qdrant storage"""
import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams

# Initialize Qdrant client
client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY")
)

COLLECTION = "test_content_check"

# Clean up if exists
try:
    client.delete_collection(COLLECTION)
except:
    pass

# Create collection
client.create_collection(
    collection_name=COLLECTION,
    vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
)

# Test content - plain text
test_content = "This is a test of plain text content for RAG retrieval. It should be readable and not compressed."

print("=" * 60)
print("BEFORE STORAGE:")
print("=" * 60)
print(f"Content type: {type(test_content)}")
print(f"Content: {test_content}")
print(f"Content repr: {repr(test_content)}")

import uuid
# Create point with payload
point = PointStruct(
    id=str(uuid.uuid4()),
    vector=[0.1] * 1024,
    payload={
        "content": test_content,
        "source_url": "https://example.com/test",
        "section": "test"
    }
)

print("\n" + "=" * 60)
print("POINT PAYLOAD BEFORE UPSERT:")
print("=" * 60)
print(f"Payload content type: {type(point.payload['content'])}")
print(f"Payload content: {point.payload['content']}")

# Upsert
client.upsert(
    collection_name=COLLECTION,
    points=[point]
)

print("\n" + "=" * 60)
print("AFTER RETRIEVAL:")
print("=" * 60)

# Retrieve
results = client.query_points(
    collection_name=COLLECTION,
    query=[0.1] * 1024,
    limit=1,
    with_payload=True
)

retrieved = results.points[0]
retrieved_content = retrieved.payload.get('content', 'NOT FOUND')

print(f"Retrieved content type: {type(retrieved_content)}")
print(f"Retrieved content: {retrieved_content}")
print(f"Content matches: {retrieved_content == test_content}")

# Cleanup
client.delete_collection(COLLECTION)

print("\n" + "=" * 60)
print("CONCLUSION:")
print("=" * 60)
if retrieved_content == test_content:
    print("✅ Qdrant stores and retrieves plain text correctly")
    print("   The issue is in the ingestion pipeline, not Qdrant")
else:
    print("❌ Content is corrupted")
    print(f"   Expected: {repr(test_content[:50])}")
    print(f"   Got: {repr(retrieved_content[:50])}")
