"""Supported file formats and extension mappings."""

from docling.datamodel.base_models import FormatToExtensions, InputFormat

SUPPORTED_EXTENSIONS = {
    ".pdf", ".docx", ".pptx", ".xlsx",
    ".html", ".xhtml",
    ".md",
    ".csv",
    ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp",
    ".adoc", ".tex",
}

# Build extension -> InputFormat lookup from Docling's own mapping
EXT_TO_FORMAT: dict[str, InputFormat] = {}
for _fmt, _exts in FormatToExtensions.items():
    for _ext in _exts:
        EXT_TO_FORMAT[_ext] = _fmt
