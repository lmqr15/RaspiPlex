#!/usr/bin/env python
# -*- coding: UTF-8 -*-

""" 
  program :     sf_temp41.py
  author  :     crobat
  created :     20131129
  update  :     20160519
  node    :     RP50 IP 192.168.1.50 
  hostname:     Solarfarm

  NOTES : 
   On the 1W bus a resistor of 4K7 must be placed over the thermistor else the data dir will
   not be created

   =========== S T U B S to be implemented later ==========
   TEMPALERT and LED_BLINK are not finished awaiting installation Pi's @kitchen and @studio
   LED_BLINK will pilot:
   led_seven : seven segment display to indicate temp @ kachel
   led_rgb   : rgb led @ kachel
   led_8x8   : 2 color led array 8x8 @kachel
   led_32x32 : @kitchen & @studio

"""

import os, time, datetime, glob, sys
import RPi.GPIO as GPIO
import ephem

from bieb import *
from config_hms import *
from time import sleep

#                                                #
# ------------- INITIALIZING SYSTEM -------------#
#                                                #

# defines
DEBUG      = 0

# numerics
nSensors   = 0          	# number of  temp sensor
nTreshold  = 7          	# SF temp should be higher than Heater
nSleep     = 60
nTreshold_old = nTreshold 	# to preserve old preset

# string vars
base_dir  = '/sys/bus/w1/devices/'      # dir of all 1w divices
cKlep1    = KLEP1_STAND_A   		# 3-way valve
cMsg      = ''

# booleans
lKlep56   = False		# energy to atelier
lKlep78   = False		# energy to house
bEngaged  = False     		# solarfarm is closed when False

# -------------- SYSTEM INITIALISATION -------------------- #

GPIO.setwarnings(False)			# sys error disable
GPIO.setmode(GPIO.BCM)			# board settings

os.chdir(cDataDir)			# set doc directory
cSeason, nDoY = season()		# bieb.py from 273 - 130 = winter
""" One can override season manually by changing pool_status.sem not to contain 'open' """
if not pool_status():
  cSeason = "winter"

####################
cSeason = 'winter'	# REMOVE WHEN nDoY > 272
####################

# -------- set up 1w mod and temp dirs --------- #
if not file_exists(base_dir):
   if DEBUG:
      print "creating 1W device folders"

   os.system('sudo modprobe w1-gpio')
   os.system('sudo modprobe w1-therm')

try:
   device_folder = glob.glob(base_dir + '*')[0]            # dir waar sensor bestanden staan
   device_file   = device_folder + '/w1_slave'             # file temperatuur en ID sensoren
   dirlist       = os.listdir(base_dir)                    # lijst met bestanden sensoren

   for i in dirlist:                                       # laden files en sensoren
     if i[0:2] == '10' or i[0:2] == '28':
       device_folder = glob.glob(base_dir + i)[0]
       device_file = device_folder + '/w1_slave'
       file_list.append(str(device_file))

   nSensors = len(file_list)                               # no. of sensors in device dir

except:
   cMsg = TimeStamp("l") + ' | No data for sensors Garage'
   alert(cMsg,"No data 4 sensors Garage", "solarfarm")
   semafoor("sf.log", cMsg, "a")
   nSensors = 0

# --------------------------------------- #
# ------------- FUNCTIONS --------------- #
# --------------------------------------- #

#
# ---- open or close valve to cooling circuit ---- #
#
def cooling(bSwitch, cSection):

   aStand = ("off", "on")
   nStatus = 0

   GPIO.setup(KLEP_10_PIN,GPIO.OUT)           # init valve to circuit

   # valves are normal closed : NC
   if bSwitch:
      if cSection == "SF":
         # open valve 9 : Solar / pool too hot
         GPIO.output(KLEP_10_PIN, GPIO.HIGH)        # open circuit
      elif cSection == "FL":			    # floor studio
         # floor cooling
         # open valves to ate & cv and 3way to A
         pass

   elif not bSwitch:
      # close valve 10 : solar / pool cooled off
      GPIO.output(KLEP_10_PIN, GPIO.LOW)           # close circuit

   nStatus = GPIO.input(KLEP_10_PIN)

   cMsg = TimeStamp('sf') + " | sf_temp4 - cooling temperature t=" + str(nCooling) + "\n"
   cMsg += TimeStamp("sf") + " | sf_temp4 - valve cooling circuit v=" + aStand[nStatus]
   semafoor("cooling.dat", cMsg, "w")

   if DEBUG:
      print cMsg


   return

