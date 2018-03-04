#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
""" This is scconv.py (Socketcan Converter) script to convert New Dep CAN Bus dump files to Socketcan format.

This file is a temporary script for test & debug.

In this version we implemented a simple script to convert New Dep CAN Bus dump files
into the socketcan dump file format. To use this script you have to copy source files
into the same script's directory. Format converted files are copied into the same
directory so source and destination files cannot have the same name. We suggest to
change at least the file extension and keep the same name of the source file.

=========================================================================================

Versions history:

v.0.0.1 (20180222):
- added Version history to this script description.

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
from datetime import datetime                               # Date and Time management

# Custom functions here
# def custom_function():
#     pass

# Global variables here
source = 'new_dep_can_dump_file.txt'                        # Set input filename here (New Dep CAN Bus dump file format)
destination = 'new_dep_can_dump_file.dump'                  # Set output filename here (Socketcan CAN Bus dump file format)
                                                            # Please, NOTE that input and output
                                                            # files must be under the same directory
                                                            # of this script and that we changed only the file extension

# Start of input and output file processing here                                                        
with open(source, 'r') as inputfile:                        # Start processing source file

    inputlist = []                                          # This list will contain all the file sinlge row items
    canbus = ''                                             # Used to trace which CAN Bus channel the line refers to
    loop = False                                            # Used to continue processing the file or stop in case of errors

    for line in inputfile:                                  # Start processing each source file rows
        inputlist = line.split()                            # Add the processed row items into a list

        if len(inputlist) > 0 and inputlist[0] == '1':      # Skip empty rows and rows without significant data
            canbus = 'can0'                                 # If first item of the row is 1 then CAN Bus channel is can0
            loop = True                                     # Continue to process the file
        elif len(inputlist) > 0 and inputlist[0] == '2':    # Else
            canbus = 'can1'                                 # If first item of the row is 2 then CAN Bus channel is can1
            loop = True                                     # Continue to process the file
        else:                                               # Else
            canbus = 'ERR'                                  # This is not a CAN Bus channel row
            loop = False                                    # So stop processing this row

        if loop == True:                                    # Check whether makes sense to continue row processing

            hours = 0                                       # Initialize fake acquisition time with hours
            sec, millis, micros = inputlist[1].split(':')   # seconds, milliseconds and microseconds from source dump file row
            minutes, seconds = divmod(int(sec), 60)         # Properly convert into seconds, minutes and hours
            hours, minutes = divmod(minutes, 60)
            microseconds = millis + micros                  # Generate a proper string to represent microseconds

            # Generates Epoch Unix timestamp from fake hours, minutes and seconds
            # Please, NOTE that date is set to 14/06/2016, when we first collected the Ford Fiesta (kevin) CAN Bus recordings
            # Fake 'hours' is an offset from 04.00 pm (16.00), the time we started the CAN Bus recording activity
            # All these assumptions are required because the original recordings don't carry the date and time timestamp
            # so we had to find a way to generate a working Epoch Unix timestamp conversion
            logtime = str(datetime.timestamp(datetime(2016, 6, 14, 16 + hours, minutes, seconds, int(microseconds))))

            if len(logtime) == 14:                          # Processing the Epoch Unix timestamp padding to have the
                logtime = logtime + '000'                   # same Epoch values lenght
            elif len(logtime) == 15:
                logtime = logtime +'00' 
            elif len(logtime) == 16:
                logtime = logtime + '0'

            if inputlist[4] == '00':                        # Processing CAN IDs padding to have the same values lenght
                cancode = '0' + inputlist[5]
            else:
                cancode = inputlist[4].lstrip('0') + inputlist[5]

            payload = ''                                    # Initialize CAN Bus messages payload

            if cancode == '280':                            # Processing of Ford CAN Bus messages payload lenght
                for index in range(6, 8):                   # according to what we found from a Ford Focus C-Max (Year 2003)
                    payload += inputlist[index]             # lenght of the same CAN IDs (this can be managed in a different
            elif cancode == '240' or cancode == '275':      # manner if we want to be sure that we don't loose any data during
                for index in range(6, 9):                   # the processing of CAN IDs: to be modified in future releases)
                    payload += inputlist[index]
            elif cancode == '428' or cancode == '4F2':
                for index in range(6, 10):
                    payload += inputlist[index]
            elif cancode == '430':
                for index in range(6, 12):
                    payload += inputlist[index]
            elif cancode == '080' or cancode == '231':
                for index in range(6, 13):
                    payload += inputlist[index]
            else:
                for index in range(6, 14):
                    payload += inputlist[index]
 
            canstring = cancode + '#' + payload             # Convert the CAN Bus messages into the Socketcan dump file format
            
            # Builds the final complete Socketcan dump file row output                              
            outline = '(' + logtime + ') ' + canbus + ' ' + canstring + '\n'

            with open(destination, 'a') as outfile:         # Add a row to the output file with the Socketcan dump file format
                outfile.write(outline)
            outfile.close()

        else:                                               # Send to the standard output a warning that the file contains
            print('A line cannot be processed!')            # a row with no meaningful data

inputfile.close()                                           # End processing of inputfile and close the I/O activity