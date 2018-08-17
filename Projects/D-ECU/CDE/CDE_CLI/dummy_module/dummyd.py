#!/usr/bin/env python

""" 
dummyd.py is a daemon executable to be used for testing the cde_cli.

This file is part of iaiaGi project and is available under 
the Creative Commons 4.0 International: CC-BY-SA license.
See: https://github.com/iaiaGi/iaiaGi_ZEV_Kit/blob/master/LICENSE.rtf

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS AS IS AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. 
IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE.
""" 

import sys, os, time

try:
    os.remove("dummy_test.txt")
except:
    pass

#increment step
step = int(sys.argv[1])

i = 0
while True:
    time.sleep(1)
    # writes to a local file
    out_file = open("dummy_test.txt","a+")
    out_file.write("Iteration: " + str(i) + "\n")
    out_file.close()
    i=i+step
