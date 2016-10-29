import RPi.GPIO as GPIO
import glob, sys

from time import sleep #, localtime
from bieb import *
from config_hms import *

# vars
nSensors  = 0                                   # number of temp sensors
nSleep    = 60                                  # sleep loop
nPompRun  = 600                                 # seconds CVpomp to run
nTreshold = 4                                   # degrees higher than floor / heater
nKachel   = 999                                 # temperatures from sensor
nFloor    = 999                                 # id
nOutside  = 999                                 # id
nSolar    = 999                                 # id

# lists
file_list   = list()                            # creat empty array
aStand      = ("on", "off")
aTrend      = []

# Statics
RELAY_CV    = 17                            # relays poort no..
RELAY_FLOOR = 2                             # relay floorp pump
KLEP51_PIN  = 3                             # 3 way valve
DEBUG 	    = 0

os.chdir(cDataDir)                              # set doc directory

cSeason, nDay = season()                        # bieb.py

""" One can override season manually by changing pool_status.sem not to contain 'open' """
if not pool_status():
  cSeason = "winter"

# prevent unwanted error msgs from Raspi IO
GPIO.setwarnings(False)

# setup IO ports
GPIO.setmode(GPIO.BCM)
GPIO.setup(RELAY_CV, GPIO.OUT)
GPIO.setup(RELAY_FLOOR, GPIO.OUT)

# initialization interfaces 1W sensors
if not file_exists(base_dir):
   os.system('sudo modprobe w1-gpio')                   # 1w output dir
   os.system('sudo modprobe w1-therm')                  # 1w dir

try:
   device_folder = glob.glob(base_dir + '*')[0]          # dir of sensor files
   device_file   = device_folder + '/w1_slave'           # file temp and ID sensors
   dirList       = os.listdir(base_dir)                  # list sensor files

   for i in dirList:                                     # load files & sensors
      if i[0:2] == '10' or i[0:2] == '28':
         device_folder = glob.glob(base_dir + i)[0]
         device_file = device_folder + '/w1_slave'
         file_list.append(str(device_file))

   nSensors = len(file_list)                             # number of sensors in device dir

except:
  cMsg = TimeStamp("l") + " | pl_temp3 - No data for sensors central heating"
  alert(cMsg, "No data 4 sensors Heater", "Heater")

  if DEBUG: 
     print cMsg
     print 'nSensors',nSensors
  else:
     semafoor("sf.log", cMsg, "a")


#
# =====================  read temp from mod file  =======================
#
def read_temps():

   global nKachel
   global nFloor
   global nSolar
   global nOutside
   global nGarage

   with open("solar.dat", "r") as f:
      line   = f.readline()
      cStr   = line.split('t=')[-1]
      cStr   = cStr[:-1]                                # read solar temp
      nSolar = float(cStr)                              # read solar temp

   with open("buit.dat", "r") as f:
      line   = f.readline()
      cStr   = line.split('t=')[-1]
      cStr   = cStr[:-1]                                # read out temp
      nOutside = float(cStr)                            # read out temp

   with open("sfgar.dat", "r") as f:
      line    = f.readline()
      cStr    = line.split('t=')[-1]
      cStr   = cStr[:-1]                                # read garage temp
      nGarage = float(cStr)                             # read garage temp

   if nSensors <> 0:
      for x in xrange(0, nSensors):                     # read all sensors
         device_file = file_list[x]                     # data file
         sensorID    = device_file[30:len(device_file)-9]  # ID sensor

         cTemp = temp_read(device_file)                 # bieb.py

         if sensorID == ID_kachel:

            nKachel = float(cTemp)
            cStr = TimeStamp("CV") + " | " + sensorID + " Furnace t=" + cTemp
            if DEBUG:
               print cStr

            sleep(.5)

         elif sensorID == ID_floor:

            nFloor  = float(cTemp)
            cStr = TimeStamp("CV") + " | " + sensorID + " Floor t=" + cTemp
            if DEBUG:
               print cStr

            sleep(.5)

   # heater sensor is defunct 4 the moment - 20160201.
   # repaired 20161024
   # nKachel = nFloor

   cStr    = TimeStamp("CV") + " | Heater t=" + str(nKachel)
   cStr1    = TimeStamp("CV") + " | Floor t=" + str(nFloor)

   if not DEBUG:
      semafoor("kachel.dat",cStr, 'w')
      semafoor("floor.dat",cStr1, 'w')

   return True


