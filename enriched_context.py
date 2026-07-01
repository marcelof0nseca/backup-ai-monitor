from graph.dependency_graph import find_dependency_context
from rag_retriever import retrieve_relevant_documents


MAX_DOCUMENT_CHARS = 700


def format_documents(documents):
    if not documents:
        return "Nenhum trecho relevante dos PDFs foi encontrado."

    lines = []

    for index, document in enumerate(documents, start=1):
        metadata = document.get("metadata") or {}
        source = metadata.get("source", "fonte desconhecida")
        page = metadata.get("page", "pagina desconhecida")
        text = document.get("text", "").strip()

        if len(text) > MAX_DOCUMENT_CHARS:
            text = text[:MAX_DOCUMENT_CHARS].rstrip() + "..."

        lines.append(
            f"[Documento {index}] {source}, pagina {page}\n{text}"
        )

    return "\n\n".join(lines)


def format_graph_context(graph_context):
    if not graph_context:
        return "Nenhuma dependencia relacionada foi encontrada no grafo local."

    lines = []

    for item in graph_context:
        component = item["component"]
        lines.append(
            f"Componente: {component['name']} "
            f"({component['type']}, id={component['id']})"
        )

        for relation in item["relations"]:
            related = relation["related_component"]
            lines.append(
                "- "
                f"{relation['direction']} {relation['type']} "
                f"{related['name']} ({related['type']}): "
                f"{relation.get('description') or 'sem descricao'}"
            )

    return "\n".join(lines)


def build_enriched_context(analysis, context_lines):
    try:
        documents = retrieve_relevant_documents(analysis, context_lines, top_k=3)
        graph_context = find_dependency_context(
            analysis,
            context_lines,
            documents,
        )

        return (
            "Documentacao interna relevante:\n"
            f"{format_documents(documents)}\n\n"
            "Dependencias e impactos provaveis:\n"
            f"{format_graph_context(graph_context)}"
        )
    except Exception as error:
        return f"Contexto RAG/grafo indisponivel: {error}"
