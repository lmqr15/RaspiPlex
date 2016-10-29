# config_hms.py

# numerics
nBackUp      = 0                                # switch om backup aan te maken
nBadPomp     = 0                                # badpomp aansturing

nCVPomp      = 0                                # CV pomp aansturing
nCVtemp      = 0                                # temp CV garage

nDaglicht    = 0				# daglicht sensor 0 = nacht
nOndergrens  = 6				# als temp ubde 6 graden dan pomp
nOutput      = 0                                # temp output exchanger

nPin         = 12                               # poort nummer temperatuur opne$
nPomp        = 0                                # switch pomp
nPompAanI    = 3                                # status SF pomp intermitterend
nPompUitI    = 4                                # status pomp intermitterend

nSensors     = 0                                # aantal temp opnemers
nSleep3      = 3                                # pause tijd motorische drieweg$
nSleep       = 60                               # generieke wachttijd volgende $
nSolartemp   = 0                                # temp soalr collector
nSolMax      = 85                               # maximum temp solarcollector >$

nTeller      = 0                                # teller generiek
nTemp        = 0                                # temperatuur var
nTempMinimum = 32                               # minimum temp SF
nTryout      = 0                                # teller om testcyclus kort te $
nZwm         = 0				# temperatuur zwembad
tMax         = 27                               # temperatuur waarbij klep zich$
tMin         = 19                               # temperatuur waarbij klep zich$


# ======== booleans =============
bZomer       = True                             # switch voor zomer aan, zie se$


# ======= strings ==========
base_dir     = '/sys/bus/w1/devices/'           # dir van alle divices
pad          = "/home/pi/scripts/"              # set dir naar default doc dire$
cDataDir     = "/media/ssd/solarfarm/"          # data dir on all secundary nodes
cWebDir      = "/data/web/"

gmail_user   = “YOUR USERNAME"

cHeader      = "\n=========================== House Management System: temps =====================\n"
cFooter      = "\n================================================================================"
cSeizoen     = "zomer"
cTemp        = "" 				# temperatuur string
device_file  = ""                               # file temperatuur en ID sensor$
device_folder= ""                               # dir waar sensor bestanden sta$
dirList      = ""                               # lijst met bestanden sensoren
lines        = ""                               # inhoud opnemer file
aTypeCloud   = ("Extreme dark", "Very dark", "Dark", "Cloudy", "Sunny", "Bright daylight")


gmail_pwd    = “YOUR PASSWORD"
rp_usr      = “RASPI USER”
rp_pwd      = “RASPI PASSWORD”

file_list    = list()                           # aanmaken lege array
sensor_list  = list()                           # lijst met sensornamen

# LET OP families van deze sensoren kunnen verschillend zijn 10, 28 etc
# see dir : /sys/bus/w1/devices:

ID_accu      = "681ff"                          # temp accumulator
ID_cooling   = "681ff"                          # temp cooling circuit
ID_sfgar     = "3abd8"                          # aankomst SF in garage
ID_retour    = "46bff"                          # retour CV garage
ID_atel      = "6ebff"				# temp atelier 

ID_buiten    = "556c0"                          # temp in pomphuisje
ID_solar     = "679ff"				# temp solarfarm
ID_pool      = "fdaff"    		        # output warmtewisselaar
ID_ground    = "c72ff"    		        # temp in ground, 1m below surface

ID_floor    = "397ce"				# temp floor studio
ID_kachel   = "5d1ff" 				# temp CV kachel changed 20161024

# let op deze kan zomaar veranderen als er andere sensoren aan komen
ID_test      = "41ce7"				# temp testbank
ID_test2     = "6b5ff"				# temp testbank 2

cStr         = ""				# container input / strings 
temp_c       = ""				# container temperatuur


# ============= STATICS  ======================== 
BADPOMP_PIN  = 17       # Badpomp
BADPOMPAAN   = 1        # define's status
BADPOMPUIT   = 0        #

# RP50
KLEP1_STAND_A   = "A"   # 3-way valve
KLEP1_STAND_B   = "B"   # 3-way valve

#     NOTE!!!
#
# in close_all.py adapt collection when pins change
                                            
KLEP_1_PIN   = 22       # drieweg klep
KLEP_5_6_PIN = 8        # ATELIER (via solar)
KLEP_7_8_PIN = 3        # huis
KLEP_9_PIN   = 10       # hot tub
KLEP_10_PIN  = 9        # cooling - superseeds accu
SFPOMP_PIN   = 11       # pomp solarfarm
RELAY_H_PIN  = 7        # reserve
RELAY_B_PIN  = 27       # reserve

# RP53
SCHEMER_PIN  = 22       # IO poort schemer schakelaar

SFPOMPAAN    = 0        #
SFPOMPUIT    = 1        #
PL_LAMP      = 11	# indicator lamp at pool
PL_PUMP      = 17	# start / stop pool pump
PL_RELAY_8   = 25	# NOP
PL_RELAY_7   = 24	# NOP
PL_RELAY_6   = 11	# NOP
PL_RELAY_5   = 9	# NOP
PL_RELAY_4   = 10	# speed pump
PL_RELAY_3   = 22	# speed pump
PL_RELAY_2   = 27	# speed pump
PL_RELAY_1   = 17	# badpomp aan

# MPI  configuration
MPI_PORT  = 10956
MPI_SL    = 50		# solarfarm
MPI_CV    = 51		# central heating stove
MPI_DE    = 52		# development
MPI_PL    = 53		# pool
MPI_KI    = 54		# kitchen
MPI_AT    = 55		# atelier
MPI_AP    = 56          # appartment
MPI_ST    = 57          # studio
MPI_LMQR  = 60		# hub - central node
MPI_RP61  = 61		# RP 3
MPI_RP62  = 62		# RP 3
MPI_BP1   = 58		# firewall
MPI_CL	  = 70		# cluster
