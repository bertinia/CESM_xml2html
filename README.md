# CESM xml2html

Python tools for auto-generating HTML from CESM and CIME XML configuration files.
The jinja2 template files use the CESM web site skins and styles. Modeling groups
other than CESM will want to modify the templates for their specific model.

## Requirements
  
  CIME v maint-5.6 (06/26/2018 or later)
  
  CESM >= 2.0.beta09
  
  jinja2 template python module available from https://pypi.python.org/pypi/Jinja2
  
  >pip install --user jinja2

  CIMEROOT environment variable pointing to local CIME root location

  On CGD machines, jinja2 is available in python2.7.14

  >module load lang/python/2.7.14

## Python tools

***************************************************
Steps to generate namelist definitions to html

Synopsis:
  Parses a namelist XML file and generates a html page. Note: some namelist
  values are not valid in XML. The "&" character needs to be manually modified
  to be "&amp;" in order for the schema checks to work correctly. 

Example:
  >nmldef2html.py 
    --nmlfile ~/cesm2_0_alpha06/cime/src/drivers/mct/cime_config/namelist_definition_drv.xml 
    --comp Driver 
    --htmlfile drv.html

  This example reads the XML namelist file "namelist_definition_drv.xml" for the
  "Driver" component and generates an output html file "drv.html".

  You can view the file either locally using:
  >open drv.html
  
  or copy the drv.html file to a web server for remote viewing.
  
Options:
  >nmldef2html.py --help

***************************************************
Steps to generate compsets html 

   >compsetdef2html.py --htmlfile compsets.html --version CESM2.Y.Z

Update the /cesmweb/html/models/cesm2/config/2.Y.Z/rows-include-comp.html
files to include the new version in the pulldown option menu

rm /cesmweb/html/models/cesm2/config/compsets.html
ln -s /cesmweb/html/models/cesm2/config/2.Y.Z/compsets.html

***************************************************
Steps to generate the grids html

1. run cime/scripts/query_config --grids --long > grids.txt
2. edit the grids.txt to remove all lines up to the first line containing 'alias:'
2. run griddef2html.py --txtfile /fully-qualified-path-to/grids.txt --htmlfile /fully-qualified-path-to/grids.html --version CESM2.Y.Z

update all the /cesmweb/html/models/cesm2/config/2.Y.Z/grids.html files with new version in pulldown option menu
rm /cesmweb/html/models/cesm2/config/grids.html
ln -s /cesmweb/html/models/cesm2/config/2.Y.Z/grids.html

***************************************************
Steps to generate the machines html

   >machdef2html.py --htmlfile /fully-qualified-path-to/machines.html --version CESM2.Y.Z --supported cheyenne,hobart --tested cori,edison,stampede2,bluewaters,theta

update all the /cesmweb/html/models/cesm2/config/2.Y.Z/machines.html files with new version in pulldown option menu
rm /cesmweb/html/models/cesm2/config/machines.html
ln -s /cesmweb/html/models/cesm2/config/2.Y.Z/machines.html

***************************************************


There are 2 scripts in this repo to generate all namelist definition files and all CASEROOT variable files for all components

   >gen_all_nml
   >gen_all_input

Check the variables CESMROOT and OUTPUT at the top of the files to be sure the directory paths are correct. Also, update the
model component version values to match those in the CESM Externals.cfg file.

Update the /cesmweb/html/models/settings/2.Y.Z/index.html files to include a new dropdown option in the verion menu
rm /cesmweb/html/models/settings/current
ln -s /cesmweb/html/models/settings/2.Y.Z current

