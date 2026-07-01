from pathlib import Path


DEFAULT_PDF_FOLDER = Path("docs") / "internal_pdfs"


def load_pdf_documents(pdf_folder=DEFAULT_PDF_FOLDER):
    documents = []
    pdf_folder = Path(pdf_folder)

    if not pdf_folder.exists():
        return documents

    pdf_paths = sorted(pdf_folder.glob("*.pdf"))

    if not pdf_paths:
        return documents

    try:
        import fitz
    except ImportError as error:
        raise RuntimeError(
            "PyMuPDF nao esta instalado. Instale com: pip install pymupdf"
        ) from error

    for pdf_path in pdf_paths:
        with fitz.open(pdf_path) as pdf:
            for page_index, page in enumerate(pdf, start=1):
                text = page.get_text("text").strip()

                if not text:
                    continue

                documents.append(
                    {
                        "source": str(pdf_path),
                        "page": page_index,
                        "text": text,
                    }
                )

    return documents
