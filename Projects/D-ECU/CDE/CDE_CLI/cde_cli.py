#!/usr/bin/env python

""" 
cde_cli.py implements thd CDE CLI - command line interface.
It offers a consistent environment to operate the various CDE Modules.

This file is part of iaiaGi project and is available under 
the Creative Commons 4.0 International: CC-BY-SA license.
See: https://github.com/iaiaGi/iaiaGi_ZEV_Kit/blob/master/LICENSE.rtf

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS AS IS AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. 
IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE.
"""
import os, sys, pwd, grp, stat, subprocess, shutil, datetime, time, signal
import click
from click_repl import repl, register_repl, exit as repl_exit
import psutil

from cde_cli_registry import CDE_CLI_Registry, CDE_ROOT_DIR, CDE_EMPTY_PID

__version__    =  "0.2"
__author__     =  "Alberto Trentadue"
__copyright__  =  "Copyright 2018, iaiaGi Project"
__credits__    =  []
__license__    =  "Creative Commons 4.0 International: CC-BY-SA"
__maintainer__ =  "Alberto Trentadue"
__email__      =  "alberto.trentadue@iaiagi.com"
__status__     =  "Development"

__TEMP_EXTRACTION_DIR = '/tmp/cdetmp/'
__CDE_REGISTRY = CDE_CLI_Registry()

# The Daemon status labels
__DAEMON_RUNNING = 1
__DAEMON_NOT_RUNNING = 0
__DAEMON_RUNNING_NOT_REG = 2
__DAEMON_RESTARTED_NOT_REG = 3
__DAEMON_EXITED_NOT_REG = -1

def backup_module_dir(mname):
    """
    Makes a backup of a module's installation directory as a file
    located in the CDE Root directory with this naming convention
    <module_name>-<version>-<yyyymmddhhmm>.zip
    """

    module_root_dir = os.path.join(CDE_ROOT_DIR, mname)
    oldv = __CDE_REGISTRY.mod_version(mname)
    bcktime = format(datetime.datetime.now(), '%Y%m%d%H%M')
    zipfile_name = mname + '-' + oldv + '-bck-' + bcktime + '.zip'
    back_zipfile=os.path.join(CDE_ROOT_DIR, zipfile_name)
    FNULL = open(os.devnull, 'w')
    try:
        subprocess.call(['zip', '-r', back_zipfile, module_root_dir], stdout=FNULL, stderr=subprocess.STDOUT)
    except Exception as e:
        click.echo('Module backup compression failed, exiting.')
        click.echo('Error was:'+ str(e))
        sys.exit(1)

def module_ex_dir():    
    """
    Returns the directory name created by the module file decompression.
    This directory is not known in advance and contains the module.info file
    """
    for path, dirs, files in os.walk(__TEMP_EXTRACTION_DIR):
        if 'module.info' in files:            
            return path


def search_process(exepath):
    """
     Searches and returns the PID of a process by its executable full path
     If not found, returns CDE_EMPTY_PID
    """
    for p in psutil.process_iter(attrs=["cmdline"]):
        if len(p.cmdline()) > 0:
            if p.cmdline()[0] == exepath:
                return p.pid
        #This check is needed if a scripts starts with a shebang line!
        if len(p.cmdline()) > 1 and p.cmdline()[1] == exepath:
            return p.pid
            
    return CDE_EMPTY_PID


def kill_process(pid):
    """
     Stops a process.
     Tries to stop it by sending SIGTERM signal 10 times spaced by 1 sec
     if the process does not exit like this, sends a SIGKILL to the process
    """
    for i in range(10):
        os.kill(pid, signal.SIGTERM)
        time.sleep(1)
        if not psutil.pid_exists(pid):
            return
    #forcefully KILL
    os.kill(pid, signal.SIGKILL)
    #give some time more...
    time.sleep(1)
    

