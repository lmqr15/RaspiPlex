#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import RPi.GPIO as GPIO
import os
import time, datetime
from bieb import *

# ====== STATICS ==============

BADPOMP_PIN     = 17    # Badpomp
KLEP_1_PIN      = 18    # relay C drieweg klep
KLEP_5_6_PIN    = 8     # ATELIER (via solar)
KLEP_7_8_PIN    = 3     # huis
KLEP_9_PIN      = 10    # accu 2 vanuit solarfarm
KLEP_10_PIN     = 9     # accu 2 vanuit CV
SFPOMP_PIN      = 15    # circulatiepomp solarfarm
RELAY_H_PIN     = 7     # reserve

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

os.chdir("/media/ssd/solarfarm/")                       # set doc directory

#
# alle kleppen dicht zetten
#
def kleppen():

#    collection = [17,15,18,9,10,3,8,7]  #  alle kleppen en keer open en dicht
    collection = [17,15,9,10,3,8,7]  #  alle kleppen en keer open en dicht

    GPIO.setup(BADPOMP_PIN,GPIO.OUT)    # badpomp

    GPIO.setup(KLEP_5_6_PIN,GPIO.OUT)   # klep 5 & 6  atelier
    GPIO.setup(KLEP_7_8_PIN,GPIO.OUT)   # klep 7 & 8  CV huis
    GPIO.setup(KLEP_9_PIN,GPIO.OUT)     # klep 9
    GPIO.setup(KLEP_10_PIN,GPIO.OUT)    # klep 10
    GPIO.setup(RELAY_H_PIN,GPIO.OUT)    # onbezet
    GPIO.setup(SFPOMP_PIN,GPIO.OUT)     # solarfarm pomp in winter allways ON
    GPIO.setup(KLEP_1_PIN,GPIO.OUT)     # driewegklep will be set bij othe scripts

    cStr =""

    for x in collection:
        cStr += str(x) + ","
        GPIO.output(x,GPIO.HIGH)
        time.sleep(0.5)
        GPIO.output(x,GPIO.LOW)
        time.sleep(0.5)

    GPIO.output(SFPOMP_PIN,GPIO.LOW)   # altijd weer aan zetten!!!

    # moet een manier komen om de stand van de klep te controleren!
    # iets met een ledje / spiegeltje of een magneetje o.i.d. 
    GPIO.output(KLEP_1_PIN,GPIO.HIGH)  # relays C drieweg klep stand A

    cMsg = TimeStamp("klep") + " | driewegklep reset stand t=A" 
    semafoor("drieweg.dat",cMsg,"w")

    cMsg = TimeStamp("l") + " | valves " + cStr + " reset"
    semafoor("sf.log",cMsg,"a")

    cStr = ""

# M A I N

kleppen()


