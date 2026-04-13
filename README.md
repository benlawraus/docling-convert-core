# docling-convert-core

Shared utility library for document-to-markdown conversion with smart OCR routing, built on [Docling](https://github.com/DS4SD/docling).

For PDFs, it detects whether a file is "born-digital" (has good embedded text) and skips expensive OCR when possible. Non-PDF formats always go through the OCR pipeline.

Supported formats: PDF, DOCX, PPTX, XLSX, HTML, XHTML, Markdown, CSV, images, AsciiDoc, and LaTeX.

## Installation

```bash
pip install git+https://github.com/benlawraus/docling-convert-core.git
```

## Usage

```python
from docling_convert_core import convert_file

# Convert any supported document to markdown
md = convert_file("paper.pdf")

# Use Tesseract instead of OcrMac
md = convert_file("scanned.pdf", ocr_backend="tesseract")

# Enable table structure recognition
md = convert_file("report.pdf", do_table_structure=True)
```

### PDF utilities

```python
from docling_convert_core import has_good_text, get_page_count, split_pdf_pages

# Check if a PDF has good embedded text (born-digital)
if has_good_text("paper.pdf"):
    print("No OCR needed")

# Get page count
pages = get_page_count("paper.pdf")

# Split a PDF into individual pages
split_pdf_pages("paper.pdf", output_dir="pages/")
```

## License

GPL-3.0 - see [LICENSE](LICENSE) for details.

Copyright (c) 2026 Ben
