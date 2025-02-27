import os
import shutil
import sys
import re
import wx
import wx.stc
import traceback
import logging
import json
import subprocess
import platform
from pathlib import Path

from pypdf import PdfReader, PdfWriter, PageObject, Transformation, generic

# Try to import PyMuPDF.
has_pymupdf = True
try:
    import pymupdf  # This imports PyMuPDF

except:
    try:
        import fitz as pymupdf  # This imports PyMuPDF using old name

    except:
        try:
            import fitz_old as pymupdf # This imports PyMuPDF using temporary old name

        except:
            has_pymupdf = False

# after pip uninstall PyMuPDF the import still works, but not `open()`
# check if it's possible to call pymupdf.open()
if has_pymupdf:
    try:
        pymupdf.open()
    except:
        has_pymupdf = False

# Try to import pdfCropMargins.
has_pdfcropmargins = True
try:
    from pdfCropMargins import crop  # This imports pdfCropMargins
except:
    has_pdfcropmargins = False

_logger = logging.getLogger(__name__)


def exception_msg(info: str, tb=True):
    msg = f"{info}\n\n" + (
        traceback.format_exc() if tb else '')
    try:
        wx.MessageBox(msg, 'Error', wx.OK | wx.ICON_ERROR)
    except wx._core.PyNoAppError:
        print(f'Error: {msg}', file=sys.stderr)


def io_file_error_msg(function: str, input_file: str, folder: str = '', more: str = '', tb=True):
    if(folder != ''):
        input_file = input_file + " in " + folder
        
    msg = f"{function} failed\nOn input file {input_file}\n\n{more}" + (
        traceback.format_exc() if tb else '')
    try:
        wx.MessageBox(msg, 'Error', wx.OK | wx.ICON_ERROR)
    except wx._core.PyNoAppError:
        print(f'Error: {msg}', file=sys.stderr)

def colorize_pdf_pymupdf_with_transparency(folder, input_file, output_file, color, transparency):
    opacity = 1-float(transparency / 100)

    doc = pymupdf.open(os.path.join(folder, input_file))
    page = doc[0]
    paths = page.get_drawings()  # extract existing drawings
    # this is a list of "paths", which can directly be drawn again using Shape
    # -------------------------------------------------------------------------
    #
    # define some output page with the same dimensions
    outpdf = pymupdf.open()
    outpage = outpdf.new_page(width=page.rect.width, height=page.rect.height)
    shape = outpage.new_shape()  # make a drawing canvas for the output page
    # --------------------------------------
    # loop through the paths and draw them
    # --------------------------------------
    for path in paths:
        #print("Object:")
        #print("fill_opacity:", type(path["fill_opacity"]))
        #print("stroke_opacity:", type(path["stroke_opacity"]))
        if(path["color"] == None):
            new_color = None
        else:
            new_color = color #tuple((float(0.0), float(1.0), float(1.0)))

        if(path["fill"] == None):
            new_fill = None
        else:
            new_fill = color #tuple((float(1.0), float(0.0), float(1.0)))

        if(path["fill_opacity"] == None):
            new_fill_opacity = None
        else:
            new_fill_opacity = opacity #float(0.5)

        if(path["stroke_opacity"] == None):
            new_stroke_opacity = None
        else:
            new_stroke_opacity = opacity #float(0.5)

        #pprint.pp(path)

        # ------------------------------------
        # draw each entry of the 'items' list
        # ------------------------------------
        for item in path["items"]:  # these are the draw commands
            if item[0] == "l":  # line
                shape.draw_line(item[1], item[2])
            elif item[0] == "re":  # rectangle
                shape.draw_rect(item[1])
            elif item[0] == "qu":  # quad
                shape.draw_quad(item[1])
            elif item[0] == "c":  # curve
                shape.draw_bezier(item[1], item[2], item[3], item[4])
            else:
                raise ValueError("unhandled drawing", item)
        # ------------------------------------------------------
        # all items are drawn, now apply the common properties
        # to finish the path
        # ------------------------------------------------------
        if new_fill_opacity:
            shape.finish(
                fill=new_fill,  # fill color
                color=new_color,  # line color
                dashes=path["dashes"],  # line dashing
                even_odd=path.get("even_odd", True),  # control color of overlaps
                closePath=path["closePath"],  # whether to connect last and first point
                #lineJoin=path["lineJoin"],  # how line joins should look like
                #lineCap=max(path["lineCap"]),  # how line ends should look like
                width=path["width"],  # line width
                #stroke_opacity=new_stroke_opacity,  # same value for both
                fill_opacity=new_fill_opacity,  # opacity parameters
                )

        if new_stroke_opacity:
            shape.finish(
                fill=new_fill,  # fill color
                color=new_color,  # line color
                dashes=path["dashes"],  # line dashing
                even_odd=path.get("even_odd", True),  # control color of overlaps
                closePath=path["closePath"],  # whether to connect last and first point
                #lineJoin=path["lineJoin"],  # how line joins should look like
                #lineCap=max(path["lineCap"]),  # how line ends should look like
                lineJoin=2,
                lineCap=1,
                width=path["width"],  # line width
                stroke_opacity=new_stroke_opacity,  # same value for both
                #fill_opacity=new_fill_opacity,  # opacity parameters
                )


    # all paths processed - commit the shape to its page
    shape.commit()

    page = outpdf[0]
    paths = page.get_drawings()  # extract existing drawings

    #for path in paths:
    #    print("Object:")
    #    pprint.pp(path)

    outpdf.save(os.path.join(folder, output_file), clean=True)

    return True

