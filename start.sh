#!/bin/bash
cd /home/debian/bbwmixer
if [[ $# -ne 1 ]]; then
    sleep 60
else
    /usr/bin/pkill python3
fi
/usr/bin/sudo -H -u debian bash -c 'make; make upload'
source /home/debian/venv3.7/bin/activate
/usr/bin/nohup python3 mixerserver.py > nohup.out &
