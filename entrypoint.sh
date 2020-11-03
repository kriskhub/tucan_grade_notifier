#!/bin/sh
service postfix restart 
python ./tucan_grade_notifier.py -l debug.log -u <uniquetuid> -p <password> -m <mail@example.com> -i 30
