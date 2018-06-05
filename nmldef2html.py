#!/usr/bin/env python

"""Generator of html file for component namelists
"""

# Typically ignore this.
# pylint: disable=invalid-name

# Disable these because this is our standard setup
# pylint: disable=wildcard-import,unused-wildcard-import,wrong-import-position

import os, sys, re, glob
import datetime

CIMEROOT = os.environ.get("CIMEROOT")
if CIMEROOT is None:
    raise SystemExit("ERROR: must set CIMEROOT environment variable")
sys.path.append(os.path.join(CIMEROOT, "scripts", "Tools"))

from standard_script_setup import *
from CIME.utils import expect
from CIME.XML.generic_xml import GenericXML
import re

# check for  dependency module
try:
    import jinja2
except:
    raise SystemExit("ERROR: nmldef2html.py depends on the jinja2 template module. " /
                     "Install using 'pip --user install jinja2'")

# global variables
_now = datetime.datetime.now().strftime('%Y-%m-%d')
_comps = ['AQUAP', 'CAM', 'CLM', 'CISM', 'POP2', 'MARBL', 'CICE', 'RTM', 'MOSART',
          'WW3', 'Driver', 'DATM', 'DESP', 'DICE', 'DLND', 'DOCN', 'DROF', 'DWAV']
_cime_comps = ['Driver', 'DATM', 'DESP', 'DICE', 'DLND', 'DOCN', 'DROF', 'DWAV']
_exclude_defaults_comps = ['POP2']
_exclude_groups = {
    'AQUAP': [],
    'CAM': ['cime_driver_inst','seq_cplflds_inparm','seq_cplflds_userspec',
            'ccsm_pes','seq_infodata_inparm','seq_timemgr_inparm',
            'prof_inparm','papi_inparm','pio_default_inparm',
            'drydep_inparm','megan_emis_nl','fire_emis_nl',
            'carma_inparm','ndep_inparm','dom_inparm',
            'docn_nml','shr_strdata_nml','aquap_nl'],
    'CLM': [],
    'CISM': [],
    'POP2': [],
    'MARBL': [],
    'CICE': [],
    'RTM' : [],
    'MOSART': [],
    'WW3': [],
    'Driver': [],
    'DATM': [],
    'DESP': [],
    'DICE': [],
    'DLND': [],
    'DOCN': [],
    'DROF': [],
    'DWAV': []}
logger = logging.getLogger(__name__)
hilight = '<span style="color:blue">'
closehilight = '</span>'

###############################################################################
def commandline_options():
###############################################################################

    """ Process the command line arguments.
    """
    parser = argparse.ArgumentParser(
        description='Read the component namelist file and generate a corresponding HTML file.')

    CIME.utils.setup_standard_logging_options(parser)

    parser.add_argument('--nmlfile', nargs=1, required=True,
                        help='Fully nquailfied path to input namelist XML file.')

    parser.add_argument('--comp', nargs=1, required=True, choices=_comps,
                        help='Component name.')

    parser.add_argument('--htmlfile', nargs=1, required=True,
                        help='Fully quailfied path to output HTML file.')

    parser.add_argument('--comptag', nargs=1, required=False,
                        help='Component tag')

    parser.add_argument('--compversion', nargs=1, required=False,
                        help='Component version. Example: 4.0, 4.5, 5.0, etc...')

    parser.add_argument('--marbl-json', required=False, action='store_true', dest='JSON',
                        help='Flag to look for MARBL JSON file instead of XML')

    options = parser.parse_args()

    CIME.utils.parse_args_and_handle_standard_logging_options(options)

    return options

