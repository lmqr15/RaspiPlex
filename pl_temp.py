#!/usr/bin/python
# -*- coding: utf-8 -*-

""" 
  source .... zwembad.py
  created ... 20150507
  author .... crobat
  updates ... 20151223

  UPDATES ARE WRITTEN and tested in pl_temp11.py
  then copied to pl_temp.py

specs pump
   pump regulator ATV12H075M2 price 190E
   pump type M2 71/2 price 440E incl filter system
   fournisseur: www.variateur-frequence.fr

design

  OK to replace barometric value in climate.txt 
	OK 20160519 humidity DHT22
	moved to pl_climate
  OK to replace pool temp in pool.dat
  OK to replace poolpump.dat
  OK to vary pump speeds in ranges of temps
  OK OSError handling when raspi fails to start
  OK IOError handling when raspi fails to write to file
  OK 20160519 barometer BM080
	moved to pl_climate
  OK 20160519 luminocity
	moved to pl_climate
  OK 20160816 cooling during night hours
  OK 20160903 extra threshold 'nSummer' is set to zero when daynumber > 250
        see yeargraph intranet
  OK 20160904 made threshold engaging higher than threshold disengaging > nThreshold 
        is now resp. 6 and 4; see: http://www.energieplus-lesite.be/index.php?id=16760

  TODO 
     compensate for energy on certain day = sun above horizon
        if sun low threshold becomes lower

     to analyse optimal temp and rpm ranges

     to fill dictionary to make swithing relays more efficient: fill_dict()
     
     create MPI interface to send msg to other nodes
           to open valves via RP50 when temp pool > 28C @ night
              from stats: 06-07 is coldest moment of day
           to activate night vision
           to follow intruders

     to establish a hardware reset when raspi does not start
         or communicates with network via resetbutton
            1) interrupt driven deamon on RP50 and or RP60 should 
               powerdown RP53 when no connection via relais
            2) relais connected to RP50 (that one should check RP53)
               when power should be interupted via PoE
            3) power down signal could also be generated via RP60 via MPI

     to create a PoE power supply to draw current from AP in pump house

     to have a camera installed that can be moved from a distance => see raspi SE90 
	sound check
        sheep count : delegated to james jackman via work-a-way
	cloudiness
	security
        motion control with motors (parts received 20160520)
           20160816 assembled first unit
           need PWM possibly combo with RPI3 
           camera test environment = SE90 + camera

     a motion detector during night or absence

     distance detection coupled on motion detector and camera
        gives alert when OOO.

     to anticipate on weather predictions next 2 days
        needs to screenscrape meteo france site
           20160804 screenscraping prototype works
        if prediction is bad weather then cooling should not take place
          cooling will then be done by natural low temperatures or cloudyness

     it would be interesting to see what the influence is of nightly 
       low temps the next sunny day and how that influences the warming up
       or cooling down. e.g. how long does it takes to warm up to 29 degr.
       after cold nights or hot days or forced natural cooling when pumps stay on

     to callibrate lumen meter, now lumens are measured but the impression is the 
        measurements give back too low values. It could be considered to replace the
        opaque dome with a clear dome to get better readings.

     connect rp51 to lamp in studio to indicate cooling seq is running
        or attach lamp on rooftop pumphouse
        move both 'pump running' and 'cooling on' to turret pumphouse
        RGB leds could give better indication + combine with PWM  

     20160816 ADDED lights() 
        see TO for development: lights.py
        move to pl_lights() [also burglar alert or doorbell]  
        lights(DEFINE,1)  : to switch a light 1=on 0=off
        still needs to define and connect relays
        install leds in garden 
        switch alert light on when cooling

   ################                                      ##############
      NOTE: in winter remove pool sensor when possible > temp = outside temp
   ################                                      ##############

"""

import os, glob, socket, sys
import time, datetime, ephem
import RPi.GPIO as GPIO

from bieb import *
from config_hms import *
from time import sleep

# =====  directories and sensors  =========
#
cMsg            = ""

nSol    	= 11.11
nPool    	= 11.11
nBuiten   	= 11.11
nGround         = 11.11
nThreshold	= 6	# threshold for exchanger / pool / pump
nPoolThreshold  = 28
nSleep  	= 60	# wait till pump sucks enough water
nOldSet 	= 99

aHz             = [0,10,15,25,30,35,40,50]
aRpm            = ["0","560","840","1400", "1680","1960", "2240", "2800"]
aSet            = ["000","001","010","011","100","101","110","111"]

dict()

file_list       = list() 

script_name     = os.path.basename(sys.argv[0])

