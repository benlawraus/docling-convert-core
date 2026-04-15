"""Docling document-to-markdown conversion with smart OCR routing."""

from __future__ import annotations

import threading
from pathlib import Path

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    OcrMacOptions,
    PdfPipelineOptions,
    TesseractCliOcrOptions,
    TableFormerMode,
    TableStructureOptions,
)
from docling.document_converter import DocumentConverter, PdfFormatOption, ImageFormatOption

from .pdf_utils import get_page_count, has_good_text


def build_no_ocr_format_options() -> dict:
    """Build Docling format options with OCR disabled."""
    pipeline_options = PdfPipelineOptions(
        do_ocr=False, generate_picture_images=True,
    )
    return {
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options),
        InputFormat.IMAGE: ImageFormatOption(pipeline_options=pipeline_options),
    }


def build_ocr_format_options(
    ocr_backend: str = "tesseract",
    *,
    force_full_page_ocr: bool = True,
    generate_picture_images: bool = True,
    do_table_structure: bool = False,
    table_mode: TableFormerMode = TableFormerMode.ACCURATE,
) -> dict:
    """Build Docling format options with OCR enabled.

    Args:
        ocr_backend: "tesseract" or "ocrmac"
        force_full_page_ocr: Force OCR on entire pages (vs selective regions)
        generate_picture_images: Extract images from documents
        do_table_structure: Enable table structure recognition
        table_mode: TableFormer mode (ACCURATE or FAST)
    """
    if ocr_backend == "ocrmac":
        ocr_options = OcrMacOptions(force_full_page_ocr=force_full_page_ocr, lang=["en-US"])
    else:
        ocr_options = TesseractCliOcrOptions(lang=["eng"], force_full_page_ocr=force_full_page_ocr)

    pipeline_options = PdfPipelineOptions(
        do_ocr=True,
        ocr_options=ocr_options,
        generate_picture_images=generate_picture_images,
    )
    if do_table_structure:
        pipeline_options.do_table_structure = True
        pipeline_options.table_structure_options = TableStructureOptions(
            do_cell_matching=True,
            mode=table_mode,
        )

    return {
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options),
        InputFormat.IMAGE: ImageFormatOption(pipeline_options=pipeline_options),
    }


# Lazy-initialised converters keyed by (ocr_backend, table_structure) to avoid
# reloading model weights on every call.
_converters: dict[tuple, DocumentConverter] = {}
_converter_no_ocr: DocumentConverter | None = None
_convert_lock = threading.Lock()


def _get_converter_no_ocr() -> DocumentConverter:
    global _converter_no_ocr
    if _converter_no_ocr is None:
        _converter_no_ocr = DocumentConverter(format_options=build_no_ocr_format_options())
    return _converter_no_ocr


def _get_converter_ocr(ocr_backend: str, do_table_structure: bool) -> DocumentConverter:
    key = (ocr_backend, do_table_structure)
    if key not in _converters:
        _converters[key] = DocumentConverter(
            format_options=build_ocr_format_options(
                ocr_backend=ocr_backend,
                do_table_structure=do_table_structure,
            )
        )
    return _converters[key]


def convert_file(
    filepath: str | Path,
    *,
    ocr_backend: str = "ocrmac",
    do_table_structure: bool = False,
) -> str:
    """Convert a single document to markdown with smart OCR routing.

    For PDFs, checks whether the file has good embedded text (born-digital)
    and skips OCR if so. Non-PDF files always go through the OCR pipeline.

    Args:
        filepath: Path to the document.
        ocr_backend: "tesseract" or "ocrmac".
        do_table_structure: Enable table structure recognition.

    Returns:
        Markdown string.
    """
    import sys
    from . import __version__
    filepath = Path(filepath)
    file_size = filepath.stat().st_size if filepath.exists() else -1
    print(f"DEBUG docling-convert-core v{__version__}: {filepath.name} — size={file_size} bytes", file=sys.stderr, flush=True)

    # Smart OCR routing for PDFs
    is_pdf = filepath.suffix.lower() == ".pdf"
    if is_pdf:
        page_count = get_page_count(filepath)
        print(f"DEBUG docling: {filepath.name} — {page_count} pages", file=sys.stderr, flush=True)

        good_text = has_good_text(filepath)
        print(f"DEBUG docling: {filepath.name} — has_good_text={good_text}", file=sys.stderr, flush=True)
        if good_text:
            print(f"DEBUG docling: {filepath.name} — born-digital PDF, skipping OCR", file=sys.stderr, flush=True)
            converter = _get_converter_no_ocr()
        else:
            print(f"DEBUG docling: {filepath.name} — scanned PDF, using OCR backend={ocr_backend} table_structure={do_table_structure}", file=sys.stderr, flush=True)
            converter = _get_converter_ocr(ocr_backend, do_table_structure)
    else:
        print(f"DEBUG docling: {filepath.name} — non-PDF, using OCR backend={ocr_backend} table_structure={do_table_structure}", file=sys.stderr, flush=True)
        converter = _get_converter_ocr(ocr_backend, do_table_structure)

    converter_id = id(converter)
    print(f"DEBUG docling: {filepath.name} — converter={converter_id} acquiring lock...", file=sys.stderr, flush=True)
    with _convert_lock:
        print(f"DEBUG docling: {filepath.name} — starting converter.convert()", file=sys.stderr, flush=True)
        result = converter.convert(str(filepath))
        print(f"DEBUG docling: {filepath.name} — convert() returned, extracting document", file=sys.stderr, flush=True)
        doc = result.document
        print(f"DEBUG docling: {filepath.name} — exporting markdown", file=sys.stderr, flush=True)
    md = doc.export_to_markdown()
    print(f"DEBUG docling: {filepath.name} — done ({len(md)} chars)", file=sys.stderr, flush=True)
    return md
