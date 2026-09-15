import json
from pathlib import Path

PROCESSED_DIR = Path("data/processed/history")

CHAPTER_TITLES = {
    1: "The Rise of Nationalism in Europe",
    2: "Nationalism in India",
    3: "The Making of a Global World",
    4: "The Age of Industrialisation",
    5: "Print Culture and the Modern World",
}

def chunk_text(text, chunk_size=150, overlap=30):
    """Fixed-size word chunking with overlap — same function as chunking_experiment.py."""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        if end >= len(words):
            break
        start = end - overlap
    return chunks

if __name__ == "__main__":
    all_chunks = []

    for chapter_num in range(1, 6):
        text_path = PROCESSED_DIR / f"chapter{chapter_num}.txt"
        text = text_path.read_text(encoding="utf-8")

        chunks = chunk_text(text, chunk_size=150, overlap=30)
        print(f"Chapter {chapter_num} ({CHAPTER_TITLES[chapter_num]}): {len(chunks)} chunks")

        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "chapter": chapter_num,
                "chapter_title": CHAPTER_TITLES[chapter_num],
                "chunk_index": i,
                "text": chunk,
            })

    out_path = PROCESSED_DIR / "chunks.json"
    out_path.write_text(json.dumps(all_chunks, indent=2), encoding="utf-8")
    print(f"\nTotal chunks written: {len(all_chunks)} -> {out_path}")