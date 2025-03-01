import json
import traceback
import sys
import wx
import os

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

def get_drawing_worksheet_from_project(project_file_path: str) -> bool | str:
    try:
        # Open the file and read the JSON data
        with open(project_file_path, 'r') as file:
            data = json.load(file)

        # Check if 'pcbnew' exists
        if 'pcbnew' in data:
            if 'page_layout_descr_file' in data['pcbnew']:
                return True, data['pcbnew']['page_layout_descr_file']

    except FileNotFoundError:
        exception_msg(f"Error when fetching drawing sheet path: The file {project_file_path} does not exist.")
        return False, ''
    except json.JSONDecodeError:
        exception_msg(f"Error when fetching drawing sheet path: Failed to decode JSON from the file.")
        return False, ''
    except Exception as e:
        exception_msg(f"Error when fetching drawing sheet path: An unexpected error occurred: {e}")
        return False, ''

    return False, ''

def set_drawing_worksheet_in_project(project_file_path: str, worksheet_path) -> bool:
    try:
        # Open the file and read the JSON data
        with open(project_file_path, 'r') as file:
            data = json.load(file)

        # Check if 'pcbnew' exists, if not, create it
        if 'pcbnew' not in data:
            data['pcbnew'] = {}

        # Update variables
        data['pcbnew']['page_layout_descr_file'] = worksheet_path

        # Write the updated JSON back to the file
        with open(project_file_path, 'w') as file:
            json.dump(data, file, indent=2)

    except FileNotFoundError:
        exception_msg(f"Error when updating drawing sheet path: The file {project_file_path} does not exist.")
        return False
    except json.JSONDecodeError:
        exception_msg(f"Error when updating drawing sheet path: Failed to decode JSON from the file.")
        return False
    except Exception as e:
        exception_msg(f"Error when updating drawing sheet path: An unexpected error occurred: {e}")
        return False

    return True

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