def create_blank_page(input_file_path: str, output_file_path: str):
    try:
        # Open input file and create a page with the same size
        pdf_reader = PdfReader(input_file_path)
        src_page: PageObject = pdf_reader.pages[0]
        page = PageObject.create_blank_page(width=src_page.mediabox.width, height=src_page.mediabox.height)

        # Create the output file with the page in it
        output = PdfWriter()
        output.add_page(page)
        with open(output_file_path, "wb") as output_stream:
            output.write(output_stream)

    except:
        io_file_error_msg(create_blank_page.__name__, input_file_path, output_file_path)
        return False

    return True

def get_page_size(file_path: str):
    try:
        # Open the file and check what size it is
        pdf_reader = PdfReader(file_path)
        src_page: PageObject = pdf_reader.pages[0]
        print("File:", str(file_path))
        page_width = src_page.mediabox.width
        print("Width:", str(page_width))
        page_height = src_page.mediabox.height
        print("Height:", str(page_height))

    except:
        io_file_error_msg(get_page_size.__name__, file_path)
        return False, float(0), float(0)

    return True, page_width, page_height

def merge_and_scale_pdf(input_folder: str, input_files: list, output_folder: str, output_file: str, frame_file: str,
                    scale_or_crop: dict, template_name: str):
    # I haven't found a way to scale the pdf and preserve the popup-menus.
    # For now, I'm taking the easy way out and handle the merging differently depending
    # on if scaling is used or not. At least the popup-menus are preserved when not using scaling.
    # https://github.com/pymupdf/PyMuPDF/discussions/2499
    # If popups aren't used, I'm using the with_scaling method to get rid of annotations
    if(scale_or_crop['scaling_method'] == '3'):
        # If scaling_method = 3, use a different method when using pymupdf
        output_file_path = os.path.join(output_folder, output_file)
        scaling_factor = float(scale_or_crop['scaling_factor'])
        return merge_pdf_pymupdf_with_scaling(input_folder, input_files, output_file_path, frame_file, template_name, scaling_factor)

    # If scaling_method is 1 or 2 the merged file is not the final file.
    if(scale_or_crop['scaling_method'] == '1' or scale_or_crop['scaling_method'] == '2'):
        merged_file_path = os.path.join(input_folder, "merged_" + output_file)
    else:
        merged_file_path = os.path.join(output_folder, output_file)

    if(scale_or_crop['scaling_method'] == '2' and frame_file != 'None'):
        # The frame layer should not be scaled, so don't merge this with the others.
        input_files.remove(frame_file)

    # Merge input_files to output_file
    return_value = merge_pdf_pymupdf(input_folder, input_files, merged_file_path, frame_file, template_name)
    if not return_value:
        return False

    # If scaling_method is 1 or 2, the merged file shall be cropped
    if(scale_or_crop['scaling_method'] == '1'):
        whitespace = scale_or_crop['crop_whitespace']
        cropped_file_path = os.path.join(output_folder, output_file)
    elif(scale_or_crop['scaling_method'] == '2'):
        whitespace = scale_or_crop['scale_whitespace']
        cropped_file = "cropped_" + output_file
        cropped_file_path = os.path.join(input_folder, cropped_file)

    if(scale_or_crop['scaling_method'] == '1' or scale_or_crop['scaling_method'] == '2'):
        # Crop the file
        output_doc_pathname, exit_code, stdout_str, stderr_str = crop(
                             ["-p", "0", "-a", "-" + whitespace, "-t", "250", "-A", "-o", cropped_file_path, merged_file_path],
                             string_io=True, quiet=False)

        if(exit_code):
            exception_msg("Failed to crop file.\npdfCropMargins exitcode was: " + str(exit_code) + "\n\nstdout_str: " + str(stdout_str) + "\n\nstderr_str: " + str(stderr_str))
            return False

    if(scale_or_crop['scaling_method'] == '2'):
        # If no frame layer is selected, create a blank file with same size as the first original file
        if(frame_file == 'None'):
            first_file = input_files[0]
            frame_file = "blank_file.pdf"
            if not create_blank_page(os.path.join(input_folder, first_file), os.path.join(input_folder, frame_file)):
                return False

        # Scale the cropped file.
        scaled_file_path = os.path.join(output_folder, output_file)

        new_file_list = [cropped_file, frame_file]
        return merge_pdf_pymupdf_with_scaling(input_folder, new_file_list, scaled_file_path, frame_file, template_name, 1.0)
            
    return True

