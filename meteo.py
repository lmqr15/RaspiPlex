#! /usr/bin/env python
# -*- coding: utf-8 -*-

''' 
docs.python-guide.org/en/latest/scenarios/scrape/

http://www.meteofrance.com/previsions-meteo-france/vauvillers/70210

<!-- A day --> <article class="bloc-day-summary "> 
<header> <h4><a href="#detail-day-02">samedi 30</a></h4> </header> 
<ul class="day-data"> 

<li class="day-summary-temperature">
<span class="min-temp">15C Minimale</span> / 
<span class="max-temp">28C Maximale</span></li> 

<li class="day-summary-image">
<span class="picTemps J_W1_0-N_0">Ensoleillé</span></li>

<li class="day-summary-uv">UV 7</li>

<li class="day-summary-wind"> 
<p class="picVent V_SSO">Vent sud-sud-ouest</p> 
<p class="vent-detail-vitesse">Vent 10 km/h 
<span class="vent-detail-type"></span></p> 
</li> 

</ul> 
</article> 

read unicode files:
-----------------------------------------------
import codecs
fileObj = codecs.open( "someFile", "r", "utf-8" )
u = fileObj.read() # Returns a Unicode string from the UTF-8 bytes in the file


this does the trick as well:
curl http://wttr.in/vauvillers
Weather for City: Vauvillers, France

     \   /     Clear 
      .-.      20 °C          
   ― (   ) ―   ↖ 4 km/h       
      `-’      10 km          
     /   \     0.0 mm         
                                                       ┌─────────────┐                                                       
┌──────────────────────────────┬───────────────────────┤ Thu 25. Aug ├───────────────────────┬──────────────────────────────┐
│           Morning            │             Noon      └──────┬──────┘    Evening            │            Night             │
├──────────────────────────────┼──────────────────────────────┼──────────────────────────────┼──────────────────────────────┤
│     \   /     Sunny          │     \   /     Sunny          │     \   /     Sunny          │     \   /     Clear          │
│      .-.      22 – 23 °C     │      .-.      30 – 32 °C     │      .-.      33 – 37 °C     │      .-.      31 – 35 °C     │
│   ― (   ) ―   ↖ 6 – 15 km/h  │   ― (   ) ―   ↑ 6 – 14 km/h  │   ― (   ) ―   ↘ 13 – 14 km/h │   ― (   ) ―   ↘ 6 – 17 km/h  │
│      `-’      10 km          │      `-’      10 km          │      `-’      10 km          │      `-’      10 km          │
│     /   \     0.0 mm | 0%    │     /   \     0.0 mm | 0%    │     /   \     0.0 mm | 0%    │     /   \     0.0 mm | 0%    │
└──────────────────────────────┴──────────────────────────────┴──────────────────────────────┴──────────────────────────────┘


''' 

import requests, os, fcntl, ephem, sys

from config_hms import *
from time import sleep
from lxml import html
from bieb import semafoor, TimeStamp, file_exists

reload(sys)
sys.setdefaultencoding('utf8')

DEBUG = 0

cUrl = 'http://www.meteofrance.com/previsions-meteo-france/vauvillers/70210'
page = requests.get(cUrl)

#nLen = len(page.text)

# dictionary of weather types
# put u before unicode
dDict = {u'Éclaircies':'Cloudy ',
         u'Ensoleillé':'Sunny',
          'Averses orageuses':'Thundershowers',
         u'Très nuageux':'Very cloudy',
         u'Pluies éparses':'Havy rain',
          'Rares averses':'Rare showers',
         u'Ciel voilé':'Cloudy'
        }

try:
   os.chdir(cDataDir)
except:
   # force mounting disk solarfarm RP60
   cStr ="sudo mount -t cifs -o user=" + rp_usr + ",password=" + rp_pwd + " //192.168.1.60/share /media/ssd"
   os.system(cStr)


#
# --------------- get positions of requested sub strings ------------ #
#
def locations_of_substring(string, substring):
    """Return a list of locations of a substring."""

    substring_length = len(substring)    
    def recurse(locations_found, start):
        location = string.find(substring, start)
        if location != -1:
            return recurse(locations_found + [location], location+substring_length)
        else:
            return locations_found

    return recurse([], 0)

