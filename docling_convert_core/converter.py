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

from .pdf_utils import has_good_text


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
    filepath = Path(filepath)

    # Smart OCR routing for PDFs
    if filepath.suffix.lower() == ".pdf" and has_good_text(filepath):
        converter = _get_converter_no_ocr()
    else:
        converter = _get_converter_ocr(ocr_backend, do_table_structure)

    with _convert_lock:
        doc = converter.convert(str(filepath)).document
    return doc.export_to_markdown()
