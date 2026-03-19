import os
import json
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import AzureError

def get_blob_service():
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    if not connection_string:
        print("⚠️ Warning: AZURE_STORAGE_CONNECTION_STRING not found in environment.")
        return None
    try:
        return BlobServiceClient.from_connection_string(connection_string)
    except Exception as e:
        print(f"⚠️ Failed to initialize Blob Service: {e}")
        return None

def upload_report_to_blob(report_data, filename):
    blob_service = get_blob_service()
    if not blob_service:
        return False

    container_name = "honeysentinel-reports"

    try:
        # Create container if it doesn't exist
        container_client = blob_service.get_container_client(container_name)
        if not container_client.exists():
            container_client.create_container()

        blob_client = blob_service.get_blob_client(container=container_name, blob=filename)
        json_data = json.dumps(report_data, indent=2)
        blob_client.upload_blob(json_data, overwrite=True)
        print(f"☁️ Successfully uploaded {filename} to Azure Blob Storage.")
        return True
    except AzureError as e:
        print(f"❌ Azure Storage Upload Error: {e}")
        return False

def load_reports_from_blob():
    blob_service = get_blob_service()
    if not blob_service:
        return []

    container_name = "honeysentinel-reports"
    reports = []

    try:
        container_client = blob_service.get_container_client(container_name)
        if not container_client.exists():
            return []

        for blob in container_client.list_blobs():
            try:
                blob_client = container_client.get_blob_client(blob.name)
                data = blob_client.download_blob().readall()
                report = json.loads(data)
                reports.append(report)
            except Exception as e:
                print(f"⚠️ Failed to parse blob {blob.name}: {e}")
                
    except AzureError as e:
        print(f"❌ Azure Storage Retrieval Error: {e}")
        
    return reports