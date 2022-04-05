#!/usr/bin/env python

import os
import pygsheets
import pandas as pd
import requests
import time
from datetime import datetime, timedelta

# Functions
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

def update_athlete(athlete_id, change_val, column):
  gc = pygsheets.authorize(service_file='strava2hive.json')
  sh = gc.open("StravaActivity")
  wks = sh[0]
  row = []
  athletes = 5
  for i in range(athletes):
    row = wks.get_row(i + 1)
    if row[6] == athlete_id:
      cell_value = column + str(i + 1)
      wks.update_value(cell_value, change_val)
      row = wks.get_row(i + 1)
      break
  return row

def activity_posted(athlete_id, activity_id):
  gc = pygsheets.authorize(service_file='strava2hive.json')
  sh = gc.open("StravaActivity")
  wks = sh[1]
  row = []
  posted = False
  cells = wks.get_all_values(majdim='ROWS', include_tailing_empty=False, include_tailing_empty_rows=False)
  total_rows = len(cells)
  for i in range(total_rows):
    row = wks.get_row(i + 1)
    print(row[1])
    if row[1] == activity_id:
      posted = True
      break
  return posted

def record_post(athlete_id, activity_id):
  gc = pygsheets.authorize(service_file='strava2hive.json')
  sh = gc.open("StravaActivity")
  wks = sh[1]
  cells = wks.get_all_values(majdim='ROWS', include_tailing_empty=False, include_tailing_empty_rows=False)
  # Add athlete id
  cell_value = "A" + str(len(cells) + 1)
  wks.update_value(cell_value, athlete_id)
  # Now add the activity
  cell_value = "B" + str(len(cells) + 1)
  wks.update_value(cell_value, activity_id)
    
def refresh_access_token(athlete):
  # We need to update the access_token in strava every six hours
  try:
    response = requests.post("https://www.strava.com/api/v3/oauth/token",
                             params={'client_id': os.getenv('STRAVA_CLIENT_ID'), 'client_secret': os.getenv('STRAVA_SECRET'), 
                             'code': athlete[6], 'grant_type': 'refresh_token', 'refresh_token': athlete[9] })
    access_info = dict()
    activity_data = response.json()
    access_info['access_token'] = activity_data['access_token']
    access_info['expires_at'] = activity_data['expires_at']
    access_info['refresh_token'] = activity_data['refresh_token']
    update_athlete(athlete[6], access_info['access_token'], 'H')
    update_athlete(athlete[6], access_info['expires_at'], 'I')
    print(update_athlete(athlete[6], access_info['refresh_token'], 'J'))
    
  except:
    print("Log - An Error occurred trying to authenticate with the {} Strava token".format(athlete[6]))
    return False
  
def new_user_access_token(athlete):
  # New users have a different process for getting access tokens
  try:
    response = requests.post("https://www.strava.com/api/v3/oauth/token",
                             params={'client_id': os.getenv('STRAVA_CLIENT_ID'), 'client_secret': os.getenv('STRAVA_SECRET'),
                                     'code': athlete[6], 'grant_type': 'authorization_code'})
    access_info = dict()
    activity_data = response.json()
    access_info['access_token'] = activity_data['access_token']
    access_info['expires_at'] = activity_data['expires_at']
    access_info['refresh_token'] = activity_data['refresh_token']
    update_athlete(athlete[6], access_info['access_token'], 'H')
    update_athlete(athlete[6], access_info['expires_at'], 'I')
    print(update_athlete(athlete[6], access_info['refresh_token'], 'J'))
  except:
    print("Log - An Error occurred trying to authenticate with the Strava token")
    return False

