# PyPDF4
PyPDF4 is a pure-python PDF library capable of splitting, merging together,
cropping, and transforming the pages of PDF files. It can also add custom data,
viewing options, and passwords to PDF files.  It can retrieve text and metadata
from PDFs as well as merge entire files together.

What happened to PyPDF2?  Nothing; it's still available at
https://github.com/mstamy2/PyPDF2.  For various reasons @claird will eventually
explain, I've simply decided to mark a new "business model" with a
slightly-renamed project name.
While PyPDF4 will continue to be available at no charge, I have strong plans
for better ongoing support to start in August 2018.

Homepage (available soon): http://claird.github.io/PyPDF4/.

## Examples
Please see the `samplecode/` folder.

## Documentation
Documentation soon will be available, although probably not at
https://pythonhosted.org/PyPDF4/.

## FAQ
Please see http://claird.github.io/PyPDF4/FAQ.html (available in early August).

## Tests
PyPDF4 includes a modest (but growing!) test suite built on the unittest
framework. All tests are located in the `tests/` folder and are distributed
among dedicated modules. Tox makes running all tests over all versions of Python
quick work:

```
python -m pip install tox
python -m tox
```

Individual tests are accessible as conventional **Pytest** sources;

```
pytest -v tests/test_pdf.py
```

is an example which assumes the `pytest` executable is activated.

## Contributing
For an exhaustive overview of what rules you are expected to maintain, please
visit [Contributing](https://github.com/claird/PyPDF4/wiki/Contributing) in the
project Wiki. A quick outline of these is:

* **Provide test cases** for individual units of development of your own.
Proper testing is highly encouraged: *Code without tests is broken by design*
\- Jacob Kaplan-Moss, Django's original development team member.
* Follow the [PEP 8](https://www.python.org/dev/peps/pep-0008/) style conventions, such as:
	* lower_case_with_underscores nomenclature (e.g., `file_name` rather than `fileName`,
	and `write_file()` rather than `writeFile()`).
    * Line lengths of `79` characters or less.
    * Correct spacing between global-scoped classes and functions (two newlines
	in between etc.) and within internal code blocks.
* Target your code for Python 3 but maintain retrocompatibility with Python 2
(do we retain Py2?  Still under active consideration).
* Provide [docstring documentation](https://www.python.org/dev/peps/pep-0257/)
for public classes and functions. 
* Utilize `# TO-DO` or `TO-DO` markings within
[docstrings](https://www.python.org/dev/peps/pep-0257/) for indicating a
feature that is yet to be implemented or discussed. Some IDEs feature TO-DOs
detection consoles.
