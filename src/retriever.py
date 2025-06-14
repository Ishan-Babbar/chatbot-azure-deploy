import faiss
import numpy as np
import json
import os
from openai import AzureOpenAI
from dotenv import load_dotenv
import tiktoken

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
CHAT_MODEL = os.getenv("DEPLOYMENT_NAME")  

# Load FAISS index and metadata
index_path = os.path.join(base_folder, "embeddings", "faiss_index.index")
metadata_path = os.path.join(base_folder, "embeddings", "metadata.json")
index = faiss.read_index(index_path)
with open(metadata_path, "r", encoding="utf-8") as f:
    metadata = json.load(f)

#Normalise the query vector
def embed_query(query: str) -> np.ndarray:
    response = client.embeddings.create(input=query, model=EMBED_MODEL)
    vec = np.array(response.data[0].embedding).astype("float32")
    vec /= np.linalg.norm(vec)  # Normalize to unit vector
    return vec.reshape(1, -1)

def retrieve_top_k(query: str, k: int = 10, threshold: float = 0.6):
    query_vector = embed_query(query)
    distances, indices = index.search(query_vector, k)
    results = []
    for i, dist in zip(indices[0], distances[0]):
        similarity = 1 - dist  # Approximate cosine similarity
        if similarity >= threshold:
            results.append(metadata[i])
    return rerank_chunks(query, results)

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
        tokens = len(enc.encode(chunk["text"]))
        if total_tokens + tokens > max_tokens:
            break
        filtered.append(chunk)
        total_tokens += tokens
    return filtered

def rerank_chunks(query, chunks):
    if not chunks:
        return []

    prompt = f"""You are a helpful assistant. Given the query and the following chunks, rank them by their relevance to the query.

Query: {query}

Chunks:
"""
    for i, chunk in enumerate(chunks):
        text = chunk["text"][:300].replace("\n", " ")
        source = chunk.get("source", "Unknown Source")
        prompt += f"{i+1}. ({source}) {text}...\n\n"


    prompt += "Return the chunk numbers in order of relevance, one per line (e.g., 3, 1, 2)."

    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0,
        top_p=1,
        max_tokens=300
    )

    raw_output = response.choices[0].message.content.strip()
    print("🔧 Reranker raw output:\n", raw_output)

    try:
        lines = raw_output.splitlines()
        indices = []
        for line in lines:
            line = line.strip().strip(",.")
            if line.isdigit():
                idx = int(line) - 1
                if 0 <= idx < len(chunks):
                    indices.append(idx)
        if indices:
            return [chunks[i] for i in indices]
    except Exception as e:
        print("Failed to parse reranker output:", e)

    # Fallback: return original chunks
    return chunks

def decompose_query(query):
    prompt = f"Decompose the following complex query into simpler sub-questions:\n\nQuery: {query}\n\nSub-questions:"
    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0,
        top_p=1,
        max_tokens=800
    )
    sub_questions = response.choices[0].message.content.strip().split("\n")
    return [q.strip() for q in sub_questions if q.strip()]

def multi_hop_retrieve(query, k=10):
    sub_questions = decompose_query(query)
    all_chunks = []
    for sub_query in sub_questions:
        chunks = retrieve_top_k(sub_query, k)
        all_chunks.extend(chunks)
    seen = set()
    unique_chunks = []
    for chunk in all_chunks:
        key = chunk["text"]
        if key not in seen:
            seen.add(key)
            unique_chunks.append(chunk)
    return filter_chunks(unique_chunks, max_tokens=4000)

# Example usage
if __name__ == "__main__":
    user_query = "What recommendations does the report make for retailers and brands?"
    top_chunks = multi_hop_retrieve(user_query, k=10)
    print("\n Top Retrieved Chunks:\n")
    for i, chunk in enumerate(top_chunks, 1):
        print(f"{i}. [{chunk['source']}] {chunk['text'][:300]}...\n")