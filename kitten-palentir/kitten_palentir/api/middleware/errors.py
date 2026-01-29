"""Error handling middleware."""

import logging
from typing import Callable

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for handling errors gracefully."""

    async def dispatch(self, request: Request, call_next: Callable) -> JSONResponse:
        """Handle errors and return appropriate responses.

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response or error response
        """
        try:
            response = await call_next(request)
            return response

        except Exception as e:
            logger.error(f"Unhandled error in middleware: {e}", exc_info=True)

            # Return error response
            try:
                from kitten_palentir.config.settings import get_settings
                settings = get_settings()
                error_detail = str(e) if settings.debug else "An internal error occurred"
            except:
                error_detail = "An internal error occurred"

            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Internal server error",
                    "detail": error_detail,
                    "path": str(request.url.path),
                },
            )

