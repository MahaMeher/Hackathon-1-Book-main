"""
Directly check what's stored in Qdrant right now and attempt to decompress
"""
import os
import zlib
import base64
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from qdrant_client import QdrantClient

client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY"),
    timeout=30
)

# Query one point
results = client.query_points(
    collection_name="book_vectors",
    query=[0.1] * 1024,
    limit=1,
    with_payload=True
)

if not results.points:
    print("No points found")
    exit(1)

point = results.points[0]
content = point.payload.get("content", "NOT FOUND")

print("=" * 60)
print("RAW CONTENT ANALYSIS")
print("=" * 60)
print(f"Type: {type(content)}")
print(f"Length: {len(content)}")
print(f"First 200 chars (repr):")
print(repr(content[:200]))

# Try to decompress
print("\n" + "=" * 60)
print("DECOMPRESSION ATTEMPTS")
print("=" * 60)

# Try zlib
try:
    raw_bytes = content.encode('latin-1')  # Preserve byte values
    decompressed = zlib.decompress(raw_bytes)
    print(f"✅ zlib decompression successful!")
    print(f"Decompressed text: {decompressed.decode('utf-8')[:300]}")
except Exception as e:
    print(f"❌ zlib failed: {e}")

# Try zlib with wbits
try:
    raw_bytes = content.encode('latin-1')
    decompressed = zlib.decompress(raw_bytes, -zlib.MAX_WBITS)
    print(f"✅ zlib (raw) successful!")
    print(f"Decompressed text: {decompressed.decode('utf-8')[:300]}")
except Exception as e:
    print(f"❌ zlib (raw) failed: {e}")

# Try gzip
import gzip
try:
    raw_bytes = content.encode('latin-1')
    decompressed = gzip.decompress(raw_bytes)
    print(f"✅ gzip decompression successful!")
    print(f"Decompressed text: {decompressed.decode('utf-8')[:300]}")
except Exception as e:
    print(f"❌ gzip failed: {e}")
