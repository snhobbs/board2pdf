import os
from pypdf import PdfReader, PdfWriter, PageObject
from utils import exception_msg, io_file_error_msg

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


def pymupdf_loaded() -> bool:
    return has_pymupdf

def pdfcropmargins_loaded() -> bool:
    return has_pdfcropmargins

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