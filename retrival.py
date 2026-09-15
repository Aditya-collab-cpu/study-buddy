import json
import chromadb
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer, CrossEncoder
import numpy as np

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
chroma_client = chromadb.PersistentClient(path="data/chroma_db")


def load_chunks(path="data/processed/history/chunks.json"):
    with open(path, "r") as f:
        records = json.load(f)
    entries = [r["text"] for r in records]
    metadata = [
        {"chapter": r["chapter"], "chapter_title": r["chapter_title"], "chunk_index": r["chunk_index"]}
        for r in records
    ]
    return entries, metadata


def build_bm25_index(entries):
    tokenized = [entry.lower().split() for entry in entries]
    return BM25Okapi(tokenized)


def bm25_search(query, entries, bm25, top_k=3):
    tokenized_query = query.lower().split()
    scores = bm25.get_scores(tokenized_query)
    ranked = sorted(zip(entries, scores), key=lambda pair: pair[1], reverse=True)
    return ranked[:top_k]


def build_vector_entries(entries, metadata, collection_name="history_chunks"):
    existing = [c.name for c in chroma_client.list_collections()]
    if collection_name in existing:
        collection = chroma_client.get_collection(collection_name)
        if collection.count() == len(entries):
            return collection
        chroma_client.delete_collection(collection_name)

    collection = chroma_client.create_collection(name=collection_name, metadata={"hnsw:space": "cosine"})
    embeddings = embedding_model.encode(entries).tolist()
    ids = [f"entry-{i}" for i in range(len(entries))]
    collection.add(ids=ids, embeddings=embeddings, documents=entries, metadatas=metadata)
    return collection


def vector_search(query, entries, collection, top_k=3):
    query_embedding = embedding_model.encode([query])[0].tolist()
    results = collection.query(query_embeddings=[query_embedding], n_results=top_k)
    docs = results["documents"][0]
    distances = results["distances"][0]
    scores = [1 - d for d in distances]
    return list(zip(docs, scores))


def reciprocal_rank_fusion(bm25_results, vector_results, k=2):
    scores = {}
    for rank, (entry, _) in enumerate(bm25_results, start=1):
        scores[entry] = scores.get(entry, 0) + 1 / (k + rank)
    for rank, (entry, _) in enumerate(vector_results, start=1):
        scores[entry] = scores.get(entry, 0) + 1 / (k + rank)
    return sorted(scores.items(), key=lambda pair: pair[1], reverse=True)


def hybrid_search(query, entries, bm25, embeddings, top_k=3):
    vector_results = vector_search(query, entries, embeddings, top_k=len(entries))
    bm25_results = bm25_search(query, entries, bm25, top_k=len(entries))
    fused = reciprocal_rank_fusion(bm25_results, vector_results)
    return fused[:top_k]


def rerank(query, candidates, top_k=3):
    pairs = [[query, entry] for entry, _ in candidates]
    scores = reranker.predict(pairs)
    reranked = sorted(zip([entry for entry, _ in candidates], scores), key=lambda pair: pair[1], reverse=True)
    return reranked[:top_k]


def search_with_rerank(query, entries, bm25, embeddings, top_k=3, candidate_pool=10):
    candidates = hybrid_search(query, entries, bm25, embeddings, top_k=candidate_pool)
    return rerank(query, candidates, top_k=top_k)


if __name__ == "__main__":
    entries, metadata = load_chunks()
    bm25 = build_bm25_index(entries)
    embeddings = build_vector_entries(entries, metadata)

    query = input("\nAsk a History question:\n")
    results = search_with_rerank(query, entries, bm25, embeddings, top_k=3, candidate_pool=10)
    for entry, score in results:
        print(f"\n[score={score:.4f}] {entry[:200]}...")