from __future__ import annotations

from dataclasses import dataclass

from google.api_core.exceptions import NotFound
from google.cloud import storage


@dataclass(frozen=True)
class CheckpointStore:
    bucket_name: str
    blob_name: str = "checkpoints/reverse-contacts.txt"
    client: storage.Client | None = None

    def load(self) -> str | None:
        bucket = (self.client or storage.Client()).bucket(self.bucket_name)
        blob = bucket.blob(self.blob_name)
        try:
            value = blob.download_as_text().strip()
        except NotFound:
            return None
        return value or None

    def save(self, value: str) -> None:
        bucket = (self.client or storage.Client()).bucket(self.bucket_name)
        bucket.blob(self.blob_name).upload_from_string(value, content_type="text/plain")
