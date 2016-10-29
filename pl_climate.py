#!/usr/bin/python
# -*- coding: utf-8 -*-

""" 
  source .... pl_barometer.py
  created ... 20150423
  author .... crobat
  updates ... 20151223

  design

  to write climate values in climate.dat
  humidity
  luminosity
  air pressure

  get_humid()
  get_light()
  get_baro()

  TODO
  get_windspeed()
  get_winddir()
  get_pluvio()
"""

import Adafruit_BMP.BMP085 as BMP085
import Adafruit_DHT
import os, smbus
import math
import fcntl
import ephem
from time import sleep
from bieb import semafoor, TimeStamp, get_hour
from config_hms import *


# constants
calibration = 31                        # diff with meteo reports

# DEFINES
DEBUG   = 0
HUM_PIN = 14
BAR_PIN = None
LUX_PIN = None
FILE    = "climate.dat"

# system setup
os.chdir(cDataDir)                      # set doc directory

B_Sensor = BMP085.BMP085()
H_Sensor = Adafruit_DHT.DHT22
L_Sensor = None

# -------- FUNCTIONS ------------- #
def RoundOff(num, d = [0.0, 0.3, 0.7, 1.0]): 
   """ 
   def customRound(num, d = [0.00, 0.25, 0.75, 1.0]): 
   you can change this list to any e.g. [0.0, 0.1, 0.4, 0$
   you can change this list to any e.g. [0.0, 0.1, 0.4, 0.9, 1.0]
   """
   lux = num

   if num < 10:
      dec = num%1
      r = num - dec
      round_dec = min([(abs(i - dec),i) for i in d])[1]
      lux = r + round_dec
   else:
      lux = int(lux)
      
   return lux

#
# ---------- sun rise ------------ #
#
def sunrise():

   cSun       = ""
   home_lat   = '47.921'        # adapted after google maps solar farm
   home_long  = '6.132'
   home_elev  = 283             # has almost no influence 
   home_hor   = '5'            # degrees sun above horizont for twiligh and dusk

   #determine previous/next sunset and -rise
   o = ephem.Observer()
   o.lat  = home_lat
   o.long = home_long
   o.elevation = home_elev
   o.horizon = home_hor

   #define sun as object of interest
   s = ephem.Sun()
   sunrise = o.next_rising(s)
   sunset  = o.next_setting(s)

   Sunrise = ephem.localtime(sunrise).strftime("%H")
   Sunset  = ephem.localtime(sunset).strftime("%H")

   return int(float(Sunrise)), int(float(Sunset))


# ----------- END FUNCTIONS ------ #

####
#
### modules ##############
                         #
                      ####

#
# --------- get humidity --------- #
#
def get_humid():

   """ 
   DHT data connected to GPIO14.

   Try to grab a sensor reading.  Use the read_retry method which will retry up
   to 15 times to get a sensor reading (waiting 2 seconds between each retry).
   Note that sometimes you won't get a reading and
   the results will be null (because Linux can't
   guarantee the timing of calls to read the sensor).
   If this happens try again!
   """

   humidity, temperature = Adafruit_DHT.read_retry(H_Sensor, HUM_PIN)

   if humidity is not None and temperature is not None:
      cMsg = TimeStamp("l") + ' | pl_climate Humidity r={1:0.1f}'.format(temperature,humidity)
   else:
      cMsg = TimeStamp("l") + ' | pl_climate failed reading Humidity r= 11.13'

#   semafoor("humid.dat", cMsg, "w")

   return cMsg, humidity, temperature

#
# -------------- get lux --------- #
#
def get_light():

   """ 
   Indoor light conditions LMQR
   0            no lights
   0.7          1W led on ceiling
   5            both lights buro
   15           light stairs
   20           lights corridor
   50-85        with TL lights

   ref:   https://en.wikipedia.org/wiki/Daylight

   daytime
   120.000 	Brightest sunlight
   111.000 	Bright sunlight
   10752        Full Daylight
   1075         Overcast Day
   107		very dark day
 
   midday
   20000 	Shade illuminated by entire clear blue sky, midday
   1000 2000  	Typical overcast day, midday
   <200  	Extreme of darkest storm clouds, midday

   sunset/rise
   400  	Sunrise or sunset on a clear day (ambient illumination).
   40   	Fully overcast, sunset/sunrise
   10.8		Twilight
   1.08		Deep Twilight 	
   <1   	Extreme of darkest storm clouds, sunset/rise

   nighttime
   <1	 	Moonlight
   0.25 - 0.108  	Full Moon on a clear night
   0.01 - .0108  	Quarter Moon
   0.002 - .0011 	Starlight clear moonless night sky including airglow[4]
   0.0002  		Starlight clear moonless night sky excluding airglow[4]
   0.00014  		Venus at brightest
   0.0001  		Starlight overcast moonless night sky
   """

   # Define some constants from the datasheet
   DEVICE     = 0x23 # Default device I2C address
   POWER_DOWN = 0x00 # No active state
   POWER_ON   = 0x01 # Power on
   RESET      = 0x07 # Reset data register value

   # Device is automatically set to Power Down after measurement.

   ONE_TIME_HIGH_RES_MODE_1 = 0x20 

   bus = smbus.SMBus(1)  # Rev 2 Pi uses 1

   lux = 0.1
   old_lux = lux

   data = bus.read_i2c_block_data(DEVICE, ONE_TIME_HIGH_RES_MODE_1)
   lux = ((data[1] + (256 * data[0])) / 1.2) # convert 2 bytes to decimal
   lux = RoundOff(lux)

   if old_lux <> lux:
      old_lux = lux

   #2016-05-19|15:40:02 | Luminocity l=36.7
   cMsg = TimeStamp("l") + " | pl_climate Light level in lux l=" + str(lux) 

   return cMsg, lux

