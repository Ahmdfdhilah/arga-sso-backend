"""
File Upload utility

Provides functions untuk handle multipart file uploads dengan validasi.
Support berbagai tipe file (images, documents, videos, dll).
"""

from fastapi import UploadFile
from typing import List, Tuple, Optional
import os
import filetype
import logging
import httpx
from io import BytesIO

from app.config.settings import settings
from app.core.exceptions import FileValidationError

logger = logging.getLogger(__name__)


async def validate_file_type(file: UploadFile, allowed_types: set) -> str:
    """
    Validate file type berdasarkan MIME type dan magic bytes

    Args:
        file: UploadFile object dari FastAPI
        allowed_types: Set dari allowed MIME types

    Returns:
        str: Validated MIME type

    Raises:
        FileValidationError: Jika file type tidak diizinkan

    Example:
        >>> file_type = await validate_file_type(
        ...     file=uploaded_file,
        ...     allowed_types=settings.ALLOWED_IMAGE_TYPES
        ... )
    """
    logger.debug(f"Validating file type for: {file.filename}")

    # Check content type dari upload
    content_type = file.content_type

    if content_type is None:
        raise FileValidationError("File tidak memiliki content type")

    if content_type not in allowed_types:
        logger.warning(f"File type '{content_type}' not allowed for file: {file.filename}")
        raise FileValidationError(
            f"File type '{content_type}' tidak diizinkan. "
            f"Allowed types: {', '.join(allowed_types)}"
        )
    
    # Verify dengan magic bytes
    content = await file.read(2048)
    await file.seek(0)  # Reset file pointer

    # Detect MIME type dari content
    kind = filetype.guess(content)
    
    if kind is not None:
        detected_mime = kind.mime
        
        # Verify detected MIME type matches allowed types
        if detected_mime not in allowed_types:
            logger.warning(f"File content mismatch for {file.filename}: detected {detected_mime}, expected one of {allowed_types}")
            raise FileValidationError(
                f"File content tidak sesuai dengan extension. "
                f"Detected type: {detected_mime}"
            )
        
        logger.debug(f"File type validated: {detected_mime} for {file.filename}")
        return detected_mime
    
    # Fallback to content_type if detection failed
    logger.debug(f"Magic bytes detection failed, using content_type: {content_type} for {file.filename}")
    return content_type


async def validate_file_size(file: UploadFile, max_size: int) -> int:
    """
    Validate ukuran file

    Args:
        file: UploadFile object dari FastAPI
        max_size: Maximum size dalam bytes

    Returns:
        int: Ukuran file dalam bytes

    Raises:
        FileValidationError: Jika file terlalu besar

    Example:
        >>> size = await validate_file_size(
        ...     file=uploaded_file,
        ...     max_size=settings.MAX_IMAGE_SIZE
        ... )
    """
    logger.debug(f"Validating file size for: {file.filename}")
    
    # Get file size
    content = await file.read()
    file_size = len(content)
    await file.seek(0)  # Reset file pointer

    if file_size > max_size:
        max_size_mb = max_size / (1024 * 1024)
        file_size_mb = file_size / (1024 * 1024)
        logger.warning(f"File {file.filename} too large: {file_size_mb:.2f} MB (max: {max_size_mb:.2f} MB)")
        raise FileValidationError(
            f"File terlalu besar. Maximum size: {max_size_mb:.2f} MB"
        )

    logger.debug(f"File size validated: {file_size} bytes for {file.filename}")
    return file_size


async def validate_image_file(
    file: UploadFile, max_size: Optional[int] = None
) -> Tuple[str, int]:
    """
    Validate image file (type + size)

    Args:
        file: UploadFile object
        max_size: Maximum file size (default 5 MB)

    Returns:
        Tuple[str, int]: (MIME type, file size)

    Raises:
        FileValidationError: Jika validasi gagal

    Example:
        >>> mime_type, size = await validate_image_file(uploaded_file)
    """
    logger.info(f"Validating image file: {file.filename}")
    
    if max_size is None:
        max_size = settings.MAX_IMAGE_SIZE
    mime_type = await validate_file_type(file, settings.ALLOWED_IMAGE_TYPES)
    file_size = await validate_file_size(file, max_size)
    
    logger.info(f"Image file validated: {file.filename}, type: {mime_type}, size: {file_size} bytes")
    return mime_type, file_size


