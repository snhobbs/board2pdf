import os
import shutil
import sys
import pcbnew
import wx
import re
import traceback
import tempfile
import logging
import json
from pathlib import Path

try:
    from .pypdf import PdfReader, PdfWriter, PageObject, Transformation, generic
except ImportError:
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


def colorize_pdf_pymupdf(folder, input_file, output_file, color, transparency):
    # If transparency is non zero, run colorize_pdf_pymupdf_with_transparency instead.
    if not transparency == 0:
        return colorize_pdf_pymupdf_with_transparency(folder, input_file, output_file, color, transparency)

    try:
        with pymupdf.open(os.path.join(folder, input_file)) as doc:
            xref_number = doc[0].get_contents()
            stream_bytes = doc.xref_stream(xref_number[0])
            new_color = ''.join([f'{c:.3g} ' for c in color])
            _logger.debug(f'{new_color=}')
            stream_bytes = re.sub(br'(\s)0 0 0 (RG|rg)', bytes(fr'\g<1>{new_color}\g<2>', 'ascii'), stream_bytes)

            doc.update_stream(xref_number[0], stream_bytes)
            doc.save(os.path.join(folder, output_file), clean=True)

    except RuntimeError as e:
        if "invalid key in dict" in str(e):
            io_file_error_msg(colorize_pdf_pymupdf.__name__, input_file, folder,
                              "This error can be due to PyMuPdf not being able to handle pdfs created by KiCad 7.0.1 due to a bug in KiCad 7.0.1. Upgrade KiCad or switch to pypdf instead.\n\n")
        return False

    except:
        io_file_error_msg(colorize_pdf_pymupdf.__name__, input_file, folder)
        return False

    return True


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


def colorize_pdf_pypdf(folder, input_file, output_file, color, transparency):
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
                    scale_or_crop: dict, template_name: str, pymupdf_merge: bool):
    # I haven't found a way to scale the pdf and preserve the popup-menus.
    # For now, I'm taking the easy way out and handle the merging differently depending
    # on if scaling is used or not. At least the popup-menus are preserved when not using scaling.
    # https://github.com/pymupdf/PyMuPDF/discussions/2499
    # If popups aren't used, I'm using the with_scaling method to get rid of annotations
    if(scale_or_crop['scaling_method'] == '3'):
        # If scaling_method = 3, use a different method when using pymupdf
        output_file_path = os.path.join(output_folder, output_file)
        scaling_factor = float(scale_or_crop['scaling_factor'])
        if(pymupdf_merge):
            return merge_pdf_pymupdf_with_scaling(input_folder, input_files, output_file_path, frame_file, template_name, scaling_factor)
        else:
            return merge_pdf_pypdf(input_folder, input_files, output_file_path, frame_file, template_name, scaling_factor)

    # If scaling_method is 1 or 2 the merged file is not the final file.
    if(scale_or_crop['scaling_method'] == '1' or scale_or_crop['scaling_method'] == '2'):
        merged_file_path = os.path.join(input_folder, "merged_" + output_file)
    else:
        merged_file_path = os.path.join(output_folder, output_file)

    if(scale_or_crop['scaling_method'] == '2' and frame_file != 'None'):
        # The frame layer should not be scaled, so don't merge this with the others.
        input_files.remove(frame_file)

    # Merge input_files to output_file
    if(pymupdf_merge):
        return_value = merge_pdf_pymupdf(input_folder, input_files, merged_file_path, frame_file, template_name)
    else:
        return_value = merge_pdf_pypdf(input_folder, input_files, merged_file_path, frame_file, template_name, 1.0)
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

        if(pymupdf_merge):
            new_file_list = [cropped_file, frame_file]
            return merge_pdf_pymupdf_with_scaling(input_folder, new_file_list, scaled_file_path, frame_file, template_name, 1.0)
        else:
            return_value, frame_file_width, frame_file_height = get_page_size(os.path.join(input_folder, frame_file))
            if not return_value:
                return False
            
            resized_cropped_file = "resized_" + cropped_file
            resized_cropped_file_path = os.path.join(input_folder, resized_cropped_file)
            
            resize_page_pypdf(cropped_file_path, resized_cropped_file_path, frame_file_width, frame_file_height)
            
            new_file_list = [frame_file, resized_cropped_file]
            return merge_pdf_pypdf(input_folder, new_file_list, scaled_file_path, frame_file, template_name, 1.0)
            
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

