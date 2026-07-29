"""Minimal test: Store a real chunk in Qdrant and retrieve it"""
import os
import uuid
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams

COLLECTION = "test_real_content"

client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY"),
    timeout=30
)

# Delete if exists
try:
    client.delete_collection(COLLECTION)
except:
    pass

# Create
client.create_collection(
    collection_name=COLLECTION,
    vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
)

# Real chunk content from ingestion
real_content = """Welcome to the Humanoid Robotics Academy! This comprehensive guide is specifically designed for AI students with Python knowledge who are beginning their journey into humanoid robotics. About This Book This book focuses on ROS 2 (Robot Operating System 2) as the middleware that enables communication and control in humanoid robots."""

print("STORING:")
print(f"Type: {type(real_content)}")
print(f"Content: {real_content[:100]}...")

point = PointStruct(
    id=str(uuid.uuid4()),
    vector=[0.1] * 1024,
    payload={
        "content": real_content,
        "source_url": "https://hackathon-1-book-chi.vercel.app/docs/intro.html",
        "section": "docs/intro.html",
        "chunk_index": 0,
    }
)

client.upsert(collection_name=COLLECTION, points=[point])
print("\n✅ Stored successfully")

# Retrieve
results = client.query_points(
    collection_name=COLLECTION,
    query=[0.1] * 1024,
    limit=1,
    with_payload=True
)

retrieved = results.points[0].payload.get("content", "")
print("\nRETRIEVED:")
print(f"Type: {type(retrieved)}")
print(f"Content: {retrieved[:100]}...")
print(f"\nMatch: {retrieved == real_content}")

# Cleanup
client.delete_collection(COLLECTION)
