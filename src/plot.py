import os
import shutil
import sys
import re
import wx
import wx.stc
import traceback
import logging
import subprocess
import platform
from pathlib import Path

from utils import create_kicad_color_template, create_kicad_jobset, set_variables_in_project_file
from pdf_utils import colorize_pdf_pymupdf_with_transparency, merge_and_scale_pdf, create_pdf_from_pages, pdfcropmargins_loaded, pymupdf_loaded

_logger = logging.getLogger(__name__)

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
    kicad_cli_path: str = kwargs.pop('kicad_cli_path', '')
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
    
    if not pymupdf_loaded():
        msg_box(
        "PyMuPdf wasn't loaded.\n\nIt must be installed.\n\nMore information under Install dependencies in the Wiki at board2pdf.dennevi.com",
        'Error', wx.OK | wx.ICON_ERROR)
        set_progress_status(100, "Failed to load PyMuPDF.")
        return False

    if not pdfcropmargins_loaded():
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
        cli_command = [kicad_cli_path, "jobset", "run", "-f", "jobset.kicad_jobset", pcb_file_path]
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