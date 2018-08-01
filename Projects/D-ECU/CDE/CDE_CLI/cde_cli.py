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
import os, sys, pwd, grp, stat
import click
from click_repl import repl, register_repl, exit as repl_exit

from cde_cli_registry import CDE_CLI_Registry

__version__    =  "0.1"
__author__     =  "Alberto Trentadue"
__copyright__  =  "Copyright 2018, iaiaGi Project"
__credits__    =  []
__license__    =  "Creative Commons 4.0 International: CC-BY-SA"
__maintainer__ =  "Alberto Trentadue"
__email__      =  "alberto.trentadue@iaiagi.com"
__status__     =  "Development"

__CDE_ROOT_DIR = '/opt/d-ecu'
__TEMP_EXTRACTION_DIR = '/tmp'
__CDE_REGISTRY = CDE_CLI_Registry()


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    if ctx.invoked_subcommand is None:
        repl(ctx, prompt_kwargs={'message':u'-->> '})
        
@cli.command()
@click.argument('zfile', type=click.Path(exists=True), metavar='<zfile>')
def install(zfile):
    """Installs a cde module from its zip file"""

    click.echo('Extracting module in file ' + zfile)
    #Unpacks the module under /tmp
    try:
        subprocess.call(['unzip', zfile, '-d', __TEMP_EXTRACTION_DIR])
    except:
        click.echo('cde-cli package extraction failed, exiting.')
        click.ClickException(sys.exc_info[0])
        sys.exit(1)
            
    #Builds the representation of the module.info
    try:
        moduleinfo = __CDE_REGISTRY.load_moduleinfo(__TEMP_EXTRACTION_DIR + '/module.info')
        mname = moduleinfo[0]
        infodata = moduleinfo[1]
    except:
        click.echo('Failed parsing the module.info file, exiting.')
        click.ClickException(sys.exc_info[0])
        sys.exit(1) 
            
    #Checks if there is already this module installed.    
    res = __CDE_REGISTRY.compare_versions(mname, infodata)
    backup = False
    if res != None:
        #Some different version is already installed
        if res == 0:
            #Same version installed, nothing to do
            click.echo('Module version is already installed. Nothing to do.')
            sys.exit(0)
        
        if res == 1:
            #Newer version is installed, installation not allowed
            click.echo('Module is already installed with newer version. Nothing to do.')
            sys.exit(0)

        if res == -1:
            #Older version is installed, ask confirmation to upgrade
            click.confirm('Older version of module is installed. Backup and replace?', abort=True)
            backup = True                            
        
    if backup:
        #backup of the existing module and then drop it
        pass
        
    #Now ready to install
    click.echo('Installing module ' + mname + '.' + infodata['version'])
    
    # Store the module info in the registry 
    __CDE_REGISTRY.store_moduleinfo(mname, infodata)
    
    # Creates symbolic links of the executables in appropriate Linux directories.
    # TODO
    
    module_root_dir = __CDE_ROOT_DIR + '/' + mname
    # Assigns all the CDE Root dir to the cde user recursively
    cdeuid = getpwnam('cde')[2]
    cdegid = getgrnam('cde')[2]
    os.chown(module_root_dir, cdeuid, cdegid)
    for rdir, dirs, files in os.walk(module_root_dir):  
        for m in dirs:  
            os.chown(os.path.join(rdir, m), cdeuid, cdegid)
        for m in files:
            os.chown(os.path.join(rdir, m), cdeuid, cdegid)
            
    # Executes the post installation tasks if any
    if os.path.isfile(__CDE_ROOT_DIR + '/scpt/post_inst.py'):
        click.echo('Executing post-installation tasks')
        subprocess.call(__CDE_ROOT_DIR + '/scpt/post_inst.py')             

    click.echo('Installation completed.')
    
@cli.command()
@click.argument('module')
def uninstall():
    click.echo('Uninstall ' + module)

@cli.command()
@click.argument('module')
def drop():
    click.echo('Drop ' + module)

@cli.command()
def listmod():
    click.echo('Installed Modules')
    
@cli.command()
def conscheck():
    click.echo('Consistency check')
    
@cli.command()
def quit():    
    repl_exit()    


# Cli startup    
if __name__ == '__main__':
    click.echo('D-ECU CDE console v.'+ __version__ +'. Type --help for the command list.')
    register_repl(cli)
    cli(obj={})


