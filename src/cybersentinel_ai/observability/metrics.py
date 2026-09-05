from prometheus_client import Counter, Gauge, Histogram

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

DEPENDENCY_UP = Gauge(
    "cybersentinel_dependency_up",
    "Whether a required service dependency is reachable.",
    ["dependency"],
)

COPILOT_REQUESTS_TOTAL = Counter(
    "cybersentinel_copilot_requests_total",
    "SOC Copilot requests grouped by outcome.",
    ["outcome"],
)
