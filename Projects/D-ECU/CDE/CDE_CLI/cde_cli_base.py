#!/usr/bin/env python

""" 
cde_cli_base.py is the bootstrap initializer of the cde-cli environment.
It creates the cde-cli objects and structures in a clean system to allow
management of the CDE modules through the common cde-cli management framework.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS AS IS AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. 
IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE.
"""
import os, sys, pwd, grp, stat, subprocess, shutil, datetime
import zipfile
import click

__version__    =  "0.1"

__author__     =  "Alberto Trentadue"
__copyright__  =  "Copyright 2018, iaiaGi Project"
__credits__    =  []
__license__    =  "Creative Commons 4.0 International: CC-BY-SA"
__maintainer__ =  "Alberto Trentadue"
__email__      =  "alberto.trentadue@iaiagi.com"
__status__     =  "Development"

__CDE_ROOT_DIR = '/opt/d-ecu'
__CDE_CLI_DIR = __CDE_ROOT_DIR + '/cde_cli'
__CDE_CLI_BIN_DIR = __CDE_CLI_DIR + '/bin'
__CDE_CLI_SCPT_DIR = __CDE_CLI_DIR + '/scpt'

"""
 Makes a backup of the whole cde directory tree as a file
 located in the CDE Root directory with this naming convention
 cde-<version>-<yyyymmddhhmm>.zip
"""
def backup_cde_dir(oldv):    
    bcktime = format(datetime.datetime.now(), '%Y%m%d%H%M')
    back_zipfile='/opt/cde-' + oldv + '-bck-' + bcktime + '.zip'
    FNULL = open(os.devnull, 'w')
    try:
        subprocess.call(['zip', '-r', back_zipfile, __CDE_ROOT_DIR], stdout=FNULL, stderr=subprocess.STDOUT)
    except:
        click.echo('CDE directory tree backup compression failed, exiting.')
        click.ClickException(sys.exc_info[0])
        sys.exit(1)

@click.group()
def cli():
    pass

@click.command()
@click.argument('zfile', type=click.Path(exists=True), metavar='<zfile>')
def install(zfile):
    """Installs the cde_cli package <zfile> and initializes the CDE CLI environment"""
    if pwd.getpwuid(os.getuid())[0] != 'root':
        click.echo('The cde-cli-base must be executed as root, exiting.')
        click.ClickException('Invalid non-root user')
        sys.exit(1)
        
    click.echo('CDE environment installation tool version ' + __version__)
    # If the CDE environment already exists, exit with message
    if os.path.isdir(__CDE_ROOT_DIR):        
        click.echo('The CDE Root directory is present. Drop and backup before installing a new version.')
        sys.exit(1)
    else:
        # Creates the root cde module directory /opt/d-ecu/.
        os.mkdir(__CDE_ROOT_DIR, 0750);

    # Creates the "cde" group
    subprocess.call(['groupadd','-f', 'cde'])
            
    # Checks the "cde" user
    try:
        pwd.getpwnam('cde')
        click.echo('The cde user already exists, moving on.')
    except KeyError:
        click.echo('Creating the cde user:')
        subprocess.call(['useradd', '-s', '/bin/bash', '-g', 'cde', '-G', 'adm,dialout,sudo,plugdev', '-m', 'cde'])
        #TODO: Check the groups applicable on the RPi
    
    # chmod 750 of CDE Root
    os.chmod(__CDE_ROOT_DIR, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP )
        
    # Installs the cde-cli as a CDE module from the .zip file
    # The package .zip file must be in the same dir of this script
    click.echo('Installing the CDE environment.')
    FNULL = open(os.devnull, 'w')
    try:
        subprocess.call(['unzip', zfile, '-d', __CDE_ROOT_DIR], stdout=FNULL, stderr=subprocess.STDOUT)
    except:
        click.echo('cde-cli package extraction failed, exiting.')
        click.ClickException(sys.exc_info[0])
        sys.exit(1)
    
    # Initializes the CDE CLI Registry from the cde-cli module.info    
    sys.path.insert(0, __CDE_CLI_BIN_DIR)
    from cde_cli_registry import CDE_CLI_Registry
    reg = CDE_CLI_Registry()
    moduleinfo = reg.read_moduleinfo(__CDE_CLI_DIR + '/module.info')
    reg.store_infodata(moduleinfo[0], moduleinfo[1])
        
    # Assigns all the CDE Root dir to the cde user recursively
    cdeuid = pwd.getpwnam('cde')[2]
    cdegid = grp.getgrnam('cde')[2]
    os.chown(__CDE_ROOT_DIR, cdeuid, cdegid)
    for rdir, dirs, files in os.walk(__CDE_ROOT_DIR):  
        for m in dirs:  
            os.chown(os.path.join(rdir, m), cdeuid, cdegid)
        for m in files:
            os.chown(os.path.join(rdir, m), cdeuid, cdegid)
    
    # Executes the post installation tasks of cde_cli
    click.echo('Executing post-installation tasks')
    subprocess.call(__CDE_CLI_SCPT_DIR+'/post_inst.py')    
    
    click.echo('CDE environment ready. Type cde_cli sto start the CLI.')


@click.command()
def drop():
    """Drops a CDE dirtree by prior doing a file backup"""
    
    click.echo('The drop command will uninstall ALL installed CDE Modules.')
    if click.confirm('Please confirm to proceed with the CDE drop operation:'):        
        #Executes all the post_uninst.py scripts of the installed modules        
        sys.path.insert(0, __CDE_CLI_BIN_DIR)
        from cde_cli_registry import CDE_CLI_Registry
        reg = CDE_CLI_Registry()
        for mname in reg.get_modules():            
            module_root_dir = __CDE_ROOT_DIR + '/' + mname
            if os.path.isfile(module_root_dir + '/scpt/post_uninst.py'):                
                subprocess.call(module_root_dir + '/scpt/post_uninst.py')        
        #Makes the CDE dir backup
        oldv = reg.mod_version('cde_cli')
        backup_cde_dir(oldv)
        #Finally removes the CDE dir tree
        try:
            shutil.rmtree(__CDE_ROOT_DIR)
        except:
            click.echo('An error occurred when trying to remove the CDE directory '+ __CDE_ROOT_DIR)
            click.echo('Please check and remove manually the directory')
    
cli.add_command(install)
cli.add_command(drop)    
    
if __name__ == '__main__':
    cli()