# in case main disk does not mount try it again
# libraries are also available locally
try:
   os.chdir(cDataDir)
except:
   # force mounting disk solarfarm RP60
   cStr ="sudo mount -t cifs -o user=" + rp_usr + ",password=" + rp_pwd + " //192.168.1.60/share /media/ssd"
   os.system(cStr)
   os.chdir(cDataDir)

cSeason, nDay   = season()

""" One can override season manually by changing pool_status.sem not to contain 'open' """
if not pool_status(): 
  cSeason = "winter"

GPIO.setwarnings(False) 
GPIO.setmode(GPIO.BCM)

DEBUG         = 0

# set relay GPIO numbers when installed
RELAY_POOL    = 0
RELAY_ALERT   = 0
RELAY_GARDEN  = 0
SEPARATOR     = 'ID_'

cNet = "192.168.1." # node IP.self = get_ip()

#                                                    #
# ------------  F U N C T I O N S  ----------------- #
#                                                    #

# ------ fill dictionary -------- #
def fill_dict():

   with open("config_hms.py",'r') as d:
      for line in d.readlines():
         if SEPARATOR in line:
            s = line.split('=')
            value = s[0].strip(SEPARATOR).strip()
            if  DEBUG:
               print value

            key = s[1].split('"')
            dict[key[1]]=value

      if DEBUG:
         print dict

#
# ------ switch pool light on / off -------- #
#
def lights(nRelay, nSet):
   # TODO 
   #    with PWM make a running light for cooling and alert
   #    pass modus to indicate pwm of not / flashing
   #    if nSet = 112 => BURGLAR ALERT

   GPIO.setup(RELAY_POOL, GPIO.OUT)              # init relays 
   GPIO.setup(RELAY_ALERT, GPIO.OUT)
   GPIO.setup(RELAY_GARDEN, GPIO.OUT)

   if nSet == 0 and cSelect =="all":
      # switch off all lights
      GPIO.output(RELAY_POOL, GPIO.LOW)
      GPIO.output(RELAY_ALERT, GPIO.LOW)
      GPIO.output(RELAY_GARDEN, GPIO.LOW)
   elif nSet <> 0:
      GPIO.output(nRelay, GPIO.HIGH)
   elif nSet == 0:
      GPIO.output(nRelay, GPIO.LOW)
 
   return True

   
# 
# --------------- MESSAGE PROTOCOL INTERFACE ----------------- #
#
def MPI_client(cRule = None, nRPI = None):
   
   if nRPI == None:
      return

   nPort  = MPI_PORT
   bOK    = True	# all went OK?
   nCount = 0

   cNode = cNet + str(nRPI)

   # create socket connection to node: nNode
   s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

   s.connect(cNode, nPort)

   # send cRule to RP50 port 192016
   # actions can be 
   #   cRule : 'open cooling'
   #   cRule : 'close cooling'
   # see rules.py on RP52 too
   print 'send to server: ' + cRule
   s.send(cRule)
  
   while s.recv(2048) != "ack":
      print "waiting for ack"
      nCount +=1
      if nCout > 5:
         bOK = False
         break

   print "ack received!"

   s.close()

   return bOK

# 
# --------------- close all relays ----------------- #
#
def relays_close():

   if file_exists('pl_utils.sem'):
      return

   GPIO.setup(PL_PUMP,   GPIO.OUT)             	# init relay 1
   GPIO.setup(PL_RELAY_2,GPIO.OUT)             	# init relay 2
   GPIO.setup(PL_RELAY_3,GPIO.OUT)             	# init relay 3
   GPIO.setup(PL_RELAY_4,GPIO.OUT)             	# init relay 4
   GPIO.setup(PL_LAMP,   GPIO.OUT)             	# init relay 6

   GPIO.output(PL_PUMP,    GPIO.HIGH)
   GPIO.output(PL_RELAY_2, GPIO.HIGH)		# relays 2-4 binary combination
   GPIO.output(PL_RELAY_3, GPIO.HIGH)		# of speed setting : 8 speeds
   GPIO.output(PL_RELAY_4, GPIO.HIGH)
   GPIO.output(PL_LAMP,    GPIO.HIGH)

   cMsg = TimeStamp("l") + " | " + script_name + " Relays 1-6 closed"
   semafoor("sf.log",cMsg,"a")

   # simplified 2 signal pump on or off
   cMsg = TimeStamp("l") + " | pl_temp - status poolpump t=off\n"
   cMsg += TimeStamp("l") + " | pl_temp - Pump runs at r=0"
   semafoor("poolpump.dat", cMsg, "w")

   return

