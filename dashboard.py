#! /usr/bin/env python
# -*- coding: utf-8 -*-
""" 
  source .... dashboard.py
  created ... 20150407
  author .... crobat
  updates ... 2015

design
  a template is created with lines looking like:

  <td valign="top">Sunrise<br></td><td valign="top">xSunrise<br></td></tr>'
  
  read all lines from template into an array: aData
  replace all labels starting with x with values
  write aData to tempfile: web_out.html
  move tempfile to destination

  S Q L 
    when scripts are definitive
    all variables, constants. labels, paths and other 
    definitions will be inserted in a config.sql database

  WEATHER  local
  http://www.viewweather.com/w1884883-weather-forecast-for-vauvillers-franche-comte.html

# http://www.authorcode.com/scrolling-text-right-to-left-in-html5/
<html>
<head>
    <title>Text Animation</title>
    <style>
        canvas{border: 1px solid #bbb;}
        .subdiv{width: 320px;}
        .text{margin: auto; width: 290px;}
    </style>
 
    <script type="text/javascript">
        var can, ctx, step, steps = 0,
              delay = 20;
 
        function init() {
            can = document.getElementById("MyCanvas1");
            ctx = can.getContext("2d");
            ctx.fillStyle = "blue";
            ctx.font = "20pt Verdana";
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            step = 320;
            steps = 0;
            RunTextLeftToRight();
        }
 
        function RunTextLeftToRight() {
            step- -;
            ctx.clearRect(0, 0, can.width, can.height);
            ctx.save();
            ctx.translate(step, can.height / 2);
            ctx.fillText("Welcome", 0, 0);
            ctx.restore();
            if (step == steps)
                step = 320;
            if (step > steps)
                var t = setTimeout('RunTextLeftToRight()', delay);
        }
    </script>
 
</head>
<body onload="init();">
    <div class="subdiv">
        <canvas id="MyCanvas1" width="300" height="200">
  This browser or document mode doesn't support canvas object</canvas>
        <p class="text">
            Example 1 – Marquee Text right to left– scrolling text
        </p>
    </div>
</body>
</html>
"""

import os, time, datetime, sys, ephem
import shutil  # remove, copyfile
import socket, subprocess, errno
import math

from time import sleep, localtime
from datetime import timedelta
from config_hms import *   		# system parameter
from os import remove
from bieb import TimeStamp,  boot_script, get_hour, semafoor

cDummy         = '11.1'
cNOP           = "NOP.gif"
cSymbolOn      = "green33.gif"
cSymbolOff     = "red33.gif"
c3WayOn        = "W3B.gif"    # open to house
c3WayOff       = "W3A.gif"    # recirculating to SF

template_file  = 'web_template.html'
out_file       = 'web_out.html'
target_file    = 'index.html'

ySolartemp     = cDummy
yOutsidetemp   = cDummy
yHeatertemp    = cDummy
yPooltemp      = cDummy
yAteliertemp   = cDummy
yCoolingtemp   = cDummy
yRetourtemp    = cDummy
yRetourCVtemp  = cDummy
yCorridortemp  = cDummy
yTubtemp       = cDummy
yFloortemp     = cDummy
ySunrise       = "11:11"	# HH:MM
ySunset        = "11:11"	# HH:MM
yBarometer     = "1000"		# hPa
yHumidity      = "50"		# RH%
yLight         = '5'	 	# lux
ySolarpump     = cSymbolOff
yHeaterpump    = cSymbolOff
yFloorpump     = cSymbolOff
yPoolpump      = cSymbolOff
yPumpspeed     = "0 rpm"
y3wayvalve     = c3WayOff
yHousevalve    = cSymbolOff
yAteliervalve  = cSymbolOff
yCoolingvalve  = cSymbolOff
yTubvalve      = cSymbolOff
yFloorRelays   = cSymbolOff
yCloudType     = ""

yMiniMax       = "minimum t"             # string minimum and max temps + groud temp
yTempsYest     = "temps yesterday"

# global var's get_trend
nStart         = 0

DEBUG 	       = 0			# for testing purposes set to 1
# set doc directory
cDataDir = "/data/solarfarm/"
os.chdir(cDataDir) 
      
script_name =  os.path.basename(sys.argv[0])

