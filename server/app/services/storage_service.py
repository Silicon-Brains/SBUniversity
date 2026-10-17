import os
from pathlib import Path
from typing import Optional
from app.core.config import settings
from app.core.logging import logger

try:
    from supabase import Client, create_client
    supabase_client: Optional[Client] = None
    if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_KEY:
        supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
except Exception as e:
    supabase_client = None
    logger.warning("Supabase client init failed or skipped: %s", e)

LOCAL_STORAGE_DIR = Path("storage_local")
LOCAL_STORAGE_DIR.mkdir(parents=True, exist_ok=True)


class StorageService:
    @staticmethod
    async def upload_file(path: str, content: bytes, content_type: str = "application/pdf") -> str:
        """Uploads file to Supabase Storage bucket, or local disk fallback."""
        if supabase_client:
            try:
                bucket = settings.SUPABASE_STORAGE_BUCKET
                res = supabase_client.storage.from_(bucket).upload(
                    path=path,
                    file=content,
                    file_options={"content-type": content_type, "upsert": "true"},
                )
                logger.info("Uploaded %s to Supabase Storage", path)
                return path
            except Exception as e:
                logger.warning("Failed uploading to Supabase Storage: %s. Falling back to local.", e)

        # Local storage fallback
        local_path = LOCAL_STORAGE_DIR / path
        local_path.parent.mkdir(parents=True, exist_ok=True)
        with open(local_path, "wb") as f:
            f.write(content)
        return str(local_path.resolve())

    @staticmethod
    async def download_file(path: str) -> Optional[bytes]:
        """Downloads file bytes from Supabase Storage or local disk fallback."""
        if supabase_client:
            try:
                bucket = settings.SUPABASE_STORAGE_BUCKET
                res = supabase_client.storage.from_(bucket).download(path)
                return res
            except Exception as e:
                logger.warning("Failed downloading from Supabase Storage: %s. Checking local.", e)

        local_path = Path(path)
        if not local_path.is_absolute():
            local_path = LOCAL_STORAGE_DIR / path
        if local_path.exists():
            with open(local_path, "rb") as f:
                return f.read()

        return None

    @staticmethod
    async def delete_file(path: str) -> None:
        """Deletes a stored object from Supabase Storage or local disk."""
        if supabase_client and not Path(path).is_absolute():
            try:
                bucket = settings.SUPABASE_STORAGE_BUCKET
                supabase_client.storage.from_(bucket).remove([path])
                return
            except Exception as e:
                logger.error("Failed deleting %s from Supabase Storage: %s", path, e)
                raise RuntimeError("Could not delete stored file") from e

        local_path = Path(path)
        if not local_path.is_absolute():
            local_path = LOCAL_STORAGE_DIR / path
        try:
            local_path.unlink(missing_ok=True)
        except OSError as e:
            logger.error("Failed deleting local stored file %s: %s", local_path, e)
            raise RuntimeError("Could not delete stored file") from e