def status_of_daemon(mname, pname):
    """
     Returns a tuple with the following items:
      - the Daemon status label for a given daemon
      - the pid of the actual running process
     None if the Daemon does not exists
    """
    is_daemon = __CDE_REGISTRY.is_daemon(mname, pname)
    exepath = __CDE_REGISTRY.get_exepath(mname, pname)
    if exepath != None:        
        pid = __CDE_REGISTRY.get_pid(mname, pname)    
        s_pid = search_process(exepath)
        
        if pid == s_pid:
            if pid == CDE_EMPTY_PID:
                return __DAEMON_NOT_RUNNING, CDE_EMPTY_PID
            else:
                return __DAEMON_RUNNING, s_pid           
        
        if pid == CDE_EMPTY_PID and s_pid > 0:
            return __DAEMON_RUNNING_NOT_REG, s_pid
        
        if pid > 0 and s_pid == CDE_EMPTY_PID:
            return __DAEMON_EXITED_NOT_REG, CDE_EMPTY_PID
        
        if pid > 0 and s_pid != pid:
            return __DAEMON_RESTARTED_NOT_REG, s_pid
    else:
        return (None, -1)
    
    
def extract_from_zipfile(zfile):
    """
     Extracts the content of a package file into a temp directory
     and reads the package module information contained in it
     
     If successful, returns a tuple with 3 elements
     - the moduleinfo object obtained by parsing the module.info file
     - the extracted module name
     - the infodata object of the extracted module     
    """
    #Unpacks the module under the temp extraction dir 
    click.echo('Extracting module from file ' + zfile)
    shutil.rmtree(__TEMP_EXTRACTION_DIR, ignore_errors=True)
    
    FNULL = open(os.devnull, 'w')
    try:
        subprocess.call(['unzip', zfile, '-d', __TEMP_EXTRACTION_DIR], stdout=FNULL, stderr=subprocess.STDOUT)
    except Exception as e:
        click.echo('Module package extraction failed, exiting.')
        click.echo('Error was:'+str(e))
    
    #Builds the representation of the module.info
    moduleexdir = module_ex_dir()
    try:
        moduleinfo = __CDE_REGISTRY.read_moduleinfo(os.path.join(moduleexdir, 'module.info'))
        mname = moduleinfo[0]
        infodata = moduleinfo[1]
        
        return (moduleinfo, mname, infodata)
    
    except Exception as e:
        click.echo('Failed parsing the module.info file, exiting.')
        click.echo('Error was:'+str(e))
        #Cleans up the extraction dir 
        shutil.rmtree(__TEMP_EXTRACTION_DIR, ignore_errors=True)        
        sys.exit(1) 
    

def replace_spec_module_dir(mname, moduleexdir, target_dir):
    """
     This function replaces an individual directory inside a module
     from the directory where the new module has been extracted.
     Used for upgrades.     
    """
    module_root_dir = os.path.join(CDE_ROOT_DIR, mname)        
    tgdir = os.path.join(module_root_dir, target_dir)
    if os.path.exists(tgdir):
        shutil.rmtree(tgdir)
    crdir = os.path.join(moduleexdir, target_dir)    
    shutil.copytree(crdir, tgdir)
    

def update_files_module_dir(mname, moduleexdir, target_dir, new_ver):
    """
     This function moves the new files from an upgrade package into the
     target directory and names them with the suffix: .<new_version>.NEW
     Also cleans up all pre existing .NEW files
     If the target module dir has been removed in the new package file
     it will be removed also in the current installation.
     Used for upgrades.     
    """
    module_root_dir = os.path.join(CDE_ROOT_DIR, mname)        
    #Removes pre-existing .NEW files
    tgdir = os.path.join(module_root_dir, target_dir)
    all_files = os.listdir(tgdir)
    for item in all_files:
        if item.endswith(".NEW"):
            os.remove(os.path.join(tgdir, item))
    #Copies the extracted files to the target and appends to them .new_version.NEW
    crdir = os.path.join(moduleexdir, target_dir)
    if os.path.isdir(crdir):
        all_files = os.listdir(crdir)
        for item in all_files:
            orig_file_path = os.path.join(crdir, item)
            new_file_name = item + '.' + new_ver + '.NEW'
            dest_file_path = os.path.join(module_root_dir, target_dir, new_file_name)
            shutil.copyfile(orig_file_path, dest_file_path)
    else:
        shutil.rmtree(tgdir)
        

