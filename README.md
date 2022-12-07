# Board2Pdf

Board2Pdf is a KiCad Action Plugin to create good looking pdf files from the board. The outputted pdf is vector based and searchable.

Two examples of what the plugin can output can be found here:<br>
[armory-Assembly.pdf](https://gitlab.com/dennevi/Board2Pdf/-/raw/main/resources/armory-Assembly.pdf "USB armory from WithSecure Foundry") (1 982 kB) Project is found [here](https://github.com/f-secure-foundry/usbarmory "USB armory from WithSecure Foundry")<br>
[hackrf-one-Assembly.pdf](https://gitlab.com/dennevi/Board2Pdf/-/raw/main/resources/hackrf-one-Assembly.pdf "HackRF by Great Scott Gadgets") (1 579 kB) Project is found [here](https://github.com/greatscottgadgets/hackrf "HackRF by Great Scott Gadgets")<br>

When loaded the plugin looks like this. Here the user can configure how the pdf shall look.
![Screenshot](https://gitlab.com/dennevi/Board2Pdf/-/raw/main/resources/screenshot.png "Screenshot")

This plugin ONLY works with the KiCad 6.0.x. It does NOT work with KiCad 5.1.x. Take the leap! You won\'t regret it.

[https://gitlab.com/dennevi/Board2Pdf/](https://gitlab.com/dennevi/Board2Pdf/)

## Dependencies
**Note!** The information below is only valid from version v0.8. For information on earlier versions, please see [tag v0.7](https://gitlab.com/dennevi/Board2Pdf/-/tree/v0.7).

Board2Pdf requires [PyMuPDF](https://github.com/pymupdf/PyMuPDF) as a dependency. You can install it with ``python -m pip install --upgrade pymupdf`` This command must be run from the **KiCad 6.0 Command Prompt**. Not from your default terminal or from the Scripting Console within the PCB Editor.

For more detailed instructions, see the [Wiki - Install dependencies](https://gitlab.com/dennevi/Board2Pdf/-/wikis/Install-dependencies).

## Installation
The easiest way to install is to open KiCad -> Plugin And Content Manager. Select Board2Pdf in the Plugins tab, press Install and then Apply Changes.

You also have to install the dependencies mentioned above.

### Manual Installation
Clone or download and unpack this plugin to the correct path on your system. The path varies depending on your operating system. The plugin shall be placed in a new directory in this path. Under Windows the recommended path is %USERPROFILE%\Documents\KiCad\6.0\scripting\plugins\. More information can be found [here](https://dev-docs.kicad.org/en/python/pcbnew/)

You can also find this directory from inside the PCB Editor (Pcbnew) by pressing the Folder icon (\"Open Plugin Directory\") under Preferences -> Preferences -> PCB Editor -> Action Plugins. Here you can also see all your installed plugins, and if one of them doesn\'t load correctly you can get information from the button with the yellow warning triangle.

You also have to install the dependencies mentioned above.

## Usage
The plugin includes a default configuration which should make it more or less self explanatory if you test it out. The basic idea is that each template will result in a page in the pdf file that\'s created by this plugin. You can enable any number of templates to get different views and color modes of the pcb. Each template can be individually configured to give the desired output. It\'s completely up to you which layers to show, and which colors the layers shall have.

Some more information can be found in the [Wiki](https://gitlab.com/dennevi/Board2Pdf/-/wikis/home).

If you want to revert your locally saved settings and go back to the default configuration, just delete the config.ini file in the plugin directory. If config.ini is not found, default_config.ini will be used instead.

## Support
First search the [KiCad forum](https://forum.kicad.info/) to see if someone else has asked the same thing. If not, post your question in [this thread](https://forum.kicad.info/t/32269) in the forum. That way I will see your post and answer as soon as I can.

## Contributing
If you find a bug, please add an issue in the GitLab project.

If you make some improvements, please issue a pull request. All help is appreciated!

## Authors and acknowledgment
This script is written by Albin Dennevi. If you need to come in contact with me please use the KiCad forum as described under Support. But for bugs and feature requests, please add an issue in GitLab.

Credit goes to qu1ck, the author of the [InteractiveHtmlBom](https://github.com/openscopeproject/InteractiveHtmlBom) plugin. I used the GUI of this project as a starting point when making the GUI for this project.

## License
This plugin is licensed under the open-source GNU AGPL V3 license. A copy of the license is included in this software, and it can also be viewed [here](https://www.gnu.org/licenses/agpl-3.0.en.html)

## Project status
This project is considered to be finished. When serious bugs are reported I will try my best to fix them, but don\'t expect to much progress in adding features from my side.
