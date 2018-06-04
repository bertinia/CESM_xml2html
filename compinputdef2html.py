#!/usr/bin/env python

"""Generator of html file for component input parameters
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
from CIME.XML.component import Component

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

    parser.add_argument('--inputfile', nargs=1, required=True,
                        help='Fully nquailfied path to config_component.xml input XML file.')

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

    # Initialize variables for the html template
    html_dict = dict()
    cesm_version = 'CESM2'
    comp = ''
    if options.comp:
        comp = options.comp[0]

    # Create a component object from the xml file
    filename = options.inputfile[0]
    expect(os.path.isfile(filename), "File %s does not exist"%filename)
    component = Component(filename, comp)
    helptext, html_dict = component.return_values()
    
    # get the component tag from the command line args
    comptag = ''
    if options.comptag:
        comptag = options.comptag[0]

    # get the component version from the command line args
    compversion = ''
    if options.compversion:
        compversion = options.compversion[0]

    # load up jinja template
    templateLoader = jinja2.FileSystemLoader( searchpath='{0}/templates'.format(work_dir) )
    templateEnv = jinja2.Environment( loader=templateLoader )

    # populate the template variables
    tmplFile = 'compinputdef2html.tmpl'
    template = templateEnv.get_template( tmplFile )
    templateVars = { 'html_dict'    : html_dict,
                     'today'        : _now,
                     'cesm_version' : cesm_version,
                     'comp'         : comp,
                     'comptag'      : comptag,
                     'compversion'  : compversion,
                     'hilight'      : hilight,
                     'closehilight' : closehilight,
                     'helptext'     : helptext
                 }
        
    # render the template
    comp_tmpl = template.render( templateVars )

    # write the output file
    with open( options.htmlfile[0], 'w') as html:
        html.write(comp_tmpl)

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




