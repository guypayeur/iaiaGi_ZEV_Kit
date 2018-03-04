#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
""" This is canloop.py script to manage automatic missing CAN IDs re-integration.

This file is a temporary script for test & debug.

In this version we implemented an infinite loop that waits to see if CAN Bus messages
are generated by the original car electronics and sends all missing CAN IDs to restore
proper operation of all car electronic devices like the ESC (Electric Stearing Wheel Controller).
If no messages are detected on the CAN Bus the script does nothing, so only when the car is on 
integration messages are generated.

=========================================================================================

Versions history:

v.0.0.1 (20180222):
- added version history to this script description.

v.0.0.0 (20180221):
- baseline version.

=========================================================================================

This script can be improved a lot!"""

__version__    =  "0.0.0"

__author__     =  "Valerio Vannucci"
__copyright__  =  "Copyright 2018, iaiaGi Project"
__credits__    = ["Enrico Melotti", "Valerio Vannucci"]
__license__    =  "Creative Commons 4.0 International: CC-B-Y-S-A"
__maintainer__ =  "Valerio Vannucci"
__email__      =  "valerio.vannucci@iaiagi.com"
__status__     =  "Prototype"

# Import statements here
import time                                  # Time management
import can                                   # CAN Bus Python library

from can import Message                      # To manage CAN Bus messages with easy
from can.interface import Bus                # To manage CAN Bus interfaces with easy

# Custom functions here
def can_send_msg(canbusobj, canmsgobj, delay):
    """ Send a message on a specified CAN Bus channel and wait for a time in seconds """
    canbusobj.send(canmsgobj)                # Send a predefined message on the specified CAN Bus interface
    time.sleep(delay)                        # Wait for 'delay' time before returning to main application body
    return

# Global variables here
CAN_INTERFACE = 'socketcan'                  # Set CAN Bus interface support type
CAN_CHANNEL = 'can0'                         # Set CAN Bus interface channel name
CAN_BITRATE = 500000                         # Set CAN Bus interface channel bitrate


# Setting up can bus interface
can.rc['interface'] = CAN_INTERFACE          # Initiate can interface
can.rc['channel'] = CAN_CHANNEL              # Initiate can channel
can.rc['bitrate'] = CAN_BITRATE              # Initiate can bitrate

bus = Bus()                                  # Initiate CAN Bus

#
# Configuring Ford Fiesta CAN ID 0x201 to carry the following information:
#
# - Engine revolutions per minute: 870 (0x366) [combustion engine ON at minimum rpms]
# - Leave all other data bytes to their CAN Bus recordings detected value
#
msg = Message(extended_id=False, arbitration_id=0x201, data=[0x3, 0x66, 0x40, 0x0, 0x0, 0x0, 0x0, 0x80])

# Set message delay in seconds
msg_delay = 0.09                             # Message delay is 90ms 
disc_tout = 0.01                             # CAN Bus activity discovery timeout is 10ms

while True:                                  # Loops forever until application is stopped
    if bus.recv(disc_tout) != None:          # Waits 'disc_tout' seconds to see if monitored CAN Bus channel is active
        can_send_msg(bus, msg, msg_delay)    # If it is active send 'msg' on the monitored CAN Bus channel
                                             # and wait for "msg_delay' seconds