@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """
    The Click Command group definition
    """
    if ctx.invoked_subcommand is None:
        repl(ctx, prompt_kwargs={'message':u'-->> '})

        
@cli.command()
@click.argument('zfile', type=click.Path(exists=True), metavar='<zfile>')
def install(zfile):
    """Installs a cde module from its package .zip file"""        
        
    (moduleinfo, mname, infodata) = extract_from_zipfile(zfile)
            
    #Module files are now extracted and ready to be installed    
    #Check if there is already this module installed.    
    no_backup = False
    toinstall = True
    res = __CDE_REGISTRY.precheck_modinfo(mname, infodata)
    #Check cases where module is already present
    if res == 0:
        #Same version installed, nothing to do
        click.echo('Module version is already installed. Nothing to do.')
        toinstall = False
    
    if res == 1:
        #Newer version is installed, installation not allowed
        click.echo('Module is already installed with newer version. Nothing to do.')
        toinstall = False

    if res == -1:
        #Older version is installed, it has to be upgraded by 'upgrade'
        oldv = __CDE_REGISTRY.mod_version(mname)
        click.echo('Previous version '+ oldv +' is present. Please use the \'upgrade\' command instead.')
        toinstall = False

    #Module dependencies check
    if not __CDE_REGISTRY.check_dependencies(infodata):
        click.echo('Dependencies are not satisfied, installation cancelled.')
        toinstall = False
    
    if toinstall:        
        #Now ready to install
        click.echo('Installing module ' + mname + ' version ' + infodata['version'])
        
        #Move the temporary extraction dir into the CDE directory tree
        moduleexdir = module_ex_dir()
        shutil.move(moduleexdir, CDE_ROOT_DIR)
        
        # Store the module info in the registry 
        __CDE_REGISTRY.store_infodata(mname, infodata)
            
        module_root_dir = os.path.join(CDE_ROOT_DIR, mname)
                
        # Executes the post installation tasks if any
        inst_task_path = os.path.join(module_root_dir, 'scpt', 'post_inst.py')
        if os.path.isfile(inst_task_path):
            click.echo('Executing post-installation tasks')
            subprocess.call(inst_task_path)             

        click.echo('Installation completed.')
    
    #Cleans up the extraction dir 
    shutil.rmtree(__TEMP_EXTRACTION_DIR, ignore_errors=True)
    

