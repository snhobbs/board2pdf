
import os
import shutil
import pcbnew
import wx
import re
import traceback


try:
    import fitz #pymupdf
except ImportError or ModuleNotFoundError:
    wx.MessageBox("PyMuPdf import failed. Use 'python -m pip install --upgrade pymupdf' to install it." + "\n\n" + traceback.format_exc(), 'Error', wx.OK | wx.ICON_ERROR)


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
        with fitz.open(os.path.join(folder, inputFile)) as doc:
            xref_number = doc[0].get_contents()
            stream_bytes =doc.xref_stream(xref_number[0])
            new_color = str(color[0]) + ' ' + str(color[1]) + ' ' + str(color[2]) + ' '  
            new_color_RG = bytes(new_color + 'RG', 'ascii')
            new_color_rg = bytes(new_color + 'rg', 'ascii')

            stream_bytes = re.sub(b'0.0.0.RG', new_color_RG, stream_bytes)
            stream_bytes = re.sub(b'0.0.0.rg', new_color_rg, stream_bytes)
            
            doc.update_stream(xref_number[0], stream_bytes)
            doc.save(os.path.join(folder, outputFile), clean=True)

    except:
        wx.MessageBox("colorize_pdf failed\nOn input file " + inputFile + " in " + folder + "\n\n" + traceback.format_exc(), 'Error', wx.OK | wx.ICON_ERROR)

def merge_pdf(input_folder, input_files, output_folder, output_file):
    try:
        output = fitz.open()
        i=0
        for filename in reversed(input_files):
            try:
                # using "with" to force RAII and avoid another "for" closing files
                with fitz.open(os.path.join(input_folder, filename)) as file:

                    if i == 0:
                        output.insert_pdf(file)
                    else:
                        output[0].show_pdf_page(file[0].rect,  # select output rect
                                            file,  # input document
                                            0,  # input page number
                                            overlay=False) 
                i=i+1
            except:
                wx.MessageBox("merge_pdf failed\n\nOn input file " + filename + " in " + input_folder + "\n\n" + traceback.format_exc(), 'Error', wx.OK | wx.ICON_ERROR)
                    
        output.save(os.path.join(output_folder, output_file))
        

    except:
        wx.MessageBox("merge_pdf failed\n\nOn output file " + output_file + " in " + output_folder + "\n\n" + traceback.format_exc(), 'Error', wx.OK | wx.ICON_ERROR)


def create_pdf_from_pages(input_folder, input_files, output_folder, output_file):

    try:

        output = fitz.open()
        for filename in input_files:
            with fitz.open(os.path.join(input_folder, filename)) as file:
                output.insert_pdf(file)
        output.save(os.path.join(output_folder, output_file))

    except:
        wx.MessageBox("create_pdf_from_pages failed\n\nOn output file " + output_file + " in " + output_folder + "\n\n" + traceback.format_exc(), 'Error', wx.OK | wx.ICON_ERROR)


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
    final_assembly_file = base_filename + "-Assembly.pdf"
    final_assembly_file_with_path = os.path.abspath(os.path.join(output_dir, final_assembly_file))

    # Create the directory if it doesn't exist already
    os.makedirs(output_dir, exist_ok=True)

    # Check if we're able to write to the output file.
    try:
        #os.access(os.path.join(output_dir, final_assembly_file), os.W_OK)
        open(os.path.join(output_dir, final_assembly_file), "w")

    except:
        wx.MessageBox("The output file is not writeable. Perhaps it's open in another " +
                      "application?\n\n" + final_assembly_file_with_path, 'Error', wx.OK | wx.ICON_ERROR)
        progress = 100
        setProgress(progress)
        dialog_panel.m_staticText_status.SetLabel("Status: Failed to write to output file.")
        return

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
                        #dialog_panel.m_staticText_status.SetLabel("test1")
                        # I'm having a bug where code can hang from here...
                        if el in templates[t]["layers_negative"]: # Bool specifying if layer is negative
                            if templates[t]["layers_negative"][el] == "true":
                                s.append(True)
                            else:
                                s.append(False)
                        else:
                            s.append(False)
                        # dialog_panel.m_staticText_status.SetLabel("test2")
                        # to here...
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
            plot_controller.OpenPlotfile(layer_info[0], pcbnew.PLOT_FORMAT_PDF, template_name)
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

    create_pdf_from_pages(temp_dir, template_filelist, output_dir, final_assembly_file)

    # Delete temp files if setting says so
    if (del_temp_files):
        try:
            shutil.rmtree(temp_dir)
            dialog_panel.m_staticText_status.SetLabel("Status: All done! Temporary files deleted.")
        except:
            wx.MessageBox("del_temp_files failed\n\nOn dir " + temp_dir + "\n\n" + traceback.format_exc(), 'Error', wx.OK | wx.ICON_ERROR)
    else:
        dialog_panel.m_staticText_status.SetLabel("Status: All done!")

    progress = 100
    setProgress(progress)

    wx.MessageBox("All done!\n\nPdf created: " + os.path.abspath(os.path.join(output_dir, final_assembly_file)))
