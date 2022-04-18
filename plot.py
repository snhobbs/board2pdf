
import os
import shutil
import pcbnew
import wx

from . import PyPDF4

import traceback

def print_exception():
    etype, value, tb = exc_info()
    info, error = format_exception(etype, value, tb)[-2:]
    print(f'Exception in:\n{info}\n{error}')

def hex_to_rgb(value):
    """Return (red, green, blue) in float between 0-1 for the color given as #rrggbb."""
    value = value.lstrip('#')
    lv = len(value)
    rgb = tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))
    rgb = (rgb[0]/255, rgb[1]/255, rgb[2]/255)
    return rgb

def colorize_pdf(folder, inputFile, outputFile, color):
    try:
        with open(os.path.join(folder, inputFile), "rb") as f:
            source = PyPDF4.PdfFileReader(f, "rb")
            output = PyPDF4.PdfFileWriter(os.path.join(folder, outputFile))

            page = source.getPage(0)

            content_object = page["/Contents"].getObject()
            content = PyPDF4.pdf.ContentStream(content_object, source)

            i = 0
            for operands, operator in content.operations:
                if operator == PyPDF4.b_("rg") or operator == PyPDF4.b_("RG"):
                    if operands == [0, 0, 0]:
                        rgb = content.operations[i][0]
                        content.operations[i] = (
                            [PyPDF4.generic.FloatObject(color[0]), PyPDF4.generic.FloatObject(color[1]), PyPDF4.generic.FloatObject(color[2])], content.operations[i][1])
                    #else:
                    #    print(operator, operands[0], operands[1], operands[2], "The type is : ", type(rgb[0]),
                    #          type(rgb[1]), type(rgb[2]))
                i = i + 1

            page.__setitem__(PyPDF4.generic.NameObject('/Contents'), content)
            output.addPage(page)
            output.write()
            output.close()

    except:
        wx.MessageBox("colorize_pdf failed\nOn input file " + inputFile + " in " + folder + "\n\n" + traceback.format_exc(), 'Error', wx.OK | wx.ICON_ERROR)

def merge_pdf(input_folder, input_files, output_folder, output_file):
    try:
        output = PyPDF4.PdfFileWriter(os.path.join(output_folder, output_file))
        i = 0
        open_files = []
        for filename in input_files:
            try:
                file = open(os.path.join(input_folder, filename), 'rb')
                open_files.append(file)
                pdfReader = PyPDF4.PdfFileReader(file)
                pageObj = pdfReader.getPage(0)
                if(i == 0):
                    merged_page = pageObj
                else:
                    merged_page.mergePage(pageObj)
                i = i + 1
                #pdfReader.stream.close()
            except:
                error_bitmap = ""
                error_msg = traceback.format_exc()
                if 'KeyError: 0' in error_msg:
                    error_bitmap = "This error can be caused by the presence of a bitmap image on this layer. Bitmaps are only allowed on the layer furthest down in the layer list. See Issue #11 for more information.\n\n"
                wx.MessageBox("merge_pdf failed\n\nOn input file " + filename + " in " + input_folder + "\n\n" + error_bitmap + error_msg, 'Error', wx.OK | wx.ICON_ERROR)
        output.addPage(merged_page)

        output.write()
        output.close()

    except:
        wx.MessageBox("merge_pdf failed\n\nOn output file " + output_file + " in " + output_folder + "\n\n" + traceback.format_exc(), 'Error', wx.OK | wx.ICON_ERROR)

    # Close the input files
    for f in open_files:
        f.close()

def create_pdf_from_pages(input_folder, input_files, output_folder, output_file):
    try:
        output = PyPDF4.PdfFileWriter(os.path.join(output_folder, output_file))
        open_files = []
        for filename in input_files:
            try:
                file = open(os.path.join(input_folder, filename), 'rb')
                open_files.append(file)
                pdfReader = PyPDF4.PdfFileReader(file)
                pageObj = pdfReader.getPage(0)
                pageObj.compressContentStreams()
                output.addPage(pageObj)
                #pdfReader.stream.close()
            except:
                wx.MessageBox("create_pdf_from_pages failed\n\nOn input file " + filename + " in " + input_folder + "\n\n" + traceback.format_exc(), 'Error', wx.OK | wx.ICON_ERROR)

        output.write()
        output.close()
    except:
        wx.MessageBox("create_pdf_from_pages failed\n\nOn output file " + output_file + " in " + output_folder + "\n\n" + traceback.format_exc(), 'Error', wx.OK | wx.ICON_ERROR)

    # Close the files
    for f in open_files:
        f.close()