def merge_pdf_pypdf(input_folder: str, input_files: list, output_file_path: str, frame_file: str,
                    template_name: str, layer_scale: float):
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
        output.add_outline_item(title=template_name, page_number=0)
        with open(output_file_path, "wb") as output_stream:
            output.write(output_stream)

    except:
        io_file_error_msg(merge_pdf_pypdf.__name__, output_file_path)
        return False

    return True

def resize_page_pypdf(input_file_path: str, output_file_path: str, page_width: float, page_height: float):
    reader = PdfReader(input_file_path)
    page = reader.pages[0]
    writer = PdfWriter()

    w = float(page.mediabox.width)
    h = float(page.mediabox.height)
    scale_factor = min(page_height/h, page_width/w)

    # Calculate the final amount of blank space in width and height
    space_w = page_width - w*scale_factor
    space_h = page_height - h*scale_factor

    # Calculate offsets to center the scaled result
    x_offset = -page.cropbox.left*scale_factor + space_w/2
    y_offset = -page.cropbox.bottom*scale_factor + space_h/2

    transform = Transformation().scale(scale_factor).translate(x_offset, y_offset)

    page.add_transformation(transform)

    page.cropbox = generic.RectangleObject((0, 0, page_width, page_height))
    page.mediabox = generic.RectangleObject((0, 0, page_width, page_height))

    writer.add_page(page)
    writer.write(output_file_path)

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

    def __init__(self, layer_names: dict, layer_name: str, template: dict, frame_layer: str, popups: str):
        self.name: str = layer_name
        self.id: int = layer_names[layer_name]
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
    def __init__(self, name: str, template: dict, layer_names: dict):
        self.name: str = name  # the template name
        self.mirrored: bool = template.get("mirrored", False)  # template is mirrored or not
        self.tented: bool = template.get("tented", False)  # template is tented or not
        self.scale_or_crop: dict = { "scaling_method": template.get("scaling_method", "0"),
                                     "crop_whitespace": template.get("crop_whitespace", "10"),
                                     "scale_whitespace": template.get("scale_whitespace", "30"),
                                     "scaling_factor": template.get("scaling_factor", "3.0") }

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

def create_kicad_color_template(template_settings, template_file_path: str) -> bool:
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
        "B.Adhesive" : "b_adhes",
        "F.Adhesive" : "f_adhes",
        "B.Paste" : "b_paste",
        "F.Paste" : "f_paste",
        "B.Silkscreen" : "b_silks",
        "F.Silkscreen" : "f_silks",
        "B.Mask" : "b_mask",
        "F.Mask" : "f_mask",
        "User.Drawings" : "dwgs_user",
        "User.Comments" : "cmts_user",
        "User.Eco1" : "eco1_user",
        "User.Eco2" : "eco2_user",
        "Edge.Cuts" : "edge_cuts",
        "Margin" : "margin",
        "B.Courtyard" : "b_crtyd",
        "F.Courtyard" : "f_crtyd",
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
    layers_dict = {}
    for layer_info in template_settings:
        color_string = "rgb(" + str(layer_info.color_rgb_int[0]) + ", " + str(layer_info.color_rgb_int[1]) + ", " + str(layer_info.color_rgb_int[2]) + ")"
        if pcbnew.IsCopperLayer(layer_info.id):
            copper_dict[layer_color_name[layer_info.name]] = color_string
        else:
            layers_dict[layer_color_name[layer_info.name]] = color_string
        
        # If this is the frame layer then set "worksheet" to this color as well.
        # This doesn't work in KiCad 7.0. Was fixed in KiCad 8.0. See https://gitlab.com/kicad/code/kicad/-/commit/077159ac130d276af043695afbf186f0565035e9
        if layer_info.with_frame:
            layers_dict["worksheet"] = color_string
        
    layers_dict["copper"] = copper_dict
    color_template = { "board" : layers_dict, "meta" : { "name" : "Board2Pdf Template", "version" : 5 } }
    
    with open(template_file_path, 'w') as f:
        json.dump(color_template, f, ensure_ascii=True, indent=4, sort_keys=True)
    
    return True