#
# ---------- sun rise ------------ #
#
def sunrise():

   cSun       = ""
   home_lat   = '47.921'        # adapted after google maps solar farm
   home_long  = '6.132'
   home_elev  = 283             # has almost no influence 
   home_hor   = '0'             # degrees sun above horizont

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

   Sunrise = ephem.localtime(sunrise).strftime("%H:%M")
   Sunset  = ephem.localtime(sunset).strftime("%H:%M")

   return Sunrise, Sunset

#
# ------- environment values ------------
#
""" 
   Sun licht: 100 000 - 130 000 lux (100 - 130 klx)
   Day light, indirect sun licht: 10 000 - 20 000 lux (10 - 20 klx)
   clouded day: 1000 lux (1 klx)
   very clouded day: 100 lux
   dusk /dawn: 10 lux
   dark dawn schemering: 1 lux
   full moon: 0,1 lux
   quarter moon: 0,01 lux (10 mlx)
   new moon not no clouds: 0,001 lux (1 mlx)
   clouded night no moon: 0,0001 lux (0,1 mlx)

   atmospheric pressure is measured in hPa
   1 mBar = 1 hPa

   The relative humidity of an air-water mixture is defined as the ratio of 
   the partial pressure of water vapor (H2O) in the mixture to the saturated 
   vapor pressure of water at a given temperature.
"""
def climate():

   nTeller = 0
   hpa = "1111"
   rv = "11"
   lux = "1111"

   while nTeller < 3:
      try:
         with open("climate.dat", "r") as fin:
            for line in fin.readlines():
               if line.find('p=') != -1:
                  cStr = line.split('p=')[-1]
                  hpa = cStr[:-1]
               if line.find('r=') != -1:
                  cStr = line.split('r=')[-1]
                  rv = cStr[:-1]
               if line.find('l=') != -1:
                  cStr = line.split('l=')[-1]
                  lux = cStr[:-1]
         break
      except:
         nTeller += 1
         sleep(1)

   return hpa, rv, lux

#
# -------- get cooling data --------
#

def cooling():

   global yCoolingvalve
   global yCoolingtemp

   nTeller = 0
   yCoolingvalve = cSymbolOff
   yCoolingtemp  = "11.11"

   while nTeller < 3:
      try:
         with open("cooling.dat", "r") as fin:
            for line in fin.readlines():
               if line.find('t=') != -1:
                  cStr = line.split('t=')[-1]
                  yCoolingtemp = cStr[:-1]
               if line.find('v=on') != -1:
                  yCoolingvalve = cSymbolOn
         break
      except:
         nTeller += 1
         sleep(1)

   if DEBUG:
      print "Cooling temperature .... : ", yCoolingtemp
      print "Cooling valve .......... : ", yCoolingvalve



   return


#
# -------- determine pump on or off --------
#
""" 
with raspi type 3 you will have remote access to remote GPIO pins
so there will be no longer a need to have semafoor files 
4 future upgrades change programme accordingly when RP50,51,53, and 60 
boards are replaced with RP3's 
"""
def pumps():

   global ySolarpump
   global yHeaterpump
   global yFloorpump
   global yPoolpump
   global yPumpspeed

   ySolarpump      = cSymbolOn

   with open("solarpump.dat", "r") as f:
      line = f.readline()

      if line.find("t=on") == -1:
         ySolarpump      = cSymbolOff

   sleep(0.1)

   yHeaterpump      = cSymbolOn

   with open("cv_pump.dat", "r") as f:
      line = f.readline()

      if line.find('t=on') == -1:
         yHeaterpump      = cSymbolOff

   sleep(0.1)

   yFloorpump = cSymbolOn

   with open("floorpump.dat", "r") as f:
      line = f.readline()

      if line.find('t=on') == -1:
         yFloorpump      = cSymbolOff

   sleep(0.1)

   nTeller = 0
   yPoolpump      = cSymbolOff
   yPumpspeed     = "0"
   
   while nTeller < 3:
      try:
         with open("poolpump.dat", "r") as fin:
            for line in fin.readlines():
               if line.find('r=') != -1:
                  cStr = line.split('=')
                  yPumpspeed = " " + cStr[1].rstrip()
               elif line.find('t=on') != -1:
                  yPoolpump  = cSymbolOn

            if DEBUG:
               print 'pump is  ',cStr, 'running @ ', yPumpspeed, 'rpm'

         break
      except:
         nTeller += 1
         sleep(1)


   sleep(0.1)


   return

