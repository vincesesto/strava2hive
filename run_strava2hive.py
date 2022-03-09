#!/usr/bin/env python

import os

print("Running Strava 2 Hive")

def strava_screenshot(activity):
  # Create the command to run on chrome
  chrome_command = 'google-chrome --headless --screenshot="./screenshot"' + activity + '.png "https://www.strava.com/activities/' + activity + '"'
  print(chrome_command)
  os.system('google-chrome --headless --screenshot="./screenshot.png" "https://www.strava.com/activities/6790387629"')
  
print("Take screenshot of activity")  
strava_screenshot(6790387629)
