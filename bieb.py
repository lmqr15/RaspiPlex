import os
import time, datetime
import socket
import ephem

from datetime import timedelta
from config_hms import *
from time import sleep

""" 
CONTENTS

alert(text,subject,sender)
boot_script()			# to signal booting a script
connection(ip, targetname)
file_exists(filename)
get_hour()
get_ip()
get_ext_ip()	  # returns external ip
get_mac_address() # returns classic mac, mac hex and mac decimal
get_net()     	  # to test if network connection OK
get_serial()  	  # returns raspi's CPU's serial number
getCPUtemp()
getCPUuse()
getRAMuse()
pool_status()
print_season()
season()
semafoor(cFilename, cText, modus):
sunset()
temp_read()
TimeStamp(cPipe)
truncate(filename,nlines)

"""
#
# --------------- sending email alert ------------------
#
""" 
   TODO
   expand alert to have attachments see gmail1.py
   or use gmail1.py for this (see todo at gmail1.py)
"""
def alert(text, subject, sender):

    import smtplib                      # Import smtplib for the actual sending function
    import mimetypes                    # for guessing mime types
    import email                        # actual sending mail
    import email.mime.application       # to attach parts

    # Create a text/plain message
    msg = email.mime.Multipart.MIMEMultipart()
    msg['Subject'] = subject 
    msg['From']    = sender 
    msg['To']      = 'raspi@solarfarm@gmail.com'

    # The main body is just another attachment
    body = email.mime.Text.MIMEText(text)

    msg.attach(body)

    s = smtplib.SMTP('smtp.gmail.com:587')
    s.starttls()

    s.login(gmail_user,gmail_pwd) # see config file
    s.sendmail(gmail_user,[gmail_user], msg.as_string())
    s.quit()

#
# ----------- report start script -------------------
#
def boot_script(cDataDir, script_name):

# set system wide data dir
   try:
      os.chdir(cDataDir)
      cMsg = TimeStamp("l") + ' | datadir mounted : ' + cDataDir + ' from ' + script_name
   except OSError as e:
      cMsg = TimeStamp("l") + ' | ' + script_name + str(e)

      # mount SSD
      cStr = "sudo mount -t cifs -o user=" + rp_usr
      cStr += ",password=" + rp_pwd + "  //192.168.1.60/share/media/ssd"
      os.system(cStr)
      cMsg += "\n" + TimeStamp("l") + ' | pl_temp SSD mounted'

      cDatadir = '/home/pi/scripts/'
      cMsg += "\n" + TimeStamp("l") + ' | exception datadir mounted: ' + cDataDir + 'from '+ script_name

   os.chdir(cDataDir)
   semafoor("sf.log", cMsg, "a")

   ip4 = get_ip()   # node

   # get current script name and host ID
   cMsg = script_name
   cMsg = TimeStamp("l") + " | " + cMsg + " started from "

   if socket.gethostname().find('.')>=0:
      cMsg += socket.gethostname()
   else:
      cMsg += socket.gethostbyaddr(socket.gethostname())[0]

   cMsg += " @ " + ip4

   semafoor("sf.log", cMsg, "a")                # write to log file

   return cDataDir

#
# ------- check network connection --------------
#
def connection(ip, target):

   bConnect = False
   cHost = socket.gethostname().upper()
   sleep(0.5)

   s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
   s.settimeout(0.5)

   try:
      s.connect((ip,22))
      cMsg = TimeStamp('l') +' | ' + cHost+' connected to '+target
      bConnect = True
   except Exception, e:
      cMsg = TimeStamp('l') +' | Connection to '+target+'from '+cHost+' failed'
      semafoor("sf.log", cMsg, "a")
      alert(cMsg, 'connection lost', cHost)

   s.close()

   return bConnect

#
# ---- does file xyz exists ------
#
def file_exists(filename):

   try:
      with open(filename) as f:
         return True
   except:
      return False

#
# ----------  get local time / hour ---------------
#
def get_hour():

   now     = datetime.datetime.now()           # date now
   bu_date = now.date()                        # date
   t       = now.time()                        # time

   return t.hour                               # hour

