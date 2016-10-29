#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import RPi.GPIO as GPIO
import time
import os
import glob
import time, datetime
import re, sys
import signal
import ephem    # bereken plaats hemellichamen

from bieb import semafoor, TimeStamp, sunset
from datetime import timedelta
from time import sleep, localtime
from config_hms import *

# ====== initialisation =======
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
#os.system('sudo modprobe w1-gpio')                      # aanmaken output dir
#os.system('sudo modprobe w1-therm')                     # aanmaken bestand d$
os.chdir("/media/ssd/solarfarm/")         		# set doc directory

# file vars  
#base_dir      = '/sys/bus/w1/devices/'                  # dir van alle divic$
#dirList       = os.listdir(base_dir)                    # lijst met bestande$
#device_folder = glob.glob(base_dir + '*')[0]          # dir waar sensor bestanden staan
#device_file   = device_folder + '/w1_slave'             # file temperatuur en ID sensoren
#dirlist       = os.listdir(base_dir)                    # lijst met bestanden sensoren
    
# ====== STATICS ==============
LEDPORT         = 18                            # led
RELAY_CV        = 17                            # relays poort no..
RELAY_FLOOR     = 2                             # NOP !!!! relay
RELAY_KLEP51    = 3
RELAY_BOILER    = 14 				# GPIO  - PIN => 8
RELAY_STUDIO    = 18 				# GPIO  - PIN => 12

ID_kachel       = "397ce"                       # temp water heater
ID_floor        = "40801"			# temp floor


# ========= string vars ======
answer = ""

def boiler1():

# boiler works the other way around as pumps

   aStand = ("off","on")
   answer = ""

   GPIO.setup(RELAY_BOILER,GPIO.OUT)     # FLOOR PUMP

   bl_status = GPIO.input(RELAY_BOILER)
   status_old = bl_status

   while True:

      print "\nBoiler is : ", aStand[bl_status]

      answer = raw_input("\n Boiler ROOMS (u)p or (d)own (q)uit : ")

      if answer == "u":
         GPIO.output(RELAY_BOILER,GPIO.HIGH)
      elif answer == "d":
         GPIO.output(RELAY_BOILER,GPIO.LOW)

      sleep(0.3)
      bl_status = GPIO.input(RELAY_BOILER)

      if answer == "q":
         break

      if status_old <> bl_status:
         bl_status = GPIO.input(RELAY_BOILER)
         cMsg = TimeStamp("cv") + " cv_utils - Boiler ROOMS t=" + aStand[bl_status]
         semafoor("boiler-rooms.dat",cMsg,"w")
         cMsg = TimeStamp("l") + " | cv_utils - Boiler ROOMS switched: " + aStand[bl_status]
         semafoor("sf.log",cMsg,"a")

      status_old = bl_status

   return


def boiler5():

# boiler works the other way around as pumps

   aStand = ("off","on")
   answer = ""

   GPIO.setup(RELAY_STUDIO,GPIO.OUT)     # FLOOR PUMP

   bl_status = GPIO.input(RELAY_STUDIO)
   status_old = bl_status

   while True:

      print "\nBoiler STUDIO is : ", aStand[bl_status]

      answer = raw_input("\n Boiler STUDIO (u)p or (d)own (q)uit : ")

      if answer == "u":
         GPIO.output(RELAY_STUDIO,GPIO.HIGH)
      elif answer == "d":
         GPIO.output(RELAY_STUDIO,GPIO.LOW)

      sleep(0.3)
      bl_status = GPIO.input(RELAY_STUDIO)

      if answer == "q":
         break

      if status_old <> bl_status:
         bl_status = GPIO.input(RELAY_STUDIO)
         cMsg = TimeStamp("cv") + " cv_utils - Boiler STUDIO t=" + aStand[bl_status]
         semafoor("boiler-studio.dat",cMsg,"w")
         cMsg = TimeStamp("l") + " | cv_utils - Boiler STUDIO switched: " + aStand[bl_status]
         semafoor("sf.log",cMsg,"a")

      status_old = bl_status

   return


#
# ---------- toggle 3 way valve 51 ---------------
#
def drieweg51():

  pass

  return

