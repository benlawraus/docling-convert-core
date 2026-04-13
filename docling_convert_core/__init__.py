"""Shared Docling document-to-markdown conversion with smart OCR routing."""

from .converter import convert_file, build_ocr_format_options, build_no_ocr_format_options
from .pdf_utils import has_good_text, get_page_count, split_pdf_pages
from .formats import SUPPORTED_EXTENSIONS, EXT_TO_FORMAT

__all__ = [
    "convert_file",
    "build_ocr_format_options",
    "build_no_ocr_format_options",
    "has_good_text",
    "get_page_count",
    "split_pdf_pages",
    "SUPPORTED_EXTENSIONS",
    "EXT_TO_FORMAT",
]