#
# ---------- sun rise ------------ #
#
def sunrise():

   cSun       = ""
   home_lat   = '47.921'        # adapted after google maps solar farm
   home_long  = '6.132'
   home_elev  = 283             # has almost no influence
   home_hor   = '5'            # degrees sun above horizont for twilight and dusk

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

   cStr = "Sunrise " + Sunrise + " sunset " + Sunset

   return cStr


#
# --------------- get tomorrow's weather forcast ------------ #
#
def tomorrow():
   # breaking down detail-day-02 line
   aPos = locations_of_substring(page.text, '#detail-day-02')
   line = page.text[aPos[0] : aPos[0] + 300]

   # get last part of detail-day-02 line 
   #   </span></li> <li class="day-summary-image"><span class="picTemps J_W1_0-N_0">Ensoleillé</span>
   #print line

   aPos = line.find("picTemps")

   # breaking down previsions:
   cStr = line[aPos:]
   cStr = cStr.replace('<','|')			# replace markers
   cStr = cStr.replace('>','|')
   aPos = locations_of_substring(cStr, "|") 	# find markers
   cStr = cStr[aPos[0]+1 : aPos[1]]		# extract
   cStr = cStr.strip()

   try:
      cStr =  dDict[cStr]
   except:
     cStr = 'Unknown'

   cStr = 'Weather forecast tomorrow: ' + cStr.upper()
 
   return cStr

#
# --------------- get todays weather  ------------ #
#
def today():
   # breaking down detail-day-01 line
   aPos = locations_of_substring(page.text, '#detail-day-01')
   line = page.text[aPos[0] : aPos[0] + 280]

   # get last part of detail-day-01 line
   # print line

   aPos = line.find("picTemps")

   # breaking down previsions:
   cStr = line[aPos:]
   cStr = cStr.replace('<','|')			# replace markers
   cStr = cStr.replace('>','|')
   aPos = locations_of_substring(cStr, "|")     # find markers
   cStr = cStr[aPos[0]+1 : aPos[1]]             # extract
   cStr = cStr.strip()

   try:
      cStr =  dDict[cStr]
   except:
     cStr = 'Unknown'

   cStr = 'Weather forecast today: ' + cStr.upper()

   return cStr

#
# --------------- get temps weather forcast ------------ #
#
def temps(nDay):

   tree = html.fromstring(page.content)

   aTempMin = tree.xpath('//span[@class="min-temp"]/text()')
   aTempMax = tree.xpath('//span[@class="max-temp"]/text()')

   if nDay == 1:
      cStr1 = aTempMin[0]
      cStr2 = aTempMax[0]

   elif nDay == 2:
      cStr1 = aTempMin[1]
      cStr2 = aTempMax[1]

   cStr1 = cStr1.replace('Minimale', '')
   cStr1 = 'Minimal temp ' + cStr1
   cStr2 = cStr2.replace('Maximale', '')
   cStr2 = 'Maximal temp ' + cStr2

   if nDay == 1:
      cStr = "TD "
   else:
      cStr = "TM "
   return  cStr + cStr1 + ' ' + cStr2


#
# --------------- compose weather forcast ------------ #
#
def main():

   aText = list()
   aText.append("Weater predictions for Le Mouton Qui Rit - " + TimeStamp('f'))   
   aText.append(sunrise())
   aText.append(today())
   aText.append(temps(1))
   aText.append(tomorrow())
   aText.append(temps(2))
   aText.append("Forecast generated " + TimeStamp('f'))   

      
   nCount = 0

   if DEBUG:
      print aText, "\n"
   
   if not file_exists('forecast.sem'):
      os.system('touch forecast.sem')
      os.system('chmod 644 forecast.sem')

   while nCount < 3:
      try:
         if DEBUG:
            print "writing 'forecast.sem' file"

         with open("forecast.sem", 'w') as fout:
            fcntl.flock(fout.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            fout.writelines( "%s\n" % item for item in aText )
      except:
         nCount += 1
         print 'file forecast.sem could not be written to',nCount
         sleep(1)
      finally:
         exit()



########### M A I N ##################

if __name__ == "__main__":

   main()


