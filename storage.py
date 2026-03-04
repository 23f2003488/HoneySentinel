import os
import json
from azure.storage.blob import BlobServiceClient


def get_blob_service():
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    return BlobServiceClient.from_connection_string(connection_string)


def upload_report_to_blob(report_data, filename):

    blob_service = get_blob_service()
    container_name = "honeysentinel-reports"

    blob_client = blob_service.get_blob_client(
        container=container_name,
        blob=filename
    )

    json_data = json.dumps(report_data, indent=2)

    blob_client.upload_blob(json_data, overwrite=True)


def load_reports_from_blob():

    blob_service = get_blob_service()
    container_name = "honeysentinel-reports"

    container_client = blob_service.get_container_client(container_name)

    reports = []

    for blob in container_client.list_blobs():

        blob_client = container_client.get_blob_client(blob.name)

        data = blob_client.download_blob().readall()

        report = json.loads(data)

        reports.append(report)

    return reports