#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ccastHue.py - toggles Philipps Hue lights when using Chromecast
# (c) 2017 Federico Gentile

# Import needed modules

import yaml, requests, signal, sys, qhue, logging, os
from xml.etree import ElementTree
from time import sleep
import pychromecast
import pychromecast.controllers.youtube as youtube


# Preliminary logging engine setup

"Set up ccastHue's own logger"
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(asctime)s - %(message)s', datefmt='%Y/%m/%d %H:%M:%S')
logger = logging.getLogger(__name__)
"Set Request module's logger to only log message with a level of at least WARNING"
logging.getLogger("urllib3").setLevel(logging.WARNING)

# Functions

def get_ccast():
    casts = pychromecast.get_chromecasts()
    if len(casts) == 0:
        logPrint("No Chromecast devices found. Aborting ...",40)
        exit()
    return casts[0]

def ccast_active(cast):
    current_cast_status = cast.status.display_name
    if current_cast_status == config["ccast"]["app"]:
        return False
    else:
        return True

def hue_check_grp ( groups, designated_group ):
   "Check power state of designated Hue light group"
   return groups[designated_group]()["state"]["all_on"]

def hue_turn_grp ( hue_group ):
   "Turn designated Hue light group on or off"

def logPrint( message, level ):
   "Place holder for future proper loghandler"
   logger.log(level, message)

def sigint_handler(signal, frame):
   "SIGINT signal handler"
   global sigint_caught
   sigint_caught = True;

def tick_tock ():
   global tick_tock_state
   tick_tock_state = not tick_tock_state
   if tick_tock_state:
      return "[# ]"
   else:
      return "[ #]"

# Preliminary setup

"Set SIGINT signal handler variable to standard state (i.e. SIGINT not caught yet"
sigint_caught = False;

"Catch SIGINT"
signal.signal(signal.SIGINT, sigint_handler)

"Set status check variables to default values"
lock_in_use = False
lock_lights_off = False
tick_tock_state = False
status_message = ""

# Runtime

"Print welcome message"
print("ccastHue.py (c) 2017 Federico Gentile")
print()
logPrint("Starting ...",20)

"Load the configuration file in YAML format"
logPrint("Loading configuration file ... ",20)

try:
   stream = open(os.path.dirname(os.path.abspath(__file__))+"/config", 'r')
except IOError:
   logPrint("Could not find configuration file!",40)
   sys.exit("Aborting ...")
else:
   with stream:
      try:
         config = yaml.safe_load(stream)
         logPrint("Configuration file loaded successfully.",20)
      except yaml.YAMLError as yaml_error:
         logPrint("A YAML error was raised while reading the configuration file: " + str(yaml_error),40)
         sys.exit("Aborting ...")

"Initialising Hue bridge object from Qhue"
hue_bridge = qhue.Bridge(config["hue"]["ip"],config["hue"]["key"])

"Load Hue groups"
try:
   hue_groups = hue_bridge.groups
except qhue.QhueException as error:
   logPrint("Hue related error thrown: " + str(error) + ".",40)
   sys.exit("Aborting ...")

"Get Chromecast device"
cast = get_ccast()
logPrint("Got Chromecast: "+str(cast.device),20)
sleep(1)

while True:
   if ccast_active(cast):
      "Chromecast is being used"
      if lock_in_use == False:
         lock_in_use = True
         if hue_check_grp(hue_groups, config["self"]["group"]) == False:
            lock_lights_off = True
            status_message = "Chromecast in use, lights left untouched as they were already off."
         else:
            hue_groups[config["self"]["group"]].action(on=False)
            status_message = "Chromecast in use, lights turned off. "
   else:
      "Chromecast is not being used"
      if lock_in_use:
         if lock_lights_off == False:
            hue_groups[config["self"]["group"]].action(on=True)
            status_message = "Chromecast not in use anymore. Turning lights back on."
         else:
            lock_lights_off = False
            status_message = "Chromecast not in use anymore. Leaving lights off as they were off to start with."
         lock_in_use = False
   if sigint_caught:
      print()
      logPrint("SIGINT caught. Exiting ...",20)
      sys.exit(0)
   if status_message:
      print("\r", end="")
      logPrint("[>>] " + status_message,20)
      status_message = ""
   print("\r" + tick_tock() + " Sleep interval set to " + str(config["self"]["interval"]) + " seconds.",end="\r")
   sleep(config["self"]["interval"])


# Temporary testing

