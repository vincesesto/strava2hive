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
  cells = wks.get_all_values(majdim='ROWS', include_tailing_empty=False, include_tailing_empty_rows=False)
  print(cells[-1])
  return cells[-1]

def get_athlete(activity):
  gc = pygsheets.authorize(service_file='strava2hive.json')
  sh = gc.open("HiveAthletes")
  wks = sh[0]
  athletes = 5
  for i in range(athletes):
    print(i)
    print(wks.get_row(i))
    row = wks.get_row(i)
    if row[6] == activity:
      print(row[6])
      break
  return row
    
#print("Take screenshot of activity")  
#strava_screenshot(6790387629)

print("Get the latest Activity")
activity = get_last_activity()

print("See if the activity is a Run")
if activity[6] == "Run":
  print("Yay, activity is a run, so ship it!!!")
  athlete = get_athlete(activity[0])
  print(athlete)
  
  

