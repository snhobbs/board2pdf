# from __future__ import absolute_import

import os
import shutil
import sys
import pcbnew
import wx

version = "1.4-dev"

if __name__ == "__main__":
    # Circumvent the "scripts can't do relative imports because they are not
    # packages" restriction by asserting dominance and making it a package!
    dirname = os.path.dirname(os.path.abspath(__file__))
    __package__ = os.path.basename(dirname)
    sys.path.insert(0, os.path.dirname(dirname))
    __import__(__package__)

from . import plot
from . import dialog
from . import persistence


def run_with_dialog():
    board = pcbnew.GetBoard()
    pcb_file_name = board.GetFileName()
    board2pdf_dir = os.path.dirname(os.path.abspath(__file__))
    pcb_file_dir = os.path.dirname(os.path.abspath(pcb_file_name))
    configfile = os.path.join(pcb_file_dir, "board2pdf.config.ini")

    # Not sure it this is needed any more.
    if not pcb_file_name:
        wx.MessageBox('Please save the board file before plotting the pdf.')
        return

    # If config.ini file doesn't exist, copy the default file to this file.
    if not os.path.exists(configfile):
        default_configfile = os.path.join(board2pdf_dir, "default_config.ini")
        shutil.copyfile(default_configfile, configfile)

    config = persistence.Persistence(configfile)
    config.load()

    def perform_export(dialog_panel):
        plot.plot_gerbers(board, dialog_panel.outputDirPicker.Path, config.templates,
                          dialog_panel.templatesSortOrderBox.GetItems(),
                          dialog_panel.m_checkBox_delete_temp_files.IsChecked(),
                          dialog_panel.m_checkBox_create_svg.IsChecked(),
                          dialog_panel.m_checkBox_delete_single_page_files.IsChecked(), dialog_panel,
                          layer_scale=config.layer_scale,
                          assembly_file_extension=config.assembly_file_extension)
        dialog_panel.m_progress.SetValue(100)
        dialog_panel.Refresh()
        dialog_panel.Update()

    dlg = dialog.SettingsDialog(config, perform_export, version)
    try:
        icon_path = os.path.join(os.path.dirname(__file__), 'icon.png')
        icon = wx.Icon(icon_path)
        dlg.SetIcon(icon)
    except Exception:
        pass

    # Update dialog with data from saved config.
    dlg.panel.outputDirPicker.Path = config.output_path
    dlg.panel.templatesSortOrderBox.SetItems(config.enabled_templates)
    dlg.panel.disabledTemplatesSortOrderBox.SetItems(config.disabled_templates)
    dlg.panel.m_checkBox_delete_temp_files.SetValue(config.del_temp_files)
    dlg.panel.m_checkBox_create_svg.SetValue(config.create_svg)
    dlg.panel.m_checkBox_delete_single_page_files.SetValue(config.del_single_page_files)

    # Check if able to import fitz. If it's possible then select fitz, otherwise select pypdf.
    try:
        import fitz  # This imports PyMuPDF

        fitz.open()  # after pip uninstall PyMuPDF the import still works, but not `open()`
        dlg.panel.m_radio_pypdf.SetValue(False)
        dlg.panel.m_radio_merge_pypdf.SetValue(False)
        dlg.panel.m_radio_fitz.SetValue(True)
        dlg.panel.m_radio_merge_fitz.SetValue(True)
    except (ImportError, AttributeError):
        dlg.panel.m_radio_fitz.SetValue(False)
        dlg.panel.m_radio_merge_fitz.SetValue(False)
        dlg.panel.m_radio_pypdf.SetValue(True)
        dlg.panel.m_radio_merge_pypdf.SetValue(True)

    dlg.ShowModal()
    # response = dlg.ShowModal()
    # if response == wx.ID_CANCEL:

    dlg.Destroy()


class board2pdf(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = f"Board2Pdf\nversion {version}"
        self.category = "Plot"
        self.description = "Plot pcb to pdf."
        self.show_toolbar_button = True  # Optional, defaults to False
        self.icon_file_name = os.path.join(os.path.dirname(__file__), 'icon.png')  # Optional

    def Run(self):
        run_with_dialog()


if __name__ == "__main__":
    run_with_dialog()
