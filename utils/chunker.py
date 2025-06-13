import fitz  # PyMuPDF
import os
import json
import re
from dotenv import load_dotenv


"""
Improvements Made
-Replaced line-based splitting with sentence-based splitting.
-Added 1-sentence overlap between chunks.
-Used token count instead of character count for chunk size.
-Removed dependency on NLTK to avoid runtime issues.
"""
# Load environment variables
load_dotenv()
base_folder = os.getenv("BASE_FOLDER_PATH")

def split_into_sentences(text):
    # Basic sentence splitter using punctuation
    return re.split(r'(?<=[.!?]) +', text)

def semantic_chunk_pdf(pdf_path, max_tokens=500, overlap=1):
    doc = fitz.open(pdf_path)
    all_text = ""
    for page in doc:
        all_text += page.get_text() + " "

    sentences = split_into_sentences(all_text)
    chunks = []
    current_chunk = []
    current_length = 0

    for sentence in sentences:
        token_count = len(sentence.split())
        if current_length + token_count > max_tokens:
            chunks.append(" ".join(current_chunk))
            current_chunk = current_chunk[-overlap:]  # retain overlap
            current_length = sum(len(s.split()) for s in current_chunk)
        current_chunk.append(sentence)
        current_length += token_count

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks

if __name__ == "__main__":
    pdf_path = os.path.join(base_folder, "data", "Capgemini_Consumer_Trends_2025.pdf")
    chunks = semantic_chunk_pdf(pdf_path)
    chunks_dir = os.path.join(base_folder, "chunks")
    os.makedirs(chunks_dir, exist_ok=True)
    chunks_file_path = os.path.join(chunks_dir, "chunks.json")
    with open(chunks_file_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2)
    print(f"✅ Extracted and saved {len(chunks)} chunks to {chunks_file_path}")