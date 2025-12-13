"""
Custom exceptions untuk use cases khusus

Berisi exception-exception yang tidak termasuk kategori client/server errors standar
tapi spesifik untuk business logic aplikasi.
"""

from app.core.exceptions.base import AppException


class FileValidationError(AppException):
    """
    Exception untuk file validation errors

    Raised ketika uploaded file tidak memenuhi kriteria validasi:
    - File type tidak diizinkan
    - File size melebihi limit
    - File content tidak sesuai dengan extension

    HTTP Status Code: 400 Bad Request

    Example:
        >>> raise FileValidationError("File terlalu besar. Maximum size: 5 MB")
        >>> raise FileValidationError("File type 'image/svg+xml' tidak diizinkan")
    """

    def __init__(self, message: str = "File validation failed"):
        super().__init__(message, 400)
