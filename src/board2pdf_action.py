# from __future__ import absolute_import

import os
import shutil
import sys
import pcbnew
import wx
import pathlib
import logging

_log=logging.getLogger("board2pdf")

dirname = os.path.dirname(os.path.abspath(os.path.realpath(__file__)))
_package = os.path.basename(dirname)

try:
    from . _version import __version__
except ImportError:
    # sys.path.insert(0, os.path.dirname(dirname))
    sys.path.append(os.path.dirname(dirname))
    # Pretend we are part of a module
    # Avoids: ImportError: attempted relative import with no known parent package
    __package__ = _package
    __import__(__package__)
    _log.debug("Package: %s\tDir: %s", __package__, dirname)

from . _version import __version__
from . import plot
from . import dialog
from . import persistence
_log.debug("File: %s\tVersion: %s", __file__, __version__)

_board = None
def set_board(board: pcbnew.BOARD):
    global _board
    assert isinstance(board, pcbnew.BOARD)
    _board = board

def get_board() -> pcbnew.BOARD:
    if _board is None:
        set_board(pcbnew.GetBoard())
    return _board


def run_with_dialog():
    board = get_board()
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
        plot.plot_pdfs(board, dialog_panel,
                          output_path=dialog_panel.outputDirPicker.Path,
                          templates=dialog_panel.config.templates,
                          enabled_templates=dialog_panel.templatesSortOrderBox.GetItems(),
                          create_svg=dialog_panel.m_checkBox_create_svg.IsChecked(),
                          del_temp_files=dialog_panel.m_checkBox_delete_temp_files.IsChecked(),
                          del_single_page_files=dialog_panel.m_checkBox_delete_single_page_files.IsChecked(),
                          assembly_file_extension=config.assembly_file_extension,
                          page_info=dialog_panel.m_textCtrl_page_info.GetValue(),
                          info_variable=str(dialog_panel.m_comboBox_info_variable.GetCurrentSelection()))
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
        dialog_panel.m_textCtrl_page_info.SetValue(config.page_info)
        dlg.panel.m_comboBox_info_variable.SetSelection(int(config.info_variable))
        dialog_panel.ClearTemplateSettings()
        dialog_panel.hide_template_settings()

    dlg = dialog.SettingsDialog(config, perform_export, load_saved, version=__version__, board=get_board())
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
    dlg.panel.m_textCtrl_page_info.SetValue(config.page_info)
    if not config.info_variable:
        info_variable_int = 0
    else:
        info_variable_int = int(config.info_variable)
    dlg.panel.m_comboBox_info_variable.SetSelection(info_variable_int)
    dlg.panel.m_staticText_status.SetLabel(f'Status: loaded {configfile_name} settings')

    # Check if able to import PyMuPDF.
    has_pymupdf = True
    try:
        import pymupdf  # This imports PyMuPDF

    except ImportError:
        try:
            import fitz as pymupdf  # This imports PyMuPDF using old name
            _log.info("pymupdf old version found")

        except ImportError:
            try:
                import fitz_old as pymupdf # This imports PyMuPDF using temporary old name
                _log.info("pymupdf found")


            except ImportError:
                _log.info("pymupdf not found, using pypdf")
                has_pymupdf = False

    # after pip uninstall PyMuPDF the import still works, but not `open()`
    # check if it's possible to call pymupdf.open()
    if has_pymupdf:
        try:
            pymupdf.open()
        except Exception as e:
            _log.error("pymupdf partially initialized, falling back on pypdf. Error: %s", str(e))
            has_pymupdf = False

    if pcbnew.Version()[0:3] == "6.0":
        # KiCad 6.0 has no support for color. 7.0 has support, but the drawing sheet (frame) is always the same color.
        dlg.panel.m_radio_kicad.Disable()

    if ( pcbnew.Version()[0:3] == "6.0" or pcbnew.Version()[0:3] == "7.0" ):
        # If it was possible to import and open PyMuPdf, select pymupdf for coloring otherwise select pypdf.
        if has_pymupdf:
            dlg.panel.m_radio_merge_pymupdf.SetValue(True)
        else:
            dlg.panel.m_radio_merge_pypdf.SetValue(True)
    else:
        # Set KiCad as default engine for coloring
        dlg.panel.m_radio_kicad.SetValue(True)

    # If it was possible to import and open PyMuPdf, select pymupdf for merging otherwise select pypdf.
    if has_pymupdf:
        dlg.panel.m_radio_merge_pymupdf.SetValue(True)
    else:
        dlg.panel.m_radio_merge_pypdf.SetValue(True)

    # Check if able to import pdfCropMargins.
    has_pdfcropmargins = True
    try:
        from pdfCropMargins import crop  # This imports pdfCropMargins
    except:
        has_pdfcropmargins = False

    if has_pdfcropmargins:
        dlg.panel.m_staticText_pdfCropMargins.SetLabel(f'pdfCropMargins Status: Installed')
    else:
        dlg.panel.m_staticText_pdfCropMargins.SetLabel(f'pdfCropMargins Status: NOT Installed')

    dlg.ShowModal()
    dlg.Destroy()


class board2pdf(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = f"Board2Pdf\nversion {__version__}"
        self.category = "Plot"
        self.description = "Plot pcb to pdf."
        self.show_toolbar_button = True  # Optional, defaults to False
        self.icon_file_name = os.path.join(os.path.dirname(__file__), 'icon.png')  # Optional

    def Run(self):
        run_with_dialog()


def main():
    if not wx.App.Get():
        _log.debug("No existing app found, creating App")
        app = wx.App()
    run_with_dialog()


if __name__ == "__main__":
    logging.basicConfig()
    _log.setLevel(logging.DEBUG)
    board = None
    try:
        board_path = pathlib.Path(sys.argv[1]).absolute()
        assert board_path.exists()
        board = pcbnew.LoadBoard(str(board_path))
    except IndexError:
        _log.info("No board path passed as argument, trying kicad environment")
        board = pcbnew.GetBoard()

    if board is not None:
        set_board(board)
        main()
    else:
        _log.error("No board path passed or found in environment")