#
# ---------- toggle out of office -----------------
#
def out_of_office():

   with open("ooo.sem", "r") as fo:
      line = fo.readlines()

   if "NO" in line[0]:
      cStr = "NO"
   else:
      cStr = "YES"
      
   cOld = cStr

   print "\nOut of Office set to: ", cOld, "\n"

   answer = raw_input("\n Out of office? (Y)es N(o) (q)uit : ")

   if answer.upper() == "Y":
      cStr = "YES"
   elif answer.upper() == "N":
      cStr = "NO"
   elif answer.upper() == "Q":
      return

   print "\nOut of Office is now: ", cStr, "\n"
   cMsg = TimeStamp("ooo") + "Out of Office t="+cStr
   semafoor("ooo.sem",cMsg,"w")

   return    

#
# ----------  manage floor pump studio ------------
#
def pump_studio():

   # write semafoor to SSD @kachel will react on that
   # replace with SQL

   # get temp kachel from semafoor file


   aStand = ("on","off")
   answer = ""

   GPIO.setup(RELAY_FLOOR,GPIO.OUT)   	# FLOOR PUMP

   pump_status = GPIO.input(RELAY_FLOOR)
   status_old = pump_status

   while True:

      print "\nFloor pump is : ", aStand[pump_status]

      answer = raw_input("\n Pomp Studio (a)an of (u)it (q)uit : ")

      if answer == "a":
         GPIO.output(RELAY_FLOOR,GPIO.LOW)
      elif answer == "u":
         GPIO.output(RELAY_FLOOR,GPIO.HIGH)

      sleep(0.3)

      pump_status = GPIO.input(RELAY_FLOOR)

      if answer == "q":
         break

   pump_status = GPIO.input(RELAY_FLOOR)
   cMsg = TimeStamp("cv") + " cv_utils - Floor pump t=" + aStand[pump_status]
   semafoor("floorpump.dat",cMsg,"w")
   cMsg = TimeStamp("l") + " | cv_utils - Floor pump switched: " + aStand[pump_status]
   semafoor("sf.log",cMsg,"a")
   
   return


###### HEATER PUMP ON / OFF #############
#
#
def pump_cv():

   answer = ""

   GPIO.setup(RELAY_CV,GPIO.OUT)   # heater pump
   aStand = ("on","off")

   pump_status = GPIO.input(RELAY_CV)
   status_old = pump_status

   while True:

      print "\nHeater pump is : ", aStand[pump_status]

      answer = raw_input("\nHeater pump (a)an (q)uit of (u)it : ")

      if answer == "a":
         GPIO.output(RELAY_CV,GPIO.LOW)
      elif answer == "u":
         GPIO.output(RELAY_CV,GPIO.HIGH)

      sleep(0.3)
      pump_status = GPIO.input(RELAY_CV)
      print cHeader
      print pump_status

      if answer == "q":
        break

   pump_status = GPIO.input(RELAY_CV)

   cMsg = TimeStamp("cv") + " cv_utils - Heater pump t=" + aStand[pump_status]
   semafoor("cv_pump.dat",cMsg,"w")
   cMsg = TimeStamp("l") + " | cv_utils - Heater pump switched: " + aStand[pump_status]
   semafoor("sf.log",cMsg,"a")

#
# ========= tail logfile ==========
# 
# log file vanaf een bepaalde regel laten zien
# 	head -30 text.file | tail -20 > output.file 
# backup logfile 
#	1 x maand en nieuwe log starten met laatste 10 regels

def logfile():

   while True:
   
      answer = raw_input("\nToon staart log file, type aantal regels of (q)uit : ")

      if answer <> "q" or answer <> "":
         cStr = "tail -" + answer + " sf.log" 

         if answer == "": 
            cStr = "tail sf.log" 

         print "\n============= staart logfile SF ============\n"  
         os.system(cStr)
         print "\n============== end logfile SF ==============\n"  

         cMsg = TimeStamp("l") + " | logfile CV shown"
         semafoor("sf.log",cMsg,"a")

      if answer == "q":
         break

