from dataclasses import dataclass

from cybersentinel_ai.rag.knowledge_base import build_default_knowledge_base
from cybersentinel_ai.rag.ollama_client import OllamaClient
from cybersentinel_ai.rag.retriever import (
    RetrievalResult,
    TfidfRetriever,
)
from cybersentinel_ai.threat_intel.attack_mapping import map_attack_label

SYSTEM_PROMPT = """You are CyberSentinel AI, a SOC analyst copilot.
Use only the supplied security context when making factual claims.
If the context is insufficient, clearly say what additional evidence is needed.
Do not invent indicators, CVEs, MITRE techniques, hosts, users, or attack evidence.
Keep recommendations practical, prioritized, and suitable for a SOC analyst.
"""

KNOWN_ATTACK_LABELS = (
    "PortScan",
    "DDoS",
    "DoS GoldenEye",
    "DoS Hulk",
    "DoS Slowhttptest",
    "DoS slowloris",
    "FTP-Patator",
    "SSH-Patator",
    "Web Attack - Brute Force",
    "Web Attack - Sql Injection",
    "Web Attack - XSS",
    "Heartbleed",
)


@dataclass(frozen=True)
class CopilotSource:
    document_id: str
    title: str
    source: str
    score: float


@dataclass(frozen=True)
class CopilotAnswer:
    answer: str
    sources: tuple[CopilotSource, ...]
    model: str


class SOCCopilot:
    def __init__(
        self,
        retriever: TfidfRetriever | None = None,
        llm_client: OllamaClient | None = None,
    ) -> None:
        self.retriever = retriever or TfidfRetriever(
            build_default_knowledge_base()
        )
        self.llm_client = llm_client or OllamaClient()

    @staticmethod
    def _format_context(
        results: list[RetrievalResult],
    ) -> str:
        sections = []

        for index, result in enumerate(results, start=1):
            document = result.document

            sections.append(
                "\n".join(
                    [
                        f"[SOURCE {index}]",
                        f"Title: {document.title}",
                        f"Source: {document.source}",
                        f"Content: {document.content}",
                    ]
                )
            )

        return "\n\n".join(sections)

    def _mapped_mitre_documents(
        self,
        alert_context: str | None,
    ) -> list[RetrievalResult]:
        if not alert_context:
            return []

        context_lower = alert_context.lower()
        technique_ids: set[str] = set()

        for label in KNOWN_ATTACK_LABELS:
            if label.lower() not in context_lower:
                continue

            technique_ids.update(
                technique.technique_id
                for technique in map_attack_label(label)
            )

        if not technique_ids:
            return []

        results = []

        for document in self.retriever.documents:
            technique_id = document.metadata.get("technique_id")

            if technique_id in technique_ids:
                results.append(
                    RetrievalResult(
                        document=document,
                        score=1.0,
                    )
                )

        return results

    @staticmethod
    def _merge_results(
        primary: list[RetrievalResult],
        secondary: list[RetrievalResult],
        top_k: int,
    ) -> list[RetrievalResult]:
        merged: list[RetrievalResult] = []
        seen: set[str] = set()

        for result in [*primary, *secondary]:
            document_id = result.document.document_id

            if document_id in seen:
                continue

            seen.add(document_id)
            merged.append(result)

        return merged[:top_k]

    def ask(
        self,
        question: str,
        alert_context: str | None = None,
        top_k: int = 4,
    ) -> CopilotAnswer:
        question = question.strip()

        if not question:
            raise ValueError("question must not be empty")

        if top_k < 1:
            raise ValueError("top_k must be at least 1")

        retrieval_query = question

        if alert_context:
            retrieval_query = f"{question} {alert_context}"

        semantic_results = self.retriever.search(
            retrieval_query,
            top_k=top_k,
        )

        mapped_results = self._mapped_mitre_documents(
            alert_context
        )

        results = self._merge_results(
            mapped_results,
            semantic_results,
            top_k=top_k,
        )

        knowledge_context = self._format_context(results)

        prompt_parts = [
            f"Analyst question:\n{question}",
        ]

        if alert_context:
            prompt_parts.append(
                f"Alert context:\n{alert_context}"
            )

        if knowledge_context:
            prompt_parts.append(
                f"Retrieved security knowledge:\n{knowledge_context}"
            )
        else:
            prompt_parts.append(
                "Retrieved security knowledge: No relevant documents found."
            )

        prompt_parts.append(
            "Provide: assessment, supporting evidence, and recommended next actions."
        )

        response = self.llm_client.generate(
            prompt="\n\n".join(prompt_parts),
            system=SYSTEM_PROMPT,
        )

        sources = tuple(
            CopilotSource(
                document_id=result.document.document_id,
                title=result.document.title,
                source=result.document.source,
                score=round(result.score, 6),
            )
            for result in results
        )

        return CopilotAnswer(
            answer=response.response,
            sources=sources,
            model=response.model,
        )