#
# ---- open or close valve to accumulator ---- #
# O B S O L E T E : copy for cooling circuit
#
def Accumulator(bSwitch, cSection):
   

      # remove accu.sem
   if file_exists("accu.sem"):
      os.system("rm accu.sem")

   if bSwitch:
      if cSection == "SF":
         # open valve 9 : SF too hot
         GPIO.setup(KLEP_9_PIN,GPIO.OUT)           # init valve to accu
         GPIO.output(KLEP_9_PIN, GPIO.HIGH)        # open accu
      else:
         # open valve 9 : CV too hot
         GPIO.setup(KLEP_10_PIN,GPIO.OUT)           # init valve to accu
         GPIO.output(KLEP_10_PIN, GPIO.HIGH)        # open accu
   else:
      if cSection == "SF":
         # close valve 9 : SF cooled off
         GPIO.setup(KLEP_9_PIN,GPIO.OUT)           # init valve to accu
         GPIO.output(KLEP_9_PIN, GPIO.LOW)        # open accu
      else:
         # close valve 10 : CV cooled off
         GPIO.setup(KLEP_10_PIN,GPIO.OUT)           # init valve to accu
         GPIO.output(KLEP_10_PIN, GPIO.LOW)        # open accu
      

   return
#
# ------ determine daylight time ------ #
#
def daytime():

    nHour = get_hour()

    # google maps pos. solar farm
    home_lat   = '47.921485'
    home_long  = '6.132854'
    home_elev  = 280
    # sun above horizont in MSP bij 25
    home_hor   = '15'

    # set up parameters for observer / point ephem library
    o = ephem.Observer()
    o.lat  = home_lat
    o.long = home_long
    o.elevation = home_elev
    o.horizon = home_hor

    #define sun as object of interest
    s = ephem.Sun()
    # next sunset & sunrise
    sunrise = o.next_rising(s)
    sunset  = o.next_setting(s)
    sr_next = ephem.localtime(sunrise)
    ss_next = ephem.localtime(sunset)

    if DEBUG:
       print "nHour ..... :",nHour
       print "sunrise ... :",sr_next.hour + 1
       print "sun set ... :",ss_next.hour + 1

    if (nHour >= sr_next.hour + 1) and (nHour <= ss_next.hour):
       return True

    return False
#
# ---------- Open all valves to the house from the SolarFarm ----------------
#
def Open_SF():

   GPIO.setup(KLEP_5_6_PIN,GPIO.OUT)           # init valve to atelier
   GPIO.output(KLEP_5_6_PIN, GPIO.HIGH)        # open atelier

   GPIO.setup(KLEP_7_8_PIN,GPIO.OUT)           # init valves to house
   GPIO.output(KLEP_7_8_PIN, GPIO.HIGH)        # open house

   GPIO.setup(KLEP_1_PIN,GPIO.OUT)             # init klep1
   GPIO.output(KLEP_1_PIN,GPIO.LOW)            # set 3W valve to position B

   cMsg  = TimeStamp("l") + " | SolarFarm opened at " + str(nSolar) + " temp SF garage at " + str(nGarage)
   cMsg += "\n" + TimeStamp("l") + " | 3W valve50 in position " + KLEP1_STAND_B
   semafoor("sf.log",cMsg,"a")

   cMsg = TimeStamp("l") + " | 3W valve in position t=" + KLEP1_STAND_B
   semafoor("drieweg.dat",cMsg,"w")
   cMsg = TimeStamp("l") + " | valves 5 & 6 - atelier t=on"
   semafoor("klep56.dat",cMsg,"w")
   cMsg = TimeStamp("l") + " | valves 7 & 8 - house t=on"
   semafoor("klep78.dat",cMsg,"w")

   return True

#
# ---------- Open all valves to the house from the SolarFarm ----------------
#
def Close_SF():

   GPIO.setup(KLEP_1_PIN,GPIO.OUT)             # init klep1
   GPIO.output(KLEP_1_PIN,GPIO.HIGH)           # set 3W valve to position A

   GPIO.setup(KLEP_5_6_PIN,GPIO.OUT)           # init valve to atelier
   GPIO.output(KLEP_5_6_PIN, GPIO.LOW)         # close valve to atelier

   GPIO.setup(KLEP_7_8_PIN,GPIO.OUT)           # init valves to house
   GPIO.output(KLEP_7_8_PIN, GPIO.LOW)         # close valve to house

   cMsg  = TimeStamp("l") + " | SolarFarm closed at " + str(nSolar) + " temp SF garage at " + str(nGarage)
   cMsg += "\n" + TimeStamp("l") + " | 3W valve50 in position " + KLEP1_STAND_A
   semafoor("sf.log",cMsg,"a")

   cMsg = TimeStamp("l") + " | 3W valve50 in position t=" + KLEP1_STAND_A
   semafoor("drieweg.dat",cMsg,"w")
   cMsg = TimeStamp("l") + " | valves 5 & 6 - atelier t=off"
   semafoor("klep56.dat",cMsg,"w")
   cMsg = TimeStamp("l") + " | valves 7 & 8 - house t=off"
   semafoor("klep78.dat",cMsg,"w")

   return False

#
# ----------------- SF POMP ON or OFF ----------------
#
# SF PUMP SHOULD  N E V E R  BE SWITCHED OFF IN  W I N T E R
""" 
pump is always on in winter that is provided in close_all.py 
set relay for pump low see close_all.py
"""

