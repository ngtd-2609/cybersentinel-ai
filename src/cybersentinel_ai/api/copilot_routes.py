from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from cybersentinel_ai.rag.copilot import SOCCopilot

router = APIRouter(prefix="/copilot", tags=["SOC Copilot"])


class CopilotRequest(BaseModel):
    question: str = Field(min_length=1)
    alert_context: str | None = None
    top_k: int = Field(default=4, ge=1, le=10)


class CopilotSourceResponse(BaseModel):
    document_id: str
    title: str
    source: str
    score: float


class CopilotResponse(BaseModel):
    answer: str
    model: str
    sources: list[CopilotSourceResponse]


def get_copilot() -> SOCCopilot:
    return SOCCopilot()


CopilotDependency = Annotated[
    SOCCopilot,
    Depends(get_copilot),
]


@router.post("/ask", response_model=CopilotResponse)
def ask_copilot(
    payload: CopilotRequest,
    copilot: CopilotDependency,
) -> CopilotResponse:
    result = copilot.ask(
        question=payload.question,
        alert_context=payload.alert_context,
        top_k=payload.top_k,
    )

    return CopilotResponse(
        answer=result.answer,
        model=result.model,
        sources=[
            CopilotSourceResponse(
                document_id=source.document_id,
                title=source.title,
                source=source.source,
                score=source.score,
            )
            for source in result.sources
        ],
    )
