from retrival import load_chunks, build_bm25_index, build_vector_entries, search_with_rerank

EVAL_SET = [
    {"question": "why did nationalism rise in Europe after the French Revolution?", "chapter": 1},
    {"question": "what changes did Napoleon bring through the Napoleonic Code?", "chapter": 1},
    {"question": "what was the Non-Cooperation Movement in India?", "chapter": 2},
    {"question": "why did Gandhi launch the Salt March?", "chapter": 2},
    {"question": "how did the Silk Route connect trade across the world?", "chapter": 3},
    {"question": "what caused the Great Depression?", "chapter": 3},
    {"question": "what is proto-industrialization?", "chapter": 4},
    {"question": "how did colonialism affect industrialisation in India?", "chapter": 4},
    {"question": "how did print culture spread in Europe?", "chapter": 5},
    {"question": "how were women affected by the spread of print?", "chapter": 5},
]

def context_precision(retrieved_chapters, expected_chapter):
    if not retrieved_chapters:
        return 0.0
    matches = sum(1 for ch in retrieved_chapters if ch == expected_chapter)
    return matches / len(retrieved_chapters)

def run_eval():
    entries, metadata = load_chunks()
    bm25 = build_bm25_index(entries)
    embeddings = build_vector_entries(entries, metadata)
    entry_to_chapter = dict(zip(entries, [m["chapter"] for m in metadata]))

    precisions = []
    for case in EVAL_SET:
        results = search_with_rerank(case["question"], entries, bm25, embeddings, top_k=3, candidate_pool=10)
        retrieved_chapters = [entry_to_chapter[entry] for entry, _ in results]

        p = context_precision(retrieved_chapters, case["chapter"])
        precisions.append(p)

        print(f"[{case['question']}] (expected chapter={case['chapter']})")
        print(f"  precision={p:.2f}  retrieved chapters: {retrieved_chapters}")
        print()

    print(f"=== AVG Context Precision: {sum(precisions)/len(precisions):.2f} ===")

if __name__ == "__main__":
    run_eval()