def pump_sf(cStand, bSwitch = None):

   GPIO.setup(SFPOMP_PIN,GPIO.OUT)   	# SF pomp GPIO set up

   aStatus     = (True, False)		# status switch
   aStand      = ("on", "off")

   if cStand == "a":
      GPIO.output(SFPOMP_PIN,GPIO.LOW)	# pump ON
   elif cStand == "u":
      GPIO.output(SFPOMP_PIN,GPIO.HIGH)	# pump OFF
              
   pomp_status = GPIO.input(SFPOMP_PIN)

   cMsg = TimeStamp("l") + " | SF pump pompstatus t=" + str(aStand[pomp_status])

   # 2 report only once per cycle or when situation changed
   if bSwitch:
      semafoor("sf.log",cMsg,"a")
      sleep(0.2)
      semafoor("solarpump.dat",cMsg,"w")
      bSwitch = False

   if DEBUG:
     print cMsg
 
   return aStatus[pomp_status], bSwitch

#
# -------- collect temps from semafoor files -------- #
#
""" 
solar temps are measured by RP53: solar.dat
kachel temp are measured bij RP51: kachel.dat
RP50 reads incoming SF temp: sfgar.dat

See 4 actual ID codes config_hms.py

"""

def read_temps(nTemp): 	# for testing purposes nTemp should have value > 0

   global nSolar
   global nKachel
   global nFloor

   global nGarage
   global nRetour
   global nAtel
   global nCooling

   with open("solar.dat", "r") as f:
      line = f.readline()
      cStr = line.split('t=')[-1]
      nSolar = float(cStr[:-1])
      
   with open("kachel.dat", "r") as f:
      line = f.readline()
      cStr = line.split('t=')[-1]
      nKachel = float(cStr[:-1])

   with open("floor.dat", "r") as f:
      line = f.readline()
      cStr = line.split('t=')[-1]
      nFloor = float(cStr[:-1])

   if nSensors <> 0:

      for x in xrange(0, nSensors):                        # read all sensors
         device_file = file_list[x]                        # sensor file
         sensorID    = device_file[30:len(device_file)-9]  # ID sensor

         cTemp = temp_read(device_file)		   # bieb.py
         nTemp = round(float(cTemp),1)
         
         if sensorID == ID_sfgar:
            nGarage  = nTemp
         elif sensorID == ID_cooling:
            nCooling  = nTemp
         elif sensorID  == ID_atel:
            nAtel = nTemp
         elif sensorID  == ID_retour:
             nRetour = nTemp


   return

# ---------------------------- #
# -------- M A I N ----------- #
# ---------------------------- #
def main():

   bSF_Engaged  = False			# engage SF
   bPump        = False			# engage pump
   bCool 	= False			# engage cooling circuit

   file_name =  os.path.basename(sys.argv[0])
   boot_script(cDataDir, file_name)     # report in log.sf when this script started
   read_temps(0)
   Close_SF() 				# reset SF

   GPIO.setup(SFPOMP_PIN,GPIO.OUT)   	# SF pomp GPIO set up
   
   cMsg = TimeStamp("s") + " | solarfarm loop started" + cSeason + " Pump status " + str(bPump) 

   if DEBUG:
      print cMsg

   semafoor("sf.log", cMsg, "a")   

   while True:

      if cSeason == "winter":
         if not bPump: 
            bPump = pump_sf("a", bPump)[1]		# engage SF pump

         while nGarage > (nKachel + nTreshold):   # temperature SF should be higher
            if DEBUG:
               print "nSolar, nGarage, nKachel, diff, engaged", nSolar, nGarage, nKachel,
               print (nSolar - (nKachel + nTreshold)), str(bSF_Engaged)

            if not bSF_Engaged:
               bSF_Engaged = Open_SF()	# true after first pass
            
            sleep(nSleep)
            read_temps(0)			# for testing purpose pass value

         # close SF when valves 7/8 to house are still open
         GPIO.setup(KLEP_7_8_PIN,GPIO.OUT)

         if (GPIO.input(KLEP_7_8_PIN)==1):   
            bSF_Engaged = Close_SF()

      elif cSeason == "summer":
         # no valves should open except hottub & boiler. 
         #   Or cooling to floor when desired
         # open_hottub()
         # open_boiler()

         if DEBUG:
            print "SolarFarm ....", nSolar
            print "Garage .......", nGarage
            print "Cooling ......", nCooling
            print "Floor ........", nFloor
            print "Retour .......", nRetour
            print "Treshold .....", nSolar - nSolMax

         # --- cooling --- #
         if nSolar > nSolMax:
            cooling(True, "SF")			# open valve to cooling circuit
            bCool = True
         
         if bCool:
            cooling(False, "SF")		# close valve to cooling circuit
            bCool = False
         else:
            cooling(None, "SF")			# generate cooling.dat

         pump_status = GPIO.input(SFPOMP_PIN)

         if daytime():				# sf pump ON only during daytime
            if pump_status == 1:		        	
               pump_sf("a", True)	 	# engage SF pump
         else:
            if pump_status == 0:
               pump_sf("u", True)		# dis-engage SF pump

      if not DEBUG:
         sleep(nSleep)
      else:
         sleep(15)

      read_temps(0)				# for testing purpose pass value
  

# --- GO TO M A I N ---- #
if __name__ == "__main__":
   main()