#
# ----------- get temperatures from w1_slave ------------
#

def get_temp(f_dev):

   nCount = 0
   cMsg = ""
   
   while nCount < 20:
      try:
         with open(f_dev, 'r') as f:
            lines = f.readlines()

         equals_pos = lines[1].find('t=')

         if equals_pos != -1:
            temp_string = lines[1][equals_pos+2:]
            temp_c = str(round((float(temp_string) / 1000),1))
            return temp_c

      except IOError as (errno, strerror):
         nCount += 1
         cMsg =  TimeStamp("l") + ' | I/O error({0}): {1}'.format(errno, strerror)
         print cMsg
         semafoor("sf.log", cMsg, "a")     		    # report in log
         sleep(0.02)
         
   if nCount > 0:  # failed to get temps
      cMsg = TimeStamp("l") + ' | No data for sensors SolarFarm polled'
      print cMsg
      #alert(cMsg, "Alert, pl_temp failed getting temps", "Solarfarm")    # send email

      # get last temp from pool file
      with open("pool.dat", 'r') as f:
         lines = f.readline()
 
      temp_c  = line.split('t=')[-1]
      return temp_c

   return 

#
# ----------  get temps from outside ---------------
#
def read_temps():

   global nSol
   global nPool
   global nBuiten
   global nGround

   # dummy values to avoid static data @ misfiring sequence
   nSolOld  = nSol   #11.13
   nOutOld  = nBuiten
   nGrOld   = nGround
   nPoolOld = nPool

   nSensors = 0

   file_list = list()

   if not file_exists(base_dir):
      os.system('sudo modprobe w1-gpio')
      os.system('sudo modprobe w1-therm')

   try:
      device_folder = glob.glob(base_dir + '*')[0]            	# dir waar sensor bestanden staan
      device_file   = device_folder + '/w1_slave'             	# file temperatuur en ID sensoren
      dirlist       = os.listdir(base_dir)                    	# lijst met bestanden sensoren

      for i in dirlist:                                       	# laden files en sensoren
        if i[0:2] == '10' or i[0:2] == '28':
          device_folder = glob.glob(base_dir + i)[0]
          device_file = device_folder + '/w1_slave'
          file_list.append(str(device_file))

      nSensors = len(file_list)                               	# no. of sensors in device dir

   except IOErorr as e:
      cMsg = TimeStamp("l") + ' | ' + script_name + ' no temp sensors detected ' + str(e)

      if not DEBUG:
         alert(cMsg, "Alert, no temp sensors", "Solarfarm")    	# send email
         semafoor("sf.log", cMsg, "a")     		    	# report in log
      else:
         print cMsg

      nSensors = 0

   if nSensors <> 0:

      if DEBUG: 
         print "number of sensors :",nSensors

      for x in xrange(0, nSensors):                     	# read all sensors
         device_file = file_list[x]                        	# data file
         sensorID    = device_file[30:len(device_file)-9]  	# ID sensor
         cTemp       = get_temp(device_file)
         nTemp       = float(cTemp)

         if DEBUG:
            print sensorID, cTemp, nTemp

         if sensorID == ID_solar:

            # if extreme temps are measured get last temp reading
            ceiling = 85 
            floor = 0.1    

            if nTemp > ceiling or nTemp < floor:
               if DEBUG:
                  print "solar error in temp:", nTemp, nSolOld

               with open("solar.dat", 'r') as f:
                  line   = f.readline()
                  cTemp  = line.split('t=')[-1]
                  nTemp  = float(cTemp)

            else:
               cMsg = TimeStamp("t") + " | Temp SolarFarm t=" + cTemp
               semafoor("solar.dat",cMsg, 'w')

            nSolOld = nTemp
            nSol = nTemp                 

            if DEBUG:
               print "-" * 25
               print "cMsg = ", cMsg
               os.system("cat solar.dat")
               print "-" * 25
           
         elif sensorID == ID_pool:

            # if extreme temps are measured get last temp reading
            ceiling = 50 
            floor = -21

            if nTemp > ceiling or nTemp < floor:
               with open("pool.dat", 'r') as f:
                  line   = f.readline()
                  cTemp  = line.split('t=')[-1]
                  nTemp  = float(cTemp)
            else:  
               cMsg = TimeStamp("t") + " | Temp Pool t=" + cTemp
               semafoor("pool.dat",cMsg, 'w')

            nPoolOld = nTemp
            nPool = nTemp                 

            if DEBUG:
               print "-" * 25
               os.system("cat pool.dat")
               print "-" * 25

         elif sensorID  == ID_buiten:

            nBuitenOld = nTemp

            cMsg = TimeStamp("t") + " | Temp Outside t=" + cTemp
            semafoor("buit.dat",cMsg, 'w')

            nBuiten = nTemp                 

         elif sensorID == ID_ground:
            nGroundOld = nTemp

            cMsg = TimeStamp("t") + " | Temp Ground t=" + cTemp
            semafoor("ground.dat",cMsg, 'w')

            nGround = nTemp                 


   if DEBUG:
      print "Temps: Sol, Pool, Buiten, Ground", nSol, nPool, nBuiten, nGround
        
   return True

