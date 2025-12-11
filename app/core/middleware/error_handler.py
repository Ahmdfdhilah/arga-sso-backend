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
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except AppException as e:
            logger.warning(f"AppException: {e.message} (status={e.status_code})")
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": True,
                    "message": e.message,
                    "error_code": e.error_code,
                    "details": e.details,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )
        except Exception as e:
            logger.exception(f"Unhandled exception: {str(e)}")
            return JSONResponse(
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