def merge_pdf_pymupdf(input_folder: str, input_files: list, output_file_path: str, frame_file: str, template_name: str):
    try:
        output = None
        for filename in reversed(input_files):
            try:
                if output is None:
                    output = pymupdf.open(os.path.join(input_folder, filename))
                else:
                    # using "with" to force RAII and avoid another "for" closing files
                    with pymupdf.open(os.path.join(input_folder, filename)) as src:
                        output[0].show_pdf_page(src[0].rect,  # select output rect
                                                src,  # input document
                                                overlay=False)
            except Exception:
                io_file_error_msg(merge_pdf_pymupdf.__name__, filename, input_folder)
                return False

        # Set correct page name in the table of contents (pdf outline)

        # toc = output.get_toc(simple=False)
        # print("Toc: ", toc)
        # toc[0][1] = template_name
        # output.set_toc(toc)
        # The above code doesn't work for the toc (outlines) of a pdf created by Kicad.
        # It correctly sets the name of the first page, but when clicking on a footprint it no longer zooms to that footprint

        # Lets do it the low-level way instead:
        try:
            xref = output.pdf_catalog()  # get xref of the /Catalog

            # print(output.xref_object(xref))  # print object definition
            # for key in output.xref_get_keys(xref): # iterate over all keys and print the keys and values
            #     print("%s = %s" % (key, output.xref_get_key(xref, key)))

            # The loop will output something like this:
            # Type = ('name', '/Catalog')
            # Pages = ('xref', '1 0 R')
            # Version = ('name', '/1.5')
            # PageMode = ('name', '/UseOutlines')
            # Outlines = ('xref', '20 0 R')
            # Names = ('xref', '4 0 R')
            # PageLayout = ('name', '/SinglePage')

            key_value = output.xref_get_key(xref, "Outlines") # Get the value of the 'Outlines' key
            xref = int(key_value[1].split(' ')[0]) # Set xref to the xref found in the value of the 'Outlines' key

            # The object now referenced by xref looks something like this:
            # Type = ('name', '/Outlines')
            # Count = ('int', '3')
            # First = ('xref', '11 0 R')
            # Last = ('xref', '11 0 R')

            key_value = output.xref_get_key(xref, "First") # Get the value of the 'First' key
            xref = int(key_value[1].split(' ')[0]) # Set xref to the xref found in the value of the 'First' key

            # The object now referenced by xref looks something like this:
            # Title = ('string', 'Page 1')
            # Parent = ('xref', '20 0 R')
            # Count = ('int', '-1')
            # First = ('xref', '12 0 R')
            # Last = ('xref', '12 0 R')
            # A = ('xref', '10 0 R')

            if output.xref_get_key(xref, "Title")[0] == 'string': # Check if the 'Title' key exists
                page_name = "(" + template_name + ")"
                output.xref_set_key(xref, "Title", page_name)

        except Exception:
            # If the first page was colored using colorize_pdf_pymupdf_with_transparency, then the table of
            # contents (pdf outline) has been lost.
            # Lets create a new toc with the correct page name.
            toc = [[1, template_name, 1]]
            output.set_toc(toc)

        output.save(output_file_path) # , garbage=2
        output.close()

    except Exception:
        io_file_error_msg(merge_pdf_pymupdf.__name__, output_file_path)
        return False

    return True