#
# ------------ manage heater pump -----------------------
#
def pump_cv(cSwitch):

   bSwitch = (True, False)

   GPIO.setup(RELAY_CV,GPIO.OUT)     # FLOOR PUMP

   pump_status = GPIO.input(RELAY_CV)
   status_old = pump_status
   
   if cSwitch == "?":                                   	# need only info on pum$
      print 'pump_heater: info only'
      return

   # switch to request
   if cSeason == "winter":
      if cSwitch == "on" and pump_status == 1:       	  	# pump = off
         GPIO.output(RELAY_CV,GPIO.LOW)                         # engage pump

      if cSwitch == "off" and pump_status == 0:
         GPIO.output(RELAY_CV,GPIO.HIGH)                        # disengage pump

   elif cSeason == "summer":
      if cSwitch == "on" and pump_status == 1:
         GPIO.output(RELAY_CV, GPIO.LOW)                        # relay off pomp on

      if cSwitch == "off" and pump_status == 0:
         GPIO.output(RELAY_CV, GPIO.HIGH)                       # relay on pomp off

   sleep(.5)

   pump_status = GPIO.input(RELAY_CV)

   if pump_status <> status_old:
      cMsg = TimeStamp("l") + " | cv_temp - CV pump status is " + aStand[pump_status]
      cMsg +=  " with floor @ " + str(nFloor) + " and solar @ " + str(nSolar)
      cMsg += " diff " + str(nSolar - nKachel)
      semafoor("sf.log",cMsg, "a")

      cMsg = TimeStamp("cv") + " | cv_temp - CV pump t=" + aStand[pump_status]
      semafoor("cv_pump.dat",cMsg,"w")

   return

#
# ------------ manage floor pump -----------------------
#
def pump_floor(cSwitch):

   bSwitch = (True, False)

   GPIO.setup(RELAY_FLOOR,GPIO.OUT)     # FLOOR PUMP

   pump_status = GPIO.input(RELAY_FLOOR)
   status_old = pump_status

   if cSwitch == "?":                                   # need only info on pum$
      print 'pump_floor: info only'
      return

   if cSeason == "winter":
      if cSwitch == "on" and pump_status == 1:		# pump = off
         GPIO.output(RELAY_FLOOR,GPIO.LOW)              # engage pump

      if cSwitch == "off" and pump_status == 0:
         GPIO.output(RELAY_FLOOR,GPIO.HIGH)             # disengage pump

   elif cSeason == "summer":
      if cSwitch == "on" and pump_status == 1:
         GPIO.output(RELAY_FLOOR, GPIO.LOW)             # engage pomp

      if cSwitch == "off" and pump_status == 0:
         GPIO.output(RELAY_FLOOR, GPIO.HIGH)            # relay on pomp off

   sleep(.5)
   pump_status = GPIO.input(RELAY_FLOOR)

   if pump_status <> status_old:
      cMsg = TimeStamp("l") + " | cv_temp - FLOOR pump status is " + aStand[pump_status]
      cMsg +=  " with floor @ " + str(nFloor) + " and solar @ " + str(nSolar)
      semafoor("sf.log",cMsg, "a")

      cMsg = TimeStamp("floor") + " | cv_temp - FLOOR pump t=" + aStand[pump_status]
      semafoor("floorpump.dat",cMsg,"w")

   return

#
# ------  temps trend falling or rising ----- #
#
""" 
change proposal from:raspi forum

One could implement this easily by taking the fall / rise and multiply
with a weighed multiplier with the percentage fall / rise to call this relevance score

By taking a multiplier of 0.5 a 2x lower temp should fall 2 x percentual
than the previous temp before it to become relevant.

"""

