#!/usr/bin/env python

import os
import pygsheets
import pandas as pd
import requests
import time


print("Running Strava 2 Hive")

def strava_screenshot(activity):
  # Create the command to run on chrome
  chrome_command = 'google-chrome --headless --screenshot="./screenshot_' + str(activity) + '.png" "https://www.strava.com/activities/' + str(activity) + '"'
  print(chrome_command)
  os.system(chrome_command)
  
def get_last_activity():
  # Last activity from google spreadsheet created by zapier
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
  row = []
  athletes = 5
  for i in range(athletes):
    row = wks.get_row(i + 1)
    if row[6] == activity:
      break
  return row
    
def strava_activity(athlete_id):
  print("Get latest activity from strava")
  print(athlete_id)
  
  
  
#print("Take screenshot of activity")  
#strava_screenshot(6790387629)

#print("Get the latest Activity")
#activity = get_last_activity()

#print("See if the activity is a Run")
#if activity[6] == "Run":
#  print("Yay, activity is a run, so ship it!!!")
#  athlete = get_athlete(activity[0])
#  print("Here are the athletes details")
  
print("Now use details to get activity from strava")
athlete_values = get_athlete("1778778")
print(athlete_values)

# Test if athlete bearer token is still value by testing athlete_values[8]
expire_time = athlete_values[8]
local_time = time.ctime(expire_time)
print("The local time for expire is:", local_time)



#try:
#  response = requests.post("https://www.strava.com/api/v3/oauth/token",
#                            params={'client_id': os.getenv('STRAVA_CLIENT_ID'), 'client_secret': os.getenv('STRAVA_SECRET'), 'code': 'c97c1a1e4e624972c7512a673c351f22b3d0b12d',
#                            'grant_type': 'authorization_code'})
#  access_info = dict()
#  activity_data = response.json()
#  access_info['access_token'] = activity_data['access_token']
#  print(activity_data)
#  print(access_info)
#except:
#  #print("Log - An Error occurred trying to authenticate with the {} Strava token".format(user_key))
#  print("Log - An Error occurred trying to authenticate with the Strava token")
#  # return False