###############################################################################
def _main_func(options, work_dir):
###############################################################################

    """Construct a `NamelistDefinition` from an XML file."""

    # Initialize variables for the html template
    html_dict = dict()
    cesm_version = 'CESM2'
    comp = ''
    if options.comp:
        comp = options.comp[0]

    # Create a definition object from the xml file
    filename = options.nmlfile[0]
    expect(os.path.isfile(filename), "File %s does not exist"%filename)
    if not options.JSON:
        try:
            definition = GenericXML(infile=filename)
        except:
            sys.exit("Error: unable to parse file %s" %filename)

        # Determine if have new or old schema
        basepath = os.path.dirname(filename)
        default_files = glob.glob(os.path.join(basepath,"namelist_defaults*.xml"))
        defaults = []
        if len(default_files) > 0:
            schema = "old"
            if comp not in _exclude_defaults_comps:
                for default_file in default_files:
                    default = GenericXML(infile=default_file)
                    default.read(infile=default_file, schema=schema)
                    defaults.append(default)
        else:
            schema = "new"
        # read the file into the definition object
        definition.read(infile=filename, schema=schema)
    else:
        schema = "MARBL JSON"
        derived_desc = dict()
        derived_entry_type = dict()
        derived_category = dict()

        import json
        with open(filename) as settings_file:
            MARBL_json_dict = json.load(settings_file)

        # Set up MARBL_settings_file_class object with CESM (gx1v7) default values
        MARBL_root = os.path.join(os.path.dirname(filename), "..")
        sys.path.append(MARBL_root)
        from MARBL_tools import MARBL_settings_file_class
        MARBL_args=dict()
        MARBL_args["default_settings_file"] = filename
        MARBL_args["input_file"] = None
        MARBL_args["grid"] = "CESM_x1"
        MARBL_args["saved_state_vars_source"] = "settings_file"
        MARBL_default_settings = MARBL_settings_file_class.MARBL_settings_class(**MARBL_args)

    # get the component tag from the command line args
    comptag = ''
    if options.comptag:
        comptag = options.comptag[0]

    # get the component version from the command line args
    compversion = ''
    if options.compversion:
        compversion = options.compversion[0]

    # Create a dictionary with a category key and a list of all entry nodes for each key
    category_dict = dict()
    if schema == "MARBL JSON":
        # Special category for MARBL derived types
        category_dict["MARBL_derived_types"] = dict()
        for category in [key for key in MARBL_json_dict.keys() if key[0] != "_"]:
            for marbl_varname in MARBL_json_dict[category].keys():
                if isinstance(MARBL_json_dict[category][marbl_varname]['datatype'], dict):
                    if marbl_varname not in category_dict["MARBL_derived_types"].keys():
                        category_dict["MARBL_derived_types"][marbl_varname] = dict()
                        category_dict["MARBL_derived_types"][marbl_varname][category] = []
                    for component in [key for key in MARBL_json_dict[category][marbl_varname]["datatype"] if key[0] != "_"]:
                        category_dict["MARBL_derived_types"][marbl_varname][category].append(component)
                else:
                    if category in category_dict.keys():
                        category_dict[category].append(marbl_varname)
                    else:
                        category_dict[category] = [ marbl_varname ]
    else:
        for node in definition.get_children("entry"):
            if schema == "new":
                category = definition.get_element_text("category", root=node)
            elif schema == "old":
                category = definition.get(node, "category")

            if category in category_dict:
                category_dict[category].append(node)
            else:
                category_dict[category] = [ node ]

    # Loop over each category and load up the html_dict
    for category in category_dict:

        # Create a dictionary of groups with a group key and an array of group nodes for each key
        groups_dict = dict()
        if schema == "MARBL JSON":
            if category == "MARBL_derived_types":
                for root_varname in category_dict[category].keys():
                    for real_category in category_dict[category][root_varname].keys():
                        for component in category_dict[category][root_varname][real_category]:
                            if "subcategory" in MARBL_json_dict[real_category][root_varname]["datatype"][component].keys():
                                group = MARBL_json_dict[real_category][root_varname]["datatype"][component]["subcategory"]
                                if group not in _exclude_groups[comp]:
                                    marbl_varname = "%s%%%s" % (root_varname, component)
                                    derived_desc[marbl_varname] = MARBL_json_dict[real_category][root_varname]["datatype"][component]["longname"]
                                    derived_entry_type[marbl_varname] = "dtype%%%s" % MARBL_json_dict[real_category][root_varname]["datatype"][component]["datatype"]
                                    derived_category[marbl_varname] = real_category
                                    if group in groups_dict:
                                        groups_dict[group].append(marbl_varname)
                                    else:
                                        groups_dict[group] = [ marbl_varname ]
            else:
                for marbl_varname in category_dict[category]:
                    if 'subcategory' in MARBL_json_dict[category][marbl_varname].keys():
                            group = MARBL_json_dict[category][marbl_varname]['subcategory']
                            if group not in _exclude_groups[comp]:
                                if group in groups_dict:
                                    groups_dict[group].append(marbl_varname)
                                else:
                                    groups_dict[group] = [ marbl_varname ]
        else:
            for node in category_dict[category]:
                if schema == "new":
                    group = definition.get_element_text("group", root=node)
                elif schema == "old":
                    group = definition.get(node, "group")
                if group not in _exclude_groups[comp]:
                    if group in groups_dict:
                        groups_dict[group].append(node)
                    else:
                        groups_dict[group] = [ node ]

        # Loop over the keys
        group_list = list()
        for group_name in groups_dict:

            # Loop over the nodes in each group
            for node in groups_dict[group_name]:

                # Determine the name
                # @ is used in a namelist to put the same namelist variable in multiple groups
                # in the write phase, all characters in the namelist variable name after
                # the @ and including the @ should be removed
                if schema == "MARBL JSON":
                    name = node
                    #print name
                else:
                    name = definition.get(node, "id")
                if "@" in name:
                    name = re.sub('@.+$', "", name)

                # Create the information for this node - start with the description
                if schema == "MARBL JSON":
                    if category == "MARBL_derived_types":
                        desc = derived_desc[node]
                    else:
                        if MARBL_json_dict[category][node]['subcategory'] == group_name:
                            desc = MARBL_json_dict[category][node]['longname']
                else:
                    if schema == "new":
                        raw_desc = definition.get_element_text("desc", root=node)
                    elif schema == "old":
                        raw_desc = definition.text(node)
                    desc = re.sub(r"{{ hilight }}", hilight, raw_desc)
                    desc = re.sub(r"{{ closehilight }}", closehilight, desc)

                # add type
                if schema == "new":
                    entry_type = definition.get_element_text("type", root=node)
                elif schema == "old":
                    entry_type = definition.get(node, "type")
                elif schema == "MARBL JSON":
                    if category == "MARBL_derived_types":
                        entry_type = derived_entry_type[node]
                    else:
                        if MARBL_json_dict[category][node]['subcategory'] == group_name:
                            entry_type = MARBL_json_dict[category][node]['datatype'].encode('utf-8')
                            # Is this an array?
                            if "_array_shape" in MARBL_json_dict[category][node].keys():
                                array_len = MARBL_json_dict[category][node]["_array_shape"]
                                if array_len == "_tracer_list":
                                    array_len = MARBL_default_settings.get_tracer_cnt()
                                entry_type = "%s*%d" % (entry_type, array_len)

                # add valid_values
                if schema == "new":
                    valid_values = definition.get_element_text("valid_values", root=node)
                elif schema == "old":
                    valid_values = definition.get(node, "valid_values")
                if schema == "MARBL JSON":
                    if category == "MARBL_derived_types":
                        valid_values = ''
                    else:
                        if MARBL_json_dict[category][node]["subcategory"] == group_name:
                            if "valid_values" in MARBL_json_dict[category][node].keys():
                                valid_values = ",".join(MARBL_json_dict[category][node]["valid_values"]).encode('utf-8')
                            else:
                                valid_values = None

                if entry_type == "logical":
                    valid_values = ".true.,.false."
                else:
                    if not valid_values:
                        valid_values = "any " + entry_type
                        if "char" in valid_values:
                            valid_values = "any char"

                if valid_values is not None:
                    valid_values = valid_values.split(',')

                # add default values
                values = ""
                if schema == "new":
                    value_nodes = definition.get(node,'value')
                    if value_nodes is not None and len(value_nodes) > 0:
                        for value_node in value_nodes:
                            try:
                                value = value_node.text.strip()
                            except:
                                value = 'undefined'
                            if value_node.attrib:
                                values += " is %s for: %s <br/>" %(value, value_node.attrib)
                            else:
                                values += " %s <br/>" %(value)
                elif schema == "MARBL JSON":
                    if node in MARBL_default_settings.settings_dict.keys():
                        values = MARBL_default_settings.settings_dict[node]