# 
# ----- determine positions of valves -------
#
def valves():

   global y3wayvalve   
   global yHousevalve  
   global yAteliervalve
   global yCoolingvalve
   global yTubvalve
   global yTubtemp

   # 3 way valve 50
   y3wayvalve    = c3WayOff	
   with open("drieweg.dat", "r") as f:
      line = f.readline()
      cKlep1 = line.split('t=')[-1]
      cKlep1 = cKlep1[:-1]
 
   if cKlep1 == "B":
      y3wayvalve    = c3WayOn

   # ateliervalve
   yAteliervalve = cSymbolOff
   with open("klep56.dat", "r") as f:
      line = f.readline()
      cKlep1 = line.split('t=')[-1]
      cKlep1 = cKlep1[:-1]

   if cKlep1 == "on":
      yAteliervalve = cSymbolOn

   # house valve
   yHousevalve = cSymbolOff
   with open("klep78.dat", "r") as f:
      line = f.readline()
      if line.find('t=on') !=-1:
         yHousevalve = cSymbolOn 
   
   # hot tub valve & temperature
   yTubvalve  = cSymbolOff
   yTubtemp   = cDummy
   nTeller    = 0
   while nTeller < 3:
      try:
         with open("hottub.dat", "r") as fin:
            for line in fin.readlines():
               if line.find('t=') != -1:
                  cStr = line.split('t=')[-1]
                  yTubtemp = cStr[:-1]
               if line.find('v=on') != -1:
                  yTubvalve = cSymbolOn

         if DEBUG:
            print "Hot Tub ",yTubvalve, "@ ", yTubtemp, "degrees."

         break
      except:
         nTeller += 1
         sleep(1)

   return  

#
# -------- read temps -------------
#
def temps():

   global ySolartemp
   global yOutsidetemp
   global yHeatertemp
   global yPooltemp
   global yAteliertemp
   global yRetourtemp
   global yRetourCVtemp
   global yCorridortemp
   global yFloortemp


   # solartemp
   ySolartemp     = cDummy
   nTeller = 0

   while nTeller < 3:
      try:
         with open("solar.dat", "r") as f:
            line = f.readline()
            cStr = line.split('t=')[-1]
            ySolartemp = cStr[:-1]
         break
      except:
         nTeller += 1
         sleep(1)

   # outside temperature
   yOutsidetemp   = cDummy
   nTeller = 0

   while nTeller < 3:
      try:
         with open("buit.dat", "r") as f:
            line = f.readline()
            cStr = line.split('t=')[-1]
            yOutsidetemp = cStr[:-1]
         break
      except:
         nTeller += 1
         sleep(1)

   # heater
   yHeatertemp    = cDummy
   nTeller = 0

   while nTeller < 3:
      try:
         with open("kachel.dat", "r") as f:
            line = f.readline()
            cStr = line.split('t=')[-1]
            yHeatertemp = cStr[:-1]
         break
      except:
         nTeller += 1
         sleep(1)

   # temp retour to solarfarm
   yRetourtemp    = cDummy
   nTeller = 0

   while nTeller < 3:
      try:
         with open("sfgar.dat", "r") as f:
            line = f.readline()
            cStr = line.split('t=')[-1]
            yRetourtemp = cStr[:-1]
         break
      except:
         nTeller += 1
         sleep(1)

   # temp pool
   yPooltemp    = cDummy
   nTeller = 0

   while nTeller < 3:
      try:
         with open("pool.dat", "r") as f:
            line = f.readline()
            cStr = line.split('t=')[-1]
            yPooltemp = cStr[:-1]
         break
      except:
         nTeller += 1
         sleep(1)

   # temp retour from heater
   yRetourCVtemp  = cDummy
   nTeller = 0

   while nTeller < 3:
      try:
         with open("retour.dat", "r") as f:
            line = f.readline()
            cStr = line.split('t=')[-1]
            yRetourCVtemp = cStr[:-1]
         break
      except:
         nTeller += 1
         sleep(1)

   # temp in winter ateier
   yAteliertemp  = cDummy
   nTeller = 0

   while nTeller < 3:
      try:
         with open("atel.dat", "r") as f:
            line = f.readline()
            cStr = line.split('t=')[-1]
            yAteliertemp = cStr[:-1]
         break
      except:
         nTeller += 1
         sleep(1)


   # temp in corridor
   yCorridortemp  = "11.1"
   while nTeller < 3:
      try:
         with open("corridor.dat", "r") as f:
            line = f.readline()
            cStr = line.split('t=')[-1]
            yCorridortemp = cStr[:-1]
         break
      except:
         nTeller += 1
         sleep(1)


   # temp floor
   yFloortemp      = "11.1"
   while nTeller < 3:
      try:
         with open("floor.dat", "r") as f:
            line = f.readline()
            cStr = line.split('t=')[-1]
            yFloortemp = cStr[:-1]
         break
      except:
         nTeller += 1
         sleep(1)

   return

