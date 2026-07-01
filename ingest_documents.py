from rag_embeddings import EmbeddingService
from rag_pdf_loader import DEFAULT_PDF_FOLDER, load_pdf_documents
from rag_text_splitter import split_documents
from rag_vector_store import ChromaVectorStore


def main():
    documents = load_pdf_documents(DEFAULT_PDF_FOLDER)

    if not documents:
        print(f"Nenhum PDF encontrado em {DEFAULT_PDF_FOLDER}.")
        return

    chunks = split_documents(documents)

    if not chunks:
        print("PDFs encontrados, mas nenhum texto foi extraido.")
        return

    embedding_service = EmbeddingService()
    vector_store = ChromaVectorStore()
    total = vector_store.add_chunks(chunks, embedding_service)

    print(f"Ingestao concluida: {total} trecho(s) salvos no ChromaDB.")


if __name__ == "__main__":
    main()
