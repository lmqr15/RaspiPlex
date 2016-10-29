#!/usr/bin/env python
# -*- coding: UTF-8 -*-

""" 
  program :     day.py
  author  :     crobat
  created :     20161024
  update  :     
  node    :     RP51 IP 192.168.1.51 
  hostname:     Kachel

  script runs @ 0900 and 1600 via crontab

  checkin    time  RM AD EF DI BD PD PAY AMT REP NGT NAME
  2016-06-27 16:00 K1 A2 *  D2 B1 PD PB 102 1 * *
 
  rooms 1-4 are not permanently rented
  room 5 is permanently rented except when OOO is True 
     room 5 should be reheated after 2200 unless room 12 is rented
  
"""
import datetime
import time, os, sys
import RPi.GPIO as GPIO

from time import sleep
from datetime import datetime, timedelta
from bieb import *
from config_hms import *

CHECKIN   = 0
TIME      = 1
ROOM      = 2
ADULTS    = 3
KIDS      = 4
ANIMAL    = 0
DINNER    = 5
BABYBED   = 6
BREAKFAST = 7
MEANS     = 8
AMOUNT    = 9
REPEAT    = 10
NIGHTS    = 11
NAME      = 12

DEBUG     = 1

RELAY_BOILER = 14 # GPIO  - PIN => 8
RELAY_STUDIO = 18 # GPIO = PIN => 12

nDinnerPrice = 22
nRoomPrice   = 62

dPay = {"PA":"Air BnB",
        "PB":"Banque",
        "PC":"Cheque",
        "PP":"PayPal",
        "PE":"Cash"}

aStand = ("off","on")
file_name =  os.path.basename(sys.argv[0])

 
# -------------- SET UP --------------- #

GPIO.setwarnings(False)                 # sys error disable
GPIO.setmode(GPIO.BCM)                  # board settings

os.chdir(cDataDir)                      # set doc directory


i = datetime.datetime.now()
today = i.date()
nHour = i.hour

#
# --------- convert date --------- #
#
def date(cDate=None, format='%Y-%m-%d %H:%M'):
   if not cDate:
      return datetime.today().date()
   
   return datetime.datetime.strptime(cDate, '%Y-%m-%d %H:%M')


#
# ----------- out of office ------------- #
#
# 20161024 from gmail1.py removed reporting 
#
def out_of_office(cDate):

    cOut = "NO"

    # when ooo send graph, log and temp data
    with open("ooo.sem", "r") as fo:
       line  = fo.readlines()
       cOut = line[0][-4:].strip("\n").strip("=").upper()

    return (cOut == "YES")

#
# --------- switch boiler ROOM 1-4 ------------ #
#
# if OOO = YES or 09:00 swith boilers off
#
def boiler(bBoiler1, bBoiler5):   

   room = 1
   cSwitch = 'off'

   if bBoiler1:
      cSwitch = 'on'   
      room = 1   
   
   if bBoiler5:
      cSwitch = 'on'
      room = 5     # room 5 or appartment
   
   if room == 1:

      GPIO.setup(RELAY_BOILER,GPIO.OUT)

      bl_status = GPIO.input(RELAY_BOILER)
      status_old = bl_status

      if nHour == 9 or out_of_office(today):
         cSwitch = "off"
  
      if cSwitch == 'off':
         GPIO.output(RELAY_BOILER, GPIO.LOW)         # switch off
      elif cSwitch == 'on':
         GPIO.output(RELAY_BOILER, GPIO.HIGH)         # switch on

      bl_status = GPIO.input(RELAY_BOILER)

      cMsg = TimeStamp("l") + " | day.py - Boiler ROOMS switched t=" + aStand[bl_status]

      if DEBUG:
         cMsg = '\n' + '-'*30 + ' MESSAGES ' + '-'*30 + '\n'+ cMsg
         print cMsg

      if bl_status <> status_old:
         semafoor("boiler-rooms.dat",cMsg,"w")
         sleep(.3)
         semafoor("sf.log",cMsg,'a')

   if room == 5 or room == 12:
      # room 5 is permanently rented except when OOO IS True
      GPIO.setup(RELAY_STUDIO,GPIO.OUT)

      bl_status = GPIO.input(RELAY_STUDIO)
      status_old = bl_status

      if nHour == 9 or out_of_office(today):
         cSwitch = "off"
      else:			# 1600 boiler should go  on
         cSwitch =  'on'
  
      if cSwitch == 'off':
         GPIO.output(RELAY_STUDIO, GPIO.LOW)         # switch off
      elif cSwitch == 'on':
         GPIO.output(RELAY_STUDIO, GPIO.HIGH)         # switch on

      bl_status = GPIO.input(RELAY_STUDIO)

      cMsg = TimeStamp("l") + " | day.py - Boiler STUDIO switched t=" + aStand[bl_status]

      if DEBUG:
         cMsg = '\n' + '-'*30 + ' MESSAGES ' + '-'*30 + '\n'+ cMsg
         print cMsg

      if bl_status <> status_old:
         semafoor("boiler-studio.dat",cMsg,"w")
         sleep(.3)
         semafoor("sf.log",cMsg,'a')


   return