#
# ------ read minimum and max temps from cv_now.dat -------
#
""" 
  generate report with minimax temps on demand from cv_now.dat
  to display on dashboard
"""
def minimax():

   global yMiniMax
   global yTempsYest

   yMiniMax    = ""
   cSolarOld   = cDummy
   cOutOld     = cDummy
   cHeatOld    = cDummy
   cPoolOld    = cDummy
   cTSmax      = cDummy
   cTSmin      = cDummy
   cOSmax      = cDummy
   cOSmin      = cDummy
   cGTS        = cDummy
   cGround     = cDummy

   nSpaces     = 7				# filling spaces in columns
   nMaxSol     = 0
   nMinSol     = 100
   nMaxOut     = 0
   nMinOut     = 100

   DATE_TIME   = 0
   SOLAR       = 2
   OUTSIDE     = 3

   bTimeSet    = False

   with open("cv_now.dat", 'r') as fo:
      read_data = fo.readlines()

   # this routine should be converted into (map, max min, array)
   for line in read_data:

       line = line.strip()
       columns = line.split()

       # to catch an empty record generate timestamp
       if columns[DATE_TIME] == None:
          columns[DATE_TIME] = TimeStamp("l")
          cMsg = TimeStamp("l") + " | Dashboard - timestamp from cv_now.dat missing, created timestamp."
          semafoor("sf.log", cMsg, "a")

       if not bTimeSet:
           cTimeDate = columns[DATE_TIME]
           bTimeSet  = True
                
       try:
           nSolar = float(columns[SOLAR])
           cSolarOld = columns[SOLAR]
       except:
           columns[SOLAR] = cSolarOld		# take last known value or dummy
           nSolar = float(cSolarOld)

       try: 
           nOut = float(columns[OUTSIDE])
           cOutOld = columns[OUTSIDE]
       except:
           columns[OUTSIDE] = cOutOld
           nOut = float(cOutOld)

       if nMaxSol < nSolar:
         nMaxSol  = nSolar
         cTSmax   = columns[DATE_TIME]

       if nMinSol > nSolar:
         nMinSol  = nSolar
         cTSmin   = columns[DATE_TIME]

       if nMaxOut < nOut:
         nMaxOut  = nOut
         cOSmax   = columns[DATE_TIME]

       if nMinOut > nOut:
         nMinOut  = nOut
         cOSmin   = columns[DATE_TIME]

   with open("ground.dat","r") as f:
     line = f.readline()
     cGround = line.split('t=')[-1][:-1]
     cGTS    = line.partition("|")[2][:5]

   cRegel  = "SolarFarm max temp" + str(nMaxSol).rjust(nSpaces) + " @ " + cTSmax.partition("|")[2][:5]
   cRegel += "  min temp " + str(nMinSol).rjust(nSpaces) + " @ "+ cTSmin.partition("|")[2][:5]
   cRegel += "<br>Outside   max temp" + str(nMaxOut).rjust(nSpaces) + " @ " + cOSmax.partition("|")[2][:5]
   cRegel += "  min temp " + str(nMinOut).rjust(nSpaces) + " @ "+  cOSmin.partition("|")[2][:5]
   cRegel += "<br>Ground temperature" + cGround.rjust(nSpaces) + " @ " + cGTS + "  100cm below groundlevel" 

   yMiniMax = cRegel

   nHour = get_hour()
   
   # preserve yesterdays minimax string
   if nHour == 8:				# this runs until 08:59 so it takes the last reading
      semafoor("minimax.sem", cRegel, "w")
      yTempsYest = cRegel
   else:
      with open("minimax.sem", "r") as f:
         yTempsYest = f.readline().strip()
         if DEBUG:
            print yTempsYest
   
   return

