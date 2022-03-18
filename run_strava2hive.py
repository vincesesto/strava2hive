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
  
def get_last_activity():
  gc = pygsheets.authorize(service_file='strava2hive.json')
  sh = gc.open("StravaActivity")
  #select the first sheet
  wks = sh[0]
  print("What is the number of rows in this sheet")
  cells = wks.get_all_values(include_empty_rows=False, include_tailing_empty=False, returnas='cells')
  print(type(cells))
  print(cells[5])
  
  
def sheets_connect(sheet_name):
  print("Test connect")
  gc = pygsheets.authorize(service_file='strava2hive.json')
  # open the google spreadsheet
  print("Test open")
  sh = gc.open(sheet_name)
  #select the first sheet
  print("Test get rows")
  wks = sh[0]
  print(wks.get_row(2))
    
print("Take screenshot of activity")  
strava_screenshot(6790387629)

print("Check values in hive users sheet")
sheets_connect("HiveAthletes")

get_last_activity()


