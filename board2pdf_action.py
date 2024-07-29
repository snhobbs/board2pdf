# from __future__ import absolute_import

import os
import shutil
import sys
import pcbnew
import wx

version = "1.5"

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
    default_configfile = os.path.join(board2pdf_dir, "default_config.ini")
    global_configfile = os.path.join(board2pdf_dir, "board2pdf.config.ini")
    local_configfile = os.path.join(pcb_file_dir, "board2pdf.config.ini")

    # Not sure it this is needed any more.
    if not pcb_file_name:
        wx.MessageBox('Please save the board file before plotting the pdf.')
        return

    # If local config.ini file doesn't exist, use global. If global doesn't exist, use default.
    if os.path.exists(local_configfile):
        configfile = local_configfile
        configfile_name = "local"
    elif os.path.exists(global_configfile):
        configfile = global_configfile
        configfile_name = "global"
    else:
        configfile = default_configfile
        configfile_name = "default"

    config = persistence.Persistence(configfile)
    config.load()
    config.default_settings_file_path = default_configfile
    config.global_settings_file_path = global_configfile
    config.local_settings_file_path = local_configfile

    def perform_export(dialog_panel):
        plot.plot_pdfs(board, dialog_panel.outputDirPicker.Path, config.templates,
                          dialog_panel.templatesSortOrderBox.GetItems(),
                          dialog_panel.m_checkBox_delete_temp_files.IsChecked(),
                          dialog_panel.m_checkBox_create_svg.IsChecked(),
                          dialog_panel.m_checkBox_delete_single_page_files.IsChecked(), dialog_panel,
                          layer_scale=config.layer_scale,
                          assembly_file_extension=config.assembly_file_extension)
        dialog_panel.m_progress.SetValue(100)
        dialog_panel.Refresh()
        dialog_panel.Update()

    def load_saved(dialog_panel, config):
        # Update dialog with data from saved config.
        dialog_panel.outputDirPicker.Path = config.output_path
        dialog_panel.templatesSortOrderBox.SetItems(config.enabled_templates)
        dialog_panel.disabledTemplatesSortOrderBox.SetItems(config.disabled_templates)
        dialog_panel.m_checkBox_delete_temp_files.SetValue(config.del_temp_files)
        dialog_panel.m_checkBox_create_svg.SetValue(config.create_svg)
        dialog_panel.m_checkBox_delete_single_page_files.SetValue(config.del_single_page_files)
        dialog_panel.ClearTemplateSettings()
        dialog_panel.hide_template_settings()

    dlg = dialog.SettingsDialog(config, perform_export, load_saved, version)
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
    dlg.panel.m_staticText_status.SetLabel(f'Status: loaded {configfile_name} settings')

    # Check if able to import fitz. If it's possible then select fitz, otherwise select pypdf.
    try:
        import fitz  # This imports PyMuPDF
    except ImportError:
        try:
            import fitz_old as fitz

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
