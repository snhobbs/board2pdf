import os
import shutil
import sys
import pcbnew
import wx
import re
import traceback
import tempfile
import logging

try:
    from .pypdf import PdfReader, PdfWriter, PageObject, Transformation, generic
except ImportError:
    from pypdf import PdfReader, PdfWriter, PageObject, Transformation, generic

try:
    import fitz  # This imports PyMuPDF

    fitz.open()
    has_fitz = True
except (ImportError, AttributeError):
    has_fitz = False

_logger = logging.getLogger(__name__)


def print_exception():
    etype, value, tb = sys.exc_info()
    info, error = traceback.format_exception(etype, value, tb)[-2:]
    print(f'Exception in:\n{info}\n{error}', file=sys.stderr)


def io_file_error_msg(function: str, input_file: str, folder: str, more: str = '', tb=True):
    msg = f"{function} failed\nOn input file {input_file} in {folder}\n\n{more}" + (
        traceback.format_exc() if tb else '')
    try:
        wx.MessageBox(msg, 'Error', wx.OK | wx.ICON_ERROR)
    except wx._core.PyNoAppError:
        print(f'Error: {msg}', file=sys.stderr)


def colorize_pdf_fitz(folder, input_file, output_file, color):
    try:
        with fitz.open(os.path.join(folder, input_file)) as doc:
            xref_number = doc[0].get_contents()
            stream_bytes = doc.xref_stream(xref_number[0])
            new_color = ''.join([f'{c:.3g} ' for c in color])
            _logger.debug(f'{new_color=}')
            stream_bytes = re.sub(br'(\s)0 0 0 (RG|rg)', bytes(fr'\g<1>{new_color}\g<2>', 'ascii'), stream_bytes)

            doc.update_stream(xref_number[0], stream_bytes)
            doc.save(os.path.join(folder, output_file), clean=True)

    except RuntimeError as e:
        if "invalid key in dict" in str(e):
            io_file_error_msg(colorize_pdf_fitz.__name__, input_file, folder,
                              "This error can be due to PyMuPdf not being able to handle pdfs created by KiCad 7.0.1 due to a bug in KiCad 7.0.1. Upgrade KiCad or switch to pypdf instead.\n\n")
        return False

    except:
        io_file_error_msg(colorize_pdf_fitz.__name__, input_file, folder)
        return False

    return True


def colorize_pdf_pypdf(folder, input_file, output_file, color):
    try:
        with open(os.path.join(folder, input_file), "rb") as f:
            class ErrorHandler(object):
                def write(self, data):
                    if "UserWarning" not in data:
                        io_file_error_msg(colorize_pdf_pypdf.__name__, input_file, folder, data + "\n\n", tb=False)
                        return False

            if sys.stderr is None:
                handler = ErrorHandler()
                sys.stderr = handler

            source = PdfReader(f)
            output = PdfWriter()

            page = source.pages[0]
            content_object = page["/Contents"].get_object()
            content = generic.ContentStream(content_object, source)

            for i, (operands, operator) in enumerate(content.operations):
                if operator in (b"rg", b"RG"):
                    if operands == [0, 0, 0]:
                        content.operations[i] = (
                            [generic.FloatObject(intensity) for intensity in color], operator)
                    # else:
                    #    print(operator, operands[0], operands[1], operands[2], "The type is : ", type(operands[0]),
                    #          type(operands[1]), type(operands[2]))

            page[generic.NameObject("/Contents")] = content
            output.add_page(page)

            with open(os.path.join(folder, output_file), "wb") as output_stream:
                output.write(output_stream)

    except Exception:
        io_file_error_msg(colorize_pdf_pypdf.__name__, input_file, folder)
        return False

    return True

def merge_pdf_fitz(input_folder: str, input_files: list, output_folder: str, output_file: str, frame_file: str,
                    layer_scale: float):
    # I haven't found a way to scale the pdf and preserve the popup-menus.
    # For now, I'm taking the easy way out and handle the merging differently depending
    # on if scaling is used or not. At least the popup-menus are preserved when not using scaling.
    # https://github.com/pymupdf/PyMuPDF/discussions/2499
    if layer_scale == 1.0:
        return merge_pdf_fitz_without_scaling(input_folder, input_files, output_folder, output_file, frame_file)
    else:
        return merge_pdf_fitz_with_scaling(input_folder, input_files, output_folder, output_file, frame_file, layer_scale)
    