#
# ---------- get barometer  --------------- #
#
def get_baro():

   calibration = 31                        # diff with meteo reports

   cPressure = str((B_Sensor.read_pressure()/100) + calibration)
   cMsg = TimeStamp("l") + " | pl_climate Barometric Pressure p=" + cPressure

   return cMsg, cPressure

#
# ---------- get barometer  --------------- #
#
def get_windspeed():

   nBeaufort = 4.0  # windspeed in  m/s

   return nBeaufort

#
# ---------- get wind direction  --------------- #
#
def get_winddir():
   
   cDirection = "S"

   return cDirection


#
# ---------- get rainfall  --------------- #
#
def get_pluvio():
   
   nPluvio = 0

   return bPluvio


#
# ---------- get cloudiness  --------------- #
#

def get_cloud(lumx):

   """  
   107520       Bright sunlight
   10752        Full Daylight
   1075         Overcast Day
   107          very dark day
 
   midday
   20000        Shade illuminated by entire clear blue sky, midday
   1000 2000    Typical overcast day, midday
   <200         Extreme of darkest storm clouds, midday

   sunset/rise
   400          Sunrise or sunset on a clear day (ambient illumination).
   40           Fully overcast, sunset/sunrise
   10.8         Twilight
   1.08         Deep Twilight   
   <1           Extreme of darkest storm clouds, sunset/rise
   """

#   aType = ("Extreme dark", "Very dark", "Dark","Overcast", "Cloudy", "Bright daylight")
   aType2 = ("Night","Dusk","Dawn")

   nDusk, nDawn = sunrise()
   
   nHour = get_hour()

   bDayTime = False

   print lumx,

   n = 0

   try: # log(0) = indefinite 
      n = int(math.log(lumx,10))
      print math.log(lumx,10),
   except:
      n = 0

   cStr = aTypeCloud[n] 

   if nHour < nDawn + 2:  # dawn
      n = 2
   elif nHour > nDusk and nHour < nDusk + 2:
      n = 1
   else:
      n = 0   # night
   
   if nHour <= nDawn or nHour >= nDusk:
      cStr = aType2[n]

   print n, cStr

   return n, cStr 

######
# -------------------- M A I N -------------- #
                                         ######
def main():

   aData  = []

   # contents climate file
   aLight = get_light()
   aData.append(aLight[0])
   
   aCloud = get_cloud(aLight[1])

   aHumid = get_humid()
   aData.append(aHumid[0])

   aBaro  = get_baro() 
   aData.append(aBaro[0])

   nWindSpeed = get_windspeed()
   cWindDir = get_winddir()

   cPluvio = str(get_pluvio())

   # create physical file from data[]:

   nCount = 0

   while nCount < 3:
      try:
         if DEBUG:
            print "writing 'climate.dat' file"

         with open("climate.dat", 'w') as fout:
            fcntl.flock(fout.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            fout.writelines( "%s\n" % item for item in aData )
      except:
         nCount += 1
         print 'file climate.dat could not be written to',nCount
         sleep(1)
      finally:
         break
      

   # format timestamp lumen, pressure, humidity, teperature, wind, direction, cloud type

   cStr  = TimeStamp("w") + " " + str(aLight[1]) + " " + str(aBaro[1]) + " " + str(round(aHumid[1],1)) + " "
   cStr +=str(round(aHumid[2],1)) + " " + str(round(nWindSpeed,0)) + " " + cWindDir + " " + str(aCloud[0])
   cStr += " " + cPluvio  
   if DEBUG:
      print cStr, aCloud[1]

   semafoor("weather.dat", cStr, 'a')
   

# ----------- redirect ---------- #
if __name__=="__main__":
   main()