async def validate_document_file(
    file: UploadFile, max_size: Optional[int] = None
) -> Tuple[str, int]:
    """
    Validate document file (type + size)

    Args:
        file: UploadFile object
        max_size: Maximum file size (default 10 MB)

    Returns:
        Tuple[str, int]: (MIME type, file size)

    Raises:
        FileValidationError: Jika validasi gagal

    Example:
        >>> mime_type, size = await validate_document_file(uploaded_file)
    """
    if max_size is None:
        max_size = settings.MAX_DOCUMENT_SIZE
    mime_type = await validate_file_type(file, settings.ALLOWED_DOCUMENT_TYPES)
    file_size = await validate_file_size(file, max_size)
    return mime_type, file_size


async def validate_video_file(
    file: UploadFile, max_size: Optional[int] = None
) -> Tuple[str, int]:
    """
    Validate video file (type + size)

    Args:
        file: UploadFile object
        max_size: Maximum file size (default 50 MB)

    Returns:
        Tuple[str, int]: (MIME type, file size)

    Raises:
        FileValidationError: Jika validasi gagal

    Example:
        >>> mime_type, size = await validate_video_file(uploaded_file)
    """
    if max_size is None:
        max_size = settings.MAX_VIDEO_SIZE
    mime_type = await validate_file_type(file, settings.ALLOWED_VIDEO_TYPES)
    file_size = await validate_file_size(file, max_size)
    return mime_type, file_size


async def validate_multiple_files(
    files: List[UploadFile], max_files: int, allowed_types: set, max_size: int
) -> List[Tuple[str, int]]:
    """
    Validate multiple files sekaligus

    Args:
        files: List of UploadFile objects
        max_files: Maximum jumlah files yang diizinkan
        allowed_types: Set dari allowed MIME types
        max_size: Maximum size per file

    Returns:
        List[Tuple[str, int]]: List of (MIME type, file size) untuk tiap file

    Raises:
        FileValidationError: Jika validasi gagal

    Example:
        >>> results = await validate_multiple_files(
        ...     files=uploaded_files,
        ...     max_files=5,
        ...     allowed_types=settings.ALLOWED_IMAGE_TYPES,
        ...     max_size=settings.MAX_IMAGE_SIZE
        ... )
    """
    logger.info(f"Validating {len(files)} files (max: {max_files})")
    
    # Check jumlah files
    if len(files) > max_files:
        logger.warning(f"Too many files: {len(files)} (max: {max_files})")
        raise FileValidationError(f"Terlalu banyak files. Maximum: {max_files} files")

    # Validate tiap file
    results = []
    for idx, file in enumerate(files):
        logger.debug(f"Validating file {idx + 1}/{len(files)}: {file.filename}")
        mime_type = await validate_file_type(file, allowed_types)
        file_size = await validate_file_size(file, max_size)
        results.append((mime_type, file_size))

    logger.info(f"Successfully validated {len(files)} files")
    return results