#
# get node's ip4 address 
#
def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 0))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

#
# ------ get external IP --------------- #
#
def get_ext_ip():
 
   cCmd = "wget -q -O - checkip.dyndns.org|sed -u -e "
   cCmd += "'s/.*Current IP Address: //' -e 's/<.*$//' > ip.sem"

   os.system(cCmd)

   with open("ip.sem") as fin:
      ip_new = fin.readline().strip()

#   print "new ip : ",ip_new

   with open("ip_old.sem") as fin:
      ip_old = fin.readline().strip()

#   print "old ip : ",ip_old

   cStr = TimeStamp("l") + " | "

   if ip_new <> ip_old:
      cStr += "LMQR's IP is changed from " + ip_old + " into: " + ip_new
      semafoor("ip_old.sem",ip_new,"w")         # write new ip to old sem file
   else:
      cStr += "LMQR's IP has not changed :" + ip_new

   return cStr

#
# ------- check health of CPU -------- #
#
def getCPUtemp():
   # is logic link
   cStr = '/sys/class/thermal/thermal_zone0/temp'

   with open(cStr) as f:
      cStr = round(float(f.readline())/1000,1)

   return str(cStr)

#
# get % use of CPU
#
def getCPUuse():
    return(str(os.popen("top -n1 | awk '/Cpu\(s\):/ {print $2}'").readline().strip(\
)))

#
# get MAC address
# ref: http://stackoverflow.com/questions/159137/getting-mac-address
#
def get_mac_address():
   from uuid import getnode as get_mac

   mac = get_mac()
   mac_b = get_mac()

   while mac <> mac_b and n < 3: # mac address could be faked caused by time out
      mac = get_mac()
      mac_b = get_mac()
      n += 1

   mac_hex = hex(mac)
   mac_str = ':'.join(("%012X" % mac)[i:i+2] for i in range(0, 12, 2))

   # print 'MAC decimal    : ', mac
   # print 'MAC hexa       : ', mac_hex
   # print 'MAC classic    : ', mac_str
   return mac_str, mac_hex, mac 

#
# to test network connection
#
def get_net():
#    conn = httplib.HTTPConnection("www.google.com")
   import httplib
   conn = httplib.HTTPConnection("192.168.1.60")
   try:
      conn.request("HEAD", "/")
      return True
   except:
      return False

#
# get serial number of raspi
#   each raspi seems to have its own unique serial number
#
def get_serial():
   # can be used as a security feature:
   #   only equests from this raspi are allowed

   # Extract serial from cpuinfo file
   cpuserial = "0000000000000000"
   try:
      with open('/proc/cpuinfo','r') as f:
         for line in f:
            if line[0:6]=='Serial':
               cpuserial = line[10:26]
   except:
      cpuserial = "ERROR000000000"

   return cpuserial
#
# ram usage in memory
#
def getRAMinfo():
    p = os.popen('free')
    i = 0
    while 1:
        i = i + 1
        line = p.readline()
        if i==2:
            return(line.split()[1:4])

#
# ----------  determine if pool is in function  --------------------
# this can also depend on day of year and season for fail safe 
#
def pool_status():
   bPool = False

   with open("poolstatus.sem", 'r') as fo:
       line = fo.readline()

   if "open" in line.lower():
      bPool = True
 
   return bPool

#
# ----------  print date / season / week no  --------------------
#
def print_season():

   dt = datetime.datetime.now()
   cWeekNo = str(dt.isocalendar()[1])
   cSeason, nDoY = season()


   cStr  = "\n" + "-" * 50 + "\n"
   cStr += "\nDate ............. : " + TimeStamp("l")
   cStr += "\nDay of Year is ... : " + str(nDoY)
   cStr += "\nWeek number is ... : " + cWeekNo
   cStr += "\nToday it is ...... : " + cSeason
   cStr += "\n\n" + "-" * 50 + "\n"

   return cStr


# ==================== determin season =======================

