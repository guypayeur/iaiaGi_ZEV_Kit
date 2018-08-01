""" 
The CDE_CLI_Registry class is the object representing the cde-cli Regisrty, the structure holding the status of
the installed CDE Modules in the CDE environment.
The Registy information is kept in serialized form into the file .cdereg located in the CDE Root directory

This file is part of iaiaGi project and is available under 
the Creative Commons 4.0 International: CC-BY-SA license.
See: https://github.com/iaiaGi/iaiaGi_ZEV_Kit/blob/master/LICENSE.rtf

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS AS IS AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. 
IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE.
""" 

import os, pickle
from ConfigParser import ConfigParser


__version__    =  "0.1"

__author__     =  "Alberto Trentadue"
__copyright__  =  "Copyright 2018, iaiaGi Project"
__credits__    =  []
__license__    =  "Creative Commons 4.0 International: CC-BY-SA"
__maintainer__ =  "Alberto Trentadue"
__email__      =  "alberto.trentadue@iaiagi.com"
__status__     =  "Development"

CDE_ROOT_DIR = '/opt/d-ecu'
CDE_REGISTRY_FILE = CDE_ROOT_DIR + '/.cdereg'

class CDE_CLI_Registry:

    """
     Initializer: loads the __reg_dict with the .cdereg file if available
     otherwise creates and empty .cdreg file.
     This Initializer assumes that both paths and file EXISTS.
     The caller may want to handle the exception at object creation, if needed.
    """
    def __init__(self):
        if os.path.isfile(CDE_REGISTRY_FILE):
            self.__reg_dict = pickle.load(open(CDE_REGISTRY_FILE))
        else:
            self.__reg_dict = {}
            pickle.dump(self.__reg_dict, open(CDE_REGISTRY_FILE,'w'))
                
    """
     Returns a tuple with 2 items:
     - the module name
     - a dictionary based structure representing other module.info data:
       {'version':<module version>, 
        'programs': {<program_name>: <filename_into_bin>, ...},
        'daemons':  {<daemon_name> : <filename_into_bin>, ...},
        'dependencies': {<module_name> : <minimal_version>, ...}
        }
      
    """
    def load_moduleinfo(self, info_file_path):
        
        config = ConfigParser()
        #Assumes info file exists in the extracted dir
        config.read(info_file_path)        
        
        mname = config.get('main','name')
        infodata={}
        infodata['version'] = config.get('main','version')
        mprograms = config.options('programs')
        pgdata = {}
        for x in mprograms:
            pgdata[x] = config.get('programs',x)
        infodata['programs'] = pgdata                
        mdaemons = config.options('daemons')
        dmdata = {}
        for x in mdaemons:
            dmdata[x] = config.get('daemons',x)
        infodata['daemons'] = dmdata                
        mdeps = config.options('dependencies')
        dpdata = {}
        for x in mdeps:
            dpdata[x] = config.get('dependencies',x)
        infodata['dependencies'] = dpdata
                
        return (mname, infodata)            
        

    """
     Stores the content of a module's module.info file into the Regisrty
    """
    def store_moduleinfo(self, mname, infodata):
        self.__reg_dict[mname] = infodata
    
    """
     Compares the module info data dictionary with the one stored in the 
     regstry with a given module name and returns:
     None: if there is no module installed equal to the passed one
     1: if the module is present with later version
     0: if the module is present with same version
     -1: if the module is present with older version
    """
    def compare_versions(self, mname, info_data):
        pass
    

    