@cli.command()
@click.argument('zfile', type=click.Path(exists=True), metavar='<zfile>')
def upgrade(zfile):
    """Upgrades a cde module from the new package .zip file"""
    
    (moduleinfo, mname, infodata) = extract_from_zipfile(zfile)
    #Module files are now extracted and ready to be installed    
    #Check if there is already this module installed.        
    toupgrade = True

    res = __CDE_REGISTRY.precheck_modinfo(mname, infodata)
    #Check possible cases 
    if res == None:
        #The package is NOT present!
        click.echo('Module is not installed. Please use the \'install\' command to install it.')
        toupgrade = False
        
    if res == 0:
        #Same version installed, nothing to do
        click.echo('Module version is already installed. Nothing to do.')
        toupgrade = False
    
    if res == 1:
        #Newer version is installed, installation not allowed
        click.echo('Module is already installed with newer version. Nothing to do.')
        toupgrade = False

    #Module dependencies check
    if not __CDE_REGISTRY.check_dependencies(infodata):
        click.echo('Dependencies are not satisfied, installation cancelled.')
        toupgrade = False
        
    if toupgrade:
        #Executes the previous version's backup
        new_ver = infodata['version']
        click.echo('Backing up the module '+ mname +' before upgrade.')
        backup_module_dir(mname)
                
        #Now ready to upgrade!
        click.echo('Upgrading module '+ mname +' to version ' + new_ver)
        module_root_dir = os.path.join(CDE_ROOT_DIR, mname)
        moduleexdir = module_ex_dir()
        #Copies or replaces the dirs from the new package
        dir_items = os.listdir(moduleexdir)
        for item in dir_items:
            item_path = os.path.join(moduleexdir, item)
            #if it is a file, it is simply copied in the target dir
            if os.path.isfile(item_path):
                shutil.copy(item_path, module_root_dir)
            else:
                #is a directory                
                if item in ['bin', 'lib', 'doc', 'scpt', 'src']:
                    #old items can be ovewritten
                    replace_spec_module_dir(mname, moduleexdir, item)                
                else:
                    #old items shall be kept
                    if os.path.exists(os.path.join(module_root_dir, item)):
                        update_files_module_dir(mname, moduleexdir, item, new_ver)
                    else:
                        replace_spec_module_dir(mname, moduleexdir, item)
                    
        #Removes the dirs in the installation that are not present in the new package
        dir_items = os.listdir(module_root_dir)
        for item in dir_items:
            pkg_item_path = os.path.join(moduleexdir, item)
            if not os.path.exists(pkg_item_path):
                item_path = os.path.join(module_root_dir, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
                        
        # Store the module info in the registry 
        __CDE_REGISTRY.store_infodata(mname, infodata)        
                
        # Executes the post upgrade tasks if any                        
        upg_task_path = os.path.join(module_root_dir,'scpt','post_upg.py')
        if os.path.isfile(upg_task_path):
            click.echo('Executing post-upgrade tasks')
            subprocess.call(upg_task_path)             

        click.echo('Upgrade completed.')

    #Cleans up the extraction dir 
    shutil.rmtree(__TEMP_EXTRACTION_DIR, ignore_errors=True)
    

@cli.command()
@click.option('--backup/--nobackup', default=True)
@click.argument('module')
def uninstall(backup, module):
    """Uninstalls a CDE module"""
        
    #Check if installed
    if __CDE_REGISTRY.mod_version(module) == None:
        click.echo('Module '+ module + ' is not installed. Nothing to do.')
        sys.exit(1)

    if module == 'cde_cli':
        click.echo('The cde_cli module must be dropped by the cde_cli_base script. Exiting.')
        sys.exit(0)
    
    if not click.confirm('Please confirm uninstallation of module '+ module):
        sys.exit(0)    
    
    #Check depenencies are not broken
    if len(__CDE_REGISTRY.dependents(module)) > 0:
        click.echo('Module cannot be uninstalled because it would break existing module dependecies.')
    else:
        do_backup = True
        if not backup:
            if click.confirm('Please confirm that module backup is NOT requested:'):
                do_backup = False
        if do_backup:
            #Executes the backup
            click.echo('Backing up the module '+ module +' before uninstallation.')
            backup_module_dir(module)

        module_root_dir = os.path.join(CDE_ROOT_DIR, module)
        # Executes the post uninstallation tasks if any
        uninst_task_path = os.path.join(module_root_dir, 'scpt', 'post_uninst.py')
        if os.path.isfile(uninst_task_path):
            click.echo('Executing post-uninstallation tasks')
            subprocess.call(uninst_task_path)

        #Remove the module info in the registry 
        __CDE_REGISTRY.remove_infodata(module)
        
        # Finally the module directory is removed        
        try:
            shutil.rmtree(module_root_dir)
        except:
            click.echo('An error occurred when trying to remove the module directory '+ module_root_dir)
            click.echo('Please check and remove manually the directory')
        
        click.echo('Uninstallation completed.')        
        

@cli.command() 
def listmod():
    """Lists the currently installed modules and their executables"""
    
    click.echo('Installed modules in the CDE environment:')
    for mname in __CDE_REGISTRY.get_modules():
        vers = __CDE_REGISTRY.mod_version(mname)
        click.echo(mname + '-' + vers)
        for mod, pname, pexec, is_daemon, pid in __CDE_REGISTRY.get_program_list(mname):
            if is_daemon:
                ds = ' (D) '
                if pid == CDE_EMPTY_PID:
                    ps = 'None'
                else:
                    ps = str(pid)
            else:
                ds = '     '
                ps = 'n/a'
            click.echo('    '+ mod +'.'+ pname + ds + 'PID:'+ ps)
                

@cli.command(context_settings=dict(
    ignore_unknown_options=True,
    allow_extra_args=True,
))
@click.argument('execname', metavar='<execname>')
@click.pass_context
def start(ctx, execname):
    """Starts an executable, either a program or a daemon"""
    
    #Executable spec must have the form: module.program_name or module.daemon_name
    #Command arguments following the executable are passed as is to the program or daemon
    modex = execname.split('.')
    if len(modex) != 2:
        click.echo('Error specifying executable: format is ''module.execname''')
        sys.exit(1)

    mname = modex[0]
    pname = modex[1]
    is_daemon = __CDE_REGISTRY.is_daemon(mname, pname)
    exepath = __CDE_REGISTRY.get_exepath(mname, pname)
    if exepath == None:
        click.echo('Wrong module or executable name: '+ execname)
        sys.exit(1)
        
    callist = [exepath]
    callist[1:] = ctx.args
    try:
        if is_daemon:
            pid = subprocess.Popen(callist).pid
            __CDE_REGISTRY.store_pid(mname, pname, pid)
            click.echo('Daemon '+ execname + ' launched with PID:'+str(pid))
        else:
            subprocess.call(callist)
    except:
        click.echo('An error occurred when launching the executable.')
        click.echo('Called command was: '+ ' '.join(callist))
    
    
@cli.command()
@click.argument('daemon', metavar='<daemon>', required=False)
@click.pass_context
def dstatus(ctx, daemon):
    """Returns the status of daemon(s)"""
    
    if daemon == None:
        #List the status of all daemons recursively
        for mod, pname, pexec, is_daemon, pid in __CDE_REGISTRY.get_program_list():
            daemon_name = mod + '.' + pname
            if is_daemon:
                ctx.invoke(dstatus, daemon=daemon_name)
        sys.exit(0)
    
    #Daemon spec must have the form: module.program_name or module.daemon_name
    modex = daemon.split('.')
    if len(modex) != 2:
        click.echo('Error specifying daemon: format is ''module.daemon_name''')
        sys.exit(1)

    mname = modex[0]
    pname = modex[1]

    (daemon_status, pid) = status_of_daemon(mname, pname)
    if daemon_status == None:
        click.echo('Wrong module or executable name: '+ daemon)
        sys.exit(1)
        
    if daemon_status == __DAEMON_NOT_RUNNING:
        click.echo('Daemon '+ daemon +' not running.')        
    
    if daemon_status == __DAEMON_RUNNING:
        click.echo('Daemon '+ daemon +' running, PID:' + str(pid))        
    
    if daemon_status == __DAEMON_RUNNING_NOT_REG:
        click.echo('Daemon '+ daemon +' running but PID not registered (started externally):'+ str(pid))
        if click.confirm('Align registry?', default=True):
            __CDE_REGISTRY.store_pid(mname, pname, pid)            
    
    if daemon_status == __DAEMON_EXITED_NOT_REG:
        click.echo('Daemon '+ daemon +' exited but PID still registered (stopped externally).')
        if click.confirm('Align registry?', default=True):
            __CDE_REGISTRY.erase_pid(mname, pname)
    
    if daemon_status == __DAEMON_RESTARTED_NOT_REG:
        click.echo('Daemon '+ daemon +' running but different PID registered (restarted externally):'+ str(pid))
        if click.confirm('Align registry?', default=True):
            __CDE_REGISTRY.store_pid(mname, pname, pid)

    
@cli.command()
@click.argument('daemon', metavar='<daemon>')
@click.pass_context
def stop(ctx, daemon):
    """Stops a running daemon"""

    #Daemon spec must have the form: module.program_name or module.daemon_name
    modex = daemon.split('.')
    if len(modex) != 2:
        click.echo('Error specifying daemon: format is ''module.daemonname''')
        sys.exit(1)

    mname = modex[0]
    pname = modex[1]
    
    #Shows the status
    ctx.invoke(dstatus, daemon=daemon)
    daemon_status, pid = status_of_daemon(mname, pname)
    if pid != CDE_EMPTY_PID:
        if click.confirm('Confirm termination of daemon '+daemon+ '?'):
            kill_process(pid)
            __CDE_REGISTRY.erase_pid(mname, pname)
    
    
@cli.command()
def quit():
    """Exits the CDE CLI"""
    repl_exit()    


# Cli startup    
if __name__ == '__main__':
    click.echo('D-ECU CDE console v.'+ __version__ +'. Type --help for the command list.')
    register_repl(cli)
    cli(obj={})
