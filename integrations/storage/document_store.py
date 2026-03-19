import logging
import os
from typing import Optional, BinaryIO

logger = logging.getLogger(__name__)


class DocumentStore:
    """MinIO/S3 document storage client."""

    def __init__(self, url: str, access_key: str, secret_key: str):
        self.url = url
        self.access_key = access_key
        self.secret_key = secret_key
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from minio import Minio
                host = self.url.replace("http://", "").replace("https://", "")
                secure = self.url.startswith("https://")
                self._client = Minio(host, access_key=self.access_key, secret_key=self.secret_key, secure=secure)
            except Exception as e:
                logger.warning(f"MinIO unavailable: {e}")
                self._client = "unavailable"
        return self._client

    def ensure_bucket(self, bucket: str) -> None:
        client = self._get_client()
        if client == "unavailable":
            return
        try:
            if not client.bucket_exists(bucket):
                client.make_bucket(bucket)
        except Exception as e:
            logger.error(f"Bucket creation failed: {e}")

    def upload(self, bucket: str, key: str, data: bytes, content_type: str = "application/octet-stream") -> bool:
        client = self._get_client()
        if client == "unavailable":
            return False
        try:
            import io
            self.ensure_bucket(bucket)
            client.put_object(bucket, key, io.BytesIO(data), len(data), content_type=content_type)
            return True
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return False

    def get_presigned_url(self, bucket: str, key: str, expires_hours: int = 1) -> Optional[str]:
        client = self._get_client()
        if client == "unavailable":
            return None
        try:
            from datetime import timedelta
            url = client.presigned_get_object(bucket, key, expires=timedelta(hours=expires_hours))
            return url
        except Exception as e:
            logger.error(f"Presigned URL failed: {e}")
            return None

    def download(self, bucket: str, key: str) -> Optional[bytes]:
        client = self._get_client()
        if client == "unavailable":
            return None
        try:
            response = client.get_object(bucket, key)
            return response.read()
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return None
