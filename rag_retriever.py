from pathlib import Path

from rag_embeddings import EmbeddingService
from rag_vector_store import DEFAULT_CHROMA_PATH, ChromaVectorStore


def build_query_text(analysis, context_lines):
    parts = [
        analysis.get("diagnosis", ""),
        analysis.get("explanation", ""),
        " ".join(analysis.get("targets", [])),
        " ".join(analysis.get("events", {}).keys()),
        "\n".join(context_lines[-10:]),
    ]
    return "\n".join(part for part in parts if part)


def retrieve_relevant_documents(analysis, context_lines, top_k=3):
    chroma_path = Path(DEFAULT_CHROMA_PATH)

    if not chroma_path.exists():
        return []

    try:
        embedding_service = EmbeddingService()
        vector_store = ChromaVectorStore()
        query_text = build_query_text(analysis, context_lines)

        if not query_text.strip():
            return []

        return vector_store.query(query_text, embedding_service, top_k=top_k)
    except Exception:
        return []
