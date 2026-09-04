import re
from contextvars import ContextVar, Token
from dataclasses import dataclass
from uuid import uuid4

from starlette.requests import Request

REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,128}$")


@dataclass(frozen=True)
class RequestAuditContext:
    request_id: str
    ip_address: str | None
    user_agent: str | None


_request_context: ContextVar[RequestAuditContext | None] = ContextVar(
    "audit_request_context", default=None
)


def resolve_client_ip(request: Request, *, trust_proxy_headers: bool) -> str | None:
    if trust_proxy_headers:
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",", maxsplit=1)[0].strip()[:45]
    return request.client.host[:45] if request.client else None


def build_request_context(request: Request, *, trust_proxy_headers: bool) -> RequestAuditContext:
    existing = getattr(request.state, "audit_context", None)
    if isinstance(existing, RequestAuditContext):
        return existing
    supplied_request_id = request.headers.get("X-Request-ID", "").strip()
    request_id = (
        supplied_request_id if REQUEST_ID_PATTERN.fullmatch(supplied_request_id) else str(uuid4())
    )
    context = RequestAuditContext(
        request_id=request_id,
        ip_address=resolve_client_ip(request, trust_proxy_headers=trust_proxy_headers),
        user_agent=request.headers.get("User-Agent", "")[:512] or None,
    )
    request.state.audit_context = context
    return context


def set_request_context(context: RequestAuditContext) -> Token:
    return _request_context.set(context)


def reset_request_context(token: Token) -> None:
    _request_context.reset(token)


def get_request_context() -> RequestAuditContext | None:
    return _request_context.get()