def merge_pdf_pymupdf_with_scaling(input_folder: str, input_files: list, output_file_path: str, frame_file: str,
                    template_name: str, layer_scale: float):
    try:
        output = pymupdf.open()
        page = None
        for filename in reversed(input_files):
            try:
                # using "with" to force RAII and avoid another "for" closing files
                with pymupdf.open(os.path.join(input_folder, filename)) as src:
                    if page is None:
                        page = output.new_page(width=src[0].rect.width * layer_scale,
                                               height=src[0].rect.height * layer_scale)
                        cropbox = pymupdf.Rect((page.rect.width - src[0].rect.width) / 2,
                                            (page.rect.height - src[0].rect.height) / 2,
                                            (page.rect.width + src[0].rect.width) / 2,
                                            (page.rect.height + src[0].rect.height) / 2)

                    pos = cropbox if frame_file == filename else page.rect
                    try:
                        page.show_pdf_page(pos,  # select output rect
                                           src,  # input document
                                           overlay=False)
                    except ValueError:
                        # This happens if the page is blank. Which it is if we've created a blank frame file.
                        pass

            except Exception:
                io_file_error_msg(merge_pdf_pymupdf_with_scaling.__name__, filename, input_folder)
                return False

        page.set_cropbox(cropbox)

        # Set correct page name in the table of contents (pdf outline)
        # When scaling is used, component references will not be retained
        toc = [[1, template_name, 1]]
        output.set_toc(toc)

        output.save(output_file_path)

    except Exception:
        io_file_error_msg(merge_pdf_pymupdf_with_scaling.__name__, output_file_path)
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

        # If popup menus are used, add the needed javascript. Pypdf and PyMuPdf removes this in most operations.
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
    std_transparency = 0

    def __init__(self, layer_name: str, template: dict, frame_layer: str, popups: str):
        self.name: str = layer_name
        self.color_hex: str = template["layers"].get(layer_name, self.std_color)  # color as '#rrggbb' hex string
        self.with_frame: bool = layer_name == frame_layer

        try:
            self.transparency_value = int(template["layers_transparency"][layer_name])  # transparency as '0'-'100' string
        except KeyError:
            self.transparency_value = 0

        try:
            # Bool specifying if layer is negative
            self.negative = template["layers_negative"][layer_name] == "true"
        except KeyError:
            self.negative = False

        try:
            # Bool specifying if footprint values shall be plotted
            self.footprint_value = template["layers_footprint_values"][layer_name] == "true"
        except KeyError:
            self.footprint_value = True

        try:
            # Bool specifying if footprint references shall be plotted
            self.reference_designator = template["layers_reference_designators"][layer_name] == "true"
        except KeyError:
            self.reference_designator = True

        # Check the popup settings.
        self.front_popups = True
        self.back_popups = True
        if popups == "Front Layer":
            self.back_popups = False
        elif popups == "Back Layer":
            self.front_popups = False
        elif popups == "None":
            self.front_popups = False
            self.back_popups = False

    @property
    def has_color(self) -> bool:
        """Checks if the layer color is not the standard color (=black)."""
        return self.color_hex != self.std_color

    @property
    def has_transparency(self) -> bool:
        """Checks if the layer transparency is not the standard value (=0%)."""
        return self.transparency_value != self.std_transparency

    @property
    def color_rgb(self) -> tuple[float, float, float]:
        """Return (red, green, blue) in float between 0-1."""
        value = self.color_hex.lstrip('#')
        lv = len(value)
        rgb = tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))
        rgb = (rgb[0] / 255, rgb[1] / 255, rgb[2] / 255)
        return rgb

    @property
    def color_rgb_int(self) -> tuple[int, int, int]:
        """Return (red, green, blue) in float between 0-1."""
        value = self.color_hex.lstrip('#')
        lv = len(value)
        rgb = tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))
        rgb = (rgb[0], rgb[1], rgb[2])
        return rgb

    @property
    def transparency(self) -> int:
        """Return 0-100 in str."""
        value = self.transparency_value
        return value

    def __repr__(self):
        var_str = ', '.join(f"{key}: {value}" for key, value in vars(self).items())
        return f'{self.__class__.__name__}:{{ {var_str} }}'


class Template:
    def __init__(self, name: str, template: dict):
        self.name: str = name  # the template name
        self.mirrored: bool = template.get("mirrored", False)  # template is mirrored or not
        self.tented: bool = template.get("tented", False)  # template is tented or not
        self.scale_or_crop: dict = { "scaling_method": template.get("scaling_method", "0"),
                                     "crop_whitespace": template.get("crop_whitespace", "10"),
                                     "scale_whitespace": template.get("scale_whitespace", "30"),
                                     "scaling_factor": template.get("scaling_factor", "3.0") }

        self.frame_layer: str = template.get("frame", "")  # layer name of the frame layer
        self.drawing_sheet: str = template.get("drawing_sheet", "")  # 'boarf2pdf/project/file'
        self.drawing_sheet_file: str = template.get("drawing_sheet_file", "")  # path to drawing sheet if drawing_sheet = 'file'
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
                    layer_info = LayerInfo(el, template, self.frame_layer, layer_popups)
                    self.settings.insert(0, layer_info)

    @property
    def steps(self) -> int:
        """number of process steps for this template"""
        return len(self.settings) + sum([layer.has_color for layer in self.settings])

    @property
    def steps_without_coloring(self) -> int:
        """number of process steps for this template"""
        return len(self.settings)

    @property
    def has_transparency(self) -> bool:
        for layer_info in self.settings:
            if layer_info.has_transparency:
                return True
        return False

    def __repr__(self):
        var_str = ', '.join(f"{key}: {value}" for key, value in vars(self).items())
        return f'{self.__class__.__name__}:{{ {var_str} }}'

