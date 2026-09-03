from cybersentinel_ai.rag.retriever import KnowledgeDocument
from cybersentinel_ai.threat_intel.attack_mapping import ATTACK_MAPPING

SOC_PLAYBOOKS = {
    "Ransomware": (
        "Prioritize containment of the affected host. Review process execution, file "
        "modification activity, network connections, authentication events, and available "
        "endpoint telemetry. Preserve evidence before remediation. Determine whether "
        "encryption or lateral movement occurred, isolate confirmed affected systems, "
        "identify additional impacted assets, and follow the organization incident "
        "response and recovery process."
    ),
    "Malware": (
        "Review endpoint process activity, executable and script execution, persistence "
        "indicators, network connections, file changes, and available security telemetry. "
        "Preserve evidence, scope potentially affected hosts, isolate systems when the "
        "evidence supports containment, and investigate the initial execution path."
    ),
    "SSH Brute Force": (
        "Review SSH authentication failures, source addresses, targeted accounts, login "
        "frequency, and successful authentication following repeated failures. Validate "
        "whether the source is authorized. Consider source blocking, rate limiting, "
        "credential reset, and stronger authentication when supported by the evidence."
    ),
    "DDoS": (
        "Investigate abnormal traffic volume, packet rate, source distribution, "
        "destination services, and infrastructure saturation. Consider rate limiting, "
        "upstream filtering, and temporary blocking when evidence supports containment."
    ),
    "PortScan": (
        "Review source addresses, destination ports, scan frequency, exposed services, "
        "and whether the activity is authorized. Correlate repeated probing with later "
        "authentication or exploitation attempts."
    ),
    "Brute Force": (
        "Review authentication failures, source addresses, targeted accounts, login rate, "
        "and successful logins following repeated failures. Consider account protection, "
        "rate limiting, MFA, and source blocking where appropriate."
    ),
    "Web Attack": (
        "Review web server logs, request paths, parameters, response codes, application "
        "errors, and related vulnerability information. Preserve evidence before "
        "containment or remediation."
    ),
}


def build_default_knowledge_base() -> list[KnowledgeDocument]:
    documents: list[KnowledgeDocument] = []

    seen_techniques: set[str] = set()

    for label, techniques in ATTACK_MAPPING.items():
        for technique in techniques:
            if technique.technique_id in seen_techniques:
                continue

            seen_techniques.add(technique.technique_id)

            documents.append(
                KnowledgeDocument(
                    document_id=f"mitre-{technique.technique_id.lower()}",
                    title=technique.technique_name,
                    content=(
                        f"MITRE ATT&CK technique {technique.technique_id}: "
                        f"{technique.technique_name}. "
                        f"Tactic: {technique.tactic}."
                    ),
                    source="MITRE ATT&CK",
                    metadata={
                        "technique_id": technique.technique_id,
                        "tactic": technique.tactic,
                        "example_label": label,
                    },
                )
            )

    for category, content in SOC_PLAYBOOKS.items():
        document_id = (
            category.lower()
            .replace(" ", "-")
            .replace("/", "-")
        )

        documents.append(
            KnowledgeDocument(
                document_id=f"soc-{document_id}",
                title=f"{category} Investigation Playbook",
                content=content,
                source="CyberSentinel SOC Knowledge",
                metadata={"category": category},
            )
        )

    return documents
