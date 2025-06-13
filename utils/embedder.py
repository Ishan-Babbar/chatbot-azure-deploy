from openai import AzureOpenAI
import faiss
import numpy as np
import json
import os
from dotenv import load_dotenv
from tqdm import tqdm

"""
Improvements Made
-Batch embedding for efficiency and API rate safety.
-Progress bar using tqdm for visibility.
-Error handling for missing environment variables.
-Cleaner structure for readability and maintainability.
"""

# Load environment variables
load_dotenv()
base_folder = os.getenv("BASE_FOLDER_PATH")

# Azure OpenAI config
EMBED_MODEL = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2023-05-15"
)

if not all([os.getenv("AZURE_OPENAI_API_KEY"), os.getenv("AZURE_OPENAI_ENDPOINT"), EMBED_MODEL]):
    raise ValueError("Please ensure AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, and AZURE_OPENAI_EMBEDDING_DEPLOYMENT are set.")

def embed_text(texts, batch_size=10):
    embeddings = []
    for i in tqdm(range(0, len(texts), batch_size), desc="Embedding chunks"):
        batch = texts[i:i+batch_size]
        response = client.embeddings.create(input=batch, model=EMBED_MODEL)
        batch_embeddings = [item.embedding for item in response.data]
        embeddings.extend(batch_embeddings)
    return embeddings

def build_faiss_index(embeddings, output_path):
    dim = len(embeddings[0])
    index = faiss.IndexFlatL2(dim)

    # Check normalization of a few vectors
    sample_vecs = np.array(embeddings[:5])
    norms = np.linalg.norm(sample_vecs, axis=1)
    print("🔍 Sample vector norms (should be close to 1.0 for cosine similarity):")
    for i, norm in enumerate(norms):
        print(f"Vector {i+1}: {norm:.4f}")

    index.add(np.array(embeddings).astype("float32"))
    faiss.write_index(index, output_path)

if __name__ == "__main__":
    chunks_path = os.path.join(base_folder, "chunks", "chunks.json")
    with open(chunks_path, "r", encoding="utf-8") as f:
        raw_chunks = json.load(f)
    # Wrap each chunk with metadata
    source_name = "Capgemini Consumer Report 2025"  
    chunks = [{"text": chunk, "source": source_name} for chunk in raw_chunks]
    # Save the transformed chunks to a new JSON file
    with open(chunks_path, 'w', encoding='utf-8') as f:
        json.dump(chunks, f, indent=2)

    embeddings = embed_text([chunk["text"] for chunk in chunks])

    embeddings_dir = os.path.join(base_folder, "embeddings")
    os.makedirs(embeddings_dir, exist_ok=True)

    index_path = os.path.join(embeddings_dir, "faiss_index.index")
    build_faiss_index(embeddings, index_path)

    metadata_path = os.path.join(embeddings_dir, "metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2)
    
    print(f"✅ FAISS index and metadata saved to {embeddings_dir}")