def plot_pdfs(board, dlg=None, **kwargs) -> bool:
    output_path: str = kwargs.pop('output_path', 'plot')
    templates: list = kwargs.pop('templates', [])
    enabled_templates: list = kwargs.pop('enabled_templates', [])
    create_svg: bool = kwargs.pop('create_svg', False)
    del_temp_files: bool = kwargs.pop('del_temp_files', True)
    del_single_page_files: bool = kwargs.pop('del_single_page_files', True)
    asy_file_extension = kwargs.pop('assembly_file_extension', '__Assembly')
    colorize_lib: str = kwargs.pop('colorize_lib', '')
    merge_lib: str = kwargs.pop('merge_lib', '')
    page_info: str = kwargs.pop('page_info', '')
    info_variable: str = kwargs.pop('info_variable', '0')

    if dlg is None:
        if(colorize_lib == 'kicad'):
            pymupdf_color = False
            kicad_color = True
        elif(colorize_lib == 'pymupdf' or colorize_lib == 'fitz'):
            pymupdf_color = True
            kicad_color = False
        else:
            pymupdf_color = False
            kicad_color = False

        pymupdf_merge = has_pymupdf and merge_lib != 'pypdf'

        def set_progress_status(progress: int, status: str):
            print(f'{int(progress):3d}%: {status}')

        def msg_box(text, caption, flags):
            print(f"{caption}: {text}")

    elif isinstance(dlg, wx.Panel):
        pymupdf_color = dlg.m_radio_pymupdf.GetValue()
        kicad_color = dlg.m_radio_kicad.GetValue()
        pymupdf_merge = dlg.m_radio_merge_pymupdf.GetValue()

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

    if (pymupdf_color or pymupdf_merge or create_svg) and not has_pymupdf:
        msg_box(
            "PyMuPdf wasn't loaded.\n\nIt must be installed for it to be used for coloring, for merging and for creating SVGs.\n\nMore information under Install dependencies in the Wiki at board2pdf.dennevi.com",
            'Error', wx.OK | wx.ICON_ERROR)
        set_progress_status(100, "Failed to load PyMuPDF.")
        return False

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

    # colorize_pdf function points to colorize_pdf_pymupdf if pymupdf_color is true, else it points to colorize_pdf_pypdf
    # This function is only used if kicad_color is False
    colorize_pdf = colorize_pdf_pymupdf if pymupdf_color else colorize_pdf_pypdf

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

    plot_options.SetOutputDirectory(temp_dir)

    # Build a dict to translate layer names to layerID
    layer_names = {}
    for i in range(pcbnew.PCBNEW_LAYER_ID_START, pcbnew.PCBNEW_LAYER_ID_START + pcbnew.PCB_LAYER_ID_COUNT):
        layer_names[board.GetStandardLayerName(i)] = i

    steps: int = 2  # number of process steps
    templates_list: list[Template] = []
    warn_about_transparancy = False
    for t in enabled_templates:
        # {  "Test-template": {"mirrored": true, "enabled_layers": "B.Fab,B.Mask,Edge.Cuts,F.Adhesive", "frame": "In4.Cu",
        #          "layers": {"B.Fab": "#000012", "B.Mask": "#000045"}}  }
        if t in templates:
            temp = Template(t, templates[t], layer_names)
            _logger.debug(temp)

            # If not using PyMuPdf, check if any layers are transparant
            if not pymupdf_color:
                if temp.has_transparency:
                    warn_about_transparancy = True

            # Count how many steps it will take to complete this operation
            if kicad_color:
                steps += 1 + temp.steps_without_coloring
            else:
                steps += 1 + temp.steps

            # Build list of templates that shall be used
            templates_list.append(temp)
    progress_step: float = 95 / steps

    if warn_about_transparancy:
        msg_box("One or more layers have transparency set. Transparancy only works when using PyMuPDF for coloring.",
                'Warning', wx.OK | wx.ICON_WARNING)

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

    use_popups = False
    template_filelist = []

    title_block = board.GetTitleBlock()
    info_variable_int = int(info_variable)

    if(info_variable_int>=1 and info_variable_int<=9):
        previous_comment = title_block.GetComment(info_variable_int-1)
    
    # Iterate over the templates
    for page_count, template in enumerate(templates_list):
        if kicad_color:
            sm = pcbnew.GetSettingsManager()
            template_file_path = os.path.join(sm.GetColorSettingsPath(), "board2pdf.json")

            if not create_kicad_color_template(template.settings, template_file_path):
                set_progress_status(100, f"Failed to create color template for template {template.name}")
                return False

            plot_controller.SetColorMode(True)
            sm.ReloadColorSettings()
            cs = sm.GetColorSettings("board2pdf")
            plot_options.SetColorSettings(cs)
            plot_options.SetBlackAndWhite(False)        
        
        page_info_tmp = page_info.replace("${template_name}", template.name)
        page_info_tmp = page_info_tmp.replace("${page_nr}", str(page_count + 1))
        page_info_tmp = page_info_tmp.replace("${total_pages}", str(len(templates_list)))
        if(info_variable_int>=1 and info_variable_int<=9):
            title_block.SetComment(info_variable_int-1, page_info_tmp)
        board.SetTitleBlock(title_block)
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
                if int(pcbnew.Version()[0:1]) < 9:
                    plot_options.SetPlotViaOnMaskLayer(template.tented)
                if int(pcbnew.Version()[0:1]) >= 8:
                    plot_options.m_PDFFrontFPPropertyPopups = layer_info.front_popups
                    plot_options.m_PDFBackFPPropertyPopups = layer_info.back_popups

                plot_controller.SetLayer(layer_info.id)
                if pcbnew.Version()[0:3] == "6.0":
                    plot_controller.OpenPlotfile(layer_info.name, pcbnew.PLOT_FORMAT_PDF, template.name)
                else:
                    plot_controller.OpenPlotfile(layer_info.name, pcbnew.PLOT_FORMAT_PDF, template.name, template.name)
                plot_controller.PlotLayer()
            except:
                msg_box(traceback.format_exc(), 'Error', wx.OK | wx.ICON_ERROR)
                set_progress_status(100, "Failed to set plot_options or plot_controller")
                return False

        plot_controller.ClosePlot()

        template_use_popups = False
        frame_file = 'None'
        filelist = []
        # Change color of pdf files
        for layer_info in template.settings:
            ln = layer_info.name.replace('.', '_')
            input_file = f"{base_filename}-{ln}.pdf"
            output_file = f"{base_filename}-{ln}-colored.pdf"
            if not kicad_color and ( layer_info.has_color or layer_info.has_transparency ):
                progress += progress_step
                set_progress_status(progress, f"Coloring {layer_info.name} for template {template.name}")

                if not colorize_pdf(temp_dir, input_file, output_file, layer_info.color_rgb, layer_info.transparency):
                    set_progress_status(100, f"Failed when coloring {layer_info.name} for template {template.name}")
                    return False

                filelist.append(output_file)
            else:
                filelist.append(input_file)

            if layer_info.with_frame:
                # the frame layer is scaled by 1.0, all others by `layer_scale`
                
                
                #### Seems wrong to set frame_file to this!! We should be able to check which layer is chosen.
                frame_file = filelist[-1]

            # Set template_use_popups to True if any layer has popups
            template_use_popups = template_use_popups or layer_info.front_popups or layer_info.back_popups

        # Merge pdf files
        progress += progress_step
        set_progress_status(progress, f"Merging all layers of template {template.name}")

        assembly_file = f"{base_filename}_{template.name}.pdf"
        assembly_file = assembly_file.replace(' ', '_')

        if not merge_and_scale_pdf(temp_dir, filelist, output_dir, assembly_file, frame_file, template.scale_or_crop, template.name, pymupdf_merge):
            set_progress_status(100, "Failed when merging all layers of template " + template.name)
            return False

        template_filelist.append(assembly_file)
        # Set use_popups to True if any template has popups
        use_popups = use_popups or template_use_popups

    if kicad_color:
        # Delete Board2Pdf color template
        try:
            os.remove(template_file_path)
        except:
            msg_box(f"Delete color template file failed\n\n" + traceback.format_exc(), 'Error',
                    wx.OK | wx.ICON_ERROR)
            set_progress_status(100, "Failed to delete color template file")
            return False
        sm = pcbnew.GetSettingsManager()
        sm.ReloadColorSettings()

    if(info_variable_int>=1 and info_variable_int<=9):
        title_block.SetComment(info_variable_int-1, previous_comment)

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

