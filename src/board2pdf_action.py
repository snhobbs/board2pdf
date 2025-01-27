import os
import shutil
import sys
import wx
import pathlib
import logging
import traceback
import tempfile
from pathlib import Path

from kipy import KiCad
from kipy.board import BoardLayer
from kipy.util.board_layer import canonical_name, is_copper_layer

_log=logging.getLogger("board2pdf")

dirname = os.path.dirname(os.path.abspath(os.path.realpath(__file__)))
_package = os.path.basename(dirname)

from _version import __version__
import plot
import dialog
import persistence
_log.debug("File: %s\tVersion: %s", __file__, __version__)

"""
_board = None
def set_board(board: pcbnew.BOARD):
    global _board
    assert isinstance(board, pcbnew.BOARD)
    _board = board

def get_board() -> pcbnew.BOARD:
    if _board is None:
        set_board(pcbnew.GetBoard())
    return _board
"""

def exception_msg(info: str, tb=True):
    msg = f"{info}\n\n" + (
        traceback.format_exc() if tb else '')
    try:
        wx.MessageBox(msg, 'Error', wx.OK | wx.ICON_ERROR)
    except wx._core.PyNoAppError:
        print(f'Error: {msg}', file=sys.stderr)

def run_with_dialog():
    kicad = KiCad()
    try:
        board = kicad.get_board()
    except:
        exception_msg("Could not connect to KiCad and get pcb")
        return
    
    pcb_file_name = os.path.splitext(board.document.board_filename)[0]
    print("pcb_file_name:", pcb_file_name)
    board2pdf_dir = os.path.dirname(os.path.abspath(__file__))
    print("board2pdf_dir:", board2pdf_dir)
    project_path = board.document.project.path #os.path.dirname(board.document.project.path)
    print("project_path:", project_path)
    default_configfile = os.path.join(board2pdf_dir, "default_config.ini")
    global_configfile = os.path.join(board2pdf_dir, "board2pdf.config.ini")
    local_configfile = os.path.join(project_path, "board2pdf.config.ini")

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

    # Create dictionary with all layers, including their names, user names and if it's in use or not.
    layers_dict = {}
    for layer in BoardLayer.values():
        layer_std_name = canonical_name(layer)
        if(layer_std_name != 'Unknown' and layer_std_name != 'Rescue'):
            layers_dict[layer_std_name] = { 'user_name' : '', 'in_use' : False, 'is_copper_layer' : is_copper_layer(layer)}

    stackup = board.get_stackup()
    for layer in stackup.layers:
        layer_std_name = canonical_name(layer.layer)
        layer_user_name = layer.user_name
        if(layer_std_name != 'Unknown'):
            layers_dict[layer_std_name]['in_use'] = True
            if(layer_user_name != layer_std_name):
                layers_dict[layer_std_name]['user_name'] = layer_user_name
    
    #for layer, value in layers_dict.items():
    #    print(layer, value['user_name'], value['in_use'], value['is_copper_layer'])

    def perform_export(dialog_panel):
        if dialog_panel.m_checkBox_delete_temp_files.IsChecked():
            # in case the files are deleted: use the OS temp directory
            temp_dir = tempfile.mkdtemp()
        else:
            temp_dir = os.path.abspath(os.path.join(project_path, "temp"))

        # Create the directory if it doesn't exist already
        os.makedirs(temp_dir, exist_ok=True)

        pcb_file_path = os.path.join(temp_dir, "pcb-file.kicad_pcb")
        print("pcb_file_path:", pcb_file_path)

        # Save the pcb to temp dir
        try:
            board.save_as(pcb_file_path, True, False)
        except:
            exception_msg("Could not save pcb to temporary path")
            return

        plot.plot_pdfs(project_path, pcb_file_path, pcb_file_name, temp_dir, dialog_panel,
                          output_path=dialog_panel.outputDirPicker.Path,
                          layers_dict=layers_dict,
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

    dlg = dialog.SettingsDialog(config, perform_export, load_saved, layers_dict, version=__version__)
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

    #if pcbnew.Version()[0:3] == "6.0":
    #    # KiCad 6.0 has no support for color. 7.0 has support, but the drawing sheet (frame) is always the same color.
    #    dlg.panel.m_radio_kicad.Disable()

    #if ( pcbnew.Version()[0:3] == "6.0" or pcbnew.Version()[0:3] == "7.0" ):
    #    # If it was possible to import and open PyMuPdf, select pymupdf for coloring otherwise select pypdf.
    #    if has_pymupdf:
    #        dlg.panel.m_radio_merge_pymupdf.SetValue(True)
    #    else:
    #        dlg.panel.m_radio_merge_pypdf.SetValue(True)
    #else:
    #    # Set KiCad as default engine for coloring
    #   dlg.panel.m_radio_kicad.SetValue(True)
    
    # If it was possible to import and open PyMuPdf, select pymupdf for coloring otherwise select pypdf.
    #if has_pymupdf:
    #    dlg.panel.m_radio_pymupdf.SetValue(True)
    #else:
    #    dlg.panel.m_radio_pypdf.SetValue(True)
    
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

    dlg.panel.m_filePicker_kicad_cli.Path = kicad.get_kicad_binary_path('kicad-cli')

    dlg.ShowModal()
    dlg.Destroy()

if __name__ == "__main__":
    app = wx.App()
    #rt = RoundTracks()
    #rt.ShowModal()
    run_with_dialog()
    app.MainLoop()
    #rt.Destroy()


"""
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
"""