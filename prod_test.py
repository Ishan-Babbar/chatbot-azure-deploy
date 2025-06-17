# import os
# from dotenv import load_dotenv
# load_dotenv()
# from azure.storage.blob import BlobServiceClient

# # Load from environment
# conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
# container_name = os.getenv("BLOB_CONTAINER_NAME")
# blob_name = os.getenv("BLOB_FILE_NAME")

# try:
#     blob_service_client = BlobServiceClient.from_connection_string(conn_str)
#     blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)

#     stream = blob_client.download_blob()
#     content = stream.read(1024)  # Read first 1KB
#     print("✅ Successfully accessed the PDF blob using connection string.")
# except Exception as e:
#     print(f"❌ Failed to access the PDF using connection string: {e}")

from azure.storage.blob import BlobServiceClient
import os
from dotenv import load_dotenv

load_dotenv()
blob_service_client = BlobServiceClient.from_connection_string(os.getenv("AZURE_STORAGE_CONNECTION_STRING"))
container_client = blob_service_client.get_container_client(os.getenv("EMBEDDINGS_CONTAINER_NAME"))

print("Blobs in container:")
for blob in container_client.list_blobs():
    print(blob.name)