def merge_pdf_fitz_without_scaling(input_folder: str, input_files: list, output_folder: str, output_file: str, frame_file: str):
    try:
        output = None
        for filename in reversed(input_files):
            try:
                if output is None:
                    output = fitz.open(os.path.join(input_folder, filename))
                else:
                    # using "with" to force RAII and avoid another "for" closing files
                    with fitz.open(os.path.join(input_folder, filename)) as src:
                        output[0].show_pdf_page(src[0].rect,  # select output rect
                                                src,  # input document
                                                overlay=False)
            except Exception:
                io_file_error_msg(merge_pdf_fitz.__name__, filename, input_folder)
                return False

        output.save(os.path.join(output_folder, output_file))

    except Exception:
        io_file_error_msg(merge_pdf_fitz.__name__, output_file, output_folder)
        return False

    return True
    
def merge_pdf_fitz_with_scaling(input_folder: str, input_files: list, output_folder: str, output_file: str, frame_file: str,
                    layer_scale: float):
    try:
        output = fitz.open()
        page = None
        for filename in reversed(input_files):
            try:
                # using "with" to force RAII and avoid another "for" closing files
                with fitz.open(os.path.join(input_folder, filename)) as src:
                    if page is None:
                        page = output.new_page(width=src[0].rect.width * layer_scale,
                                               height=src[0].rect.height * layer_scale)
                        cropbox = fitz.Rect((page.rect.width - src[0].rect.width) / 2,
                                            (page.rect.height - src[0].rect.height) / 2,
                                            (page.rect.width + src[0].rect.width) / 2,
                                            (page.rect.height + src[0].rect.height) / 2)

                    pos = cropbox if frame_file == filename else page.rect
                    page.show_pdf_page(pos,  # select output rect
                                       src,  # input document
                                       overlay=False)
            except Exception:
                io_file_error_msg(merge_pdf_fitz.__name__, filename, input_folder)
                return False

        page.set_cropbox(cropbox)
        output.save(os.path.join(output_folder, output_file))

    except Exception:
        io_file_error_msg(merge_pdf_fitz.__name__, output_file, output_folder)
        return False

    return True


def merge_pdf_pypdf(input_folder: str, input_files: list, output_folder: str, output_file: str, frame_file: str,
                    layer_scale: float):
    try:
        page = None
        for filename in input_files:
            try:
                filepath = os.path.join(input_folder, filename)
                pdf_reader = PdfReader(filepath)
                src_page: PageObject = pdf_reader.pages[0]

                op = Transformation()
                if layer_scale > 1.0:
                    if filename == frame_file:
                        x_offset = src_page.mediabox.width * (layer_scale - 1.0) / 2
                        y_offset = src_page.mediabox.height * (layer_scale - 1.0) / 2
                        op = op.translate(x_offset, y_offset)
                    else:
                        op = op.scale(layer_scale)

                if page is None:
                    page = PageObject.create_blank_page(width=src_page.mediabox.width * layer_scale,
                                                        height=src_page.mediabox.height * layer_scale)
                    page.cropbox.lower_left = ((page.mediabox.width - src_page.mediabox.width) / 2,
                                               (page.mediabox.height - src_page.mediabox.height) / 2)
                    page.cropbox.upper_right = ((page.mediabox.width + src_page.mediabox.width) / 2,
                                                (page.mediabox.height + src_page.mediabox.height) / 2)

                page.merge_transformed_page(src_page, op)

            except Exception:
                error_bitmap = ""
                error_msg = traceback.format_exc()
                if 'KeyError: 0' in error_msg:
                    error_bitmap = "This error can be caused by the presence of a bitmap image on this layer. Bitmaps are only allowed on the layer furthest down in the layer list. See Issue #11 for more information.\n\n"
                io_file_error_msg(merge_pdf_pypdf.__name__, filename, input_folder, error_bitmap)
                return False

        output = PdfWriter()
        output.add_page(page)
        with open(os.path.join(output_folder, output_file), "wb") as output_stream:
            output.write(output_stream)

    except:
        io_file_error_msg(merge_pdf_pypdf.__name__, output_file, output_folder)
        return False

    return True