def create_kicad_color_template(template_settings, template_file_path: str, layers_dict: dict) -> bool:
    layer_color_name = {
        "F.Cu" : "f",
        "In1.Cu" : "in1",
        "In2.Cu" : "in2",
        "In3.Cu" : "in3",
        "In4.Cu" : "in4",
        "In5.Cu" : "in5",
        "In6.Cu" : "in6",
        "In7.Cu" : "in7",
        "In8.Cu" : "in8",
        "In9.Cu" : "in9",
        "In10.Cu" : "in10",
        "In11.Cu" : "in11",
        "In12.Cu" : "in12",
        "In13.Cu" : "in13",
        "In14.Cu" : "in14",
        "In15.Cu" : "in15",
        "In16.Cu" : "in16",
        "In17.Cu" : "in17",
        "In18.Cu" : "in18",
        "In19.Cu" : "in19",
        "In20.Cu" : "in20",
        "In21.Cu" : "in21",
        "In22.Cu" : "in22",
        "In23.Cu" : "in23",
        "In24.Cu" : "in24",
        "In25.Cu" : "in25",
        "In26.Cu" : "in26",
        "In27.Cu" : "in27",
        "In28.Cu" : "in28",
        "In29.Cu" : "in29",
        "In30.Cu" : "in30",
        "B.Cu" : "b",
        "B.Adhes" : "b_adhes",
        "F.Adhes" : "f_adhes",
        "B.Paste" : "b_paste",
        "F.Paste" : "f_paste",
        "B.SilkS" : "b_silks",
        "F.SilkS" : "f_silks",
        "B.Mask" : "b_mask",
        "F.Mask" : "f_mask",
        "Dwgs.User" : "dwgs_user",
        "Cmts.User" : "cmts_user",
        "Eco1.User" : "eco1_user",
        "Eco2.User" : "eco2_user",
        "Edge.Cuts" : "edge_cuts",
        "Margin" : "margin",
        "B.CrtYd" : "b_crtyd",
        "F.CrtYd" : "f_crtyd",
        "B.Fab" : "b_fab",
        "F.Fab" : "f_fab",
        "User.1" : "user_1",
        "User.2" : "user_2",
        "User.3" : "user_3",
        "User.4" : "user_4",
        "User.5" : "user_5",
        "User.6" : "user_6",
        "User.7" : "user_7",
        "User.8" : "user_8",
        "User.9" : "user_9",
        "Rescue" : ""
    }

    copper_dict = {}
    template_dict = {}
    for layer_info in template_settings:
        color_string = "rgb(" + str(layer_info.color_rgb_int[0]) + ", " + str(layer_info.color_rgb_int[1]) + ", " + str(layer_info.color_rgb_int[2]) + ")"
        #if pcbnew.IsCopperLayer(layer_info.id):
        if layers_dict[layer_info.name]['is_copper_layer']:
            copper_dict[layer_color_name[layer_info.name]] = color_string
        else:
            template_dict[layer_color_name[layer_info.name]] = color_string
        
        # If this is the frame layer then set "worksheet" to this color as well.
        if layer_info.with_frame:
            template_dict["worksheet"] = color_string
        
    template_dict["copper"] = copper_dict
    color_template = { "board" : template_dict, "meta" : { "name" : "Board2Pdf-Template", "version" : 5 } }
    
    # Check if we're able to write to the output file.
    try:
        with open(template_file_path, 'w') as f:
            json.dump(color_template, f, ensure_ascii=True, indent=4, sort_keys=True)
    except:
        exception_msg("The color template file is not writeable. Perhaps it's open in another application?\n\n"
                + template_file_path, 'Error', wx.OK | wx.ICON_ERROR)
        return False
    
    return True

