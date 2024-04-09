"""Subclass of settings_dialog, which is generated by wxFormBuilder."""
import re

import wx
import wx.grid
import pcbnew

from . import dialog_base


def pop_error(msg):
    wx.MessageBox(msg, 'Error', wx.OK | wx.ICON_ERROR)


class SettingsDialog(dialog_base.SettingsDialogBase):
    def __init__(self, config, perform_export_func, version):
        dialog_base.SettingsDialogBase.__init__(self, None)
        self.panel = SettingsDialogPanel(self, config, perform_export_func)
        best_size = self.panel.BestSize
        # hack for some gtk themes that incorrectly calculate best size
        best_size.IncBy(dx=0, dy=30)
        self.SetClientSize(best_size)
        self.SetTitle('Board2Pdf %s' % version)
        if (int(pcbnew.Version()[0:1]) < 8):
            # If KiCad version < 8, no support for not exporting property popups
            self.m_comboBox_popups.Clear()
            popups_choices = []
            popups_choices.insert(0, "Only available in KiCad 8.0")
            self.m_comboBox_frame.SetItems(popups_choices)
            self.m_comboBox_popups.Disable()

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
    def __init__(self, parent, config, perform_export_func):
        self.config = config
        self.perform_export_func = perform_export_func
        self.templates: dict = config.templates
        self.current_template: str = ""
        self.current_layer: str = ""
        dialog_base.SettingsDialogPanel.__init__(self, parent)
        self.m_color_shower.SetBackgroundColour(wx.NullColour)
        self.m_color_shower.SetForegroundColour(wx.NullColour)
        self.m_color_shower.SetLabel("")
        self.hide_template_settings()
        self.hide_layer_settings()

    def hide_template_settings(self):
        self.m_textCtrl_template_name.Disable()
        self.m_comboBox_frame.Disable()
        self.m_checkBox_mirror.Disable()
        self.m_checkBox_tent.Disable()
        self.m_staticText_template_name.Disable()
        self.m_staticText_frame_layer.Disable()
        self.m_staticText_popups.Disable()
        self.m_comboBox_popups.Disable()

        self.layersSortOrderBox.Disable()
        self.m_button_layer_up.Disable()
        self.m_button_layer_down.Disable()
        self.m_button_layer_disable.Disable()
        self.disabledLayersSortOrderBox.Disable()
        self.m_button_layer_enable.Disable()
        self.m_staticText_layer_info.Disable()

    def hide_layer_settings(self):
        self.m_textCtrl_color.Disable()
        self.m_button_pick_color.Disable()
        self.m_checkBox_negative.Disable()
        self.m_checkBox_reference_designators.Disable()
        self.m_checkBox_footprint_values.Disable()
        self.m_staticText_layer_color.Disable()
        self.m_textCtrl_color.ChangeValue("")
        self.m_color_shower.SetBackgroundColour(wx.NullColour)
        self.m_color_shower.SetForegroundColour(wx.NullColour)
        self.m_color_shower.SetLabel("")
        self.m_checkBox_negative.SetValue(False)
        self.m_checkBox_footprint_values.SetValue(True)
        self.m_checkBox_reference_designators.SetValue(True)

    def show_template_settings(self):
        self.m_textCtrl_template_name.Enable()
        self.m_comboBox_frame.Enable()
        self.m_checkBox_mirror.Enable()
        self.m_checkBox_tent.Enable()
        self.m_staticText_template_name.Enable()
        self.m_staticText_frame_layer.Enable()
        if (int(pcbnew.Version()[0:1]) >= 8):
            self.m_staticText_popups.Enable()
            self.m_comboBox_popups.Enable()

        self.layersSortOrderBox.Enable()
        self.m_button_layer_up.Enable()
        self.m_button_layer_down.Enable()
        self.m_button_layer_disable.Enable()
        self.disabledLayersSortOrderBox.Enable()
        self.m_button_layer_enable.Enable()
        self.m_staticText_layer_info.Enable()

    def show_layer_settings(self):
        self.m_textCtrl_color.Enable()
        self.m_button_pick_color.Enable()
        self.m_checkBox_negative.Enable()
        self.m_checkBox_reference_designators.Enable()
        self.m_checkBox_footprint_values.Enable()
        self.m_staticText_layer_color.Enable()

    def OnExit(self, event):
        self.GetParent().EndModal(wx.ID_CANCEL)

    def OnSaveSettings(self, event):
        self.SaveTemplate()

        self.config.output_path = self.outputDirPicker.Path
        self.config.enabled_templates = self.templatesSortOrderBox.GetItems()
        self.config.disabled_templates = self.disabledTemplatesSortOrderBox.GetItems()
        self.config.create_svg = self.m_checkBox_create_svg.IsChecked()
        self.config.del_temp_files = self.m_checkBox_delete_temp_files.IsChecked()
        self.config.del_single_page_files = self.m_checkBox_delete_single_page_files.IsChecked()
        self.config.save()

        self.m_staticText_status.SetLabel('Status: settings saved')

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
            wx.MessageBox("The template name '" + item + "' already exists", "Error", wx.ICON_ERROR)
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

            new_item = item + "-Copy"
            found_en = self.templatesSortOrderBox.FindString(new_item)
            found_dis = self.disabledTemplatesSortOrderBox.FindString(new_item)
            if found_en != wx.NOT_FOUND or found_dis != wx.NOT_FOUND:
                wx.MessageBox("The template name '" + new_item + "' already exists", "Error", wx.ICON_ERROR)
                return

            if self.current_template == '':
                return
            self.templates[new_item] = self.templates[self.current_template]
            self.templatesSortOrderBox.Append(new_item)
            self.templatesSortOrderBox.SetSelection(
                self.templatesSortOrderBox.Count - 1)
            # wx.MessageBox("Created " + new_item + " as a clone of " + item)
            self.OnTemplateEdit(event)
            self.current_template = new_item
            self.SaveTemplate()

    @staticmethod
    def _listbox_reselect(listbox, selection):
        if listbox.Count > 0:
            if listbox.Count <= max(selection, 0):
                listbox.SetSelection(max(selection - 1, 0))
            else:
                listbox.SetSelection(max(selection, 0))
            return True
        return False

    def OnTemplateDisable(self, event):
        self.SaveTemplate()
        selection = self.templatesSortOrderBox.Selection
        if selection != wx.NOT_FOUND:
            item = self.templatesSortOrderBox.GetString(selection)
            self.templatesSortOrderBox.Delete(selection)
            self.disabledTemplatesSortOrderBox.Append(item)
            self._listbox_reselect(self.templatesSortOrderBox, selection)

            self.ClearTemplateSettings()
            self.hide_template_settings()
            self.OnTemplateEdit(event)

    def OnTemplateEnable(self, event):
        selection = self.disabledTemplatesSortOrderBox.Selection
        if selection != wx.NOT_FOUND:
            item = self.disabledTemplatesSortOrderBox.GetString(selection)
            self.disabledTemplatesSortOrderBox.Delete(selection)
            self.templatesSortOrderBox.Append(item)
            self._listbox_reselect(self.disabledTemplatesSortOrderBox, selection)

    def OnTemplateDelete(self, event):
        selection = self.disabledTemplatesSortOrderBox.Selection
        if selection != wx.NOT_FOUND:
            item = self.disabledTemplatesSortOrderBox.GetString(selection)
            del self.templates[item]
            self.disabledTemplatesSortOrderBox.Delete(selection)
            self._listbox_reselect(self.disabledTemplatesSortOrderBox, selection)

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
            # cd.GetColourData().SetChooseFull(True)

            if cd.ShowModal() == wx.ID_OK:
                rgb_color = cd.GetColourData().Colour[:3]
                self.m_textCtrl_color.ChangeValue(str('#%02X%02X%02X' % rgb_color))
                self.m_color_shower.SetBackgroundColour(rgb_color)
                self.m_color_shower.SetForegroundColour(rgb_color)
                self.m_color_shower.SetLabel(str(rgb_color))

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
                wx.MessageBox(
                    f"You cannot disable {item} if it's selected in the 'Draw frame on layer' setting. First change this setting.")
            else:
                self.layersSortOrderBox.Delete(selection)
                self.disabledLayersSortOrderBox.Append(item)
                if self._listbox_reselect(self.layersSortOrderBox, selection):
                    self.OnLayerEdit(self)
                else:
                    self.hide_layer_settings()
                self.SaveTemplate()

    def OnLayerEnable(self, event):
        selection = self.disabledLayersSortOrderBox.Selection
        if selection != wx.NOT_FOUND:
            item = self.disabledLayersSortOrderBox.GetString(selection)
            self.disabledLayersSortOrderBox.Delete(selection)
            self.layersSortOrderBox.Append(item)
            self._listbox_reselect(self.disabledLayersSortOrderBox, selection)
            self.SaveTemplate()

    def OnTemplateEdit(self, event):
        self.OnSaveLayer(self)
        self.SaveTemplate()

        selection = self.templatesSortOrderBox.Selection
        if selection != wx.NOT_FOUND:
            self.ClearTemplateSettings()
            self.show_template_settings()

            item = self.templatesSortOrderBox.GetString(selection)
            self.m_textCtrl_template_name.ChangeValue(item)
            self.current_template = item

            board = pcbnew.GetBoard()
            layers = []
            layers_dict = dict()
            i = pcbnew.PCBNEW_LAYER_ID_START
            while i < pcbnew.PCBNEW_LAYER_ID_START + pcbnew.PCB_LAYER_ID_COUNT:
                layer_std_name = pcbnew.BOARD.GetStandardLayerName(i)
                layer_name = pcbnew.BOARD.GetLayerName(board, i)
                layers_dict[layer_std_name] = layer_name
                if layer_std_name == layer_name:
                    layers.append(layer_name)
                else:
                    layers.append(layer_std_name + " (" + layer_name + ")")
                i += 1

            # Set enabled layers, if there are any in this template already
            if item in self.templates and "enabled_layers" in self.templates[item]:
                enabled_layers = self.templates[item]["enabled_layers"].split(',')
                enabled_layers = [l for l in enabled_layers if l != '']  # removes empty entries
                # Add the layer name within parenthesis if the layer name is not the standard layer name
                for i, layer_name in enumerate(enabled_layers):
                    if layers_dict[layer_name] != layer_name:
                        enabled_layers[i] = layer_name + " (" + layers_dict[layer_name] + ")"
                # Add all enabled layers to the enabled layers sort box.
                if enabled_layers:
                    self.layersSortOrderBox.SetItems(enabled_layers)

            # Update the listbox with disabled layers
            # Add all layers not in the enabled list
            for l in layers:
                # Remove the name within the parenthesis if there is one, before searching for the name
                layer_name = l.split(' (')[0]
                if self.layersSortOrderBox.FindString(layer_name) == wx.NOT_FOUND:
                    self.disabledLayersSortOrderBox.Append(l)

            # Create dictionary with all layers and their settings
            if item in self.templates:
                self.layersColorDict = self.templates[item].get("layers", {})
                self.layersNegativeDict = self.templates[item].get("layers_negative", {})
                self.layersFootprintValuesDict = self.templates[item].get("layers_footprint_values", {})
                self.layersReferenceDesignatorsDict = self.templates[item].get("layers_reference_designators", {})
            else:
                self.layersColorDict = {}
                self.layersNegativeDict = {}
                self.layersFootprintValuesDict = {}
                self.layersReferenceDesignatorsDict = {}

            # Update the comboBox where user can select one layer to plot the "frame"
            layers.insert(0, "None")
            self.m_comboBox_frame.SetItems(layers)
            self.m_comboBox_frame.SetSelection(0)
            # Check the saved template to see if there is a saved choice
            if item in self.templates and "frame" in self.templates[item]:
                saved_frame = self.templates[item]["frame"]
                if saved_frame and saved_frame != "None":
                    if layers_dict[saved_frame] != saved_frame:
                        saved_frame += " (" + layers_dict[saved_frame] + ")"
                    saved_frame_pos = self.m_comboBox_frame.FindString(saved_frame)
                    if saved_frame_pos != wx.NOT_FOUND:
                        self.m_comboBox_frame.SetSelection(saved_frame_pos)

            # Update the comboBox where user can select from which layer to take the popup menus
            if item in self.templates and "popups" in self.templates[item]:
                saved_popups = self.templates[item]["popups"]
            else:
                saved_popups = "Both Layers"
            saved_popups_pos = self.m_comboBox_popups.FindString(saved_popups)
            if saved_popups_pos != wx.NOT_FOUND:
                self.m_comboBox_popups.SetSelection(saved_popups_pos)

            # Set the mirror checkbox according to saved setting
            if item in self.templates and "mirrored" in self.templates[item]:
                mirrored = self.templates[item]["mirrored"]
                self.m_checkBox_mirror.SetValue(bool(mirrored))

            # Set the tent checkbox according to saved setting
            if item in self.templates and "tented" in self.templates[item]:
                tented = self.templates[item]["tented"]
                self.m_checkBox_tent.SetValue(bool(tented))

    def OnLayerEdit(self, event):
        self.OnSaveLayer(self)
        selection = self.layersSortOrderBox.Selection
        if selection != wx.NOT_FOUND:
            self.disabledLayersSortOrderBox.SetSelection(-1)
            selected_item = self.layersSortOrderBox.GetString(selection)
            item = selected_item.split(' (')[0]  # Remove parenthesis if there is one
            self.current_layer = item
            self.show_layer_settings()

            color = self.layersColorDict.get(item, "#000000")
            self.m_textCtrl_color.ChangeValue(color)

            rgb_color = tuple(int(color.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4))
            self.m_color_shower.SetBackgroundColour(rgb_color)
            self.m_color_shower.SetForegroundColour(rgb_color)
            self.m_color_shower.SetLabel(str(rgb_color))

            self.m_checkBox_negative.SetValue(self.layersNegativeDict.get(item, "false") == "true")
            self.m_checkBox_footprint_values.SetValue(self.layersFootprintValuesDict.get(item, "true") == "true")
            self.m_checkBox_reference_designators.SetValue(
                self.layersReferenceDesignatorsDict.get(item, "true") == "true")

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
        if self.current_layer:
            def bool_str(value: bool):
                return "true" if value else "false"

            cl = self.current_layer
            self.layersColorDict[cl] = self.m_textCtrl_color.GetValue()
            self.layersNegativeDict[cl] = bool_str(self.m_checkBox_negative.IsChecked())
            self.layersFootprintValuesDict[cl] = self.m_checkBox_footprint_values.GetValue()
            self.layersFootprintValuesDict[cl] = bool_str(self.m_checkBox_footprint_values.IsChecked())
            self.layersReferenceDesignatorsDict[cl] = self.m_checkBox_reference_designators.GetValue()
            self.layersReferenceDesignatorsDict[cl] = bool_str(self.m_checkBox_reference_designators.IsChecked())
        self.SaveTemplate()

    # Helper functions
    def OnSize(self, event):
        # Trick the listCheckBox best size calculations
        tmp = self.templatesSortOrderBox.GetStrings()
        self.templatesSortOrderBox.SetItems([])
        self.Layout()
        self.templatesSortOrderBox.SetItems(tmp)

    def SaveTemplate(self):
        template_name = self.m_textCtrl_template_name.GetValue()
        if template_name:
            # Check if selected frame layer is enabled. Otherwise, add it to the bottom of the enabled list.
            frame_layer = self.m_comboBox_frame.GetValue()
            if frame_layer != "None":
                if self.layersSortOrderBox.FindString(frame_layer) == wx.NOT_FOUND:
                    self.layersSortOrderBox.Append(frame_layer)
                    frame_layer_pos = self.disabledLayersSortOrderBox.FindString(frame_layer)
                    if frame_layer_pos != wx.NOT_FOUND:
                        self.disabledLayersSortOrderBox.Delete(frame_layer_pos)

            enabled_layers_list = self.layersSortOrderBox.GetItems()
            # Remove the name within the parenthesis if there is one
            for i, layer_name in enumerate(enabled_layers_list):
                enabled_layers_list[i] = layer_name.split(' (')[0]

            enabled_layers = ','.join(enabled_layers_list)
            this_template = {"mirrored": self.m_checkBox_mirror.IsChecked(),
                             "tented": self.m_checkBox_tent.IsChecked(),
                             "enabled_layers": enabled_layers,
                             "frame": frame_layer.split(' (')[0],  # Remove parenthesis if there is one
                             "popups": self.m_comboBox_popups.GetValue(),
                             "layers": self.layersColorDict,
                             "layers_negative": self.layersNegativeDict,
                             "layers_footprint_values": self.layersFootprintValuesDict,
                             "layers_reference_designators": self.layersReferenceDesignatorsDict}
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
        self.m_color_shower.SetBackgroundColour(wx.NullColour)
        self.m_color_shower.SetForegroundColour(wx.NullColour)
        self.m_color_shower.SetLabel("")
        self.m_checkBox_negative.SetValue(False)
        self.m_checkBox_footprint_values.SetValue(True)
        self.m_checkBox_reference_designators.SetValue(True)
        self.layersSortOrderBox.Clear()
        self.disabledLayersSortOrderBox.Clear()
        self.hide_layer_settings()
