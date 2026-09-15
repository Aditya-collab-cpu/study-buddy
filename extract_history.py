import pymupdf
from pathlib import Path
import re

def clean_text(text):
    text = text.replace("Reprint 2026-27", "")
    text = re.sub(r"(?m)^\d{1,4}\s*$", "", text)  # standalone page-number lines
    text = re.sub(r"\n{3,}", "\n\n", text)  # collapse excess blank lines
    return text.strip()

RAW_DIR = Path("data/raw/history")
OUT_DIR = Path("data/processed/history")
OUT_DIR.mkdir(parents=True, exist_ok=True)

CHAPTER_TITLES = {
    1: "The Rise of Nationalism in Europe",
    2: "Nationalism in India",
    3: "The Making of a Global World",
    4: "The Age of Industrialisation",
    5: "Print Culture and the Modern World",
}

def extract_pdf_text(pdf_path):
    doc = pymupdf.open(pdf_path)
    pages = [page.get_text() for page in doc]
    doc.close()
    return pages

if __name__ == "__main__":
    for chapter_num in range(1, 6):
        pdf_path = RAW_DIR / f"chapter{chapter_num}.pdf"
        pages = extract_pdf_text(pdf_path)
        full_text = "\n\n".join(pages)
        cleaned_text = clean_text(full_text)

        out_path = OUT_DIR / f"chapter{chapter_num}.txt"
        out_path.write_text(cleaned_text, encoding="utf-8")

        print(f"Chapter {chapter_num} ({CHAPTER_TITLES[chapter_num]}): "
              f"{len(pages)} pages, {len(cleaned_text)} characters extracted")
        print(f"  First 200 chars: {cleaned_text[:200]!r}")
        print()