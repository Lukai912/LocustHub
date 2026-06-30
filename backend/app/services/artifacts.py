from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.parse import quote


class ArtifactRepository:
    provider = "local_fs"
    bucket = "locusthub-local"

    def upload_text(self, object_key: str, content: str, content_type: str) -> dict:
        raise NotImplementedError

    def generate_download_url(self, object_key: str) -> str:
        raise NotImplementedError

    def read_text(self, object_key: str) -> str:
        raise NotImplementedError


class LocalArtifactRepository(ArtifactRepository):
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def upload_text(self, object_key: str, content: str, content_type: str) -> dict:
        # Keep the object key layout identical to OSS so local reports can be
        # promoted or compared with cloud artifacts without path translation.
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

    def path_for(self, object_key: str) -> Path:
        # Resolve and validate local paths so API download routes cannot be used
        # to escape the artifact root with crafted object keys.
        path = (self.root / object_key).resolve()
        if not path.is_relative_to(self.root.resolve()):
            raise ValueError("Artifact object key escapes the configured root")
        return path

    def read_text(self, object_key: str) -> str:
        return self.path_for(object_key).read_text(encoding="utf-8")


class AliyunOssArtifactRepository(ArtifactRepository):
    provider = "aliyun_oss"

    def __init__(self, endpoint: str, bucket: str, access_key_id: str, access_key_secret: str, signed_url_expire_seconds: int = 900):
        if not endpoint or not bucket or not access_key_id or not access_key_secret:
            raise ValueError("Aliyun OSS endpoint, bucket, access key id, and access key secret are required")
        # OSS is optional for local development; defer importing the SDK until
        # the provider is explicitly enabled.
        try:
            import oss2
        except ImportError as exc:
            raise RuntimeError("oss2 is required when ARTIFACT_STORAGE_PROVIDER=aliyun_oss") from exc

        self.bucket = bucket
        self._expire_seconds = signed_url_expire_seconds
        auth = oss2.Auth(access_key_id, access_key_secret)
        self._bucket = oss2.Bucket(auth, endpoint, bucket)

    def upload_text(self, object_key: str, content: str, content_type: str) -> dict:
        encoded = content.encode("utf-8")
        self._bucket.put_object(object_key, encoded, headers={"Content-Type": content_type})
        return {
            "provider": self.provider,
            "bucket": self.bucket,
            "object_key": object_key,
            "content_type": content_type,
            "size_bytes": len(encoded),
            "checksum": hashlib.sha256(encoded).hexdigest(),
        }

    def generate_download_url(self, object_key: str) -> str:
        return self._bucket.sign_url("GET", object_key, self._expire_seconds)

    def read_text(self, object_key: str) -> str:
        return self._bucket.get_object(object_key).read().decode("utf-8")


class UnconfiguredOssArtifactRepository(ArtifactRepository):
    provider = "aliyun_oss"

    def __init__(self, bucket: str = ""):
        self.bucket = bucket or "unconfigured"

    def upload_text(self, object_key: str, content: str, content_type: str) -> dict:
        raise RuntimeError("Aliyun OSS is selected but not fully configured")

    def generate_download_url(self, object_key: str) -> str:
        # Return a stable pointer for metadata previews even though uploads are
        # blocked until credentials are configured.
        return f"oss://{self.bucket}/{quote(object_key)}"

    def read_text(self, object_key: str) -> str:
        raise RuntimeError("Aliyun OSS is selected but not fully configured")
