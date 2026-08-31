from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass(frozen=True)
class KnowledgeDocument:
    document_id: str
    title: str
    content: str
    source: str
    metadata: dict[str, str]


@dataclass(frozen=True)
class RetrievalResult:
    document: KnowledgeDocument
    score: float


class TfidfRetriever:
    def __init__(
        self,
        documents: list[KnowledgeDocument],
    ) -> None:
        if not documents:
            raise ValueError("documents must not be empty")

        self.documents = documents
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2),
        )

        corpus = [
            f"{document.title} {document.content}"
            for document in documents
        ]

        self.document_matrix = self.vectorizer.fit_transform(corpus)

    def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[RetrievalResult]:
        query = query.strip()

        if not query:
            raise ValueError("query must not be empty")

        if top_k < 1:
            raise ValueError("top_k must be at least 1")

        query_vector = self.vectorizer.transform([query])

        similarities = cosine_similarity(
            query_vector,
            self.document_matrix,
        )[0]

        ranked_indices = similarities.argsort()[::-1][:top_k]

        return [
            RetrievalResult(
                document=self.documents[index],
                score=float(similarities[index]),
            )
            for index in ranked_indices
            if similarities[index] > 0.0
        ]
