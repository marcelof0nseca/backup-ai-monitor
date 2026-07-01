DEFAULT_CHUNK_SIZE = 800
DEFAULT_OVERLAP = 120


def split_text(text, chunk_size=DEFAULT_CHUNK_SIZE, overlap=DEFAULT_OVERLAP):
    if not text:
        return []

    if overlap >= chunk_size:
        raise ValueError("overlap deve ser menor que chunk_size")

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = end - overlap

    return chunks


def split_documents(documents, chunk_size=DEFAULT_CHUNK_SIZE, overlap=DEFAULT_OVERLAP):
    chunks = []

    for document in documents:
        for index, chunk_text in enumerate(
            split_text(document["text"], chunk_size, overlap),
            start=1,
        ):
            chunks.append(
                {
                    "id": (
                        f"{document['source']}::page-{document['page']}"
                        f"::chunk-{index}"
                    ),
                    "text": chunk_text,
                    "metadata": {
                        "source": document["source"],
                        "page": document["page"],
                        "chunk": index,
                    },
                }
            )

    return chunks
