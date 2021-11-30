# -*- coding: utf-8 -*-

###########################################################################
## Python code generated with wxFormBuilder (version Oct 26 2018)
## http://www.wxformbuilder.org/
##
## PLEASE DO *NOT* EDIT THIS FILE!
###########################################################################

import wx
import wx.xrc

###########################################################################
## Class SettingsDialogBase
###########################################################################

class SettingsDialogBase ( wx.Dialog ):

    def __init__( self, parent ):
        wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Board2Pdf", pos = wx.DefaultPosition, size = wx.Size( 463,497 ), style = wx.DEFAULT_DIALOG_STYLE|wx.STAY_ON_TOP|wx.BORDER_DEFAULT )

        self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )


        self.Centre( wx.BOTH )

    def __del__( self ):
        pass


###########################################################################
## Class SettingsDialogPanel
###########################################################################

class SettingsDialogPanel ( wx.Panel ):

    def __init__( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.Size( 888,757 ), style = wx.TAB_TRAVERSAL, name = wx.EmptyString ):
        wx.Panel.__init__ ( self, parent, id = id, pos = pos, size = size, style = style, name = name )

        bSizer20 = wx.BoxSizer( wx.HORIZONTAL )

        bSizer30 = wx.BoxSizer( wx.VERTICAL )

        sbSizer22 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"General Settings" ), wx.VERTICAL )

        bSizer32 = wx.BoxSizer( wx.VERTICAL )

        sortingSizer = wx.StaticBoxSizer( wx.StaticBox( sbSizer22.GetStaticBox(), wx.ID_ANY, u"Enabled Templates" ), wx.VERTICAL )

        bSizer4 = wx.BoxSizer( wx.HORIZONTAL )

        bSizer6 = wx.BoxSizer( wx.VERTICAL )

        templatesSortOrderBoxChoices = []
        self.templatesSortOrderBox = wx.ListBox( sortingSizer.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, templatesSortOrderBoxChoices, wx.LB_SINGLE|wx.BORDER_SIMPLE )
        bSizer6.Add( self.templatesSortOrderBox, 1, wx.ALL|wx.EXPAND, 5 )


        bSizer4.Add( bSizer6, 1, wx.EXPAND, 5 )

        bSizer5 = wx.BoxSizer( wx.VERTICAL )

        self.m_button_template_up = wx.Button( sortingSizer.GetStaticBox(), wx.ID_ANY, u"Up", wx.DefaultPosition, wx.Size( 60,30 ), 0|wx.BORDER_DEFAULT )
        bSizer5.Add( self.m_button_template_up, 0, wx.ALL, 5 )

        self.m_button_template_down = wx.Button( sortingSizer.GetStaticBox(), wx.ID_ANY, u"Down", wx.DefaultPosition, wx.Size( 60,30 ), 0|wx.BORDER_DEFAULT )
        bSizer5.Add( self.m_button_template_down, 0, wx.ALL, 5 )

        self.m_button_template_new = wx.Button( sortingSizer.GetStaticBox(), wx.ID_ANY, u"New", wx.DefaultPosition, wx.Size( 60,30 ), 0|wx.BORDER_DEFAULT )
        bSizer5.Add( self.m_button_template_new, 0, wx.ALL, 5 )

        self.m_button_template_disable = wx.Button( sortingSizer.GetStaticBox(), wx.ID_ANY, u"Disable", wx.DefaultPosition, wx.Size( 60,30 ), 0|wx.BORDER_DEFAULT )
        bSizer5.Add( self.m_button_template_disable, 0, wx.ALL, 5 )


        bSizer4.Add( bSizer5, 0, wx.ALIGN_RIGHT, 5 )


        sortingSizer.Add( bSizer4, 1, wx.EXPAND, 5 )

        self.m_staticText81 = wx.StaticText( sortingSizer.GetStaticBox(), wx.ID_ANY, u"Note! Template at the top of the list will become page one in pdf, and so on.", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText81.Wrap( -1 )

        sortingSizer.Add( self.m_staticText81, 0, wx.ALL, 5 )


        bSizer32.Add( sortingSizer, 1, wx.ALL|wx.EXPAND, 5 )

        layersSizer = wx.StaticBoxSizer( wx.StaticBox( sbSizer22.GetStaticBox(), wx.ID_ANY, u"Disabled Templates" ), wx.VERTICAL )

        bSizer41 = wx.BoxSizer( wx.HORIZONTAL )

        bSizer61 = wx.BoxSizer( wx.VERTICAL )

        disabledTemplatesSortOrderBoxChoices = []
        self.disabledTemplatesSortOrderBox = wx.ListBox( layersSizer.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, disabledTemplatesSortOrderBoxChoices, wx.LB_SINGLE|wx.LB_SORT|wx.BORDER_SIMPLE )
        bSizer61.Add( self.disabledTemplatesSortOrderBox, 1, wx.ALL|wx.EXPAND, 5 )


        bSizer41.Add( bSizer61, 1, wx.EXPAND, 5 )

        bSizer51 = wx.BoxSizer( wx.VERTICAL )

        self.m_button_template_enable = wx.Button( layersSizer.GetStaticBox(), wx.ID_ANY, u"Enable", wx.DefaultPosition, wx.Size( 60,30 ), 0|wx.BORDER_DEFAULT )
        bSizer51.Add( self.m_button_template_enable, 0, wx.ALL, 5 )

        self.m_button4 = wx.Button( layersSizer.GetStaticBox(), wx.ID_ANY, u"Del", wx.DefaultPosition, wx.Size( 60,30 ), 0|wx.BORDER_DEFAULT )
        bSizer51.Add( self.m_button4, 0, wx.ALL, 5 )


        bSizer41.Add( bSizer51, 0, wx.ALIGN_RIGHT, 5 )


        layersSizer.Add( bSizer41, 1, wx.EXPAND, 5 )


        bSizer32.Add( layersSizer, 1, wx.ALL|wx.EXPAND, 5 )

        sbSizer6 = wx.StaticBoxSizer( wx.StaticBox( sbSizer22.GetStaticBox(), wx.ID_ANY, u"Settings" ), wx.VERTICAL )

        fgSizer1 = wx.FlexGridSizer( 0, 2, 0, 0 )
        fgSizer1.AddGrowableCol( 1 )
        fgSizer1.SetFlexibleDirection( wx.BOTH )
        fgSizer1.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        self.m_staticText8 = wx.StaticText( sbSizer6.GetStaticBox(), wx.ID_ANY, u"Output Directory", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText8.Wrap( -1 )

        fgSizer1.Add( self.m_staticText8, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )

        self.outputDirPicker = wx.DirPickerCtrl( sbSizer6.GetStaticBox(), wx.ID_ANY, u".\\KiPcb2Pdf", u"Select bom folder", wx.DefaultPosition, wx.DefaultSize, wx.DIRP_SMALL|wx.DIRP_USE_TEXTCTRL|wx.BORDER_SIMPLE )
        fgSizer1.Add( self.outputDirPicker, 1, wx.ALIGN_CENTER_VERTICAL|wx.ALL|wx.EXPAND, 5 )


        sbSizer6.Add( fgSizer1, 1, wx.EXPAND, 5 )

        bSizer201 = wx.BoxSizer( wx.HORIZONTAL )


        bSizer201.Add( ( 0, 0), 1, wx.EXPAND, 5 )

        self.m_checkBox_delete_temp_files = wx.CheckBox( sbSizer6.GetStaticBox(), wx.ID_ANY, u"Delete temporary files when done", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer201.Add( self.m_checkBox_delete_temp_files, 0, wx.ALL, 5 )


        sbSizer6.Add( bSizer201, 1, wx.EXPAND, 5 )

        bSizer39 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_button41 = wx.Button( sbSizer6.GetStaticBox(), wx.ID_ANY, u"Save current settings", wx.DefaultPosition, wx.DefaultSize, 0|wx.BORDER_DEFAULT )
        bSizer39.Add( self.m_button41, 0, wx.ALL, 5 )


        bSizer39.Add( ( 50, 0), 0, wx.EXPAND, 5 )

        self.m_button42 = wx.Button( sbSizer6.GetStaticBox(), wx.ID_ANY, u"Perform", wx.DefaultPosition, wx.DefaultSize, 0|wx.BORDER_DEFAULT )
        bSizer39.Add( self.m_button42, 0, wx.ALL, 5 )

        self.m_button43 = wx.Button( sbSizer6.GetStaticBox(), wx.ID_CANCEL, u"Exit", wx.DefaultPosition, wx.DefaultSize, 0|wx.BORDER_DEFAULT )
        bSizer39.Add( self.m_button43, 0, wx.ALL, 5 )


        sbSizer6.Add( bSizer39, 0, wx.ALIGN_CENTER, 5 )

        self.m_progress = wx.Gauge( sbSizer6.GetStaticBox(), wx.ID_ANY, 100, wx.DefaultPosition, wx.Size( 400,-1 ), wx.GA_HORIZONTAL )
        self.m_progress.SetValue( 0 )
        sbSizer6.Add( self.m_progress, 0, wx.ALL, 5 )

        self.m_staticText_status = wx.StaticText( sbSizer6.GetStaticBox(), wx.ID_ANY, u"Status:", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText_status.Wrap( -1 )

        sbSizer6.Add( self.m_staticText_status, 0, wx.ALL, 5 )


        bSizer32.Add( sbSizer6, 0, wx.ALL|wx.EXPAND, 5 )


        sbSizer22.Add( bSizer32, 1, wx.EXPAND, 5 )


        bSizer30.Add( sbSizer22, 1, wx.EXPAND, 5 )


        bSizer20.Add( bSizer30, 1, wx.EXPAND, 5 )

        bSizer301 = wx.BoxSizer( wx.VERTICAL )

        sbSizer23 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"Template Settings" ), wx.VERTICAL )

        bSizer321 = wx.BoxSizer( wx.VERTICAL )

        sbSizer61 = wx.StaticBoxSizer( wx.StaticBox( sbSizer23.GetStaticBox(), wx.ID_ANY, u"Template Properties" ), wx.VERTICAL )

        gSizer1 = wx.GridSizer( 3, 2, 0, 0 )

        self.m_staticText10 = wx.StaticText( sbSizer61.GetStaticBox(), wx.ID_ANY, u"Template name", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText10.Wrap( -1 )

        gSizer1.Add( self.m_staticText10, 0, wx.ALL, 5 )

        self.m_textCtrl_template_name = wx.TextCtrl( sbSizer61.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 200,-1 ), 0 )
        gSizer1.Add( self.m_textCtrl_template_name, 0, wx.ALL, 5 )

        self.m_staticText12 = wx.StaticText( sbSizer61.GetStaticBox(), wx.ID_ANY, u"Mirror all layers (used for bottom)", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText12.Wrap( -1 )

        gSizer1.Add( self.m_staticText12, 0, wx.ALL, 5 )

        self.m_checkBox_mirror = wx.CheckBox( sbSizer61.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        gSizer1.Add( self.m_checkBox_mirror, 0, wx.ALL, 5 )

        self.m_staticText13 = wx.StaticText( sbSizer61.GetStaticBox(), wx.ID_ANY, u"Draw frame on layer", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText13.Wrap( -1 )

        gSizer1.Add( self.m_staticText13, 0, wx.ALL, 5 )

        m_comboBox_frameChoices = []
        self.m_comboBox_frame = wx.ComboBox( sbSizer61.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 200,-1 ), m_comboBox_frameChoices, 0 )
        gSizer1.Add( self.m_comboBox_frame, 0, wx.ALL, 5 )


        sbSizer61.Add( gSizer1, 1, wx.EXPAND, 5 )


        bSizer321.Add( sbSizer61, 0, wx.ALL|wx.EXPAND, 5 )

        sbSizer611 = wx.StaticBoxSizer( wx.StaticBox( sbSizer23.GetStaticBox(), wx.ID_ANY, u"Layer Properties" ), wx.VERTICAL )

        gSizer2 = wx.GridSizer( 1, 3, 0, 0 )

        self.m_staticText14 = wx.StaticText( sbSizer611.GetStaticBox(), wx.ID_ANY, u"Layer color", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText14.Wrap( -1 )

        gSizer2.Add( self.m_staticText14, 0, wx.ALL, 5 )

        self.m_textCtrl_color = wx.TextCtrl( sbSizer611.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        gSizer2.Add( self.m_textCtrl_color, 0, wx.ALL, 5 )

        self.m_button14 = wx.Button( sbSizer611.GetStaticBox(), wx.ID_ANY, u"Pick Color", wx.DefaultPosition, wx.DefaultSize, 0 )
        gSizer2.Add( self.m_button14, 0, wx.ALL, 5 )


        sbSizer611.Add( gSizer2, 1, wx.EXPAND, 5 )


        bSizer321.Add( sbSizer611, 0, wx.ALL|wx.EXPAND, 5 )

        sortingSizer1 = wx.StaticBoxSizer( wx.StaticBox( sbSizer23.GetStaticBox(), wx.ID_ANY, u"Enabled Layers" ), wx.VERTICAL )

        bSizer512 = wx.BoxSizer( wx.VERTICAL )

        bSizer42 = wx.BoxSizer( wx.HORIZONTAL )

        bSizer62 = wx.BoxSizer( wx.VERTICAL )

        layersSortOrderBoxChoices = []
        self.layersSortOrderBox = wx.ListBox( sortingSizer1.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, layersSortOrderBoxChoices, wx.LB_SINGLE|wx.BORDER_SIMPLE )
        bSizer62.Add( self.layersSortOrderBox, 1, wx.ALL|wx.EXPAND, 5 )


        bSizer42.Add( bSizer62, 1, wx.EXPAND, 5 )

        bSizer52 = wx.BoxSizer( wx.VERTICAL )

        self.m_button11 = wx.Button( sortingSizer1.GetStaticBox(), wx.ID_ANY, u"Up", wx.DefaultPosition, wx.Size( 60,30 ), 0|wx.BORDER_DEFAULT )
        bSizer52.Add( self.m_button11, 0, wx.ALL, 5 )

        self.m_button21 = wx.Button( sortingSizer1.GetStaticBox(), wx.ID_ANY, u"Down", wx.DefaultPosition, wx.Size( 60,30 ), 0|wx.BORDER_DEFAULT )
        bSizer52.Add( self.m_button21, 0, wx.ALL, 5 )

        self.m_button_disable1 = wx.Button( sortingSizer1.GetStaticBox(), wx.ID_ANY, u"Disable", wx.DefaultPosition, wx.Size( 60,30 ), 0|wx.BORDER_DEFAULT )
        bSizer52.Add( self.m_button_disable1, 0, wx.ALL, 5 )


        bSizer42.Add( bSizer52, 0, wx.ALIGN_RIGHT, 5 )


        bSizer512.Add( bSizer42, 1, wx.EXPAND, 5 )

        self.m_staticText16 = wx.StaticText( sortingSizer1.GetStaticBox(), wx.ID_ANY, u"Note! Layers at the top of the list will be drawn on top of layers further down.", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText16.Wrap( -1 )

        bSizer512.Add( self.m_staticText16, 0, wx.ALL, 5 )


        sortingSizer1.Add( bSizer512, 1, wx.EXPAND, 5 )


        bSizer321.Add( sortingSizer1, 1, wx.ALL|wx.EXPAND, 5 )

        layersSizer1 = wx.StaticBoxSizer( wx.StaticBox( sbSizer23.GetStaticBox(), wx.ID_ANY, u"Disabled Layers" ), wx.VERTICAL )

        bSizer411 = wx.BoxSizer( wx.HORIZONTAL )

        bSizer611 = wx.BoxSizer( wx.VERTICAL )

        disabledLayersSortOrderBoxChoices = []
        self.disabledLayersSortOrderBox = wx.ListBox( layersSizer1.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, disabledLayersSortOrderBoxChoices, wx.LB_SINGLE|wx.LB_SORT|wx.BORDER_SIMPLE )
        bSizer611.Add( self.disabledLayersSortOrderBox, 1, wx.ALL|wx.EXPAND, 5 )


        bSizer411.Add( bSizer611, 1, wx.EXPAND, 5 )

        bSizer511 = wx.BoxSizer( wx.VERTICAL )

        self.m_button_layer_enable1 = wx.Button( layersSizer1.GetStaticBox(), wx.ID_ANY, u"Enable", wx.DefaultPosition, wx.Size( 60,30 ), 0|wx.BORDER_DEFAULT )
        bSizer511.Add( self.m_button_layer_enable1, 0, wx.ALL, 5 )


        bSizer411.Add( bSizer511, 0, wx.ALIGN_RIGHT, 5 )


        layersSizer1.Add( bSizer411, 1, wx.EXPAND, 5 )


        bSizer321.Add( layersSizer1, 1, wx.ALL|wx.EXPAND, 5 )


        sbSizer23.Add( bSizer321, 1, wx.EXPAND, 5 )


        bSizer301.Add( sbSizer23, 1, wx.EXPAND, 5 )


        bSizer20.Add( bSizer301, 1, wx.EXPAND, 5 )


        self.SetSizer( bSizer20 )
        self.Layout()

        # Connect Events
        self.templatesSortOrderBox.Bind( wx.EVT_LISTBOX, self.OnTemplateEdit )
        self.m_button_template_up.Bind( wx.EVT_BUTTON, self.OnTemplatesSortOrderUp )
        self.m_button_template_down.Bind( wx.EVT_BUTTON, self.OnTemplatesSortOrderDown )
        self.m_button_template_new.Bind( wx.EVT_BUTTON, self.OnTemplatesNew )
        self.m_button_template_disable.Bind( wx.EVT_BUTTON, self.OnTemplateDisable )
        self.m_button_template_enable.Bind( wx.EVT_BUTTON, self.OnTemplateEnable )
        self.m_button4.Bind( wx.EVT_BUTTON, self.OnTemplatesDelete )
        self.m_button41.Bind( wx.EVT_BUTTON, self.OnSaveSettings )
        self.m_button42.Bind( wx.EVT_BUTTON, self.OnPerform )
        self.m_button43.Bind( wx.EVT_BUTTON, self.OnExit )
        self.m_textCtrl_template_name.Bind( wx.EVT_TEXT, self.OnTemplateNameChange )
        self.m_textCtrl_color.Bind( wx.EVT_TEXT, self.OnSaveLayer )
        self.m_button14.Bind( wx.EVT_BUTTON, self.OnPickColor )
        self.layersSortOrderBox.Bind( wx.EVT_LISTBOX, self.OnLayerEdit )
        self.m_button11.Bind( wx.EVT_BUTTON, self.OnLayerSortOrderUp )
        self.m_button21.Bind( wx.EVT_BUTTON, self.OnLayerSortOrderDown )
        self.m_button_disable1.Bind( wx.EVT_BUTTON, self.OnLayerDisable )
        self.m_button_layer_enable1.Bind( wx.EVT_BUTTON, self.OnLayerEnable )

    def __del__( self ):
        pass


    # Virtual event handlers, overide them in your derived class
    def OnTemplateEdit( self, event ):
        event.Skip()

    def OnTemplatesSortOrderUp( self, event ):
        event.Skip()

    def OnTemplatesSortOrderDown( self, event ):
        event.Skip()

    def OnTemplatesNew( self, event ):
        event.Skip()

    def OnTemplateDisable( self, event ):
        event.Skip()

    def OnTemplateEnable( self, event ):
        event.Skip()

    def OnTemplatesDelete( self, event ):
        event.Skip()

    def OnSaveSettings( self, event ):
        event.Skip()

    def OnPerform( self, event ):
        event.Skip()

    def OnExit( self, event ):
        event.Skip()

    def OnTemplateNameChange( self, event ):
        event.Skip()

    def OnSaveLayer( self, event ):
        event.Skip()

    def OnPickColor( self, event ):
        event.Skip()

    def OnLayerEdit( self, event ):
        event.Skip()

    def OnLayerSortOrderUp( self, event ):
        event.Skip()

    def OnLayerSortOrderDown( self, event ):
        event.Skip()

    def OnLayerDisable( self, event ):
        event.Skip()

    def OnLayerEnable( self, event ):
        event.Skip()