def plot_gerbers(board, output_path, templates, enabled_templates, del_temp_files, dialog_panel):
    wx.MessageBox("The process of creating a pdf from this board will now begin.\n\n" +
                  "If you have a very small board, this will take less then a minute. But if you have " +
                  "a large board you may just as well go grab a cup of coffee because this will take "
                  "longer than you would expect!")

    def setProgress(value):
        dialog_panel.m_progress.SetValue(value)
        dialog_panel.Refresh()
        dialog_panel.Update()
        
    os.chdir(os.path.dirname(board.GetFileName()))
    output_dir = os.path.abspath(os.path.expanduser(os.path.expandvars(output_path)))

    temp_dir = os.path.abspath(os.path.join(output_dir, "temp"))

    dialog_panel.m_staticText_status.SetLabel("Status: Started plotting...")
    progress = 5
    setProgress(progress)

    steps = 1
    # Count number of process steps
    for t in enabled_templates:
        steps = steps + 1
        if "enabled_layers" in templates[t]:
            enabled_layers = templates[t]["enabled_layers"].split(',')
            enabled_layers[:] = [l for l in enabled_layers if l != '']  # removes empty entries
            if enabled_layers:
                for el in enabled_layers:
                    steps = steps + 1
                    if "layers" in templates[t]:
                        if el in templates[t]["layers"]:
                            if templates[t]["layers"][el] != "#000000":
                                steps = steps + 1
    progress_step = 95//steps

    plot_controller = pcbnew.PLOT_CONTROLLER(board)
    plot_options = plot_controller.GetPlotOptions()

    base_filename = os.path.basename(os.path.splitext(board.GetFileName())[0])

    plot_options.SetOutputDirectory(temp_dir)

    templates_list = []
    for t in enabled_templates:
        temp = []
        #{  "Test-template": {"mirrored": true, "enabled_layers": "B.Fab,B.Mask,Edge.Cuts,F.Adhesive", "frame": "In4.Cu",
        #          "layers": {"B.Fab": "#000012", "B.Mask": "#000045"}}  }
        if t in templates:
            temp.append(t) # Add the template name

            if "mirrored" in templates[t]:
                temp.append(templates[t]["mirrored"]) # Add if the template is mirrored or not
            else:
                temp.append(False)
                
            if "tented" in templates[t]:
                temp.append(templates[t]["tented"]) # Add if the template is tented or not
            else:
                temp.append(False)

            frame_layer = "None"
            if "frame" in templates[t]:
                frame_layer = templates[t]["frame"] # Layer with frame

            # Build a dict to translate layer names to layerID
            layer_names = {}
            i = pcbnew.PCBNEW_LAYER_ID_START
            while i < pcbnew.PCBNEW_LAYER_ID_START + pcbnew.PCB_LAYER_ID_COUNT:
                layer_names[pcbnew.BOARD_GetStandardLayerName(i)] = i
                i += 1

            settings = []

            if "enabled_layers" in templates[t]:
                enabled_layers = templates[t]["enabled_layers"].split(',')
                enabled_layers[:] = [l for l in enabled_layers if l != '']  # removes empty entries
                if enabled_layers:
                    for el in enabled_layers:
                        s = []
                        s.append(el) # Layer name string
                        s.append(layer_names[el]) # Layer ID
                        if el in templates[t]["layers"]:
                            s.append(templates[t]["layers"][el]) # Layer color
                        else:
                            s.append("#000000") # Layer color black
                        if el == frame_layer:
                            s.append(True)
                        else:
                            s.append(False)
                        if el in templates[t]["layers_negative"]: # Bool specifying if layer is negative
                            if templates[t]["layers_negative"][el] == "true":
                                s.append(True)
                            else:
                                s.append(False)
                        else:
                            s.append(False)
                        settings.insert(0, s) # Prepend to settings

            temp.append(settings)
            templates_list.append(temp)
    #wx.MessageBox("Newly created template_list:\n" + str(templates_list))

    """
    [
        ["Greyscale Top", False,
            [
             ("F_Cu", pcbnew.F_Cu, "#F0F0F0", False, True),
             ("F_Paste", pcbnew.F_Paste, "#C4C4C4", False, False),
            ]
        ],
    ]
    """

    # Set General Options:
    plot_options.SetPlotValue(True)
    plot_options.SetPlotReference(True)
    plot_options.SetPlotInvisibleText(False)
    #plot_options.SetPlotViaOnMaskLayer(False)
    plot_options.SetExcludeEdgeLayer(True);
    # plot_options.SetPlotPadsOnSilkLayer(False);
    plot_options.SetUseAuxOrigin(False)
    plot_options.SetScale(1.0)
    plot_options.SetAutoScale(False)
    # plot_options.SetPlotMode(PLOT_MODE)
    # plot_options.SetLineWidth(2000)

    template_filelist = []

    # Iterate over the templates
    for template in templates_list:
        template_name = template[0]
        # wx.MessageBox("Now starting with template: " + template_name)
        # Plot layers to pdf files
        for layer_info in template[3]:
            dialog_panel.m_staticText_status.SetLabel("Status: Plotting " + layer_info[0] + " for template " + template_name)
            progress = progress + progress_step
            setProgress(progress)

            plot_options.SetPlotFrameRef(layer_info[3])
            plot_options.SetNegative(layer_info[4])
            plot_options.SetMirror(template[1])
            plot_options.SetPlotViaOnMaskLayer(template[2])
            if pcbnew.IsCopperLayer(layer_info[1]): # Should probably do this on mask layers as well
                plot_options.SetDrillMarksType(2)  # NO_DRILL_SHAPE = 0, SMALL_DRILL_SHAPE = 1, FULL_DRILL_SHAPE  = 2
            else:
                plot_options.SetDrillMarksType(0)  # NO_DRILL_SHAPE = 0, SMALL_DRILL_SHAPE = 1, FULL_DRILL_SHAPE  = 2
            plot_controller.SetLayer(layer_info[1])
            plot_controller.OpenPlotfile(layer_info[0], pcbnew.PLOT_FORMAT_PDF, "Assembly")
            plot_controller.PlotLayer()

        plot_controller.ClosePlot()

        filelist = []
        # Change color of pdf files
        for layer_info in template[3]:
            ln = layer_info[0].replace('.', '_')
            inputFile = base_filename + "-" + ln + ".pdf"
            if(layer_info[2] != "#000000"):
                dialog_panel.m_staticText_status.SetLabel("Status: Coloring " + layer_info[0] + " for template " + template_name)
                progress = progress + progress_step
                setProgress(progress)

                outputFile = base_filename + "-" + ln + "-colored.pdf"
                colorize_pdf(temp_dir, inputFile, outputFile, hex_to_rgb(layer_info[2]))
                filelist.append(outputFile)
            else:
                filelist.append(inputFile)

        # Merge pdf files
        dialog_panel.m_staticText_status.SetLabel("Status: Merging all layers of template " + template_name)
        progress = progress + progress_step
        setProgress(progress)

        assembly_file = base_filename + "-" + template[0] + ".pdf"
        merge_pdf(temp_dir, filelist, temp_dir, assembly_file)
        template_filelist.append(assembly_file)

    # Add all generated pdfs to one file
    dialog_panel.m_staticText_status.SetLabel("Status: Adding all templates to a single file")
    setProgress(progress)

    final_assembly_file = base_filename + "-Assembly.pdf"
    create_pdf_from_pages(temp_dir, template_filelist, output_dir, final_assembly_file)

    # Delete temp files if setting says so
    if (del_temp_files):
        try:
            shutil.rmtree(temp_dir)
        except:
            wx.MessageBox("del_temp_files failed\n\nOn dir " + temp_dir + "\n\n" + traceback.format_exc(), 'Error', wx.OK | wx.ICON_ERROR)
        dialog_panel.m_staticText_status.SetLabel("Status: All done! Temporary files deleted.")
    else:
        dialog_panel.m_staticText_status.SetLabel("Status: All done!")

    progress = 100
    setProgress(progress)

    wx.MessageBox("All done!\n\nPdf created: " + os.path.abspath(os.path.join(output_dir, final_assembly_file)))
