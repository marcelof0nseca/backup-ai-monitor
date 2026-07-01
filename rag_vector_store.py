from pathlib import Path


DEFAULT_CHROMA_PATH = Path("data") / "chroma"
DEFAULT_COLLECTION_NAME = "internal_docs"


class ChromaVectorStore:
    def __init__(
        self,
        persist_path=DEFAULT_CHROMA_PATH,
        collection_name=DEFAULT_COLLECTION_NAME,
    ):
        self.persist_path = Path(persist_path)
        self.collection_name = collection_name
        self._collection = None

    def _get_collection(self):
        if self._collection is not None:
            return self._collection

        try:
            import chromadb
        except ImportError as error:
            raise RuntimeError(
                "chromadb nao esta instalado. Instale com: pip install chromadb"
            ) from error

        self.persist_path.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=str(self.persist_path))
        self._collection = client.get_or_create_collection(
            name=self.collection_name
        )
        return self._collection

    def add_chunks(self, chunks, embedding_service):
        if not chunks:
            return 0

        collection = self._get_collection()
        texts = [chunk["text"] for chunk in chunks]
        embeddings = embedding_service.embed_texts(texts)

        collection.upsert(
            ids=[chunk["id"] for chunk in chunks],
            documents=texts,
            metadatas=[chunk["metadata"] for chunk in chunks],
            embeddings=embeddings,
        )

        return len(chunks)

    def query(self, query_text, embedding_service, top_k=3):
        collection = self._get_collection()
        embedding = embedding_service.embed_text(query_text)

        results = collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        return [
            {
                "text": document,
                "metadata": metadata,
                "distance": distance,
            }
            for document, metadata, distance in zip(documents, metadatas, distances)
        ]