def get_file_extension(filename: str) -> str:
    """
    Get file extension dari filename

    Args:
        filename: Nama file

    Returns:
        str: File extension (dengan dot, lowercase)

    Example:
        >>> ext = get_file_extension("photo.JPG")
        >>> # Result: ".jpg"
    """
    _, ext = os.path.splitext(filename)
    return ext.lower()


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename untuk menghindari security issues

    Args:
        filename: Original filename

    Returns:
        str: Sanitized filename

    Example:
        >>> safe_name = sanitize_filename("../../../etc/passwd")
        >>> # Result: "etc_passwd"
    """
    # Remove path separators
    filename = filename.replace("/", "_").replace("\\", "_")

    # Remove potentially dangerous characters
    dangerous_chars = ["<", ">", ":", '"', "|", "?", "*"]
    for char in dangerous_chars:
        filename = filename.replace(char, "_")

    # Remove leading/trailing dots and spaces
    filename = filename.strip(". ")

    return filename


async def read_file_content(file: UploadFile) -> bytes:
    """
    Read file content dan reset file pointer

    Args:
        file: UploadFile object

    Returns:
        bytes: File content

    Example:
        >>> content = await read_file_content(uploaded_file)
    """
    content = await file.read()
    await file.seek(0)  # Reset untuk bisa dibaca lagi
    return content


async def upload_file_to_gcp(
    file: UploadFile,
    entity_type: str,
    entity_id: int | str,
    subfolder: str = "profile",
    allowed_types: Optional[set] = None,
    max_size: Optional[int] = None,
) -> tuple[str, str]:
    """
    Upload file ke GCP bucket dengan validasi (generic function untuk semua entity)

    Args:
        file: UploadFile dari FastAPI
        entity_type: Tipe entity (e.g., "account_executives", "farmers")
        entity_id: ID entity (int or str)
        subfolder: Subfolder di dalam entity folder (default: "profile")
        allowed_types: Set MIME types yang diizinkan (default: settings.ALLOWED_IMAGE_TYPES)
        max_size: Max file size dalam bytes (default: settings.MAX_IMAGE_SIZE)

    Returns:
        tuple[str, str]: (signed_url, path) - Signed URL dan path mentah untuk disimpan ke database

    Raises:
        FileValidationError: Jika validasi file gagal

    Example:
        >>> # Upload profile image untuk farmer
        >>> signed_url, path = await upload_file_to_gcp(
        ...     file=profile_img,
        ...     entity_type="farmers",
        ...     entity_id=123,
        ...     subfolder="profile"
        ... )
        >>> # Save 'path' to database, return 'signed_url' to client

        >>> # Upload document untuk farmer
        >>> signed_url, path = await upload_file_to_gcp(
        ...     file=doc_file,
        ...     entity_type="farmers",
        ...     entity_id=123,
        ...     subfolder="documents",
        ...     allowed_types=settings.ALLOWED_DOCUMENT_TYPES,
        ...     max_size=settings.MAX_DOCUMENT_SIZE
        ... )
    """
    logger.info(f"Uploading file to GCP: {file.filename} for {entity_type}/{entity_id}/{subfolder}")

    from app.core.utils.gcp_storage import get_gcp_storage_client

    # Default values
    if allowed_types is None:
        allowed_types = settings.ALLOWED_IMAGE_TYPES
    if max_size is None:
        max_size = settings.MAX_IMAGE_SIZE

    # 1. Validate file type & size
    mime_type = await validate_file_type(file, allowed_types)
    file_size = await validate_file_size(file, max_size)
    logger.debug(f"File validated: {mime_type}, {file_size} bytes")

    # 2. Read file content
    file_content = await read_file_content(file)

    # 3. Get storage client
    storage_client = get_gcp_storage_client()

    # 4. Generate unique filename with entity path
    if file.filename is None:
        raise FileValidationError("File tidak memiliki filename")

    destination_path = storage_client.generate_unique_filename(
        original_filename=file.filename, prefix=f"{entity_type}/{entity_id}/{subfolder}"
    )
    logger.debug(f"Destination path: {destination_path}")

    import asyncio
    signed_url = await asyncio.to_thread(
        storage_client.upload_file,
        file_content=file_content,
        destination_path=destination_path,
        content_type=mime_type,
    )

    logger.info(f"Successfully uploaded file to GCP: {destination_path}")
    return (signed_url, destination_path)


def delete_file_from_gcp_url(file_url: str) -> bool:
    """
    Delete file dari GCP bucket berdasarkan URL (generic function)

    Args:
        file_url: URL file yang akan dihapus (public URL atau signed URL)

    Returns:
        bool: True jika berhasil dihapus, False jika gagal

    Example:
        >>> # Delete file by URL
        >>> success = delete_file_from_gcp_url(
        ...     "https://storage.googleapis.com/bucket-name/farmers/123/profile/file.jpg"
        ... )
    """
    logger.info(f"Attempting to delete file from GCP: {file_url}")

    from app.core.utils.gcp_storage import get_gcp_storage_client

    try:
        if not file_url:
            logger.warning("Empty file URL provided for deletion")
            return False

        storage_client = get_gcp_storage_client()

        # Extract file path from URL
        # URL format: https://storage.googleapis.com/bucket-name/path/to/file.jpg
        if storage_client.bucket_name in file_url:
            file_path = file_url.split(f"{storage_client.bucket_name}/")[-1]

            # Remove query parameters jika ada (untuk signed URLs)
            file_path = file_path.split("?")[0]

            result = storage_client.delete_file(file_path)
            if result:
                logger.info(f"Successfully deleted file from GCP: {file_path}")
            else:
                logger.warning(f"Failed to delete file from GCP: {file_path}")
            return result

        logger.warning(f"Bucket name not found in URL: {file_url}")
        return False
    except Exception as e:
        logger.error(f"Error deleting file from GCP: {e}")
        return False


def generate_signed_url_for_path(path: str) -> Optional[str]:
    """
    Generate signed URL untuk single file path (on-demand, 7 days expiry)

    Args:
        path: GCP storage path (e.g., "farmers/profiles/photo.jpg")

    Returns:
        Optional[str]: Signed URL atau None jika path kosong atau error

    Example:
        >>> url = generate_signed_url_for_path("farmers/123/profile/photo.jpg")
        >>> # Result: "https://storage.googleapis.com/...?X-Goog-Signature=..."
    """
    if not path:
        return None

    from app.core.utils.gcp_storage import get_gcp_storage_client

    try:
        gcp_client = get_gcp_storage_client()
        return gcp_client.get_file_url(path)
    except Exception as e:
        logger.error(f"Error generating signed URL for path {path}: {e}")
        return None


def generate_signed_urls_for_paths(paths: List[str]) -> Optional[List[str]]:
    """
    Generate signed URLs untuk array of file paths (on-demand, 7 days expiry)

    Args:
        paths: List of GCP storage paths

    Returns:
        Optional[List[str]]: List of signed URLs atau None jika paths kosong atau error

    Example:
        >>> urls = generate_signed_urls_for_paths([
        ...     "farmers/123/land/land1.jpg",
        ...     "farmers/123/land/land2.jpg"
        ... ])
        >>> # Result: ["https://storage.googleapis.com/...signed-url-1...", "https://...signed-url-2..."]
    """
    if not paths:
        return None

    from app.core.utils.gcp_storage import get_gcp_storage_client

    try:
        gcp_client = get_gcp_storage_client()
        signed_urls = []
        for path in paths:
            if path:
                url = gcp_client.get_file_url(path)
                if url:
                    signed_urls.append(url)
        return signed_urls if signed_urls else None
    except Exception as e:
        logger.error(f"Error generating signed URLs for paths: {e}")
        return None


def extract_path_from_gcp_url(file_url: str) -> Optional[str]:
    """
    Extract file path dari GCP URL (public URL atau signed URL)

    Args:
        file_url: GCP URL (e.g., "https://storage.googleapis.com/bucket-name/path/to/file.jpg?signature=...")

    Returns:
        Optional[str]: File path (e.g., "path/to/file.jpg") atau None jika invalid

    Example:
        >>> path = extract_path_from_gcp_url(
        ...     "https://storage.googleapis.com/my-bucket/farmers/123/home/0/image.jpg?X-Goog-Signature=..."
        ... )
        >>> # Result: "farmers/123/home/0/image.jpg"
    """
    from app.core.utils.gcp_storage import get_gcp_storage_client

    try:
        if not file_url:
            return None

        storage_client = get_gcp_storage_client()

        # Extract file path from URL
        # URL format: https://storage.googleapis.com/bucket-name/path/to/file.jpg
        if storage_client.bucket_name in file_url:
            file_path = file_url.split(f"{storage_client.bucket_name}/")[-1]

            # Remove query parameters jika ada (untuk signed URLs)
            file_path = file_path.split("?")[0]

            return file_path

        logger.warning(f"Bucket name not found in URL: {file_url}")
        return None
    except Exception as e:
        logger.error(f"Error extracting path from URL: {e}")
        return None


def extract_paths_from_gcp_urls(file_urls: List[str]) -> List[str]:
    """
    Extract file paths dari list of GCP URLs

    Args:
        file_urls: List of GCP URLs

    Returns:
        List[str]: List of file paths (URLs yang invalid akan di-skip)

    Example:
        >>> paths = extract_paths_from_gcp_urls([
        ...     "https://storage.googleapis.com/bucket/farmers/123/home/0/img1.jpg?sig=...",
        ...     "https://storage.googleapis.com/bucket/farmers/123/home/1/img2.jpg?sig=..."
        ... ])
        >>> # Result: ["farmers/123/home/0/img1.jpg", "farmers/123/home/1/img2.jpg"]
    """
    paths = []
    for url in file_urls:
        path = extract_path_from_gcp_url(url)
        if path:
            paths.append(path)
    return paths