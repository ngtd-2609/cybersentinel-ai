import pytest

from cybersentinel_ai.rag.retriever import (
    KnowledgeDocument,
    TfidfRetriever,
)


def build_documents() -> list[KnowledgeDocument]:
    return [
        KnowledgeDocument(
            document_id="attack-t1046",
            title="Network Service Discovery",
            content=(
                "Attackers may scan remote systems to identify "
                "network services and open ports."
            ),
            source="MITRE ATT&CK",
            metadata={"technique_id": "T1046"},
        ),
        KnowledgeDocument(
            document_id="attack-t1110",
            title="Brute Force",
            content=(
                "Attackers may use password guessing and credential "
                "attacks to gain access to accounts."
            ),
            source="MITRE ATT&CK",
            metadata={"technique_id": "T1110"},
        ),
        KnowledgeDocument(
            document_id="soc-ddos",
            title="DDoS Investigation",
            content=(
                "Investigate abnormal traffic volume, packet rate, "
                "source distribution, and affected services."
            ),
            source="CyberSentinel SOC Knowledge",
            metadata={"category": "DDoS"},
        ),
    ]


def test_retrieve_relevant_document():
    retriever = TfidfRetriever(build_documents())

    results = retriever.search(
        "scan open ports and network services",
        top_k=2,
    )

    assert results
    assert results[0].document.document_id == "attack-t1046"
    assert results[0].score > 0.0


def test_retrieve_brute_force_document():
    retriever = TfidfRetriever(build_documents())

    results = retriever.search(
        "password guessing attack",
        top_k=1,
    )

    assert len(results) == 1
    assert results[0].document.document_id == "attack-t1110"


def test_empty_query():
    retriever = TfidfRetriever(build_documents())

    with pytest.raises(ValueError):
        retriever.search("")


def test_empty_documents():
    with pytest.raises(ValueError):
        TfidfRetriever([])
