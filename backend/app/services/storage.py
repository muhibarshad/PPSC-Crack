"""
Object Storage Service (S3 / Cloudflare R2)
=============================================
Uploads scan images to S3-compatible storage and returns public URLs.

Supports:
- AWS S3
- Cloudflare R2 (via S3-compatible API)
- Local filesystem fallback (development)

Usage::

    from app.services.storage import storage_service
    url = await storage_service.upload_scan_image(file_bytes, "paper_123/q_front.jpg")
"""

from __future__ import annotations

import logging
import mimetypes
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO

import aioboto3

from app.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """Async S3-compatible object storage client."""

    def __init__(self) -> None:
        self._session = aioboto3.Session(
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
            region_name=settings.AWS_REGION,
        )
        self._bucket = settings.S3_BUCKET_NAME
        self._endpoint_url = settings.S3_ENDPOINT_URL or None
        self._public_prefix = settings.S3_PUBLIC_URL_PREFIX.rstrip("/")

    # ──────────────────────────────────────────────────────────
    # Upload
    # ──────────────────────────────────────────────────────────

    async def upload_scan_image(
        self,
        file_data: bytes,
        filename: str,
        *,
        paper_id: str | uuid.UUID,
        content_type: str | None = None,
    ) -> str:
        """Upload a scan image and return its public URL.

        Parameters
        ----------
        file_data:
            Raw image bytes (JPEG/PNG).
        filename:
            Original filename (used for extension/MIME detection).
        paper_id:
            Groups images under ``scans/{paper_id}/``.
        content_type:
            Override MIME type.

        Returns
        -------
        str
            The publicly accessible URL for the uploaded image.
        """
        if not content_type:
            content_type = mimetypes.guess_type(filename)[0] or "image/jpeg"

        # Deterministic key: scans/<paper_id>/<timestamp>_<uuid>.<ext>
        ext = Path(filename).suffix.lower() or ".jpg"
        ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        unique = uuid.uuid4().hex[:8]
        key = f"scans/{paper_id}/{ts}_{unique}{ext}"

        if settings.STORAGE_BACKEND == "local":
            return await self._upload_local(file_data, key)

        return await self._upload_s3(file_data, key, content_type)

    async def _upload_s3(
        self,
        file_data: bytes,
        key: str,
        content_type: str,
    ) -> str:
        """Upload to S3 / Cloudflare R2."""
        try:
            async with self._session.client(
                "s3",
                endpoint_url=self._endpoint_url,
            ) as s3:
                await s3.put_object(
                    Bucket=self._bucket,
                    Key=key,
                    Body=file_data,
                    ContentType=content_type,
                    CacheControl="max-age=31536000, immutable",
                )

            # Build public URL
            if self._public_prefix:
                url = f"{self._public_prefix}/{key}"
            elif self._endpoint_url:
                # R2 style
                url = f"{self._endpoint_url}/{self._bucket}/{key}"
            else:
                # Standard S3
                url = f"https://{self._bucket}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"

            logger.info("Uploaded scan image: %s (%d bytes)", key, len(file_data))
            return url

        except Exception as exc:
            logger.exception("Failed to upload %s: %s", key, exc)
            raise RuntimeError(f"Storage upload failed: {exc}") from exc

    async def _upload_local(
        self,
        file_data: bytes,
        key: str,
    ) -> str:
        """Fallback: save to local filesystem (development only)."""
        local_dir = Path("uploads") / Path(key).parent
        local_dir.mkdir(parents=True, exist_ok=True)
        local_path = Path("uploads") / key
        local_path.write_bytes(file_data)
        logger.info("Saved scan locally: %s (%d bytes)", local_path, len(file_data))
        return f"/uploads/{key}"

    # ──────────────────────────────────────────────────────────
    # Batch upload
    # ──────────────────────────────────────────────────────────

    async def upload_scan_images(
        self,
        files: list[tuple[bytes, str]],
        paper_id: str | uuid.UUID,
    ) -> list[str]:
        """Upload multiple images and return their URLs.

        Parameters
        ----------
        files:
            List of ``(file_data, filename)`` tuples.
        paper_id:
            Paper UUID for grouping.

        Returns
        -------
        list[str]
            URLs in the same order as input.
        """
        urls: list[str] = []
        for file_data, filename in files:
            url = await self.upload_scan_image(
                file_data, filename, paper_id=paper_id,
            )
            urls.append(url)
        return urls

    # ──────────────────────────────────────────────────────────
    # Delete
    # ──────────────────────────────────────────────────────────

    async def delete_scan_images(self, keys: list[str]) -> None:
        """Delete multiple objects from storage."""
        if settings.STORAGE_BACKEND == "local":
            for key in keys:
                path = Path("uploads") / key
                path.unlink(missing_ok=True)
            return

        try:
            async with self._session.client(
                "s3",
                endpoint_url=self._endpoint_url,
            ) as s3:
                objects = [{"Key": k} for k in keys]
                if objects:
                    await s3.delete_objects(
                        Bucket=self._bucket,
                        Delete={"Objects": objects},
                    )
            logger.info("Deleted %d scan images", len(keys))
        except Exception as exc:
            logger.warning("Failed to delete scan images: %s", exc)


# ── Singleton ────────────────────────────────────────────────

_storage: StorageService | None = None


def get_storage_service() -> StorageService:
    """Get or create the singleton storage service."""
    global _storage
    if _storage is None:
        _storage = StorageService()
    return _storage
