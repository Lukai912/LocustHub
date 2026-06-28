from __future__ import annotations

import hashlib
from pathlib import Path


class ArtifactRepository:
    provider = "local_fs"
    bucket = "locusthub-local"

    def upload_text(self, object_key: str, content: str, content_type: str) -> dict:
        raise NotImplementedError

    def generate_download_url(self, object_key: str) -> str:
        raise NotImplementedError


class LocalArtifactRepository(ArtifactRepository):
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def upload_text(self, object_key: str, content: str, content_type: str) -> dict:
        path = self.root / object_key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        encoded = content.encode("utf-8")
        return {
            "provider": self.provider,
            "bucket": self.bucket,
            "object_key": object_key,
            "content_type": content_type,
            "size_bytes": len(encoded),
            "checksum": hashlib.sha256(encoded).hexdigest(),
        }

    def generate_download_url(self, object_key: str) -> str:
        return f"/artifacts/{object_key}"
