#!/usr/bin/env python

""" 
cde_cli_base.py is the bootstrap initializer of the cde-cli environment.
It creates the cde-cli objects and structures in a clean system to allow
management of the CDE modules through the common cde-cli management framework.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS AS IS AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. 
IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE.
"""
import os, sys, pwd, grp, stat, subprocess
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
    # Creates the /opt/cde-cli-bck_<hhmmss-YYYYMMdd>.gz backup file, if the system already exists.
    if os.path.isdir(__CDE_ROOT_DIR):
        #A CDE dir already exists: ask if backup or exit
        click.echo('The CDE Root directory is present.')
        click.confirm('Backup the existing and replace?', abort=True)
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
    os.chmod(__CDE_ROOT_DIR, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP)
        
    # Installs the cde-cli as a CDE module from the .zip file
    # The package .zip file must be in the same dir of this script
    click.echo('Installing the cde_cli module.')
    try:
        subprocess.call(['unzip', zfile, '-d', __CDE_ROOT_DIR])
    except:
        click.echo('cde-cli package extraction failed, exiting.')
        click.ClickException(sys.exc_info[0])
        sys.exit(1)
    
    # Initializes the CDE CLI Registry from the cde-cli module.info    
    sys.path.insert(0, __CDE_CLI_BIN_DIR)
    from cde_cli_registry import CDE_CLI_Registry
    reg = CDE_CLI_Registry()
    moduleinfo = reg.load_moduleinfo(__CDE_CLI_DIR + '/module.info')
    reg.store_moduleinfo(moduleinfo[0], moduleinfo[1])
        
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
    
    click.echo('CDE CLI environment ready')


@click.command()
def drop():
    click.echo('Drop')
    
cli.add_command(install)
cli.add_command(drop)    
    
if __name__ == '__main__':
    cli()