#
# ------------------- set relay to binary combination ------- #
#
#
#  ATTENTION: relay works inverted
#
# see: https://www.raspberrypi.org/forums/viewtopic.php?f=45&t=22334
#
def set_relays(i):

   if file_exists('pl_utils.sem'):
      return

   global nOldSet

   # set should be in binairy form: "0110"
   # for testing full power set i to 7
   # relay 1 is start and stop
   # relay 6 = lamp
   # relays 2,3,4 set speed
   # relays 5,7,8 NOP must be off

   if nOldSet == i:
      return
   else:
      nOldSet = i

   cStatus     = [ "on", "off" ]

   GPIO.setup(PL_RELAY_1,GPIO.OUT)
   GPIO.setup(PL_RELAY_2,GPIO.OUT)
   GPIO.setup(PL_RELAY_3,GPIO.OUT)
   GPIO.setup(PL_RELAY_4,GPIO.OUT)
   GPIO.setup(PL_RELAY_5,GPIO.OUT)
   GPIO.setup(PL_RELAY_6,GPIO.OUT)
   GPIO.setup(PL_RELAY_7,GPIO.OUT)
   GPIO.setup(PL_RELAY_8,GPIO.OUT)

   # close all relays when set = "0"
   if i == 0:
      GPIO.output(PL_RELAY_1, GPIO.HIGH)        # pump off
      GPIO.output(PL_RELAY_5, GPIO.HIGH)        # NOP
      GPIO.output(PL_RELAY_6, GPIO.HIGH)        # lamp off
      GPIO.output(PL_RELAY_7, GPIO.HIGH)        # NOP
      GPIO.output(PL_RELAY_8, GPIO.HIGH)        # NOP
   else:
      GPIO.output(PL_RELAY_1, GPIO.LOW)         # pump on
      GPIO.output(PL_RELAY_5, GPIO.HIGH)        # NOP
      GPIO.output(PL_RELAY_6, GPIO.LOW)         # lamp on
      GPIO.output(PL_RELAY_7, GPIO.HIGH)        # NOP
      GPIO.output(PL_RELAY_8, GPIO.HIGH)        # NOP

   if i <> 0:
      set  = aSet[i]
   else:
      set = aSet[0]     # to be sure all relays are reset

   rel2 = set[-1]
   rel3 = set[1]
   rel4 = set[:1]

   if rel2 == "0":
      GPIO.output(PL_RELAY_2, GPIO.HIGH)        # close relay 1
   else:
      GPIO.output(PL_RELAY_2, GPIO.LOW)         # open relay 1

   if rel3 == "0":
      GPIO.output(PL_RELAY_3, GPIO.HIGH)        # close relay 2
   else:
      GPIO.output(PL_RELAY_3, GPIO.LOW)         # open relay 2

   if rel4 == "0":
      GPIO.output(PL_RELAY_4, GPIO.HIGH)        # close relay 3
   else:
      GPIO.output(PL_RELAY_4, GPIO.LOW)         # open relay 3

   read_temps()

   nOldSet = i
   cMsg  = TimeStamp("l") + " | Pool pump set to : "
   cMsg += aSet[i] + " @ " +  aRpm[i] + " rpm. Sol=" + str(nSol) + " Pool=" + str(nPool)

   semafoor("sf.log",cMsg, "a")
   sleep(1)

   pomp_status = GPIO.input(PL_RELAY_1)
   cMsg = TimeStamp("l") + " | pl_temp - status pool pump t=" + cStatus[pomp_status]
   cMsg += "\n" + TimeStamp("l") + " | pl_temp - Pump runs at r=" + aRpm[i]

   semafoor("poolpump.dat",cMsg, "w")

   sleep(1)

   return

