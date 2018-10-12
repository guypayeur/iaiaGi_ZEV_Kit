#!/usr/bin/env python

"""
 cde_cli post-install tasks to be executed by the installation process
 with root privileges.
"""
import os

# Creates the appropriate symlinks
os.symlink('cde_cli.py','/opt/d-ecu/cde_cli/bin/cde_cli')
#fault tolerant symlink creation
try:
    a = os.lstat('/usr/local/bin/cde_cli')
except:
    os.symlink('/opt/d-ecu/cde_cli/bin/cde_cli','/usr/local/bin/cde_cli')