def create_pdf_from_pages(input_folder, input_files, output_folder, output_file, use_popups):
    try:
        output = PdfWriter()
        for filename in input_files:
            try:
                output.append(os.path.join(input_folder, filename))
            except:
                io_file_error_msg(create_pdf_from_pages.__name__, filename, input_folder)
                return False

        # If popup menus are used, add the needed javascript. Pypdf and fitz removes this in most operations.
        if use_popups:
            javascript_string = "function ShM(aEntries) { var aParams = []; for (var i in aEntries) { aParams.push({ cName: aEntries[i][0], cReturn: aEntries[i][1] }) } var cChoice = app.popUpMenuEx.apply(app, aParams); if (cChoice != null && cChoice.substring(0, 1) == '#') this.pageNum = parseInt(cChoice.slice(1)); else if (cChoice != null && cChoice.substring(0, 4) == 'http') app.launchURL(cChoice); }"
            output.add_js(javascript_string)

        for page in output.pages:
            # This has to be done on the writer, not the reader!
            page.compress_content_streams()  # This is CPU intensive!

        output.write(os.path.join(output_folder, output_file))

    except:
        io_file_error_msg(create_pdf_from_pages.__name__, output_file, output_folder)
        return False

    return True


class LayerInfo:
    std_color = "#000000"

    def __init__(self, layer_names: dict, layer_name: str, template: dict, frame_layer: str, popups: str):
        self.name: str = layer_name
        self.id: int = layer_names[layer_name]
        self.color_hex: str = template["layers"].get(layer_name, self.std_color)  # color as '#rrggbb' hex string
        self.with_frame: bool = layer_name == frame_layer

        try:
            # Bool specifying if footprint values shall be plotted
            self.negative = template["layers_negative"][layer_name] == "true"
        except KeyError:
            self.negative = False

        try:
            # Bool specifying if layer is negative
            self.footprint_value = template["layers_negative"][layer_name] == "true"
        except KeyError:
            self.footprint_value = False

        try:
            # Bool specifying if footprint values shall be plotted
            self.reference_designator = not template["layers_footprint_values"][layer_name] == "false"
        except KeyError:
            self.reference_designator = True
            
        # Check the popup settings.
        self.front_popups = False
        self.back_popups = False
        if popups == "Front Layer":
            self.front_popups = True
        elif popups == "Back Layer":
            self.back_popups = True
        elif popups == "Both Layers":
            self.front_popups = True
            self.back_popups = True

    @property
    def has_color(self) -> bool:
        """Checks if the layer color is not the standard color (=black)."""
        return self.color_hex != self.std_color

    @property
    def color_rgb(self) -> tuple[float, float, float]:
        """Return (red, green, blue) in float between 0-1."""
        value = self.color_hex.lstrip('#')
        lv = len(value)
        rgb = tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))
        rgb = (rgb[0] / 255, rgb[1] / 255, rgb[2] / 255)
        return rgb

    def __repr__(self):
        var_str = ', '.join(f"{key}: {value}" for key, value in vars(self).items())
        return f'{self.__class__.__name__}:{{ {var_str} }}'


class Template:
    def __init__(self, name: str, template: dict, layer_names: dict):
        self.name: str = name  # the template name
        self.mirrored: bool = template.get("mirrored", False)  # template is mirrored or not
        self.tented: bool = template.get("tented", False)  # template is tented or not

        frame_layer: str = template.get("frame", "")  # layer name of the frame layer
        popups: str = template.get("popups", "")  # setting saying if popups shall be taken from front, back or both

        # collection the settings of the enabled layers
        self.settings: list[LayerInfo] = []

        if "enabled_layers" in template:
            enabled_layers = template["enabled_layers"].split(',')
            for el in enabled_layers:
                if el:
                    # If this is the first layer, use the popup settings.
                    if el == enabled_layers[0]:
                        layer_popups: str  = popups
                    else:
                        layer_popups: str  = "None"
                    # Prepend to settings
                    layer_info = LayerInfo(layer_names, el, template, frame_layer, layer_popups)
                    self.settings.insert(0, layer_info)

    @property
    def steps(self) -> int:
        """number of process steps for this template"""
        return len(self.settings) + sum([layer.has_color for layer in self.settings])

    def __repr__(self):
        var_str = ', '.join(f"{key}: {value}" for key, value in vars(self).items())
        return f'{self.__class__.__name__}:{{ {var_str} }}'


