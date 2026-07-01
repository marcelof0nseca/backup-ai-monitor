DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"


class EmbeddingService:
    def __init__(self, model_name=DEFAULT_EMBEDDING_MODEL):
        self.model_name = model_name
        self._model = None

    def _load_model(self):
        if self._model is not None:
            return self._model

        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as error:
            raise RuntimeError(
                "sentence-transformers nao esta instalado. "
                "Instale com: pip install sentence-transformers"
            ) from error

        self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed_texts(self, texts):
        model = self._load_model()
        embeddings = model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return embeddings.tolist()

    def embed_text(self, text):
        return self.embed_texts([text])[0]