def trend(nSF, nCV):

   nLen     = 8
   nCount   = 0

   # take last 'nLen' times = times nSleep (60 secs) see config_hms.py
   while nCount <= nLen:   # fill array
      aTrend.append(nSF)
      nCount += 1
      return True

   # rotate array
   nValue = aTrend.pop()        # slice last value
   aTrend.insert(0, nValue)     # insert last value = first
   aTrend[nLen] = nSF           # append new value

   if DEBUG:
      print aTrend

   # compare last 8 values if all smaller than previous trend is falling
   if aTrend[0]<aTrend[1]<aTrend[2]<aTrend[3]<aTrend[4]<aTrend[5]<aTrend[6]<aTrend[8]:
      if nCV > 20:                        # if CV burns never put pumps off
         return True
      elif nSF > ( nCV + nTreshold + 4):  # Solar should be significantly higher than CV
         print "Tendence not defined ", aTrend
         return True
      else:
         print "Tendence falling ", aTrend
         return False                     # tendens is falling and Solar is colder
   else:
      print "Tendence stable ", aTrend
      return True                         # no falling tendency

   return True


#                                                 #
# #################################################
#                     M A I N                     #


#  ============== M A I N * L O O P ======================
def main():

   file_name =  os.path.basename(sys.argv[0])

   if not DEBUG:
      boot_script(cDataDir, file_name)     # report in log.sf when this script started

   bCycle = True                        # daily pump cycle in summer

   if DEBUG:
      print "It is ", cSeason, "and day number",nDay

   read_temps()
   
   pump_cv("off")    
   pump_floor("off")

   while 1:

      nHour = get_hour()

      ####
      #   W I N T E R
      #########################
                              #
                           ####
      while cSeason == "winter":

         # when either SF or CV is hot
         
         while (nGarage >= nKachel + nTreshold) or (nKachel > 40):

            pump_cv("on")
            pump_floor("on")

#            with open("drieweg51.dat", "r") as f:
#               line   = f.readline()
#            if line.find('t=A')<> -1 and nKachel <= nGarage:
#               break

#           if not trend():		# trend is falling
#              pump_cv("off")
#              pump_floor("off")
#              break

	    if DEBUG:
               sleep(10)
	    else:
               sleep(nSleep*3)

            read_temps()

         if nOutside >= 0:  # Pump = On
            cMsg = TimeStamp("l") + " | Stopping pumps, temps GAR : HEATER + Treshold "
            cMsg += str(nGarage) + " : " + str(nKachel + nTreshold)
            pump_cv("off")
            pump_floor("off")

         elif nOutside < 0: #Pump = off
            pump_cv("on")
            pump_floor("on")
 
         if DEBUG:
            sleep(10)
         else:
            sleep(nSleep * 3)

         read_temps()

      ####
      #    S U M M E R
      ############################
                                 #
                              ####

      # During summer CV and Floor pumps are circulating 1 hour per day
      # from 22:00 till 23:00  nStart - nStop
      # edf tarif tempo heure creuse 22 - 06
      while cSeason == "summer":

         while (nHour >= nStart) and (nHour < nStop):
            if bCycle:                                  # bCycle is reset when RP51 reboots @0800
               cMsg = TimeStamp("l") + " | cv_temp: daily summer pump cycle start"
               semafoor("sf.log",cMsg, "a")
               pump_cv("on", True)
               pump_floor("on", True)
               bCycle = False

            sleep(nSleep*5)
            nHour = get_hour()

         # cv and floor are both switched on in this cycle
         # use pump_status.py to test status off-line
         if GPIO.input(RELAY_CV) == 0 or GPIO.input(RELAY_FLOOR) == 0:
            cMsg = TimeStamp("l") + " | cv_temp: daily summer pump cycle stopping"
            semafoor("sf.log",cMsg, "a")

            pump_cv("off", True)
            pump_floor("off", True)
#            GPIO.output(RELAY_CV, GPIO.HIGH)                # relay OFF
#            sleep(1)                                       # to prevent water thumb
#            GPIO.output(RELAY_FLOOR, GPIO.HIGH)             # relay floorpump OFF
            GPIO.output(LED_PIN, GPIO.LOW)                  # led OFF

         if DEBUG:
            sleep(1)
         else:
            sleep(nSleep*10)

         read_temps()


#
# ======== MAIN ===========
#
if __name__ == "__main__":

   main()

