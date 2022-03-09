#!/usr/bin/env python

import os


print("Running Strava 2 Hive")

def strava_screenshot():
  os.system('google-chrome --headless --screenshot="screenshot.png" "https://www.strava.com/activities/6790387629"')
  
print("Take screenshot of activity")  
strava_screenshot()