def create_kicad_jobset(template: dict, layers_dict: dict, template_dir: str, board2pdf_path: str):
    # Template:{ name: Black And White TOP, mirrored: False, tented: False, scale_or_crop: {'scaling_method': '0', 'crop_whitespace': '10', 'scale_whitespace': '30', 'scaling_factor': '3.0'}, settings: [
    #  LayerInfo:{ name: F.Cu, color_hex: #F0F0F0, with_frame: False, transparency_value: 0, negative: False, footprint_value: True, reference_designator: True, front_popups: False, back_popups: False },
    #  LayerInfo:{ name: F.Paste, color_hex: #C4C4C4, with_frame: False, transparency_value: 0, negative: False, footprint_value: True, reference_designator: True, front_popups: False, back_popups: False },
    # ]
    
    jobs_list = []
    for layer_info in template.settings:
        # https://gitlab.com/kicad/code/kicad/-/blob/master/common/jobs/job_export_pcb_pdf.cpp
        settings_dict = {}
        settings_dict["back_fp_property_popups"] = layer_info.back_popups
        settings_dict["black_and_white"] = False
        settings_dict["color_theme"] = "Board2Pdf-Template"
        settings_dict["description"] = ""

        if layer_info.with_frame:
            if template.drawing_sheet == 'file':
                settings_dict["drawing_sheet"] = template.drawing_sheet_file
            elif template.drawing_sheet == 'project':
                settings_dict["drawing_sheet"] = ""
            else:
                settings_dict["drawing_sheet"] = os.path.join(board2pdf_path, "drawing_sheet", "template.kicad_wks")
        else:
            settings_dict["drawing_sheet"] = ""

        if layers_dict[layer_info.name]['is_copper_layer']:
            settings_dict["drill_shape"] = "full"
        else:
            settings_dict["drill_shape"] = "none" # "full/small/none"

        settings_dict["front_fp_property_popups"] = layer_info.front_popups
        settings_dict["layers"] = [layer_info.name]
        settings_dict["layers_to_include_on_all_layers"] = []
        settings_dict["mirror"] = template.mirrored
        settings_dict["negative"] = layer_info.negative
        settings_dict["output_filename"] = layer_info.name
        settings_dict["pdf_gen_mode"] = "one-page-per-layer-one-file" # "all-layers-separate-files/all-layers-one-file"
        settings_dict["pdf_metadata"] = True
        settings_dict["plot_drawing_sheet"] = layer_info.with_frame
        settings_dict["plot_footprint_values"] = layer_info.footprint_value
        settings_dict["plot_pad_numbers"] = False
        settings_dict["plot_ref_des"] = layer_info.reference_designator
        settings_dict["single_document"] = False
        settings_dict["sketch_pads_on_fab_layers"] = False
        settings_dict["subtract_solder_mask_from_silk"] = False
        settings_dict["use_drill_origin"] = False

        job_dict = {}
        job_dict["description"] = "Plot " + layer_info.name
        job_dict["id"] = os.urandom(4).hex()+"-"+os.urandom(2).hex()+"-"+os.urandom(2).hex()+"-"+os.urandom(2).hex()+"-"+os.urandom(6).hex()
        job_dict["settings"] = settings_dict
        job_dict["type"] = "pcb_export_pdf"

        jobs_list.append(job_dict)

    outputs_dict = {}
    outputs_dict["description"] = "Generate " + template.name
    outputs_dict["id"] = os.urandom(4).hex()+"-"+os.urandom(2).hex()+"-"+os.urandom(2).hex()+"-"+os.urandom(2).hex()+"-"+os.urandom(6).hex()
    outputs_dict["only"] = []
    outputs_dict["settings"] = { "output_path": "." }
    outputs_dict["type"] = "folder"

    jobsets_dict = {}
    jobsets_dict["jobs"] = jobs_list
    jobsets_dict["meta"] = { "version": 1 }
    jobsets_dict["outputs"] = [ outputs_dict ]

    # Create the path for the jobset file
    jobset_file_path = os.path.join(template_dir, "jobset.kicad_jobset")

    # Check if we're able to write to the output file.
    try:
        with open(jobset_file_path, 'w') as f:
            json.dump(jobsets_dict, f, ensure_ascii=True, indent=2, sort_keys=False)
    except:
        exception_msg("The jobsets file is not writeable. Perhaps it's open in another application?\n\n"
                + jobset_file_path, 'Error', wx.OK | wx.ICON_ERROR)
        return False
    
    return True

