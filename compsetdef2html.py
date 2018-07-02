#!/usr/bin/env python

import os, sys, re
import datetime

CIMEROOT = os.environ.get("CIMEROOT")
if CIMEROOT is None:
    raise SystemExit("ERROR: must set CIMEROOT environment variable")
sys.path.append(os.path.join(CIMEROOT, "scripts", "Tools"))

from standard_script_setup import *

from CIME.utils           import expect
from CIME.XML.files       import Files
from CIME.XML.compsets    import Compsets
from CIME.XML.component import Component
import argparse

# check for  dependency module
try:
    import jinja2
except:
    raise SystemExit("ERROR: nmldef2html.py depends on the jinja2 template module. " /
                     "Install using 'pip --user install jinja2'")

# global variables
_now = datetime.datetime.now().strftime('%Y-%m-%d')

logger = logging.getLogger(__name__)
###############################################################################
def commandline_options():
###############################################################################

    parser = argparse.ArgumentParser(
        description='Read all the config_compset.xml files and generate a corresponding HTML file.')

    CIME.utils.setup_standard_logging_options(parser)

    parser.add_argument('--component',
                        help="Specify component of interest\n"
                        "If not specified, apply to all components.")

    parser.add_argument('--htmlfile', nargs=1, required=True,
                        help='Fully quailfied path to output HTML file.')

    parser.add_argument('--version', nargs=1, required=True,
                        help='Model version (e.g. CESM2.0)')

    options = parser.parse_args()

    CIME.utils.parse_args_and_handle_standard_logging_options(options)

    return options

###############################################################################
def _main_func(options, work_dir):
###############################################################################

    files = Files()
    model_version = options.version[0]
    
    comp_classes = ("CPL", "ATM", "LND", "ICE", "OCN", "ROF", "GLC", "WAV", "ESP")
    components = ["allactive"]
    for comp in comp_classes:
        components.extend(files.get_components("COMP_ROOT_DIR_{}".format(comp)))
    compset_files = []
    compset_dict = {}
    for comp in components:
        compset_file = files.get_value("COMPSETS_SPEC_FILE", attribute={"component":comp})
        if compset_file not in compset_files:
            expect(os.path.isfile(compset_file), "Could not find file {}".format(compset_file))
            compset_files.append(compset_file)
            compset = Compsets(infile=compset_file, files=files)
            longnames = compset.get_compset_longnames()
            for longname in longnames:
                _, alias, science_support = compset.get_compset_match(name=longname)
                elements = longname.split("_")
                numelems = len(elements)
                expect(numelems > 7, "This longname not supported {}".format(longname))
                compset_dict[longname] = {"alias" : alias, "science_support_grids": science_support,
                                          "defined_by": comp, "init_opt":elements[0], "atm_opt" : elements[1],
                                          "lnd_opt": elements[2], "seaice_opt": elements[3], "ocn_opt":elements[4],
                                          "rof_opt": elements[5], "glc_opt": elements[6], "wav_opt": elements[7]}

                for i in range(8, numelems):
                    if elements[i].startswith("BGC"):
                        compset_dict[longname].update({"bgc_opt":elements[i]})
                    elif 'ESP' in elements[i]:
                        compset_dict[longname].update({"esp_opt":elements[i]})
                    elif elements[i] == 'TEST':
                        logger.info("Longname is {}".format(longname))
                    else:
                        logger.warn("Unrecognized longname: {} {} {} ".format(longname, i, elements[i]))

                components = []
                for element in elements:
                    if element.startswith("BGC%") or element.startswith("TEST"):
                        continue
                    else:
                        element_component = element.split('%')[0].lower()
                        if "ww" not in element_component:
                            element_component = re.sub(r'[0-9]*',"",element_component)
                        components.append(element_component)
                for i in range(1,len(components)):
                    comp_class = comp_classes[i]
                    comp_config_file = files.get_value("CONFIG_{}_FILE".format(comp_class), {"component":components[i]})
                    compobj = Component(comp_config_file, comp_class)
                    compset_dict[longname].update({"{}_desc".format(comp_class):compobj.get_description(longname)})

                        
##    print ("compset_dict = {}".format(compset_dict))

    # load up jinja template
    templateLoader = jinja2.FileSystemLoader( searchpath='{0}/templates'.format(work_dir) )
    templateEnv = jinja2.Environment( loader=templateLoader )
    tmplFile = 'compsetdef2html.tmpl'
    template = templateEnv.get_template( tmplFile )

    #TODO change the template to just loop through the html_dict
    templateVars = { 'compset_dict'  : compset_dict,
                     'today'         : _now,
                     'model_version' : model_version }
        
    # render the template
    comp_tmpl = template.render( templateVars )

    # write the output file
    with open( options.htmlfile[0], 'w') as html:
        html.write(comp_tmpl)

    return 0

###############################################################################

if (__name__ == "__main__"):

    options = commandline_options()
    work_dir = os.getcwd()
    try:
        status = _main_func(options, work_dir)
        sys.exit(status)
    except Exception as error:
        print(str(error))
        sys.exit(1)

    _main_func(__doc__)
