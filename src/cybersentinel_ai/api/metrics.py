from time import perf_counter

from fastapi import FastAPI, Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)

HTTP_REQUESTS_TOTAL = Counter(
    "cybersentinel_http_requests_total",
    "Total HTTP requests handled by CyberSentinel AI.",
    ["method", "path", "status"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "cybersentinel_http_request_duration_seconds",
    "HTTP request latency in seconds.",
    ["method", "path"],
)


def configure_metrics(app: FastAPI) -> None:
    @app.middleware("http")
    async def prometheus_middleware(
        request: Request,
        call_next,
    ) -> Response:
        start_time = perf_counter()

        response = await call_next(request)

        duration = perf_counter() - start_time

        path = request.url.path

        HTTP_REQUESTS_TOTAL.labels(
            method=request.method,
            path=path,
            status=str(response.status_code),
        ).inc()

        HTTP_REQUEST_DURATION_SECONDS.labels(
            method=request.method,
            path=path,
        ).observe(duration)

        return response

    @app.get("/metrics", include_in_schema=False)
    def prometheus_metrics() -> Response:
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST,
        )