#                        print "%s = %s" % (node, values)
                    else:
                        if category == "MARBL_derived_types":
                            pass
                        else:
                            if "default_value" in MARBL_json_dict[category][node].keys():
                                if isinstance(MARBL_json_dict[category][node]["default_value"], dict):
                                    if 'PFT_defaults == "CESM2"' in MARBL_json_dict[category][node]["default_value"].keys():
                                        default_values = MARBL_json_dict[category][node]["default_value"]['PFT_defaults == "CESM2"']
                                    elif 'GCM == "CESM"' in MARBL_json_dict[category][node]["default_value"].keys():
                                        default_values = MARBL_json_dict[category][node]["default_value"]['GCM == "CESM"']
                                    else:
                                        default_values = MARBL_json_dict[category][node]["default_value"]["default"]
                                else:
                                    default_values = MARBL_json_dict[category][node]["default_value"]
                                if isinstance(default_values, list):
                                    values = []
                                    for value in default_values:
                                        if type(value) == type (u''):
                                            values.append(value.encode('utf-8'))
                                        else:
                                            values.append(value)
                                elif type(default_values) == type (u''):
                                    values = default_values.encode('utf-8')

                # exclude getting CAM and POP default value - it is included in the description text
                elif comp not in _exclude_defaults_comps:
                    for default in defaults:
                        for node in default.get_children(name=name):
                            if default.attrib(node):
                                values += " is %s for: %s <br/>" %(default.text(node), default.attrib(node))
                            else:
                                values += " %s <br/>" %(default.text(node))

                # create the node dictionary
                node_dict = { 'name'           : name,
                              'desc'           : desc,
                              'entry_type'     : entry_type,
                              'valid_values'   : valid_values,
                              'default_values' : values,
                              'group_name'     : group_name }

                # append this node_dict to the group_list
                group_list.append(node_dict)
                if category == "MARBL_derived_types":
                    real_category = derived_category[node]

            # update the group_list for this category in the html_dict
            if category == "MARBL_derived_types":
                category_group = real_category
            else:
                category_group = category
            html_dict[category_group] = group_list

    # load up jinja template
    templateLoader = jinja2.FileSystemLoader( searchpath='{0}/templates'.format(work_dir) )
    templateEnv = jinja2.Environment( loader=templateLoader )

    # populate the template variables
    tmplFile = 'nmldef2html.tmpl'
    template = templateEnv.get_template( tmplFile )
    templateVars = { 'html_dict'    : html_dict,
                     'today'        : _now,
                     'cesm_version' : cesm_version,
                     'comp'         : comp,
                     'comptag'      : comptag,
                     'compversion'  : compversion,
                     'hilight'      : hilight,
                     'closehilight' : closehilight
                 }

    # render the template
    nml_tmpl = template.render( templateVars )

    # write the output file
    with open( options.htmlfile[0], 'w') as html:
        html.write(nml_tmpl)

    return 0

###############################################################################

if __name__ == "__main__":

    options = commandline_options()
    work_dir = os.getcwd()
    try:
        status = _main_func(options, work_dir)
        sys.exit(status)
    except Exception as error:
        print(str(error))
        sys.exit(1)




