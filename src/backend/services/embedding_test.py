'''
Test file to see if embeddigs are working correctly or not
'''

from sentence_transformers import SentenceTransformer

model=SentenceTransformer("BAAI/bge-base-en-v1.5")

with open("sample_chunks.txt","r") as f:
    chunks=[c.strip() for c in f.readlines() if c.strip()]


embeddings=model.encode(chunks)

print("Total chunks:",len(chunks))
print("Embedding dimension:",len(embeddings[0]))
print("\nSample vector (first 10 values):")
print(embeddings[0][:10])