def set_variables_in_project_file(pro_file_path: str, template_name: str, page: int, total_pages: int) -> bool:
    try:
        # Open the file and read the JSON data
        with open(pro_file_path, 'r') as file:
            data = json.load(file)

        # Check if 'text_variables' exists, if not, create it
        if 'text_variables' not in data:
            data['text_variables'] = {}

        # Update variables
        data['text_variables']['B2P_TEMPLATENAME'] = template_name
        data['text_variables']['B2P_PAGE'] = str(page)
        data['text_variables']['B2P_TOTAL'] = str(total_pages)

        # Write the updated JSON back to the file
        with open(pro_file_path, 'w') as file:
            json.dump(data, file, indent=2)

    except FileNotFoundError:
        exception_msg(f"Error when updating variables: The file {pro_file_path} does not exist.", 'Error', wx.OK | wx.ICON_ERROR)
        return False
    except json.JSONDecodeError:
        exception_msg(f"Error when updating variables: Failed to decode JSON from the file.", 'Error', wx.OK | wx.ICON_ERROR)
        return False
    except Exception as e:
        exception_msg(f"Error when updating variables: An unexpected error occurred: {e}", 'Error', wx.OK | wx.ICON_ERROR)
        return False

    return True

class DebugDialog(wx.Dialog):
    def __init__(self, parent, title, text):
        super(DebugDialog, self).__init__(parent, title=title, size=(520, 550))
        pnl = wx.Panel(self)
        #vbox = wx.BoxSizer(wx.VERTICAL)

        sb = wx.StaticBox(pnl)
        sbs = wx.StaticBoxSizer(sb, orient=wx.VERTICAL)
        m_styledTextCtrl = wx.stc.StyledTextCtrl(pnl, size=wx.Size(500, 500))
        sbs.Add(m_styledTextCtrl)
        m_styledTextCtrl.SetText(text)

    def OnClose(self, e):
        self.Destroy()

