"""PDF utilities: born-digital detection, page counting, and splitting."""

from __future__ import annotations

from pathlib import Path

import pypdfium2


def has_good_text(path: Path, min_chars: int = 50, min_quality: float = 0.5) -> bool:
    """Check if a PDF page has good embedded text (born-digital).

    Returns True if any page has at least *min_chars* characters and the ratio
    of alphanumeric to non-whitespace characters meets *min_quality*.
    """
    try:
        with pypdfium2.PdfDocument(str(path)) as doc:
            for page in doc:
                text = page.get_textpage().get_text_range()
                stripped = text.strip()
                if len(stripped) < min_chars:
                    continue
                non_ws = [c for c in stripped if not c.isspace()]
                if not non_ws:
                    continue
                alnum = sum(1 for c in non_ws if c.isalnum())
                if alnum / len(non_ws) >= min_quality:
                    return True
    except Exception:
        pass
    return False


def get_page_count(path: Path) -> int:
    """Return page count via pypdfium2, or 0 on error."""
    try:
        with pypdfium2.PdfDocument(str(path)) as doc:
            return len(doc)
    except Exception:
        return 0


def split_pdf_pages(
    source: Path, pages_dir: Path, rel_subdir: Path,
) -> list[Path]:
    """Split a multi-page PDF into one PDF per page.

    Files are written to pages_dir/rel_subdir/{stem}_p{NNN}.pdf where NNN is
    zero-padded to the width needed for the total page count.

    Returns the list of per-page PDF paths in page order.
    """
    with pypdfium2.PdfDocument(str(source)) as doc:
        n_pages = len(doc)
        if n_pages <= 1:
            return []

        out_dir = pages_dir / rel_subdir
        out_dir.mkdir(parents=True, exist_ok=True)

        width = len(str(n_pages))
        stem = source.stem
        page_paths: list[Path] = []

        for i in range(n_pages):
            page_num = i + 1
            page_name = f"{stem}_p{page_num:0{width}}.pdf"
            page_path = out_dir / page_name

            if not page_path.exists():
                new_doc = pypdfium2.PdfDocument.new()
                new_doc.import_pages(doc, [i])
                with open(page_path, "wb") as f:
                    new_doc.save(f)
                new_doc.close()

            page_paths.append(page_path)

    return page_paths
