""" 
The CDE_CLI_Registry class is the object representing and managing the cde-cli Registry, 
the structure holding the status of the installed CDE Modules in the CDE environment.
The Registry structure is a dictionary having modules names and key and an infodata structure as values
An infodata structure is organized in dictionaries as follows:
  {'version':<module version>, 
   'programs': [{ 'name' : <program_name>, 
                  'exec_cmd': <execution_command>, 
                  'is_daemon': True|False
                  'pid': <daemon_pid> }, ...],
   'dependencies': [{ 'cde_module' : <module_name>, 'min_vers': <minimal_version>}, ...]
  }
  
The Registy information is kept in JSON form into the persistency file .cdereg located in the CDE Root directory

This file is part of iaiaGi project and is available under 
the Creative Commons 4.0 International: CC-BY-SA license.
See: https://github.com/iaiaGi/iaiaGi_ZEV_Kit/blob/master/LICENSE.rtf

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS AS IS AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. 
IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE.
""" 

import os, json
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
CDE_EMPTY_PID = -1

_CDE_REGISTRY_FILE = CDE_ROOT_DIR + '/.cdereg'    

class CDE_CLI_Registry:    

    def __init__(self):
        """
         Initializer: loads the __reg_dict with the .cdereg file if available
         otherwise creates and empty .cdreg file.
         This Initializer assumes that both paths and file EXISTS.
         The caller may want to handle the exception at object creation, if needed.
        """

        self.program_list = []
        if os.path.isfile(_CDE_REGISTRY_FILE):
            self._load_registry_file()
            self._make_program_list()
        else:
            self.__reg_dict = {}
            self.dump_registry()
            
    def _load_registry_file(self):
        """
        Loads a registry persistence JSON file into the registry structure                
        """
        json_data=open(_CDE_REGISTRY_FILE).read()
        self.__reg_dict = json.loads(json_data)


    def _make_program_list(self):
        """
         Builds the Program List containing the executable program available in 
         all installed modules (excluding the cde_cli itself)
         Each entry is a tuple with: module name, program name, executable file, is_daemon flag
        """
        for mname in self.get_modules():
            infodata = self._get_infodata(mname)
            programs = infodata['programs']
            for pgm in programs:                
                self.program_list.append((mname, pgm['name'], pgm['exec_cmd'], pgm['is_daemon'], pgm['pid']))
    
    
    def dump_registry(self):
        """
        Dumps the registry structure into the regitry persistency file               
        """
        with open(_CDE_REGISTRY_FILE, 'w') as fp:
            json.dump(self.__reg_dict, fp)    
    
    
    def read_moduleinfo(self, info_file_path):
        """
        Reads the module.info file provided by a module and
        returns a tuple with 2 items:
        - the module name
        - The parsed infodata structure of the module
        """        
        config = ConfigParser()
        #Assumes info file exists in the extracted dir
        config.read(info_file_path)        
        
        mname = config.get('main','name')
        infodata={}
        infodata['version'] = config.get('main','version')
        #Load program section
        mprograms = config.options('programs')        
        pgdata = []
        for x in mprograms:
            item = {}             
            item['name'] = x
            item['exec_cmd'] = config.get('programs', x)
            item['is_daemon'] = False
            item['pid'] = CDE_EMPTY_PID
            pgdata.append(item)        
        #Load daemon section
        mdaemons = config.options('daemons')
        for x in mdaemons:
            item = {}
            item['name'] = x
            item['exec_cmd'] = config.get('daemons', x)
            item['is_daemon'] = True
            item['pid'] = CDE_EMPTY_PID 
            pgdata.append(item)            
        infodata['programs'] = pgdata
        #Load dependencies section
        mdeps = config.options('dependencies')
        dpdata = []
        for x in mdeps:
            item = {}
            item['cde_module'] = x
            item['min_vers'] = config.get('dependencies',x)
            dpdata.append(item)
        infodata['dependencies'] = dpdata
                
        return (mname, infodata)            


    def store_infodata(self, mname, infodata):
        """
        Stores the content of a moduls module.info file into the Registry
        and syncs it into the persistency file.
        Then rebuilds the program list.
        """
        self.__reg_dict[mname] = infodata
        self.dump_registry()
        self.program_list = []
        self._make_program_list()


    def _get_infodata(self, mname):
        """
         Returns the module info stored in the registry for a certain module
         This should be used privately in the registry class only
        """
        return self.__reg_dict[mname]


    def remove_infodata(self, mname):
        """
        Removes the registry data from the registry for a certain module
        """
        del self.__reg_dict[mname]
        self.dump_registry()
        self.program_list = []
        self._make_program_list()


    def get_modules(self):
        """
        Returns a list with the currently regitered modules in the CDE Registry
        """
        return self.__reg_dict.keys()


    def mod_version(self, mname):
        """
         Returns the installed version string of the given module,
         or None if the module is not installed
        """
        if mname in self.__reg_dict:
            return self.__reg_dict[mname]['version']            
        

    def get_program_list(self, mname=None):
        """
         Return the CDE program list
        """
        if mname == None:
            return self.program_list
        else:
            res=[]
            for mod, name, exe, is_daemon, pid in self.program_list:
                if mod == mname:
                    res.append((mod, name, exe, is_daemon, pid))
            return res


    def is_daemon(self, mname, execname):
        """
         Convenience method: returns True is a given executable for a module is a daemon
        """
        for mod, name, exe, is_daemon, pid in self.get_program_list(mname):
            if name == execname:
                return is_daemon
            
    
    def get_exepath(self, mname, pname):
        """
         Returns the full path of the exec file for a certain executable name
         or None if not found
        """
        for mod, name, exe, is_daemon, pid in self.program_list:
            if mod == mname and name == pname:
                return CDE_ROOT_DIR + '/' + mname + '/bin/' + exe
        

    def store_pid(self, mname, pname, pid):
        """
         Stores the PID of a launched daemon and syncs the registry
         with the persistency file. Then rebuilds the program list.
        """
        infodata = self._get_infodata(mname)
        programs = infodata['programs']
        for pgdata in programs:
            if pgdata['name'] == pname:
                pgdata['pid'] = pid
                break
        #syncs with registry file
        self.dump_registry()
        self.program_list = []
        self._make_program_list()
        
        
    def get_pid(self, mname, pname):
        """
         Returns the PID registered for a certain daemon
        """
        infodata = self._get_infodata(mname)
        programs = infodata['programs']
        for pgdata in programs:
            if pgdata['name'] == pname:
                return pgdata['pid']        


    def erase_pid(self, mname, pname):
        """
         Clears the outdated PID of a daemon and syncs the registry
         with the persistency file. Then rebuilds the program list.
        """
        self.store_pid(mname, pname, CDE_EMPTY_PID)
                            
        
    def _compare_versions(self, firstv, secondv):
        """
        Compares two version strings and returns
        1: if the first is later version than the second
        0: if the versions are equal
        -1: if the first is earlier version than the second
        
        Comparison is done only upon the first TWO main version numbers because
        minor releases are not supposed to break compatibility and dependencies
        """
        first_vnums = firstv.split('.')
        second_vnums = secondv.split('.')
        for i in [0,1]:
            if first_vnums[i] > second_vnums[i]:
                return 1
            if first_vnums[i] < second_vnums[i]:
                return -1            
        
        return 0


    def precheck_modinfo(self, mname, infodata):
        """
        Inspects the module info data dictionary against the one stored in the 
        registry with a given module name and returns:
        None: if there is no module installed with same name as the parameter
        1: if the module is present with later version
        0: if the module is present with same version
        -1: if the module is present with older version
        """
        mvers = self.mod_version(mname) 
        if mvers != None:
            return self._compare_versions(mvers, infodata['version'])


    def check_dependencies(self, infodata):
        """
        Returns True if dependencies are satisfied for the info data dictionary
        passed as parameter.
        """
        deplist = infodata['dependencies']
        for depdict in deplist:
            depmodule = depdict['cde_module']
            depminvers = depdict['min_vers']
            av_vers = self.mod_version(depmodule)
            if av_vers == None:                
                return False
            if self._compare_versions(av_vers, depminvers) == -1:
                return False
            
        return True


    def dependents(self, module):
        """
        Returns the list of installed CDE modules having a dependency
        on the module passed as argument.
        """
        res=[]
        for mname in self.get_modules():
            infodata = self._get_infodata(mname)
            dep_mods = infodata['dependencies']
            for dmod in dep_mods:
                if dmod['cde_module'] == module:
                    res.append(mname)
                    break
        
        return res
    
