#!/usr/bin/env python

"""
 cde_cli post-uninstall tasks to be executed by the uninstallation process
 with root privileges 
"""
import os

# removes the symlink from the /usr/local/bin dir
os.remove('/usr/local/bin/cde_cli')
