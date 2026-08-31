from cybersentinel_ai.rag.knowledge_base import (
    build_default_knowledge_base,
)


def test_default_knowledge_base_contains_mitre_documents():
    documents = build_default_knowledge_base()

    technique_ids = {
        document.metadata.get("technique_id")
        for document in documents
    }

    assert "T1046" in technique_ids
    assert "T1110" in technique_ids
    assert "T1190" in technique_ids
    assert "T1498" in technique_ids


def test_default_knowledge_base_contains_soc_playbooks():
    documents = build_default_knowledge_base()

    categories = {
        document.metadata.get("category")
        for document in documents
    }

    assert "DDoS" in categories
    assert "PortScan" in categories
    assert "Brute Force" in categories
    assert "Web Attack" in categories


def test_document_ids_are_unique():
    documents = build_default_knowledge_base()

    document_ids = [
        document.document_id
        for document in documents
    ]

    assert len(document_ids) == len(set(document_ids))
