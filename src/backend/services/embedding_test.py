"""Quick local script to validate embedding generation and vector size."""

from sentence_transformers import SentenceTransformer

# Load the same embedding model used by the retrieval pipeline.
model=SentenceTransformer("BAAI/bge-base-en-v1.5")

# Read previously generated chunks from disk for a smoke test run.
with open("sample_chunks.txt","r") as f:
    chunks=[c.strip() for c in f.readlines() if c.strip()]


embeddings=model.encode(chunks)

print("Total chunks:",len(chunks))
print("Embedding dimension:",len(embeddings[0]))
print("\nSample vector (first 10 values):")
print(embeddings[0][:10])
