"""
Proposal asset storage service using Contabo Object Storage (S3-compatible).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import settings
from app.core.exceptions import BusinessLogicError


@dataclass(frozen=True)
class UploadedProposalAsset:
    key: str
    url: str


class ProposalAssetService:
    """Upload proposal visual assets to Contabo Object Storage."""

    MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024
    ALLOWED_CONTENT_TYPES = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/svg+xml": ".svg",
    }

    def __init__(self) -> None:
        self.endpoint_url = settings.CONTABO_S3_ENDPOINT_URL.rstrip("/")
        self.region = settings.CONTABO_S3_REGION or "default"
        self.bucket = settings.CONTABO_S3_BUCKET
        self.public_base_url = settings.CONTABO_S3_PUBLIC_BASE_URL.rstrip("/")

    def is_configured(self) -> bool:
        return all(
            [
                self.endpoint_url,
                self.bucket,
                settings.CONTABO_S3_ACCESS_KEY_ID,
                settings.CONTABO_S3_SECRET_ACCESS_KEY,
            ]
        )

    def _client(self):
        return boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            region_name=self.region,
            aws_access_key_id=settings.CONTABO_S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.CONTABO_S3_SECRET_ACCESS_KEY,
        )

    def _public_url(self, key: str) -> str:
        if self.public_base_url:
            return f"{self.public_base_url}/{key}"
        return f"{self.endpoint_url}/{self.bucket}/{key}"

    def _extension_for(self, content_type: str, filename: str) -> str:
        if content_type in self.ALLOWED_CONTENT_TYPES:
            return self.ALLOWED_CONTENT_TYPES[content_type]
        suffix = Path(filename or "").suffix.lower()
        if suffix in set(self.ALLOWED_CONTENT_TYPES.values()):
            return suffix
        raise BusinessLogicError(f"Unsupported asset content type: {content_type or 'unknown'}")

    def upload(
        self,
        *,
        organization_id: int,
        project_id: int,
        proposal_id: int,
        asset_type: str,
        filename: str,
        content_type: str,
        content: bytes,
    ) -> UploadedProposalAsset:
        if not self.is_configured():
            raise BusinessLogicError("Contabo Object Storage is not configured")
        if asset_type not in {"logo", "cover"}:
            raise BusinessLogicError("asset_type must be 'logo' or 'cover'")
        if not content:
            raise BusinessLogicError("Asset file is empty")
        if len(content) > self.MAX_FILE_SIZE_BYTES:
            raise BusinessLogicError("Asset file exceeds 5MB limit")

        extension = self._extension_for(content_type, filename)
        key = (
            f"organizations/{organization_id}/projects/{project_id}/"
            f"proposals/{proposal_id}/{asset_type}-{uuid4().hex}{extension}"
        )

        try:
            self._client().put_object(
                Bucket=self.bucket,
                Key=key,
                Body=content,
                ContentType=content_type or "application/octet-stream",
                CacheControl="public, max-age=31536000, immutable",
                ACL="public-read",
            )
        except (BotoCoreError, ClientError) as exc:
            raise BusinessLogicError("Could not upload proposal asset to Contabo") from exc

        return UploadedProposalAsset(key=key, url=self._public_url(key))