def plot_pdfs(board, output_path, templates, enabled_templates, del_temp_files, create_svg, del_single_page_files,
                 dlg=None, **kwargs) -> bool:
    asy_file_extension = kwargs.pop('assembly_file_extension', '__Assembly')
    layer_scale = kwargs.pop('layer_scale', 1.0)
    colorize_lib: str = kwargs.pop('colorize_lib', '')
    merge_lib: str = kwargs.pop('merge_lib', '')

    if dlg is None:
        use_fitz = has_fitz or create_svg
        fitz_pdf = has_fitz and colorize_lib != 'pypdf'
        fitz_merge = has_fitz and merge_lib != 'pypdf'

        def set_progress_status(progress: int, status: str):
            print(f'{int(progress):3d}%: {status}')

        def msg_box(text, caption, flags):
            print(f"{caption}: {text}")

    elif isinstance(dlg, wx.Panel):
        fitz_pdf = dlg.m_radio_fitz.GetValue()
        fitz_merge = dlg.m_radio_merge_fitz.GetValue()
        use_fitz = fitz_pdf or fitz_merge or create_svg

        def set_progress_status(progress: int, status: str):
            dlg.m_staticText_status.SetLabel(f'Status: {status}')
            dlg.m_progress.SetValue(int(progress))
            dlg.Refresh()
            dlg.Update()

        def msg_box(text, caption, flags):
            wx.MessageBox(text, caption, flags)
    else:
        print(f"Error: Unknown dialog type {type(dlg)}", file=sys.stderr)
        return False

    if use_fitz and not has_fitz:
        msg_box(
            "PyMuPdf (fitz) wasn't loaded.\n\nIt must be installed for it to be used for coloring, for merging and for creating SVGs.\n\nMore information under Install dependencies in the Wiki at board2pdf.dennevi.com",
            'Error', wx.OK | wx.ICON_ERROR)
        set_progress_status(100, "Failed to load PyMuPDF.")
        return False

    colorize_pdf = colorize_pdf_fitz if fitz_pdf else colorize_pdf_pypdf
    merge_pdf = merge_pdf_fitz if fitz_merge else merge_pdf_pypdf

    os.chdir(os.path.dirname(board.GetFileName()))
    output_dir = os.path.abspath(os.path.expanduser(os.path.expandvars(output_path)))
    if del_temp_files:
        # in case the files are deleted: use the OS temp directory
        temp_dir = tempfile.mkdtemp()
    else:
        temp_dir = os.path.abspath(os.path.join(output_dir, "temp"))

    progress = 5
    set_progress_status(progress, "Started plotting...")

    plot_controller = pcbnew.PLOT_CONTROLLER(board)
    plot_options = plot_controller.GetPlotOptions()

    base_filename = os.path.basename(os.path.splitext(board.GetFileName())[0])
    final_assembly_file = base_filename + asy_file_extension + ".pdf"
    final_assembly_file_with_path = os.path.abspath(os.path.join(output_dir, final_assembly_file))

    # Create the directory if it doesn't exist already
    os.makedirs(output_dir, exist_ok=True)

    # Check if we're able to write to the output file.
    try:
        # os.access(os.path.join(output_dir, final_assembly_file), os.W_OK)
        open(os.path.join(output_dir, final_assembly_file), "w")
    except:
        msg_box("The output file is not writeable. Perhaps it's open in another application?\n\n"
                + final_assembly_file_with_path, 'Error', wx.OK | wx.ICON_ERROR)
        set_progress_status(100, "Failed to write to output file.")
        return False

    plot_options.SetOutputDirectory(temp_dir)

    # Build a dict to translate layer names to layerID
    layer_names = {}
    for i in range(pcbnew.PCBNEW_LAYER_ID_START, pcbnew.PCBNEW_LAYER_ID_START + pcbnew.PCB_LAYER_ID_COUNT):
        layer_names[board.GetStandardLayerName(i)] = i

    steps: int = 2  # number of process steps
    templates_list: list[Template] = []
    for t in enabled_templates:
        # {  "Test-template": {"mirrored": true, "enabled_layers": "B.Fab,B.Mask,Edge.Cuts,F.Adhesive", "frame": "In4.Cu",
        #          "layers": {"B.Fab": "#000012", "B.Mask": "#000045"}}  }
        if t in templates:
            temp = Template(t, templates[t], layer_names)
            _logger.debug(temp)
            steps += 1 + temp.steps
            templates_list.append(temp)
    progress_step: float = 95 / steps

    """
    [
        ["Greyscale Top", False,
            [
             ("F_Cu", pcbnew.F_Cu, "#F0F0F0", False, True, True, True),
             ("F_Paste", pcbnew.F_Paste, "#C4C4C4", False, False, True, True),
            ]
        ],
    ]
    """
    try:
        # Set General Options:
        plot_options.SetPlotInvisibleText(False)
        # plot_options.SetPlotPadsOnSilkLayer(False);
        plot_options.SetUseAuxOrigin(False)
        plot_options.SetScale(1.0)
        plot_options.SetAutoScale(False)
        # plot_options.SetPlotMode(PLOT_MODE)
        # plot_options.SetLineWidth(2000)
        if pcbnew.Version()[0:3] == "6.0":
            # This method is only available on V6, not V6.99/V7
            plot_options.SetExcludeEdgeLayer(True)
    except:
        msg_box(traceback.format_exc(), 'Error', wx.OK | wx.ICON_ERROR)
        set_progress_status(100, "Failed to set plot_options")
        return False

    template_filelist = []

    # Iterate over the templates
    for template in templates_list:
        # msg_box("Now starting with template: " + template_name)
        # Plot layers to pdf files
        for layer_info in template.settings:
            progress += progress_step
            set_progress_status(progress, f"Plotting {layer_info.name} for template {template.name}")

            if pcbnew.Version()[0:3] == "6.0":
                if pcbnew.IsCopperLayer(layer_info.id):  # Should probably do this on mask layers as well
                    plot_options.SetDrillMarksType(
                        2)  # NO_DRILL_SHAPE = 0, SMALL_DRILL_SHAPE = 1, FULL_DRILL_SHAPE  = 2
                else:
                    plot_options.SetDrillMarksType(
                        0)  # NO_DRILL_SHAPE = 0, SMALL_DRILL_SHAPE = 1, FULL_DRILL_SHAPE  = 2
            else:  # API changed in V6.99/V7
                try:
                    if pcbnew.IsCopperLayer(layer_info.id):  # Should probably do this on mask layers as well
                        plot_options.SetDrillMarksType(pcbnew.DRILL_MARKS_FULL_DRILL_SHAPE)
                    else:
                        plot_options.SetDrillMarksType(pcbnew.DRILL_MARKS_NO_DRILL_SHAPE)
                except:
                    msg_box(
                        "Unable to set Drill Marks type.\n\nIf you're using a V6.99 build from before Dec 07 2022 then update to a newer build.\n\n" + traceback.format_exc(),
                        'Error', wx.OK | wx.ICON_ERROR)
                    set_progress_status(100, "Failed to set Drill Marks type")

                    return False

            try:
                plot_options.SetPlotFrameRef(layer_info.with_frame)
                plot_options.SetNegative(layer_info.negative)
                plot_options.SetPlotValue(layer_info.footprint_value)
                plot_options.SetPlotReference(layer_info.reference_designator)
                plot_options.SetMirror(template.mirrored)
                plot_options.SetPlotViaOnMaskLayer(template.tented)
                if int(pcbnew.Version()[0:1]) >= 8:
                    plot_options.m_PDFFrontFPPropertyPopups = layer_info.front_popups
                    plot_options.m_PDFBackFPPropertyPopups = layer_info.back_popups
                plot_controller.SetLayer(layer_info.id)
                plot_controller.OpenPlotfile(layer_info.name, pcbnew.PLOT_FORMAT_PDF, template.name)
                plot_controller.PlotLayer()
            except:
                msg_box(traceback.format_exc(), 'Error', wx.OK | wx.ICON_ERROR)
                set_progress_status(100, "Failed to set plot_options or plot_controller")
                return False

        plot_controller.ClosePlot()

        filelist = []
        # Change color of pdf files
        for layer_info in template.settings:
            ln = layer_info.name.replace('.', '_')
            input_file = f"{base_filename}-{ln}.pdf"
            output_file = f"{base_filename}-{ln}-colored.pdf"
            if layer_info.has_color:
                progress += progress_step
                set_progress_status(progress, f"Coloring {layer_info.name} for template {template.name}")

                if not colorize_pdf(temp_dir, input_file, output_file, layer_info.color_rgb):
                    set_progress_status(100, f"Failed when coloring {layer_info.name} for template {template.name}")
                    return False

                filelist.append(output_file)
            else:
                filelist.append(input_file)

            if layer_info.with_frame:
                # the frame layer is scaled by 1.0, all others by `layer_scale`
                frame_file = filelist[-1]

        # Merge pdf files
        progress += progress_step
        set_progress_status(progress, f"Merging all layers of template {template.name}")

        assembly_file = f"{base_filename}_{template.name}.pdf"

        if not merge_pdf(temp_dir, filelist, output_dir, assembly_file, frame_file, layer_scale):
            set_progress_status(100, "Failed when merging all layers of template " + template.name)
            return False

        template_filelist.append(assembly_file)

    # Add all generated pdfs to one file
    progress += progress_step
    set_progress_status(progress, "Adding all templates to a single file")
    use_popups = layer_info.front_popups or layer_info.back_popups

    if not create_pdf_from_pages(output_dir, template_filelist, output_dir, final_assembly_file, use_popups):
        set_progress_status(100, "Failed when adding all templates to a single file")
        return False

    # Create SVG(s) if settings says so
    if create_svg:
        for template_file in template_filelist:
            template_pdf = fitz.open(os.path.join(output_dir, template_file))
            try:
                svg_image = template_pdf[0].get_svg_image()
                svg_filename = os.path.splitext(template_file)[0] + ".svg"
                with open(os.path.join(output_dir, svg_filename), "w") as file:
                    file.write(svg_image)
            except:
                msg_box("Failed to create SVG in {output_dir}\n\n" + traceback.format_exc(), 'Error',
                        wx.OK | wx.ICON_ERROR)
                set_progress_status(100, "Failed to create SVG(s)")
                return False
            template_pdf.close()

    # Delete temp files if setting says so
    if del_temp_files:
        try:
            shutil.rmtree(temp_dir)
        except:
            msg_box(f"del_temp_files failed\n\nOn dir {temp_dir}\n\n" + traceback.format_exc(), 'Error',
                    wx.OK | wx.ICON_ERROR)
            set_progress_status(100, "Failed to delete temp files")
            return False

    # Delete single page files if setting says so
    if del_single_page_files:
        for template_file in template_filelist:
            delete_file = os.path.join(output_dir, os.path.splitext(template_file)[0] + ".pdf")
            try:
                os.remove(delete_file)
            except:
                msg_box(f"del_single_page_files failed\n\nOn file {delete_file}\n\n" + traceback.format_exc(), 'Error',
                        wx.OK | wx.ICON_ERROR)
                set_progress_status(100, "Failed to delete single files")
                return False

    set_progress_status(100, "All done!")

    endmsg = "Assembly pdf created: " + os.path.abspath(os.path.join(output_dir, final_assembly_file))
    if not del_single_page_files:
        endmsg += "\n\nSingle page pdf files created:"
        for template_file in template_filelist:
            endmsg += "\n" + os.path.abspath(os.path.join(output_dir, os.path.splitext(template_file)[0] + ".pdf"))

    if create_svg:
        endmsg += "\n\nSVG files created:"
        for template_file in template_filelist:
            endmsg += "\n" + os.path.abspath(os.path.join(output_dir, os.path.splitext(template_file)[0] + ".svg"))

    msg_box(endmsg, 'All done!', wx.OK)
    return True


def cli(board_filepath: str, configfile: str, **kwargs) -> bool:
    import persistence

    board = pcbnew.LoadBoard(board_filepath)
    config = persistence.Persistence(configfile)
    config_vars = config.load()
    # note: cli parameters override config.ini values
    config_vars.update(kwargs)
    return plot_pdfs(board, **config_vars)
