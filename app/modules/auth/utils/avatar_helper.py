"""
Avatar Helper Utility

Provides functions to download avatar from URL and upload to GCP Storage
"""

import logging
import httpx
from typing import Optional

from app.core.utils.gcp_storage import get_gcp_storage_client

logger = logging.getLogger(__name__)


async def download_and_upload_avatar_from_url(
    avatar_url: str, user_id: str, old_avatar_path: Optional[str] = None
) -> Optional[str]:
    """
    Download avatar dari URL (OAuth/Firebase) dan upload ke GCP private bucket

    Args:
        avatar_url: URL avatar dari OAuth provider (Google, Firebase, etc)
        user_id: User ID untuk path di GCP
        old_avatar_path: Old avatar path untuk di-delete jika ada

    Returns:
        Optional[str]: GCP path dari uploaded avatar, atau None jika gagal

    Example:
        >>> path = await download_and_upload_avatar_from_url(
        ...     avatar_url="https://lh3.googleusercontent.com/a/xxx",
        ...     user_id="user-uuid-123"
        ... )
        >>> # Result: "users/user-uuid-123/avatar/abc123.jpg"
    """
    try:
        logger.info(f"Downloading avatar from {avatar_url} for user {user_id}")

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(avatar_url)
            response.raise_for_status()

            content_type = response.headers.get("content-type", "image/jpeg")
            file_content = response.content

            # Validate content type
            if not content_type.startswith("image/"):
                logger.warning(f"Invalid content type for avatar: {content_type}")
                return None

            # Validate file size (max 5MB)
            if len(file_content) > 5 * 1024 * 1024:
                logger.warning(f"Avatar too large: {len(file_content)} bytes")
                return None

        storage_client = get_gcp_storage_client()

        ext = ".jpg"  # default
        if "png" in content_type:
            ext = ".png"
        elif "webp" in content_type:
            ext = ".webp"
        elif "gif" in content_type:
            ext = ".gif"

        destination_path = storage_client.generate_unique_filename(
            original_filename=f"avatar{ext}", prefix=f"users/{user_id}/avatar"
        )
        import asyncio
        await asyncio.to_thread(
            storage_client.upload_file,
            file_content=file_content,
            destination_path=destination_path,
            content_type=content_type,
        )

        logger.info(f"Avatar uploaded to GCP: {destination_path}")

        if old_avatar_path:
            try:
                await asyncio.to_thread(storage_client.delete_file, old_avatar_path)
                logger.info(f"Old avatar deleted: {old_avatar_path}")
            except Exception as e:
                logger.warning(f"Failed to delete old avatar {old_avatar_path}: {e}")

        return destination_path

    except httpx.HTTPError as e:
        logger.error(f"HTTP error downloading avatar: {e}")
        return None
    except Exception as e:
        logger.error(f"Error downloading and uploading avatar: {e}")
        return None