#
# ------ tend up or down ------------ #
#
def get_trend(cBar):

   global nStart

   nScore  = 0
   aBar    = (" <b>=</b>", " &#9650;", " &#9660;") 

   new_bar = int(float(cBar))

   if nStart < 100: # bar can not be 100 so this is a start option
      nStart = new_bar

   nDiff   = nStart - new_bar

   if new_bar > nStart:
      nScore = 1
   elif new_bar < nStart:
      nScore = 2
   else:
      nScore = 0

   cTrend = cBar + aBar[nScore]
   if DEBUG:
      print "Trend :", nStart, new_bar, nDiff, cTrend, nScore

#   old_bar = int(float(yBarometer))

   return cTrend

#
# ------ read index.html ------------ #
#
def read_template():

   data=[]

   with open(template_file, 'rb') as source_file:
      for line in source_file:
         data.append(line.rstrip())

   return data

#
# ----------- M A I N ------------- #
#
#if __name__ == '__main__':

boot_script(cDataDir, script_name)     # report in log.sf when this script started

while 1:

   # calculate sunrise sunset
   ySunrise, ySunset = sunrise()
   # get environment values
   yBarometer, yHumidity, yLight = climate()
   yBarometer = get_trend(yBarometer)
   # cloud type
   try:
      nCloud = int(math.log(float(yLight),10)) # log(0) not defined
      yTypeCloud = aTypeCloud[nCloud]
   except:
      yTypeCloud = "Night"
      nCloud     = 0

   nHour = get_hour()

   if nHour <= int(float(ySunrise[:2])) or nHour >= int(float(ySunset[:2])):
      yTypeCloud = "Night"
      nCloud     = 0

   print nCloud, yTypeCloud
   
   # get temps from semaphors
   temps()
   # get position from semaphors
   valves()
   # display engaged pumps
   pumps()
   # get cooling data
   cooling()
   # get template contents
   aData = read_template()
   # get minimax temps
   minimax()

  
   # populate array with current data
   for x in range(len(aData)):
      aData[x] = aData[x].replace('xSolartemp',    ySolartemp)
      aData[x] = aData[x].replace('xOutsidetemp',  yOutsidetemp)
      aData[x] = aData[x].replace('xHeatertemp',   yHeatertemp)
      aData[x] = aData[x].replace('xPooltemp',     yPooltemp)
      aData[x] = aData[x].replace('xAteliertemp',  yAteliertemp)
      aData[x] = aData[x].replace('xCoolingtemp',  yCoolingtemp)
      aData[x] = aData[x].replace('xRetourtemp',   yRetourtemp)
      aData[x] = aData[x].replace('xRetourCVtemp', yRetourCVtemp)
      aData[x] = aData[x].replace('xCorridortemp', yCorridortemp)
      aData[x] = aData[x].replace('xTubtemp',      yTubtemp)
      aData[x] = aData[x].replace('xFloortemp',    yFloortemp)
      aData[x] = aData[x].replace('xSunrise',      ySunrise)		# HH:MM
      aData[x] = aData[x].replace('xSunset',       ySunset)		# HH:MM
      aData[x] = aData[x].replace('xLight',        yLight)      	# in Lux
      aData[x] = aData[x].replace('xCloud',        yTypeCloud)      	# see defs in config_hms
      aData[x] = aData[x].replace('xMiniMax',      yMiniMax)      	# min max temps and ground  
      aData[x] = aData[x].replace('xSolarpump',    ySolarpump)
      aData[x] = aData[x].replace('xHeaterpump',   yHeaterpump)
      aData[x] = aData[x].replace('xFloorpump',    yFloorpump)
      aData[x] = aData[x].replace('xPumpspeed',    yPumpspeed)
      aData[x] = aData[x].replace('xPoolpump',     yPoolpump)
      aData[x] = aData[x].replace('x3wayvalve',    y3wayvalve)
      aData[x] = aData[x].replace('xHousevalve',   yHousevalve)
      aData[x] = aData[x].replace('xAteliervalve', yAteliervalve)
      aData[x] = aData[x].replace('xCoolingvalve', yCoolingvalve)
      aData[x] = aData[x].replace('xTubtemp',      yTubtemp)
      aData[x] = aData[x].replace('xTubvalve',     yTubvalve)
      aData[x] = aData[x].replace('xTempsYest',    yTempsYest)

   # create physical file from data[]
   fout = open(out_file, 'w')
   fout.writelines( "%s\n" % item for item in aData )
   fout.close()

   os.system('sudo cp web_out.html /data/web/index.html')

   sleep(60)