def strava_activity(athlete_id):
  athlete_details = get_athlete(athlete_id)
  # activity bearer is needed as part of the data
  print("Log - Searching For New Activities")
  bearer_header = "Bearer " + athlete_details[7]
  headers = {'Content-Type': 'application/json', 'Authorization': bearer_header}
  t = datetime.now() - timedelta(days=1)
  parameters = {"after": int(t.strftime("%s"))}
  response = requests.get("https://www.strava.com/api/v3/athlete/activities?per_page=5", headers=headers, params=parameters )
  activity_data = response.json()
  for i in range(len(activity_data)):
    activity = activity_data[i]
    if activity['type'] == "Run":
      print(activity['type'])
      print("Log - Activity is a run, now can we see if it is already posted")
      posted_val = activity_posted(athlete_id, activity['id'])
      if posted_val:
        print("Log - Activity has been posted already, move on")
      else:
        print("Log - Activity has not been posted yet, ship it!!")
        # Create a function that also adds to the sheet
        record_post(athlete_id, activity['id'])
  # Maybe seperate this into another function
  basic_data = activity_data[0]
  print("Log - Now get some more detailed information")
  strava_activity_url = "https://www.strava.com/api/v3/activities/" + str(basic_data['id'])
  response = requests.get(strava_activity_url, headers=headers, )
  more_activity_data = response.json()
  activity_info = dict()
  activity_info['id'] = basic_data['id']
  activity_info['name'] = more_activity_data['name']
  activity_info['distance'] = more_activity_data['distance']
  activity_info['type'] = more_activity_data['type']
  activity_info['start_date_local'] = more_activity_data['start_date_local']
  activity_info['location_country'] = more_activity_data['location_country']
  activity_info['description'] = more_activity_data['description']
  return activity_info
  
#print("Take screenshot of activity")  
#strava_screenshot(6790387629)

#print("Get the latest Activity")
#activity = get_last_activity()

##################################################
# Workflow from scratch
##################################################

# Now we just have a list of Strava ID's but we will eventually make a list from our sheet
strava_athletes = ['1778778']

print("Log - Use athlete details to get activity from strava")
for i in strava_athletes:
  print("Log - First get athlete details from sheet so you can access strava")
  athlete_values = get_athlete(i)
  print("Log - Athlete Values: ", athlete_values)
  # Test if athlete bearer token is still valid by testing athlete_values[8]
  if athlete_values[8] == '':
    print("Log - Expire time is empty, so need to get auth from strava")
    new_user_access_token(athlete_values)
  else:
    print("Log - User is an existing user, so we need to check if we need to update the strava token")
    expire_time = int(athlete_values[8])
    current_time = time.time()
    expired_value = expire_time - int(current_time)
    if expired_value > 0:
      print("Log - Strava Token Still Valid")
    else:
      print("Log - Strava Token Needs To Be Updated")
      refresh_access_token(athlete_values)

  print("Log - See what activity the athlete has")
  activity_details = strava_activity(i)
  print(activity_details)
  # Add a test to see if the activity was a run and then post if it is
  # we might need to also bring down all the activity for the day and not just the last

# Add details of the post to a new spreadsheet
# Start looking at hive automation
# Hive - reblogging
# Hive - posting with user posting key
# Refactor for more than one user
# Use the hive blocks explorer to help troubleshoot issues https://hiveblocks.com/@run.vince.run


# Posting to Hive
#from beem.imageuploader import ImageUploader
#from beem import Hive
#from beem.nodelist import NodeList
#
#nodelist = NodeList()
#nodelist.update_nodes()
#nodes = nodelist.get_hive_nodes()
#
#wif_post_key = getpass.getpass('Posting Key: ')
#wif = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
#hive = Hive(nodes=nodes, keys=[wif])
#author = 'strava2hive'
#image_path = '/path/to/image'
#image_name = 'IMAGE'
#image_uploader = ImageUploader(blockchain_instance=hive)
#img_link = image_uploader.upload(image_path, author, image_name=image_name)
#
#title = "Testing Posts From Code"
#body = f'''
#![{image_name}]({img_link['url']})
#
#This is a test to see if I can 
#
#Start to make posts in Hive using
#
#Code!
#'''
#
#parse_body = True
#self_vote = False
#tags = ['exhaust', 'test']
#
#hive.post(title, body, author=author, tags=tags, parse_body=parse_body, self_vote=self_vote)










