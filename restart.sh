#!/bin/bash

# restart.sh
# empty temp dir
# sudo rm /tmp/crontest.txt

# restart raspi  see etc/crontab for exact time
cd /home/pi/scripts
sudo python log.py
sudo shutdown -r now

