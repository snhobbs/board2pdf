#from __future__ import absolute_import

import os
import shutil
import sys
import pcbnew
import wx
#import ast
import json

try:
    # python 3.x
    from configparser import ConfigParser
except ImportError:
    # python 2.x
    from ConfigParser import SafeConfigParser as ConfigParser

if __name__ == "__main__":
    # Circumvent the "scripts can't do relative imports because they are not
    # packages" restriction by asserting dominance and making it a package!
    dirname = os.path.dirname(os.path.abspath(__file__))
    __package__ = os.path.basename(dirname)
    sys.path.insert(0, os.path.dirname(dirname))
    __import__(__package__)

from . import plot
from . import dialog

def run_with_dialog():
    board = pcbnew.GetBoard()
    pcb_file_name = board.GetFileName()
    board2pdf_dir = os.path.dirname(os.path.abspath(__file__))
    configfile = os.path.join(board2pdf_dir, "config.ini")

    # If config.ini file doesn't exist, copy the default file to this file.
    if not os.path.exists(configfile):
        default_configfile = os.path.join(board2pdf_dir, "default_config.ini")
        shutil.copyfile(default_configfile, configfile)

    # Not sure it this is needed any more.
    if not pcb_file_name:
        wx.MessageBox('Please save the board file before plotting the pdf.')
        return

    config = ConfigParser()
    templates = {}

    def save_config(dialog_panel):
        config.read(configfile)
        if not config.has_section('main'):
            config.add_section('main')

        config.set('main', 'output_dest_dir', dialog_panel.outputDirPicker.Path)
        # Create a string with strings separated with ','. Then save to config.
        items_string = ','.join(dialog_panel.templatesSortOrderBox.GetItems())
        config.set('main', 'enabled_templates', items_string)
        items_string = ','.join(dialog_panel.disabledTemplatesSortOrderBox.GetItems())
        config.set('main', 'disabled_templates', items_string)

        del_temp_files_setting = "False"
        if dialog_panel.m_checkBox_delete_temp_files.IsChecked():
            del_temp_files_setting = "True"
        config.set('main', 'del_temp_files', del_temp_files_setting)

        #config.set('main', 'settings', str(templates))
        config.set('main', 'settings', json.dumps(templates))

        with open(configfile, 'w') as f:
            config.write(f)

        print("save_config!")

    def perform_export(dialog_panel):
        plot.plot_gerbers(board, dialog_panel.outputDirPicker.Path, templates, dlg.panel.templatesSortOrderBox.GetItems(),
                     dlg.panel.m_checkBox_delete_temp_files.IsChecked(), dialog_panel)

    config_output_dest_dir = ""
    config_enabled_templates = []
    config_disabled_templates = []
    config_del_temp_files = False

    try:
        config.read(configfile)

        if config.has_option('main', 'settings'):
            #templates = ast.literal_eval(config.get('main', 'settings'))
            templates = json.loads(config.get('main', 'settings'))

        if config.has_option('main', 'output_dest_dir'):
            config_output_dest_dir = config.get('main', 'output_dest_dir')
        if config.has_option('main', 'enabled_templates'):
            config_enabled_templates = config.get('main', 'enabled_templates').split(',')
            config_enabled_templates[:] = [l for l in config_enabled_templates if l != '']  # removes empty entries
        if config.has_option('main', 'disabled_templates'):
            config_disabled_templates = config.get('main', 'disabled_templates').split(',')
            config_disabled_templates[:] = [l for l in config_disabled_templates if l != '']  # removes empty entries
        if config.has_option('main', 'del_temp_files'):
            if config.get('main', 'del_temp_files') == "True":
                config_del_temp_files = True

    finally:
        dlg = dialog.SettingsDialog(save_config, perform_export, 'v0.5', templates)

        # Update dialog with data from saved config.
        dlg.panel.outputDirPicker.Path = config_output_dest_dir
        dlg.panel.templatesSortOrderBox.SetItems(config_enabled_templates)
        dlg.panel.disabledTemplatesSortOrderBox.SetItems(config_disabled_templates)
        if config_del_temp_files:
            dlg.panel.m_checkBox_delete_temp_files.SetValue(True)

        dlg.ShowModal()
        #response = dlg.ShowModal()
        #if response == wx.ID_CANCEL:

        dlg.Destroy()

class board2pdf(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Board2Pdf"
        self.category = "Tool"
        self.description = "Plot pcb to pdf."
        self.show_toolbar_button = True  # Optional, defaults to False
        self.icon_file_name = os.path.join(os.path.dirname(__file__), 'icon.png')  # Optional

    def Run(self):
        run_with_dialog()

if __name__ == "__main__":
    run_with_dialog()