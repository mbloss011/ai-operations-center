"""Vector store abstraction: Qdrant first, Chroma alternative.
Embeddings come from the local LM Studio nomic model, never a cloud key
by default. If neither store is reachable, search() raises — it does not
return invented neighbours.
"""
import os, httpx

def embed_texts(texts, base_url=None, model="text-embedding-nomic-embed-text-v1.5"):
    base = (base_url or os.environ.get("LMSTUDIO_BASE_URL", "http://127.0.0.1:1234/v1")).rstrip("/")
    with httpx.Client(timeout=60) as c:
        r = c.post(f"{base}/embeddings", json={"model": model, "input": texts})
        r.raise_for_status()
        return [d["embedding"] for d in r.json()["data"]]

class VectorStore:
    def __init__(self, backend=None):
        self.backend = backend or os.environ.get("VECTOR_BACKEND", "qdrant")
    def upsert(self, collection, ids, texts, vectors, metadatas=None):
        if self.backend == "qdrant":
            from qdrant_client import QdrantClient, models
            url = os.environ.get("QDRANT_URL", "http://127.0.0.1:6333")
            client = QdrantClient(url=url)
            if not client.collection_exists(collection):
                client.create_collection(collection, vectors_config=models.VectorParams(size=len(vectors[0]), distance=models.Distance.COSINE))
            client.upsert(collection, points=[models.PointStruct(id=i, vector=v, payload=(metadatas or [{}])[k]) for k, (i, v) in enumerate(zip(ids, vectors))])
            return {"backend": "qdrant", "collection": collection, "count": len(ids)}
        elif self.backend == "chroma":
            import chromadb
            client = chromadb.PersistentClient(path=os.environ.get("CHROMA_PATH", "./data/chroma"))
            col = client.get_or_create_collection(collection)
            col.upsert(ids=[str(i) for i in ids], documents=texts, embeddings=vectors, metadatas=metadatas)
            return {"backend": "chroma", "collection": collection, "count": len(ids)}
        raise ValueError(f"unknown VECTOR_BACKEND: {self.backend}")
