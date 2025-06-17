import os
import json
from openai import AzureOpenAI
import faiss
import numpy as np
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient, ContentSettings
from io import BytesIO

# Load environment variables
load_dotenv()
conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
chunks_container = os.getenv("CHUNKS_CONTAINER_NAME")
chunks_blob_name = os.getenv("CHUNKS_BLOB_NAME")
embeddings_container = os.getenv("EMBEDDINGS_CONTAINER_NAME")
deployment_name = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")

# Initialize Azure Blob client
blob_service_client = BlobServiceClient.from_connection_string(conn_str)

# Download chunked JSON from blob
chunks_blob_client = blob_service_client.get_blob_client(container=chunks_container, blob=chunks_blob_name)
chunks_data = json.loads(chunks_blob_client.download_blob().readall())

# Wrap each chunk with metadata
source_name = os.path.splitext(os.path.basename(chunks_blob_name))[0].replace("_", " ")
chunks = [{"text": chunk, "source": source_name} for chunk in chunks_data]

# Initialize Azure OpenAI client
client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2023-05-15"
)

# Embed the chunks in batches
embeddings = []
batch_size = 10
for i in range(0, len(chunks), batch_size):
    batch = chunks[i:i + batch_size]
    response = client.embeddings.create(
        input=[item["text"] for item in batch],
        model=deployment_name
    )
    batch_embeddings = [item.embedding for item in response.data]
    embeddings.extend(batch_embeddings)

# Convert to FAISS index
dimension = len(embeddings[0])
index = faiss.IndexFlatL2(dimension)
index.add(np.array(embeddings).astype("float32"))

# Serialize FAISS index
faiss_index_path = "index.faiss"
faiss.write_index(index, faiss_index_path)

# Upload FAISS index to embeddings container
with open(faiss_index_path, "rb") as f:
    index_blob_client = blob_service_client.get_blob_client(container=embeddings_container, blob="index.faiss")
    index_blob_client.upload_blob(f, overwrite=True, content_settings=ContentSettings(content_type='application/octet-stream'))

# Upload enriched metadata to embeddings container
metadata_blob_client = blob_service_client.get_blob_client(container=embeddings_container, blob="metadata.json")
metadata_blob_client.upload_blob(json.dumps(chunks, indent=2), overwrite=True, content_settings=ContentSettings(content_type='application/json'))

# Clean up local FAISS file
os.remove(faiss_index_path)

print("✅ Embeddings and enriched metadata uploaded to 'embeddings' container.")