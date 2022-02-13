#!/usr/bin/env python
"""
Representation and utils for ranges of PDF file pages.

Copyright (c) 2014, Steve Witham <switham_github@mac-guyver.com>.
All rights reserved. This software is available under a BSD license;
see https://github.com/claird/PyPDF4/blob/master/LICENSE.md
"""

import re

from .utils import isString

_INT_RE = r"(0|-?[1-9]\d*)"  # A decimal int, don't allow "-0".
PAGE_RANGE_RE = "^({int}|({int}?(:{int}?(:{int}?)?)))$".format(int=_INT_RE)
# groups:         12     34     5 6     7 8


class ParseError(Exception):
    pass


PAGE_RANGE_HELP = """Remember, page indices start with zero.
        Page range expression examples:
            :     all pages.                   -1    last page.
            22    just the 23rd page.          :-1   all but the last page.
            0:3   the first three pages.       -2    second-to-last page.
            :3    the first three pages.       -2:   last two pages.
            5:    from the sixth page onward.  -3:-1 third & second to last.
        The third, "stride" or "step" number is also recognized.
            ::2       0 2 4 ... to the end.    3:0:-1    3 2 1 but not 0.
            1:10:2    1 3 5 7 9                2::-1     2 1 0.
            ::-1      all pages in reverse order.
"""


class PageRange(object):
    """
    A slice-like representation of a range of page indices,
        i.e. page numbers, only starting at zero.
    The syntax is like what you would put between brackets [ ].
    The slice is one of the few Python types that can't be subclassed,
    but this class converts to and from slices, and allows similar use.

    *  PageRange(str) parses a string representing a page range.
    *  PageRange(slice) directly "imports" a slice.
    *  _to_slice() gives the equivalent slice.
    *  str() and repr() allow printing.
    *  indices(n) is like slice.indices(n).
    """

    def __init__(self, arg):
        """
        Initialize with either a slice -- giving the equivalent page range,
        or a PageRange object -- making a copy,
        or a string like
            "int", "[int]:[int]" or "[int]:[int]:[int]",
            where the brackets indicate optional ints.
        {page_range_help}
        Note the difference between this notation and arguments to slice():
            slice(3) means the first three pages;
            PageRange("3") means the range of only the fourth page.
            However PageRange(slice(3)) means the first three pages.
        """
        if isinstance(arg, slice):
            self._slice = arg
            return

        if isinstance(arg, PageRange):
            self._slice = arg._to_slice()
            return

        match = isString(arg) and re.match(PAGE_RANGE_RE, arg)

        if not match:
            raise ParseError(arg)
        if match.group(2):
            # Special case: just an int means a range of one page.
            start = int(match.group(2))
            stop = start + 1 if start != -1 else None
            self._slice = slice(start, stop)
        else:
            self._slice = slice(*[int(g) if g else None for g in match.group(4, 6, 8)])

    # Just formatting this when there is __doc__ for __init__
    if __init__.__doc__:
        __init__.__doc__ = __init__.__doc__.format(page_range_help=PAGE_RANGE_HELP)

    @staticmethod
    def valid(this_input):
        """ True if input is a valid initializer for a PageRange. """
        return isinstance(this_input, (slice, PageRange)) or (
            isString(this_input) and bool(re.match(PAGE_RANGE_RE, this_input))
        )

    def _to_slice(self):
        """ Return the slice equivalent of this page range. """
        return self._slice

    def __str__(self):
        """A string like "1:2:3"."""
        s__ = self._slice
        if s__.step is None:
            if s__.start is not None and s__.stop == s__.start + 1:
                return str(s__.start)

            indices = s__.start, s__.stop
        else:
            indices = s__.start, s__.stop, s__.step
        return ":".join("" if i is None else str(i) for i in indices)

    def __repr__(self):
        """A string like "PageRange('1:2:3')"."""
        return "PageRange(" + repr(str(self)) + ")"

    def indices(self, this_n):
        """
        ``this_n`` is the length of the list of pages to choose from.
        Returns arguments for ``range()``.  See ``help(slice.indices)``.
        """
        return self._slice.indices(this_n)


PAGE_RANGE_ALL = PageRange(":")  # The range of all pages.


def parseFilenamePageRanges(args):
    """
    Given a list of filenames and page ranges, return a list of
    (filename, page_range) pairs.
    First arg must be a filename; other args are filenames, page-range
    expressions, slice objects, or PageRange objects.
    A filename not followed by a page range indicates all pages of the file.
    """
    pairs = []
    pdfFilename = None
    didPageRange = False

    for arg in args + [None]:
        if PageRange.valid(arg):
            if not pdfFilename:
                raise ValueError(
                    "The first argument must be a filename, not a page range."
                )

            pairs.append((pdfFilename, PageRange(arg)))
            didPageRange = True
        else:
            # New filename or end of list--do all of the previous file?
            if pdfFilename and not didPageRange:
                pairs.append((pdfFilename, PAGE_RANGE_ALL))

            pdfFilename = arg
            didPageRange = False

    return pairs
