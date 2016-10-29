pump_dict = dict()
pump_dict['CV'] = {'relay': 'RELAY_CV',
                   'file' : 'cv_pump.dat',
                   'str1' : 'CV pump status is ',
                   'str2' : 'CV pump t='
                  }
pump_dict['FL'] = {'relay': 'RELAY_FLOOR',
                   'file' : 'floorpump.dat',
                   'str1' : 'FLOOR pump status is ',                     
                   'str2' : 'FLOOR pump t='
                  }
pump_dict['SF'] = {'relay': 'SFPOMP_PIN',
                   'file' : 'solarpump.dat',
                   'str1' : 'SF pump status t=',                     
                   'str2' : 'SF pump status t='
                  }
pump_dict['PL'] = {'relay': 'PL_PUMP',
                   'file' : 'poolpump.dat',
                   'str1' : 'Pool pump set to : ',                     
                   'str2' : 'pl_temp - status pool pump t='
                  }


def pumps(ID):
   cRelay = pump_dict[ID]["relay"]
   cFile  = pump_dict[ID]["file"]
   cStr1  = pump_dict[ID]["str1"]
   cStr2  = pump_dict[ID]["str2"]

   print "\n","-"*60
   print "pump ID........ ", ID
   print "relay.......... ", cRelay
   print "file name...... ", cFile
   print "log string..... ", cStr1
   print "semafoor string ", cStr2
   print "-"*60

cPump = pumps("FL")
cPump = pumps("CV")
cPump = pumps("SF")
cPump = pumps("PL")
