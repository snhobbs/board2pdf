from ._version import __version__
from .generic import *
from .merger import PdfFileMerger
from .pagerange import PageRange
from .pdf import PdfFileReader, PdfFileWriter

__all__ = [
    # Basic PyPDF elements
    "PdfFileReader",
    "PdfFileWriter",
    "PdfFileMerger",
    "PageRange",
    # most used elements from generic
    "BooleanObject",
    "ArrayObject",
    "IndirectObject",
    "FloatObject",
    "NumberObject",
    "createStringObject",
    "TextStringObject",
    "NameObject",
    "DictionaryObject",
    "TreeObject",
    "Destination",
    "PageLabel",
    "Bookmark",
    # PyPDF modules
    "pdf",
    "generic",
    "utils",
    "filters",
    "merger",
    "pagerange",
    "xmp",
]
