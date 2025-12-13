import logging
import time
from datetime import datetime
from uuid import uuid4

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.exceptions import AppException

logger = logging.getLogger(__name__)


ERROR_MESSAGES_ID = {
    400: "Permintaan tidak valid",
    401: "Tidak terautentikasi",
    403: "Akses ditolak",
    404: "Data tidak ditemukan",
    409: "Data sudah ada",
    422: "Data tidak valid",
    500: "Terjadi kesalahan pada server",
}


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    
    def _handle_integrity_error(self, error):
        """Parse IntegrityError and raise appropriate ConflictException."""
        from app.core.exceptions import ConflictException
        
        error_str = str(error.orig) if hasattr(error, 'orig') else str(error)
        
        # Unique constraint violations
        if "UniqueViolationError" in error_str or "unique constraint" in error_str.lower():
            if "users_email_key" in error_str or "email" in error_str.lower():
                raise ConflictException(
                    message="Email sudah terdaftar",
                    error_code="DUPLICATE_EMAIL"
                )
            elif "users_phone_key" in error_str or "phone" in error_str.lower():
                raise ConflictException(
                    message="Nomor telepon sudah terdaftar",
                    error_code="DUPLICATE_PHONE"
                )
            else:
                raise ConflictException(
                    message="Data sudah ada dalam sistem",
                    error_code="DUPLICATE_ENTRY"
                )
        
        # Foreign key violations
        elif "ForeignKeyViolationError" in error_str or "foreign key" in error_str.lower():
            raise ConflictException(
                message="Data terkait tidak ditemukan",
                error_code="FOREIGN_KEY_VIOLATION"
            )
        
        # Not null violations
        elif "NotNullViolationError" in error_str or "not-null" in error_str.lower():
            from app.core.exceptions import BadRequestException
            raise BadRequestException(
                message="Data wajib tidak boleh kosong",
                error_code="NOT_NULL_VIOLATION"
            )
        
        # Check constraint violations
        elif "CheckViolationError" in error_str or "check constraint" in error_str.lower():
            from app.core.exceptions import BadRequestException
            raise BadRequestException(
                message="Data tidak valid atau melanggar aturan",
                error_code="CHECK_CONSTRAINT_VIOLATION"
            )
        
        else:
            logger.error(f"Unhandled IntegrityError: {error_str}")
            from app.core.exceptions import DatabaseException
            raise DatabaseException(
                message="Terjadi kesalahan pada database"
            )
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except AppException as e:
            logger.warning(f"AppException: {e.message} (status={e.status_code})")
            response = JSONResponse(
                status_code=e.status_code,
                content={
                    "error": True,
                    "message": e.message,
                    "error_code": e.error_code,
                    "details": e.details,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )
            # Add CORS headers
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "*"
            return response
        except Exception as e:
            # Check if it's an IntegrityError
            from sqlalchemy.exc import IntegrityError
            if isinstance(e, IntegrityError):
                try:
                    self._handle_integrity_error(e)
                except AppException as app_exc:
                    # Re-handle the raised AppException
                    logger.warning(f"{app_exc.__class__.__name__}: {app_exc.message}")
                    response = JSONResponse(
                        status_code=app_exc.status_code,
                        content={
                            "error": True,
                            "message": app_exc.message,
                            "error_code": app_exc.error_code,
                            "details": app_exc.details,
                            "timestamp": datetime.utcnow().isoformat(),
                        },
                    )
                    # Add CORS headers
                    response.headers["Access-Control-Allow-Origin"] = "*"
                    response.headers["Access-Control-Allow-Credentials"] = "true"
                    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
                    response.headers["Access-Control-Allow-Headers"] = "*"
                    return response
            
            # Generic error handler
            logger.exception(f"Unhandled exception: {str(e)}")
            response = JSONResponse(
                status_code=500,
                content={
                    "error": True,
                    "message": ERROR_MESSAGES_ID.get(
                        500, "Terjadi kesalahan pada server"
                    ),
                    "error_code": "INTERNAL_ERROR",
                    "details": {},
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )
            # Add CORS headers
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "*"
            return response


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid4())[:8]
        start_time = time.time()

        logger.info(
            f"[{request_id}] → {request.method} {request.url.path} "
            f"(client: {request.client.host if request.client else 'unknown'})"
        )

        response = await call_next(request)

        process_time = (time.time() - start_time) * 1000
        logger.info(
            f"[{request_id}] ← {response.status_code} " f"({process_time:.2f}ms)"
        )

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.2f}ms"

        return response