""" 
limits seasons
2015                        2015
Perihelion  Jan   4 07    Equinoxes  Mar   20 22 45    Sept  23 08 21 (fall daynumber 266)
Aphelion    July  6 20    Solstices  June  21 16 38    Dec   22 04 48

To return season == summer : pump CV / floor alternating 10 mins per day 
To determine if pump pool goes on
For gmail1 to print on page

"""
def season():

   season = "summer"
   today  = datetime.datetime.now()
   nDoY   = (today - datetime.datetime(today.year, 1, 1)).days + 1

   # limits of seasons
#   if ((nDoY > 78) and (nDoY < 172)):
#      s = 0 	#spring
#   elif ((nDoY > 171) and (nDoY < 236)):
#      s = 1 	#summer
#   elif ((nDoY > 235) and (nDoY < 354)):
#      s = 2 	#fall
#   else:
#      s = 3 	#winter

#   seasons = ["spring","summer","fall","winter"]
 
   if nDoY >= 273 and nDoY <= 130: 
      sesason = "winter"

   return season, nDoY		#seasons[s], nDoY

# ---------- write semafoor ------------------
# will be in SQL database in future
#    when in sql enable both read and write
#    this will become a stored procedure
# 
def semafoor(cFilename, cText, modus):

    cText   += "\n"
    nCounter = 0
    bOK      = True
    mac      = get_mac_address()

    while nCounter < 3:
       try:
          with open(cFilename, modus) as f:
             f.write(cText)
          bOK = True
          nCounter = 3
       except:
          nCounter +=1
          sleep(1)
          bOK = False

    if bOK == False:
       with open("sf.log", "a") as log:
          cText = TimeStamp('l') + " writing to " + cFilename + " failed from "
          cText = mac[0] + "\n"
          log.write(cText)
       
    return bOK

###### SUNSET  - SUNRISE ####################################################
#
#
def sunset():

    repeat_str = 50

    #determine present date/time
    now_double = datetime.datetime.now()
    now_minutes = (60* now_double.hour)+ now_double.minute

    cMsg = "\n"
    cMsg += "-" * repeat_str
    cMsg += "\nDate/Time   : " + now_double.strftime("%Y-%m-%d %H:%M:%S") + " minutes" + str(now_minutes)

    # MSP N 47.92104 - E 6.13312 positie garage
    # aangepast mbv google maps pos. solar farm
    home_lat   = '47.921485'
    home_long  = '6.132854'
    home_elev  = 280
    # zon voldoende boven horizont in MSP bij 25
    home_hor   = '0'

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
    sr_minutes = sr_next.hour*60 + sr_next.minute
    ss_minutes = ss_next.hour*60 + ss_next.minute

    cMsg  = "\n"
    cMsg += "-"* repeat_str
    cMsg += "\n\nGPS position:  N " + home_lat + " - E " + home_long
    cMsg += "\n\nWith sun " + home_hor +" degrees above the horizon\n\n"
    cMsg += "-" * repeat_str
    cMsg += "\nnext sunrise: " + sr_next.strftime("%Y-%m-%d %H:%M:%S") + " minutes " + str(sr_minutes)
    cMsg += "\nnext sunset : " + ss_next.strftime("%Y-%m-%d %H:%M:%S") + " minutes " + str(ss_minutes)
    cMsg += '\n'
    cMsg += "-" * repeat_str

    return cMsg
#
# ------------- get temperatures from sensors ------------
#
def temp_read(dev_file):

    temp_r = ""
    temp_c = ""

    with open(dev_file, 'r') as f:
       lines = f.readlines()

    equals_pos = lines[1].find('t=')

    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_r = str(round((float(temp_string) / 1000),1))

    return temp_r


# 
# ------  create time stamp string -------
#
def TimeStamp(cPipe):

    cTst = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if cPipe <> "l":                            # l stands for logging
       cTst = str(cTst).replace(" ",'|')        # adapt for gnuplot

    return cTst

#
# ----- get last n lines from data file ----
#
def truncate(filename,nlines):

    with open(filename, 'r') as fo:
       lines = fo.readlines()

    # get last 10 lines from logfile
    lines = lines[-nlines:]
    cText = ""

    # concatenate 4 email body
    for line in lines:
       cText += line


    return cText


