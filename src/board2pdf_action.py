import os
import shutil
import sys
import wx
import json
import logging
import traceback
import tempfile

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

def get_drawing_worksheet_from_project(project_file_path: str) -> bool | str:
    try:
        # Open the file and read the JSON data
        with open(project_file_path, 'r') as file:
            data = json.load(file)

        # Check if 'pcbnew' exists
        if 'pcbnew' in data:
            if 'page_layout_descr_file' in data['pcbnew']:
                return True, data['pcbnew']['page_layout_descr_file']

    except FileNotFoundError:
        exception_msg(f"Error when fetching drawing sheet path: The file {project_file_path} does not exist.")
        return False, ''
    except json.JSONDecodeError:
        exception_msg(f"Error when fetching drawing sheet path: Failed to decode JSON from the file.")
        return False, ''
    except Exception as e:
        exception_msg(f"Error when fetching drawing sheet path: An unexpected error occurred: {e}")
        return False, ''

    return False, ''

def set_drawing_worksheet_in_project(project_file_path: str, worksheet_path) -> bool:
    try:
        # Open the file and read the JSON data
        with open(project_file_path, 'r') as file:
            data = json.load(file)

        # Check if 'pcbnew' exists, if not, create it
        if 'pcbnew' not in data:
            data['pcbnew'] = {}

        # Update variables
        data['pcbnew']['page_layout_descr_file'] = worksheet_path

        # Write the updated JSON back to the file
        with open(project_file_path, 'w') as file:
            json.dump(data, file, indent=2)

    except FileNotFoundError:
        exception_msg(f"Error when updating drawing sheet path: The file {project_file_path} does not exist.")
        return False
    except json.JSONDecodeError:
        exception_msg(f"Error when updating drawing sheet path: Failed to decode JSON from the file.")
        return False
    except Exception as e:
        exception_msg(f"Error when updating drawing sheet path: An unexpected error occurred: {e}")
        return False

    return True

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

    def perform_export(dialog_panel):
        if dialog_panel.m_checkBox_delete_temp_files.IsChecked():
            # in case the files are deleted: use the OS temp directory
            temp_dir = tempfile.mkdtemp()
        else:
            os.chdir(project_path)
            output_dir = os.path.abspath(os.path.expanduser(os.path.expandvars(dialog_panel.outputDirPicker.Path)))
            temp_dir = os.path.abspath(os.path.join(output_dir, "temp"))

        # Delete the temp_dir if it exists to make sure there are no old temp files
        if os.path.isdir(temp_dir):
            shutil.rmtree(temp_dir)

        # Create the temp_dir
        os.makedirs(temp_dir, exist_ok=True)

        pcb_file_path = os.path.join(temp_dir, pcb_file_name+".kicad_pcb")
        print("pcb_file_path:", pcb_file_path)

        # Save the pcb to temp dir
        try:
            board.save_as(pcb_file_path, True, True)
        except:
            exception_msg("Could not save pcb to temporary path")
            return

        project_file_path = os.path.join(temp_dir, pcb_file_name+".kicad_pro")
        return_status, project_worksheet_path = get_drawing_worksheet_from_project(project_file_path)
        if return_status:
            print("project_worksheet_path:", project_worksheet_path)
            if project_worksheet_path.startswith("kicad-embed://"):
                print("Worksheet is embedded")
            elif not project_worksheet_path:
                print("No worksheet specified")
            elif os.path.isabs(project_worksheet_path):
                print("Worksheet is specified with an absolute path")
            else:
                # The worksheet template is specified with a relative path. We must copy the worksheet as well, and change the relative path.
                project_worksheet_absolute_path = os.path.abspath(os.path.join(project_path, project_worksheet_path))
                print("Worksheet is specified with a relative path. The absolute path is:", project_worksheet_absolute_path)
                try:
                    shutil.copyfile(project_worksheet_absolute_path, os.path.join(temp_dir, "worksheet.kicad_wks"))
                except:
                    exception_msg(f"Failed to copy worksheet file {project_worksheet_absolute_path}")
                set_drawing_worksheet_in_project(project_file_path, "worksheet.kicad_wks")

        plot.plot_pdfs(project_path, pcb_file_path, pcb_file_name, temp_dir, dialog_panel,
                          output_path=dialog_panel.outputDirPicker.Path,
                          kicad_cli_path=dialog_panel.m_filePicker_kicad_cli.Path,
                          board2pdf_path=board2pdf_dir,
                          layers_dict=layers_dict,
                          templates=dialog_panel.config.templates,
                          enabled_templates=dialog_panel.templatesSortOrderBox.GetItems(),
                          create_svg=dialog_panel.m_checkBox_create_svg.IsChecked(),
                          del_temp_files=dialog_panel.m_checkBox_delete_temp_files.IsChecked(),
                          del_single_page_files=dialog_panel.m_checkBox_delete_single_page_files.IsChecked(),
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
    run_with_dialog()
    app.MainLoop()