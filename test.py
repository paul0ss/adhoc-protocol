#!/usr/bin/python3

import time
from datetime import datetime

while(True):
    timestamp = int(datetime.timestamp(datetime.now()))
    print(str(timestamp))
    time.sleep(1)