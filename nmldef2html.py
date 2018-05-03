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
_comps = ['AQUAP', 'CAM', 'CLM', 'CISM', 'POP2', 'CICE', 'RTM', 'MOSART', 'WW3', 
          'Driver', 'DATM', 'DESP', 'DICE', 'DLND', 'DOCN', 'DROF', 'DWAV']
_cime_comps = ['Driver', 'DATM', 'DESP', 'DICE', 'DLND', 'DOCN', 'DROF', 'DWAV']
_exclude_defaults_comps = ['CAM','POP','CISM']
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

    options = parser.parse_args()

    CIME.utils.parse_args_and_handle_standard_logging_options(options)

    return options

###############################################################################
def _main_func(options, work_dir):
###############################################################################

    """Construct a `NamelistDefinition` from an XML file."""

    # Create a definition object from the xml file
    filename = options.nmlfile[0]
    expect(os.path.isfile(filename), "File %s does not exist"%filename)
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
        for default_file in default_files:
            default = GenericXML(infile=default_file)
            default.read(infile=default_file, schema=schema)
            defaults.append(default)
    else:
        schema = "new"

    # read the file into the definition object
    definition.read(infile=filename, schema=schema)

    # Initialize variables for the html template
    html_dict = dict()
    cesm_version = 'CESM2'
    comp = ''
    if options.comp:
        comp = options.comp[0]

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
    for node in definition.get_children("entry"):
        if schema == "new":
            category = definition.get_element_text("category", root=node)
        else:
            category = definition.get(node, "category")
        if category in category_dict:
            category_dict[category].append(node)
        else:
            category_dict[category] = [ node ]

    # Loop over each category and load up the html_dict
    for category in category_dict:

        # Create a dictionary of groups with a group key and an array of group nodes for each key
        groups_dict = dict()
        for node in category_dict[category]:
            if schema == "new":
                group = definition.get_element_text("group", root=node)
            else:
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
                name = definition.get(node, "id")
                if "@" in name:
                    name = re.sub('@.+$', "", name)

                # Create the information for this node - start with the description
                if schema == "new":
                    raw_desc = definition.get_element_text("desc", root=node)
                else:
                    raw_desc = definition.text(node)
                desc = re.sub(r"{{ hilight }}", hilight, raw_desc)
                desc = re.sub(r"{{ closehilight }}", closehilight, desc)

                # add type
                if schema == "new":
                    entry_type = definition.get_element_text("type", root=node)
                else:
                    entry_type = definition.get(node, "type")

                # add valid_values
                if schema == "new":
                    valid_values = definition.get_element_text("valid_values", root=node)
                else:
                    valid_values = definition.get(node, "valid_values")
                    
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
                                values += "value is %s for: %s <br/>" %(value, value_node.attrib)
                            else:
                                values += "value: %s <br/>" %(value)

                # exclude getting CAM and POP default value - it is included in the description text
                elif comp not in _exclude_defaults_comps:
                    for default in defaults:
                        for node in default.get_children(name=name):
                            if default.attrib(node):
                                values += "value is %s for: %s <br/>" %(default.text(node), default.attrib(node))
                            else:
                                values += "value: %s <br/>" %(default.text(node))

                # create the node dictionary
                node_dict = { 'name'           : name,
                              'desc'           : desc,
                              'entry_type'     : entry_type,
                              'valid_values'   : valid_values,
                              'default_values' : values,
                              'group_name'     : group_name }

                # append this node_dict to the group_list
                group_list.append(node_dict)

            # update the group_list for this category in the html_dict
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




