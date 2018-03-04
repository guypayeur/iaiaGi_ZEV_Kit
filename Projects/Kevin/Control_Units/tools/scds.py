#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
""" This is scds.py (Socketcan Display Statistics) script to show statistics data of CAN Bus dump files in Socketcan dump file format.

This file is a temporary script for test & debug.

In this version we implemented a simple script to compute statistics on a Socketcan dump
file format to help reverse engineering CAN Bus messages of an unknown vendor. Input file
must be under the same directory of this script and it must be named 'inputfile.dump'.
This script output is redirected to the standard output.
Output of this script is:

Unique CAN codes: #ofUniqueCAN_IDs
ID -> COD -> EVTs
UniqueCAN_ID_count_id -> UniqueCAN_ID -> #ofEvents_in_dump_file
...
CAN ID => Payload #ofPositions (#ofBytes Byte(s))
...

=========================================================================================

Versions history:

v.0.0.1 (20180222):
- added the INPUT_FILE global variable to make easy changing input file name.
- added some comments to make clear code understanding.

v.0.0.0 (20180221):
- baseline version.

=========================================================================================

This script can be improved a lot!"""

__version__    =  "0.0.1"

__author__     =  "Valerio Vannucci"
__copyright__  =  "Copyright 2017 - 2018, iaiaGi Project"
__credits__    = ["Valerio Vannucci"]
__license__    =  "Creative Commons 4.0 International: CC-B-Y-S-A"
__maintainer__ =  "Valerio Vannucci"
__email__      =  "valerio.vannucci@iaiagi.com"
__status__     =  "Prototype"

# Import statements here
import collections                                             # Specialized data types management


# Custom functions here
# def custom_function():
#     pass

# Start of input and output file processing here
INPUT_FILE = 'inputfile.dump'                                  # Set here the CAN Bus dump file name if different from default 'inputfile.dump'

file = open(INPUT_FILE)                                        # Start processing the input file which must be under the same
                                                               # directory of this Python script
# Global variables here
inputlist = []                                                 # Set the list that will contain the input items
allcodes = []                                                  # Set the list that will contain all the unique detected CAN IDs

for line in file:                                              # Start processing the input file one row at a time
    inputlist = line.split()                                   # Dissecting each line into its single components
    cancode, payload = inputlist[2].split('#')                 # Discriminate the CAN ID from its payload
    allcodes.append(cancode)                                   # Add the CAN ID at the end of 'allcodes' list

file.close()                                                   # Close the input file I/O activity

unique_cancodes = set(allcodes)                                # Generate a set containing only the detected unique CAN IDs
counter = collections.Counter()                                # Initialize a Counter collection to count events for each unique CAN IDs
for code in allcodes:                                          # Scan all detected CAN IDs
    counter[code] += 1 										   # Adds one unit to each CAN ID matching events

print('Unique CAN codes: ', len(unique_cancodes))              # Print out the number of unique detected CAN IDs
print('Unique CAN codes events:')                              # Print out description header
print('\tID -> COD -> EVTs')                                   # Print out statistical data columns header
l = 1                                                          # Formats the output in order to make columns value aligned by column
for key in counter:                                            # Output format is:
    if l < 10:                                                 # Unique CAN codes: #ofUniqueCAN_IDs
        print('\t %s -> %s -> %s' %(l, key, counter[key]))     # ID -> COD -> EVTs
    else:                                                      # UniqueCAN_ID_count_id -> UniqueCAN_ID -> #ofEvents_in_dump_file
        print('\t%s -> %s -> %s' %(l, key, counter[key]))      # ...
    l += 1

for item in counter:                                           # Start evaluating how many bytes is each CAN IDs payload
    tmplen = 0                                                 # Output format is:
    file = open(INPUT_FILE)                                    # CAN ID => Payload #ofPositions (#ofBytes Byte(s))
    for line in file:                                          # ...
        inputlist = line.split()
        cancode, payload = inputlist[2].split('#')             # Discriminate CAN IDs from their payload
        if item == cancode:
            lnt = len(payload)                                 # 'len' is the number of characters that makes up the payload
            if lnt != tmplen:
                tmplen = lnt                                   # 'tmplen' contains the number of characters that symbolize payload lenght
                print('\t%s => %s (%s Byte(s))' %(item, tmplen, int(tmplen / 2)))

    file.close()                                               # Close the input file I/O activity (see line 73 of this file)


