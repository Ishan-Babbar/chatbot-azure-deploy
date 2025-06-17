import fitz  # PyMuPDF
import os
import json
import re
from io import BytesIO
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient, ContentSettings

# Load environment variables
load_dotenv()
conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
source_container = os.getenv("BLOB_CONTAINER_NAME")
source_blob_name = os.getenv("BLOB_FILE_NAME")
chunks_container = os.getenv("CHUNKS_CONTAINER_NAME")

def split_into_sentences(text):
    return re.split(r'(?<=[.!?]) +', text)

def semantic_chunk_pdf_from_blob(max_tokens=500, overlap=1):
    # Connect to blob and download PDF
    blob_service_client = BlobServiceClient.from_connection_string(conn_str)
    blob_client = blob_service_client.get_blob_client(container=source_container, blob=source_blob_name)
    stream = blob_client.download_blob()
    pdf_stream = BytesIO(stream.readall())

    # Extract text from PDF
    doc = fitz.open(stream=pdf_stream, filetype="pdf")
    all_text = " ".join(page.get_text() for page in doc)

    # Chunking logic
    sentences = split_into_sentences(all_text)
    chunks = []
    current_chunk = []
    current_length = 0

    for sentence in sentences:
        token_count = len(sentence.split())
        if current_length + token_count > max_tokens:
            chunks.append(" ".join(current_chunk))
            current_chunk = current_chunk[-overlap:]
            current_length = sum(len(s.split()) for s in current_chunk)
        current_chunk.append(sentence)
        current_length += token_count

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks

def upload_chunks_to_chunks_container(chunks, output_blob_name):
    blob_service_client = BlobServiceClient.from_connection_string(conn_str)
    blob_client = blob_service_client.get_blob_client(container=chunks_container, blob=output_blob_name)

    json_data = json.dumps(chunks, indent=2)
    blob_client.upload_blob(
        json_data,
        overwrite=True,
        content_settings=ContentSettings(content_type='application/json')
    )
    print(f"✅ Uploaded {len(chunks)} chunks to blob: {chunks_container}/{output_blob_name}")

if __name__ == "__main__":
    chunks = semantic_chunk_pdf_from_blob()
    # Generate output blob name based on source PDF name
    base_name = os.path.splitext(os.path.basename(source_blob_name))[0]
    output_blob_name = "chunks.json"
    upload_chunks_to_chunks_container(chunks, output_blob_name)