#
# -----------------------  M A I N  --------------------- #
#
def main():

   # SEE also PL_TEMP11 for add-ons or expansion

   boot_script(cDataDir, script_name)	# report in log.sf when this script started

   # in late summer SF stays cooler and less energy from sun
   """compensate for energy on certain day = sun above horizon
      if sun low threshold becomes lower
      during summer 136 = may 15  272 = sept 28
   """
   nDay = season()[1]
   if nDay > 136 and nDay < 272:
      nSummer = 5
   else:
      nSummer = 0

   n = 1                # report once

   # to prevent unexpected behaviour via pl_utils.py
   # remove sem at startup pl_temp
   if file_exists('pl_utils.sem'):
      os.system("rm pl_utils.sem")

   relays_close()	# close relays 1 to 6
   bCool   = False      # cooling off pool between sunset and sunrise in summer
   bStart  = True       # starts pool pump
   bReport = True       # reports pump off 4 2day and switches for cooling

   #####
   #                                              
   ##############  S U M M E R  ################
                                               #
                                           #####
   while (cSeason == "summer"):

      nRpm = 7               # always starts full speed

      read_temps()
 
      # calibrate threshold to value engaging : 5 à 7 C, disengaging : 3 à 4 K.
      nThreshold = 6

      while nSol > nPool + nThreshold + nSummer:
     
         nThreshold = 4 # disengaging

         if bStart:
            cMsg =  TimeStamp("l") + ' | ' + "pl_temp pump in morning @max"
            semafoor("sf.log", cMsg, "a")

            if DEBUG:
               print cMsg

            set_relays(nRpm)  			# set pump to max

            bStart = False

         if nSol >= 55:
            nRpm = 7
         elif nSol >= 45:
            nRpm = 5
         elif nSol >= 35:
            nRpm = 3
         else:
            nRpm = 0

         set_relays(nRpm)

         if DEBUG:
            print "rpm - sol - pool:",nRpm, nSol, nPool

         sleep(nSleep)
         read_temps()
         
      # in july and august temps of pool can rise above 30
      #   to cool pool off use coolling circuit
      #   there is a special loop dug into the ground to achieve that
      #   cool until water is 28

      nHour = get_hour()
      # cool between 2200 and 0600 >> low power tariff: heure creuse
      while (nPool > nPoolThreshold) and (nHour >= 22 or nHour < 6):
         
         if DEBUG:
             print "entering cooling sequence"            

         if bReport:
            os.system('touch pl_cool.sem')
            bReport = False

         # switch only once
         if not bCool:
            set_relays(7)			# pump at max 2800

            lights(RELAY_COOL,1)		# switch light cooling on

            cMsg =  TimeStamp("l") + ' | ' + "pl_temp cooling pool @" + str(nPool)
            semafoor("sf.log", cMsg, "a")

            cMsg = TimeStamp("l") + " | pl_temp - cooling temperature t=" + str(nPool) + "\n"
            cMsg += TimeStamp("l") + " | pl_temp - valve cooling circuit v=on"
            semafoor("cooling.dat", cMsg, "w")

            if DEBUG:
               print cMsg

            #########
            # sending sem via socket client for RP50
            # if nPool > 30:
            #    bMPI  = MPI_client("open cooling",50) 
            ########

            bCool = True				

         sleep(nSleep)
         nHour = get_hour()
         read_temps()

      # pops out of or passes cooling loop

      if bCool:
         cMsg = TimeStamp("l") + " | pl_temp - pool temperature t=" + str(nPool) + "\n"
         cMsg += TimeStamp("l") + " | pl_temp - valve cooling circuit v=off"
         semafoor("cooling.dat", cMsg, "w")

         cMsg =  TimeStamp("l") + ' | ' + "pl_temp - cooling terminated @" + str(nPool)
         semafoor("sf.log", cMsg, "a")

#         bMPI  = MPI_client("close cooling",50)

         if file_exists('pl_utils.sem'):
            os.system("rm pl_utils.sem")

         if file_exists('pl_cool.sem'):
            os.system('rm pl_cool.sem')	

            lights(RELAY_COOL,0)	# switch light cooling OFF

         bCool = False			# temp pool OK
         bReport = True

      if DEBUG:
         sleep(2)
      else:
         sleep(nSleep * 5)
         if GPIO.input(PL_RELAY_1) == 0:	# if 1 -> pump = on
            relays_close()            

   #####
   #                                              
   ##############  W I N T E R  ################
                                               #
                                           #####
   while cSeason == "winter":   #else:

      read_temps()

      # check to see if relays active
      # in winter should be all off
      i = GPIO.input(PL_RELAY_6) # lamp

      # close all relays when set = "0"
      if i == 0:
         relays_close()

      sleep(nSleep * 3)
 

########### M A I N ##################

if __name__ == "__main__":

   main()
