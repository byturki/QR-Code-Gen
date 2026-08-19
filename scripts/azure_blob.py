"""Thin wrapper around the Azure Blob SDK for kpcwebsitestorageaccount.

Auth uses DefaultAzureCredential, which picks up the current `az login`
session automatically - no connection strings or keys are stored anywhere.
"""

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, ContentSettings

STORAGE_ACCOUNT = "kpcwebsitestorageaccount"
ACCOUNT_URL = f"https://{STORAGE_ACCOUNT}.blob.core.windows.net"

_client: BlobServiceClient | None = None


def get_client() -> BlobServiceClient:
    global _client
    if _client is None:
        _client = BlobServiceClient(account_url=ACCOUNT_URL, credential=DefaultAzureCredential())
    return _client


def list_containers() -> list[str]:
    return [c.name for c in get_client().list_containers()]


def blob_exists(container: str, blob_name: str) -> bool:
    blob = get_client().get_blob_client(container=container, blob=blob_name)
    return blob.exists()


def upload_file(container: str, local_path: str, blob_name: str,
                 content_type: str, overwrite: bool = False) -> str:
    """Uploads a local file and returns its blob URL."""
    blob = get_client().get_blob_client(container=container, blob=blob_name)
    with open(local_path, "rb") as f:
        blob.upload_blob(f, overwrite=overwrite,
                          content_settings=ContentSettings(content_type=content_type))
    return blob.url
