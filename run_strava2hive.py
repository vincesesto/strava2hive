#!/usr/bin/env python

import os

print("Running Strava 2 Hive")

def strava_screenshot(activity):
  # Create the command to run on chrome
  chrome_command = 'google-chrome --headless --screenshot="./screenshot_' + str(activity) + '.png" "https://www.strava.com/activities/' + str(activity) + '"'
  print(chrome_command)
  os.system(chrome_command)
  
print("Take screenshot of activity")  
strava_screenshot(6790387629)
