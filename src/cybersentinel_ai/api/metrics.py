import logging
from time import perf_counter

from fastapi import FastAPI, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from cybersentinel_ai.observability.metrics import (
    HTTP_REQUEST_DURATION_SECONDS,
    HTTP_REQUESTS_TOTAL,
)

logger = logging.getLogger("cybersentinel.http")


def configure_metrics(app: FastAPI) -> None:
    @app.middleware("http")
    async def prometheus_middleware(
        request: Request,
        call_next,
    ) -> Response:
        start_time = perf_counter()

        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
        finally:
            duration = perf_counter() - start_time
            route = request.scope.get("route")
            path = getattr(route, "path", request.url.path)

            HTTP_REQUESTS_TOTAL.labels(
                method=request.method,
                path=path,
                status=str(status_code),
            ).inc()

            HTTP_REQUEST_DURATION_SECONDS.labels(
                method=request.method,
                path=path,
            ).observe(duration)
            logger.info(
                "request_completed",
                extra={
                    "request_id": getattr(
                        getattr(request.state, "audit_context", None),
                        "request_id",
                        request.headers.get("x-request-id"),
                    ),
                    "method": request.method,
                    "path": path,
                    "status": status_code,
                    "duration_ms": round(duration * 1000, 3),
                },
            )

        return response

    @app.get("/metrics", include_in_schema=False)
    def prometheus_metrics() -> Response:
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST,
        )
