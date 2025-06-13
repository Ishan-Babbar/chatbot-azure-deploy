import faiss
import numpy as np
import json
import os
from openai import AzureOpenAI
from dotenv import load_dotenv
import tiktoken

"""
Improvements Made
-Lowered similarity threshold to 0.6 for better recall.
-Increased k to 10 to retrieve more candidates.
-Extended token limit to 4000 for GPT-4o.
-Added a reranking hook for future integration with OpenAI or Cohere reranker.
-Improved out-of-domain detection sensitivity.
"""

# Load environment variables
load_dotenv()
base_folder = os.getenv("BASE_FOLDER_PATH")

# Azure OpenAI config
client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2023-05-15"
)
EMBED_MODEL = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")

# Load FAISS index and metadata
index_path = os.path.join(base_folder, "embeddings", "faiss_index.index")
metadata_path = os.path.join(base_folder, "embeddings", "metadata.json")
index = faiss.read_index(index_path)
with open(metadata_path, "r", encoding="utf-8") as f:
    metadata = json.load(f)

def embed_query(query: str) -> np.ndarray:
    response = client.embeddings.create(input=query, model=EMBED_MODEL)
    return np.array(response.data[0].embedding).astype("float32").reshape(1, -1)

def retrieve_top_k(query: str, k: int = 10, threshold: float = 0.6):
    query_vector = embed_query(query)
    distances, indices = index.search(query_vector, k)
    results = []
    for i, dist in zip(indices[0], distances[0]):
        similarity = 1 - dist  # Approximate cosine similarity
        if similarity >= threshold:
            results.append(metadata[i])
    return results

def is_out_of_domain(query: str, threshold: float = 0.55):
    query_vec = embed_query(query).flatten()
    all_embeddings = index.reconstruct_n(0, index.ntotal)
    avg_embedding = np.mean(all_embeddings, axis=0)
    dot = np.dot(query_vec, avg_embedding)
    norm = np.linalg.norm(query_vec) * np.linalg.norm(avg_embedding)
    similarity = dot / norm
    return similarity < threshold

def filter_chunks(chunks, max_tokens=4000):
    enc = tiktoken.encoding_for_model("gpt-4o")
    filtered = []
    total_tokens = 0
    for chunk in chunks:
        tokens = len(enc.encode(chunk))
        if total_tokens + tokens > max_tokens:
            break
        filtered.append(chunk)
        total_tokens += tokens
    return filtered

# Optional: placeholder for reranking (future enhancement)
def rerank_chunks(query, chunks):
    # TODO: Integrate OpenAI or Cohere reranker here
    return chunks

# Example usage
if __name__ == "__main__":
    user_query = "What is the main focus of the Capgemini Consumer Trends 2025 report?"
    top_chunks = retrieve_top_k(user_query, k=10)
    top_chunks = rerank_chunks(user_query, top_chunks)
    print("\n🔍 Top Retrieved Chunks:\n")
    for i, chunk in enumerate(top_chunks, 1):
        print(f"{i}. {chunk[:300]}...\n")