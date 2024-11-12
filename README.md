# Board2Pdf

Board2Pdf is a KiCad Action Plugin to create good looking pdf files from the board. The outputted pdf is vector based
and searchable.

Two examples of what the plugin can output can be found here:<br>
[armory-Assembly.pdf](https://gitlab.com/dennevi/Board2Pdf/-/raw/main/resources/armory-Assembly.pdf "USB armory from WithSecure Foundry") (
1 982 kB) Project is
found [here](https://github.com/f-secure-foundry/usbarmory "USB armory from WithSecure Foundry")<br>
[hackrf-one-Assembly.pdf](https://gitlab.com/dennevi/Board2Pdf/-/raw/main/resources/hackrf-one-Assembly.pdf "HackRF by Great Scott Gadgets") (
1 579 kB) Project is found [here](https://github.com/greatscottgadgets/hackrf "HackRF by Great Scott Gadgets")<br>

When loaded the plugin looks like this. Here the user can configure how the pdf shall look.
![Screenshot](https://gitlab.com/dennevi/Board2Pdf/-/raw/main/resources/screenshot.png "Screenshot")

This plugin ONLY works with the KiCad 6.0 and later. It does NOT work with KiCad 5.1.x or earlier versions.

[https://gitlab.com/dennevi/Board2Pdf/](https://gitlab.com/dennevi/Board2Pdf/)

## Installation

The easiest way to install is to open KiCad -> Plugin And Content Manager. Select Board2Pdf in the Plugins tab, press
Install and then Apply Changes.

If you only want to use the CLI (use Board2Pdf from the command line) you can also install Board2Pdf using pip: `pip install board2pdf`. Then you can use the Board2Pdf CLI by calling board2pdf just like any other application installed from pip.

For instructions on manual installation from the repo, see [Wiki - Installation](https://gitlab.com/dennevi/Board2Pdf/-/wikis/Installation)

Also, see Dependencies below.

## Dependencies

For basic functionality Board2Pdf uses [pypdf](https://github.com/py-pdf/pypdf) which is included when installing Board2Pdf. You don’t need to install any dependencies if this functionality is enough for you.

If you install [PyMuPDF](https://github.com/pymupdf/PyMuPDF) you can create the pdf files faster. It also enables you to convert the output file to SVG, and it has better support for bookmarks (table of content).

Board2Pdf uses [pdfCropMargins](https://github.com/abarker/pdfCropMargins) for some of the crop and scaling options. pdfCropMargins includes PyMuPDF so if you choose to install pdfCropMargins you don't have to install PyMuPDF.

More information in [Wiki - Install dependencies](https://gitlab.com/dennevi/Board2Pdf/-/wikis/Install-dependencies).

## Problem with Ubuntu and some other Linux distros

When PyMuPDF (fitz) is installed with pip, KiCad crashes with a segmentation fault when Board2Pdf is loaded. Board2Pdf loads when the PCB Editor loads, so the crash happens directly when the PCB Editor is started. If this happens to you, you have two options:
1. Uninstall PyMuPDF using `python -m pip uninstall --upgrade PyMuPDF` or `pip uninstall --upgrade PyMuPDF` and use pypdf instead.
2. Uninstall PyMuPDF as in (1), but install it again using the apt package manager: `sudo apt install python3-fitz`

## Usage - GUI

The plugin includes a default configuration which should make it more or less self explanatory if you test it out. The
basic idea is that each template will result in a page in the pdf file that\'s created by this plugin. You can enable
any number of templates to get different views and color modes of the pcb. Each template can be individually configured
to give the desired output. It\'s completely up to you which layers to show, and which colors the layers shall have.

More information can be found in the [Wiki - Usage GUI](https://gitlab.com/dennevi/Board2Pdf/-/wikis/Usage---GUI).

## Usage - CLI

Board2Pdf can be executed from the command line using `python board2pdf-cli.py {PROJECT}.kicad_pcb`. If installed using pip install the binary can be executed using `board2pdf {PROJECT}.kicad_pcb`.

More information can be found in the [Wiki - Usage CLI](https://gitlab.com/dennevi/Board2Pdf/-/wikis/Usage---CLI).

## Support

First search the [KiCad forum](https://forum.kicad.info/) to see if someone else has asked the same thing. If not, post
your question in the forum and tag me by writing @albin. That way I will see your post and answer as soon as I can.

## Contributing

If you find a bug, please add an issue in the GitLab project.

If you make some improvements, please issue a pull request. All help is appreciated!

Read DEVELOPMENT.md for information on how to build Board2Pdf.

## Authors and acknowledgment

This script is written by Albin Dennevi, with contributions from [others](https://gitlab.com/dennevi/Board2Pdf/-/graphs/main?ref_type=heads). If you need to come in contact with me please use the KiCad forum as described under Support. But for bugs and feature requests, please add an issue in GitLab.

Credit goes to qu1ck, the author of the [InteractiveHtmlBom](https://github.com/openscopeproject/InteractiveHtmlBom)
plugin. I used the GUI of this project as a starting point when making the GUI for this project.

## License

This plugin is licensed under the open-source GNU GPL license, version 3.0 or later. A copy of the license is included in this software, and it can also be viewed [here](https://www.gnu.org/licenses/gpl-3.0.en.html). This is the same license as pdfCropMargins is licensed under, personally I would've choosen a more open license.

## Project status

This project is considered to be finished. When serious bugs are reported I will try my best to fix them, but don\'t
expect too much progress in adding features from my side.