#
# --------- get contents agenda -------- #
#
def read_agenda():

   aBooking=[]

   with open("agenda.dat", "r") as f:
      next(f)
      for line in f:
         aBooking.append(line.split())
   
   return aBooking

#
# --------- prepare schedule ------------ #
#
""" 
MAIL results to lemoutonquirit@gmail.com
"""
def occupation(aBooking):
    
   cSwitch = 'on'
   cMsg = "" 

   bDay    = True  # prevent printing date
   bWarning = False # reservations for tomorrow
   bBoiler1 = False # boiler rooms 1-4 off if no booking
   bBoiler5 = False # boiler room 5 off if no booking

   tot_adults = 0
   tot_diners = 0         
   tot_kids   = 0
   tot_amount = 0

   if DEBUG:
      print "="*30, " Today's occupation ", "="*30

   for x in aBooking:
      
      dStr =  x[CHECKIN]+ " " + x[TIME]
      dBook = date(dStr).date()

      print dBook, bDay

      if dBook == today + timedelta(days=1):

         if not bDay:
            cMsg += x[CHECKIN] + '\n'
            bDay = True

         cMsg += "    " + x[ROOM] + ' will be occupied from ' + str(dBook) + ' till '
         cMsg += str(dBook + timedelta(days=float(x[NIGHTS]))) + ' by: ' + x[NAME] + '\n'

         bWarning = True

      if dBook == today:

         if x[ROOM] <> 'K5':
            bBoiler1 = True   # there is a booking for one of rooms 1-4
         elif x[ROOM] == 'K12' and nHour == 16:  # appartment
            bBoiler5 = True   # there is a booking for room 12
         elif x[ROOM] == 'K5' and nHour == 22:
            bBoiler5 = True   # room 5 is occupied and heats after 2200

         if bDay:
            cMsg += x[CHECKIN] + '\n'
            bDay = False

         if x[KIDS] == '*':
            x[KIDS] = "K0"
   
         cMsg += "    " + x[ROOM] + ' is occupied by ' + x[ADULTS][1:] + ' adults ' + x[KIDS][1:] + ' kids.'
         cMsg += ' Diners ' + x[DINNER][1:] + ' | contact: ' + x[NAME] + '\n'

         nAmount = float(x[AMOUNT]) + float(x[DINNER][1:])*nDinnerPrice


         tot_amount += nAmount

         tot_adults += float(x[ADULTS][1:])
         tot_diners += float(x[DINNER][1:])
         tot_kids   += float(x[KIDS][1:])


   cMsg += '\n' + '-'*30 + 'SUMMARY' + '-'*30 + '\n'
   
   cMsg += 'Adults ' + str(tot_adults) + ' kids ' + str(tot_kids) + ' Diners '
   cMsg += str(tot_diners) + ' Bruto ' + str(tot_amount)

   if DEBUG:
      print cMsg
   else:
      alert(cMsg, 'occupancy report ' + x[CHECKIN], 'RaspiPlex')
   
   return bBoiler1, bBoiler5

#
# --------- program logic ---------- #
#
""" 
program runs via crontab @ 0900 and @ 1600

"""
def main():

   if not DEBUG:
      boot_script(cDataDir, file_name)  	# report in log.sf when this script started

#   bRead = True

   print '-'*70
   print 'Reservations: ',today, nHour, "\n"

   aBooking = read_agenda()			# read agenda.dat

   bBoiler1, bBoiler5  = occupation(aBooking)	   	# report today's reservations

   boiler(bBoiler1, bBoiler5)


# --------- divert to main ---------- #
if __name__ == "__main__":
    main()

