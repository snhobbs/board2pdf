"""Subclass of settings_dialog, which is generated by wxFormBuilder."""
import re

import wx
import wx.grid
import pcbnew

from . import dialog_base


def pop_error(msg):
    wx.MessageBox(msg, 'Error', wx.OK | wx.ICON_ERROR)

class SettingsDialog(dialog_base.SettingsDialogBase):
    def __init__(self, config_save_func, perform_export_func, version, templates):
        dialog_base.SettingsDialogBase.__init__(self, None)
        self.panel = SettingsDialogPanel(
                self, config_save_func, perform_export_func, templates)
        best_size = self.panel.BestSize
        # hack for some gtk themes that incorrectly calculate best size
        best_size.IncBy(dx=0, dy=30)
        self.SetClientSize(best_size)
        self.SetTitle('Board2Pdf %s' % version)

    # hack for new wxFormBuilder generating code incompatible with old wxPython
    # noinspection PyMethodOverriding
    def SetSizeHints(self, sz1, sz2):
        try:
            # wxPython 4
            super(SettingsDialog, self).SetSizeHints(sz1, sz2)
        except TypeError:
            # wxPython 3
            self.SetSizeHintsSz(sz1, sz2)


# Implementing settings_dialog
class SettingsDialogPanel(dialog_base.SettingsDialogPanel):
    def __init__(self, parent, config_save_func, perform_export_func, templates):
        self.config_save_func = config_save_func
        self.perform_export_func = perform_export_func
        self.templates = templates
        self.current_template = ""
        self.current_layer = ""
        dialog_base.SettingsDialogPanel.__init__(self, parent)

    def OnExit(self, event):
        self.GetParent().EndModal(wx.ID_CANCEL)

    def OnSaveSettings(self, event):
        self.SaveTemplate()
        self.config_save_func(self)

    def OnPerform(self, event):
        self.SaveTemplate()
        self.perform_export_func(self)

    def finish_init(self):
        print("finish_init()")


    # Handlers for events.
    def OnTemplateSortOrderUp(self, event):
        selection = self.templatesSortOrderBox.Selection
        if selection != wx.NOT_FOUND and selection > 0:
            item = self.templatesSortOrderBox.GetString(selection)
            self.templatesSortOrderBox.Delete(selection)
            self.templatesSortOrderBox.Insert(item, selection - 1)
            self.templatesSortOrderBox.SetSelection(selection - 1)

    def OnTemplateSortOrderDown(self, event):
        selection = self.templatesSortOrderBox.Selection
        size = self.templatesSortOrderBox.Count
        if selection != wx.NOT_FOUND and selection < size - 1:
            item = self.templatesSortOrderBox.GetString(selection)
            self.templatesSortOrderBox.Delete(selection)
            self.templatesSortOrderBox.Insert(item, selection + 1)
            self.templatesSortOrderBox.SetSelection(selection + 1)

    def OnTemplateNew(self, event):
        self.SaveTemplate()
        item = wx.GetTextFromUser(
                "Characters except for A-Z, a-z, 0-9, -, +, _ and ' ' will be ignored.",
                "Add new template")
        item = re.sub('[^A-Za-z0-9\-\+ _]', '', item)
        if item == '':
            return

        found_en = self.templatesSortOrderBox.FindString(item)
        found_dis = self.disabledTemplatesSortOrderBox.FindString(item)
        if found_en != wx.NOT_FOUND or found_dis != wx.NOT_FOUND:
            wx.MessageBox("Name already exists", "Error", wx.ICON_ERROR)
            return

        self.templatesSortOrderBox.Append(item)
        self.templatesSortOrderBox.SetSelection(
                self.templatesSortOrderBox.Count - 1)
        self.ClearTemplateSettings()
        self.OnTemplateEdit(event)

    def OnTemplateClone(self, event):
        self.SaveTemplate()

        selection = self.templatesSortOrderBox.Selection
        if selection != wx.NOT_FOUND:
            item = self.templatesSortOrderBox.GetString(selection)

            item = item + "-Copy"
            found_en = self.templatesSortOrderBox.FindString(item)
            found_dis = self.disabledTemplatesSortOrderBox.FindString(item)
            if found_en != wx.NOT_FOUND or found_dis != wx.NOT_FOUND:
                return

            if self.current_template == '':
                return
            self.templates[item] = self.templates[self.current_template]
            self.templatesSortOrderBox.Append(item)
            self.templatesSortOrderBox.SetSelection(
                self.templatesSortOrderBox.Count - 1)
            self.OnTemplateEdit(event)

    def OnTemplateDisable(self, event):
        self.SaveTemplate()
        selection = self.templatesSortOrderBox.Selection
        if selection != wx.NOT_FOUND:
            item = self.templatesSortOrderBox.GetString(selection)
            self.templatesSortOrderBox.Delete(selection)
            self.disabledTemplatesSortOrderBox.Append(item)
            if self.templatesSortOrderBox.Count > 0:
                if self.templatesSortOrderBox.Count <= max(selection, 0):
                    self.templatesSortOrderBox.SetSelection(max(selection - 1, 0))
                else:
                    self.templatesSortOrderBox.SetSelection(max(selection, 0))
            self.ClearTemplateSettings()
            self.OnTemplateEdit(event)

    def OnTemplateEnable(self, event):
        selection = self.disabledTemplatesSortOrderBox.Selection
        if selection != wx.NOT_FOUND:
            item = self.disabledTemplatesSortOrderBox.GetString(selection)
            self.disabledTemplatesSortOrderBox.Delete(selection)
            self.templatesSortOrderBox.Append(item)
            if self.disabledTemplatesSortOrderBox.Count > 0:
                if self.disabledTemplatesSortOrderBox.Count <= max(selection, 0):
                    self.disabledTemplatesSortOrderBox.SetSelection(max(selection - 1, 0))
                else:
                    self.disabledTemplatesSortOrderBox.SetSelection(max(selection, 0))

    def OnTemplateDelete(self, event):
        selection = self.disabledTemplatesSortOrderBox.Selection
        if selection != wx.NOT_FOUND:
            item = self.disabledTemplatesSortOrderBox.GetString(selection)
            self.templates.pop(item, None)
            self.disabledTemplatesSortOrderBox.Delete(selection)
            if self.disabledTemplatesSortOrderBox.Count > 0:
                if self.disabledTemplatesSortOrderBox.Count <= max(selection, 0):
                    self.disabledTemplatesSortOrderBox.SetSelection(max(selection - 1, 0))
                else:
                    self.disabledTemplatesSortOrderBox.SetSelection(max(selection, 0))

    def OnPickColor(self, event):
        _rgbstring = re.compile(r'#[a-fA-F0-9]{3}(?:[a-fA-F0-9]{3})?$')
        color_value = self.m_textCtrl_color.GetValue()
        if self.current_layer == "":
            wx.MessageBox("You must first select a layer.")
        else:
            if not bool(_rgbstring.match(color_value)):
                color_value = "#000000"

            value = color_value.lstrip('#')
            lv = len(value)
            rgb = tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))
            rgb = wx.Colour(rgb[0], rgb[1], rgb[2], 255)

            data = wx.ColourData()
            data.SetChooseFull(True)

            # set the first custom color (index 0) to the last used color
            data.SetCustomColour(0, rgb)

            # set the default color in the chooser to the last used color
            data.SetColour(rgb)

            cd = wx.ColourDialog(self, data)
            #cd.GetColourData().SetChooseFull(True)

            if cd.ShowModal() == wx.ID_OK:
                self.m_textCtrl_color.ChangeValue(str('#%02X%02X%02X' % cd.GetColourData().Colour[:3]))

            cd.Destroy()
            self.OnSaveLayer(event)

    def OnLayerSortOrderUp(self, event):
        selection = self.layersSortOrderBox.Selection
        if selection != wx.NOT_FOUND and selection > 0:
            item = self.layersSortOrderBox.GetString(selection)
            self.layersSortOrderBox.Delete(selection)
            self.layersSortOrderBox.Insert(item, selection - 1)
            self.layersSortOrderBox.SetSelection(selection - 1)

    def OnLayerSortOrderDown(self, event):
        selection = self.layersSortOrderBox.Selection
        size = self.layersSortOrderBox.Count
        if selection != wx.NOT_FOUND and selection < size - 1:
            item = self.layersSortOrderBox.GetString(selection)
            self.layersSortOrderBox.Delete(selection)
            self.layersSortOrderBox.Insert(item, selection + 1)
            self.layersSortOrderBox.SetSelection(selection + 1)

    def OnLayerDisable(self, event):
        selection = self.layersSortOrderBox.Selection
        if selection != wx.NOT_FOUND:
            item = self.layersSortOrderBox.GetString(selection)
            if item == self.m_comboBox_frame.GetValue():
                wx.MessageBox("You cannot disable " + item + " if it's selected in the 'Draw frame on layer' setting. First change this setting.")
            else:
                self.layersSortOrderBox.Delete(selection)
                self.disabledLayersSortOrderBox.Append(item)
                if self.layersSortOrderBox.Count > 0:
                    if self.layersSortOrderBox.Count <= max(selection, 0):
                        self.layersSortOrderBox.SetSelection(max(selection - 1, 0))
                    else:
                        self.layersSortOrderBox.SetSelection(max(selection, 0))
                self.SaveTemplate()

    def OnLayerEnable(self, event):
        selection = self.disabledLayersSortOrderBox.Selection
        if selection != wx.NOT_FOUND:
            item = self.disabledLayersSortOrderBox.GetString(selection)
            self.disabledLayersSortOrderBox.Delete(selection)
            self.layersSortOrderBox.Append(item)
            if self.disabledLayersSortOrderBox.Count > 0:
                if self.disabledLayersSortOrderBox.Count <= max(selection, 0):
                    self.disabledLayersSortOrderBox.SetSelection(max(selection - 1, 0))
                else:
                    self.disabledLayersSortOrderBox.SetSelection(max(selection, 0))
            self.SaveTemplate()

    def OnTemplateEdit(self, event):
        self.OnSaveLayer(self)
        self.SaveTemplate()

        selection = self.templatesSortOrderBox.Selection
        if selection != wx.NOT_FOUND:
            self.ClearTemplateSettings()

            item = self.templatesSortOrderBox.GetString(selection)
            self.m_textCtrl_template_name.ChangeValue(item)
            self.current_template = item

            layers = []
            i = pcbnew.PCBNEW_LAYER_ID_START
            while i < pcbnew.PCBNEW_LAYER_ID_START + pcbnew.PCB_LAYER_ID_COUNT:
                layers.append(pcbnew.BOARD_GetStandardLayerName(i))
                i += 1

            # Set enabled layers, if there are any in this template already
            if item in self.templates:
                if "enabled_layers" in self.templates[item]:
                    enabled_layers = self.templates[item]["enabled_layers"].split(',')
                    enabled_layers[:] = [l for l in enabled_layers if l != ''] # removes empty entries
                    if enabled_layers:
                        self.layersSortOrderBox.SetItems(enabled_layers)

            # Update the listbox with disabled layers
            # Add all layers not in the enabled list
            for l in layers:
                if self.layersSortOrderBox.FindString(l) == wx.NOT_FOUND:
                    self.disabledLayersSortOrderBox.Append(l)

            # Create dictionary with all layers and their color, and one with layer being negative or not
            if item in self.templates:
                if "layers" in self.templates[item]:
                    self.layersColorDict = self.templates[item]["layers"]
                else:
                    self.layersColorDict = {}
                if "layers_negative" in self.templates[item]:
                    self.layersNegativeDict = self.templates[item]["layers_negative"]
                else:
                    self.layersNegativeDict = {}
            else:
                self.layersColorDict = {}
                self.layersNegativeDict = {}

            # Update the comboBox where user can select one layer to plot the "frame"
            layers.insert(0, "None")
            self.m_comboBox_frame.SetItems(layers)
            self.m_comboBox_frame.SetSelection(0)
            # Check the saved template to see if there is a saved choice
            if item in self.templates:
                if "frame" in self.templates[item]:
                    saved_frame = self.templates[item]["frame"]
                    if saved_frame:
                        saved_frame_pos = self.m_comboBox_frame.FindString(saved_frame)
                        if saved_frame_pos != wx.NOT_FOUND:
                            self.m_comboBox_frame.SetSelection(saved_frame_pos)

            # Set the mirror checkbox according to saved setting
            if item in self.templates:
                if "mirrored" in self.templates[item]:
                    mirrored = self.templates[item]["mirrored"]
                    if mirrored:
                        self.m_checkBox_mirror.SetValue(True)
                        
            # Set the tent checkbox according to saved setting
            if item in self.templates:
                if "tented" in self.templates[item]:
                    tented = self.templates[item]["tented"]
                    if tented:
                        self.m_checkBox_tent.SetValue(True)

    def OnLayerEdit(self, event):
        self.OnSaveLayer(self)
        selection = self.layersSortOrderBox.Selection
        if selection != wx.NOT_FOUND:
            self.disabledLayersSortOrderBox.SetSelection(-1)
            item = self.layersSortOrderBox.GetString(selection)
            self.current_layer = item
            if item not in self.layersColorDict:
                color = "#000000"
            else:
                color = self.layersColorDict[item]
            self.m_textCtrl_color.ChangeValue(color)

            if item in self.layersNegativeDict:
                if self.layersNegativeDict[item] == "true":
                    self.m_checkBox_negative.SetValue(True)
                else:
                    self.m_checkBox_negative.SetValue(False)
            else:
                self.m_checkBox_negative.SetValue(False)

    def OnTemplateNameChange(self, event):
        template_name = self.m_textCtrl_template_name.GetValue()
        item = re.sub('[^A-Za-z0-9\-\+ _]', '', template_name)
        if item != template_name:
            self.m_textCtrl_template_name.SetValue(item)
            return

        found_en = self.templatesSortOrderBox.FindString(item)
        found_dis = self.disabledTemplatesSortOrderBox.FindString(item)
        if found_en != wx.NOT_FOUND or found_dis != wx.NOT_FOUND:
            return

        self.SaveTemplate()

    def OnSaveLayer(self, event):
        if self.current_layer != "":
            self.layersColorDict[self.current_layer] = self.m_textCtrl_color.GetValue()
            if self.m_checkBox_negative.IsChecked():
                self.layersNegativeDict[self.current_layer] = "true"
            else:
                self.layersNegativeDict[self.current_layer] = "false"
            #self.layersNegativeDict[self.current_layer] = self.m_checkBox_negative.IsChecked()
            #self.m_textCtrl_color.ChangeValue("")
            #self.current_layer = ""

    # Helper functions
    def OnSize(self, event):
        # Trick the listCheckBox best size calculations
        tmp = self.templatesSortOrderBox.GetStrings()
        self.templatesSortOrderBox.SetItems([])
        self.Layout()
        self.templatesSortOrderBox.SetItems(tmp)

    def SaveTemplate(self):
        template_name = self.m_textCtrl_template_name.GetValue()
        if template_name != "":
            # Check if selected frame layer is enabled. Otherwise, add it to the bottom of the enabled list.
            frame_layer = self.m_comboBox_frame.GetValue()
            if frame_layer != "None":
                if self.layersSortOrderBox.FindString(frame_layer) == wx.NOT_FOUND:
                    self.layersSortOrderBox.Append(frame_layer)
                    if self.disabledLayersSortOrderBox.FindString(frame_layer) != wx.NOT_FOUND:
                        self.disabledLayersSortOrderBox.Delete(frame_layer)

            enabled_layers = ','.join(self.layersSortOrderBox.GetItems())
            this_template = {"mirrored": self.m_checkBox_mirror.IsChecked(),
                             "tented": self.m_checkBox_tent.IsChecked(),
                             "enabled_layers": enabled_layers,
                             "frame": self.m_comboBox_frame.GetValue(),
                             "layers": self.layersColorDict,
                             "layers_negative": self.layersNegativeDict}
            if template_name != self.current_template:
                # Template has changed name. Remove the old name.
                self.templates.pop(self.current_template, None)
                # Change the name in the enabled templates list
                index = self.templatesSortOrderBox.FindString(self.current_template)
                if index != wx.NOT_FOUND:
                    self.templatesSortOrderBox.Delete(index)
                    self.templatesSortOrderBox.Insert(template_name, index)
                self.current_template = template_name
            self.templates[template_name] = this_template

    def ClearTemplateSettings(self):
        # Clear
        self.current_layer = ""
        self.m_textCtrl_template_name.ChangeValue("")
        self.m_checkBox_mirror.SetValue(False)
        self.m_checkBox_tent.SetValue(False)
        self.m_comboBox_frame.Clear()
        self.m_textCtrl_color.ChangeValue("")
        self.m_checkBox_negative.SetValue(False)
        self.layersSortOrderBox.Clear()
        self.disabledLayersSortOrderBox.Clear()