#
# ----- display status all valves and pumps ------
#
def status_dashboard():

   aStand = ("on","off")
   answer = ""

   GPIO.setup(RELAY_FLOOR,GPIO.OUT)     # FLOOR PUMP
   GPIO.setup(RELAY_CV,GPIO.OUT) 	# heater pump

   pump_studio = GPIO.input(RELAY_FLOOR)
   pump_heater = GPIO.input(RELAY_CV)

   with open("solarpump.dat", "r") as fo:
      line = fo.readlines()
      if "on" in line:
         pump_solar  = 0
      else:
         pump_solar  = 1

   print pump_solar
   sleep(.2)

   with open("poolpump.dat", "r") as fo:
      line = fo.readlines()
      if "on" in line:
         pump_pool  = 0
      else:
         pump_pool  = 1

   sleep(.2)

   with open("drieweg.dat", "r") as fo:
      line = fo.readlines()
      if "A" in line:
         klep50 = "A"
      else:
         klep50 = "B"

   sleep(.2)

   with open("klep56.dat", "r") as fo:
      line = fo.readlines()
      if "on" in line:
         klep56 = 0
      else:
         klep56 = 1

   sleep(.2)

   with open("klep78.dat", "r") as fo:
      line = fo.readlines()
      if "on" in line:
         klep78 = 0
      else:
         klep78 = 1

   sleep(.2)

   with open("klep9.dat", "r") as fo:
      line = fo.readlines()
      if "on" in line:
         klep9 = 0
      else:
         klep9 = 1

   sleep(.2)

   with open("klep10.dat", "r") as fo:
      line = fo.readlines()
      if "on" in line:
         klep10 = 0
      else:
         klep10 = 1

   
   klep51     = 'A'   # heater 3way valve
   klepboiler = 1
   klephottub = 1

   print "\n============ Status DashBoard ============"
   print "Solar Pump ..... : " + aStand[pump_solar]
   print "Heater Pump .... : " + aStand[pump_heater]
   print "Studio Pump..... : " + aStand[pump_studio]
   print "Pool Pump .,.... : " + aStand[pump_pool]
   print "Valve 3way 50 .. : " + klep50
   print "Valve 3way 51 .. : " + klep51
   print "Valve Atelier .. : " + aStand[klep56]
   print "Valve Accu ..... : " + aStand[klep9]
   print "Valve Accu Pool  : " + aStand[klep10]
   print "Valve Boiler ... : " + aStand[klepboiler]
   print "Valve HotTub ... : " + aStand[klephottub]
   print "="*40
   print "\n"

   return True

#
# =======  M A I N  ==============
#   
answer = ""

while True:
  
   print "\n\n ------------------- CV  U T I L S - 2 ---------------------\n"
   
   cRegel  = " (A) Out_Of_Office                   (I) Heater pump \n" 
   cRegel += " (B) Boiler ROOMS                    (K) NOP\n"
   cRegel += " (C) NOP                             (L) Studio pump \n" 
   cRegel += " (D) 3 Way valve 51                  (M) log file \n"
   cRegel += " (E) NOP                             (N) NOP  \n"
   cRegel += " (F) Status DB                       (O) temperatures \n"
   cRegel += " (G) NOP                             (P) sunset sunrise \n"
   cRegel += " (H) NOP                             (S) Boiler STUDIO \n"
   cRegel += "\n (Q) QUIT"
   
   print cRegel
   print "\n" + ('-'*80)[:60] 
   
   answer = raw_input("Keuze : ")


   answer = answer.upper()

   if answer == "A":
      out_of_office()   
   elif answer == "D":
      drieweg51()
   elif answer == "B":
      boiler1()
   #elif answer == "E":
   #elif answer == "K":
   #elif answer == "N":
   #elif answer == "D":
   elif answer == "M":
      logfile()
   elif answer == "F":
      status_dashboard()
      os.system('./get_temp.py')
   elif answer == "I":
      pump_cv()
   elif answer == "P":
      print sunset()
   elif answer == "O":
      os.system('./get_temp.py')
      print "\ncompleted\n" 
   elif answer == "L":
      pump_studio()
   #elif answer == "G":
   #   vullen()
   elif answer == "S":
      boiler5()
   elif answer == "Q":
      break

   answer =""


