#!/usr/bin/env python

import os
import pygsheets
import pandas as pd

print("Running Strava 2 Hive")

def strava_screenshot(activity):
  # Create the command to run on chrome
  chrome_command = 'google-chrome --headless --screenshot="./screenshot_' + str(activity) + '.png" "https://www.strava.com/activities/' + str(activity) + '"'
  print(chrome_command)
  os.system(chrome_command)
  
def sheets_connect(sheet_name):
  print("Test connect")
  gc = pygsheets.authorize(service_file='strava2hive.json')
  # open the google spreadsheet
  print("Test open")
  #sh = gc.open(sheet_name)
  sh = gc.open_by_url("https://docs.google.com/spreadsheets/d/1Evd8kFy28cJlU08G2GMSOj0gA2PX2Hypte5W4s_LqtI/edit?usp=drivesdk")
  #select the first sheet
  print("Test get rows")
  wks = sh[0]
  wks.get_row(2) 
    
print("Take screenshot of activity")  
strava_screenshot(6790387629)

print("Check values in hive users sheet")
sheets_connect("HiveAthletes")