def plot_pdfs(project_path: str, pcb_file_path: str, base_filename: str, temp_dir: str, dlg=None, **kwargs) -> bool:
    output_path: str = kwargs.pop('output_path', 'plot')
    board2pdf_path: str = kwargs.pop('board2pdf_path', '')
    layers_dict: dict = kwargs.pop('layers_dict', {})
    templates: list = kwargs.pop('templates', [])
    enabled_templates: list = kwargs.pop('enabled_templates', [])
    create_svg: bool = kwargs.pop('create_svg', False)
    del_temp_files: bool = kwargs.pop('del_temp_files', True)
    del_single_page_files: bool = kwargs.pop('del_single_page_files', True)
    asy_file_extension = kwargs.pop('assembly_file_extension', '__Assembly')

    if dlg is None:
        def set_progress_status(progress: int, status: str):
            print(f'{int(progress):3d}%: {status}')

        def msg_box(text, caption, flags):
            print(f"{caption}: {text}")

    elif isinstance(dlg, wx.Panel):
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

    #if (pymupdf_color or pymupdf_merge or create_svg) and not has_pymupdf:
    #    msg_box(
    #        "PyMuPdf wasn't loaded.\n\nIt must be installed for it to be used for coloring, for merging and for creating SVGs.\n\nMore information under Install dependencies in the Wiki at board2pdf.dennevi.com",
    #        'Error', wx.OK | wx.ICON_ERROR)
    #    set_progress_status(100, "Failed to load PyMuPDF.")
    #    return False

    if not has_pdfcropmargins:
        # Check if any of the enabled templates uses pdfCropMargins
        use_pdfcropmargins = False
        for t in enabled_templates:
            if t in templates:
                if "scaling_method" in templates[t]:
                    if templates[t]["scaling_method"] == "1" or templates[t]["scaling_method"] == "2":
                        use_pdfcropmargins = True
        if use_pdfcropmargins:
            msg_box(
                "pdfCropMargins wasn't loaded.\n\nSome of the Scale and Crop settings requires pdfCropMargins to be installed.\n\nMore information under Install dependencies in the Wiki at board2pdf.dennevi.com",
                'Error', wx.OK | wx.ICON_ERROR)
            set_progress_status(100, "Failed to load pdfCropMargins.")
            return False

    os.chdir(project_path)
    output_dir = os.path.abspath(os.path.expanduser(os.path.expandvars(output_path)))

    progress = 5
    set_progress_status(progress, "Started plotting...")

    final_assembly_file = base_filename + asy_file_extension + ".pdf"
    final_assembly_file_with_path = os.path.abspath(os.path.join(output_dir, final_assembly_file))

    if "assembly_file_output" in kwargs:
        final_assembly_file = kwargs.pop('assembly_file_output')
        final_assembly_file_with_path = str(Path(final_assembly_file_with_path).absolute())


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

    steps: int = 2  # number of process steps
    templates_list: list[Template] = []
    for t in enabled_templates:
        # {  "Test-template": {"mirrored": true, "enabled_layers": "B.Fab,B.Mask,Edge.Cuts,F.Adhesive", "frame": "In4.Cu",
        #          "layers": {"B.Fab": "#000012", "B.Mask": "#000045"}}  }
        if t in templates:
            temp = Template(t, templates[t])
            _logger.debug(temp)

            # Count how many steps it will take to complete this operation
            steps += 1 + temp.steps_without_coloring

            # Build list of templates that shall be used
            templates_list.append(temp)
    progress_step: float = 95 / steps
    
    if platform.system() == 'Windows':
        template_file_path = os.path.join(os.getenv('APPDATA'), "kicad", "9.0", "colors", "Board2Pdf-Template.json")
    elif platform.system() == 'Linux':
        template_file_path = os.path.join(os.getenv('HOME'), ".config", "kicad", "9.0", "colors", "Board2Pdf-Template.json")
    else: # MacOS
        template_file_path = os.path.join(os.getenv('HOME'), "Library", "Preferences", "kicad", "9.0", "colors", "Board2Pdf-Template.json")

    use_popups = False
    template_filelist = []
    
    # Iterate over the templates
    for page_count, template in enumerate(templates_list):            
        if not create_kicad_color_template(template.settings, template_file_path, layers_dict):
            set_progress_status(100, f"Failed to create color template for template {template.name}")
            return False
        
        # Create jobset file
        template_dir = os.path.join(temp_dir, template.name.replace(' ', '_'))
        os.makedirs(template_dir, exist_ok=True)
        create_kicad_jobset(template, layers_dict, template_dir, board2pdf_path)

        # Set variables in kicad project file
        pro_file_path = os.path.join(Path(pcb_file_path).parent.resolve(), base_filename+".kicad_pro")
        set_variables_in_project_file(pro_file_path, template.name, page_count+1, len(templates_list))

        # Plot layers to pdf files
        os.chdir(template_dir)
        print("template_dir:", template_dir)
        cli_command = [r'C:\Program Files\KiCad\9.0\bin\kicad-cli.exe', "jobset", "run", "-f", "jobset.kicad_jobset", pcb_file_path]
        result = subprocess.run(cli_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        return_code = result.returncode
        os.chdir(project_path)

        if return_code != 0:
            # Create text to show in DebugDialog
            cmd_output = "Executed command: " + " ".join(str(x) for x in cli_command) + "\n\n" + result.stdout + "\n\n" + result.stderr + "\n\nReturn code: " + str(return_code)

            # Remove ANSI escape sequences
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            cmd_output = ansi_escape.sub('', cmd_output)

            # Open DebugDialog
            cdDialog = DebugDialog(None, title='Failed to plot!', text=cmd_output)
            cdDialog.ShowModal()
            cdDialog.Destroy()
            return False

        #    for layer_info in template.settings:
        #        progress += progress_step
        #        set_progress_status(progress, f"Plotting {layer_info.name} for template {template.name}")

        # Build list of plotted pdfs
        filelist = []
        frame_file = 'None'
        template_use_popups = False
        for layer_info in template.settings:
            # Add the file to the list
            filename = os.path.join(layer_info.name, base_filename+".pdf")
            filelist.append(filename)

            # If this layer is plotted with frame, set the frame_file variable to this filename.
            if layer_info.with_frame:
                frame_file = filename

            # Set template_use_popups to True if any layer has popups
            template_use_popups = template_use_popups or layer_info.front_popups or layer_info.back_popups

        # Merge pdf files
        progress += progress_step
        set_progress_status(progress, f"Merging all layers of template {template.name}")

        assembly_file = f"{base_filename}_{template.name}.pdf"
        assembly_file = assembly_file.replace(' ', '_')

        if not merge_and_scale_pdf(template_dir, filelist, output_dir, assembly_file, frame_file, template.scale_or_crop, template.name):
            set_progress_status(100, "Failed when merging all layers of template " + template.name)
            return False

        template_filelist.append(assembly_file)
        # Set use_popups to True if any template has popups
        use_popups = use_popups or template_use_popups

    # Delete Board2Pdf color template
    try:
        os.remove(template_file_path)
    except:
        msg_box(f"Delete color template file failed\n\n" + traceback.format_exc(), 'Error',
                wx.OK | wx.ICON_ERROR)
        set_progress_status(100, "Failed to delete color template file")
        return False

    # Add all generated pdfs to one file
    progress += progress_step
    set_progress_status(progress, "Adding all templates to a single file")

    if not create_pdf_from_pages(output_dir, template_filelist, output_dir, final_assembly_file, use_popups):
        set_progress_status(100, "Failed when adding all templates to a single file")
        return False

    # Create SVG(s) if settings says so
    if create_svg:
        for template_file in template_filelist:
            template_pdf = pymupdf.open(os.path.join(output_dir, template_file))
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

