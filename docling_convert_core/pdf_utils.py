"""PDF utilities: born-digital detection, page counting, and splitting."""

from __future__ import annotations

from pathlib import Path

import fitz


def _is_scanned_page(page, coverage_threshold: float = 0.5) -> bool:
    """Check if a PDF page is a scanned image.

    Returns True if the page contains an image covering more than
    *coverage_threshold* of the page area.  This detects both raw scans and
    "searchable PDFs" (scanned with an invisible OCR text layer).
    """
    rect = page.rect
    page_area = rect.width * rect.height
    if page_area <= 0:
        return False

    for img_info in page.get_images(full=True):
        xref = img_info[0]
        rects = page.get_image_rects(xref)
        for r in rects:
            img_area = r.width * r.height
            if img_area / page_area > coverage_threshold:
                return True
    return False


def has_good_text(path: Path, min_chars: int = 50, min_quality: float = 0.5) -> bool:
    """Check if a PDF page has good embedded text (truly born-digital).

    Returns True if any page has at least *min_chars* characters, the ratio
    of alphanumeric to non-whitespace characters meets *min_quality*, AND the
    page is not a scanned image.  "Searchable PDFs" (scans with an OCR text
    layer) are detected via full-page image coverage and return False so they
    are routed through OCR for higher-quality text extraction.
    """
    try:
        doc = fitz.open(str(path))
        for page in doc:
            if _is_scanned_page(page):
                continue
            text = page.get_text().strip()
            if len(text) < min_chars:
                continue
            non_ws = [c for c in text if not c.isspace()]
            if not non_ws:
                continue
            alnum = sum(1 for c in non_ws if c.isalnum())
            if alnum / len(non_ws) >= min_quality:
                doc.close()
                return True
        doc.close()
    except Exception:
        pass
    return False


def get_page_count(path: Path) -> int:
    """Return page count, or 0 on error."""
    try:
        doc = fitz.open(str(path))
        n = len(doc)
        doc.close()
        return n
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
    doc = fitz.open(str(source))
    n_pages = len(doc)
    if n_pages <= 1:
        doc.close()
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
            new_doc = fitz.open()
            new_doc.insert_pdf(doc, from_page=i, to_page=i)
            new_doc.save(str(page_path))
            new_doc.close()

        page_paths.append(page_path)

    doc.close()
    return page_paths