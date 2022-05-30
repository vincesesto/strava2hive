#!/usr/bin/env python

import os
import re
import pygsheets
import pandas as pd
import requests
import time
import random
import string
import hive_work
import pipedream_modules
from selenium import webdriver
from selenium.webdriver.common.by import By
from time import sleep
from datetime import datetime, timedelta
from beem.imageuploader import ImageUploader
from beem import Hive
from beem.nodelist import NodeList
from hivesigner.operations import Comment
from hivesigner.client import Client
from hivesigner.operations import CommentOptions

# Functions
def strava_screenshot(activity):
  # Create the command to run on chrome
  #chrome_command = 'google-chrome --headless --screenshot="./screenshot_' + str(activity) + '.png" "https://www.strava.com/activities/' + str(activity) + '"'
  #print(chrome_command)
  #os.system(chrome_command)
  activity_url = "https://www.strava.com/activities/" + str(activity)
  image_name = "image_" + str(activity) + ".png"
  driver = webdriver.Chrome('/bin/chromedriver')
  driver.get(activity_url)
  sleep(10)
  driver.find_element(by=By.CLASS_NAME, value="btn-accept-cookie-banner").click() 
  #driver.find_element_by_class_name("btn-accept-cookie-banner").click() 
  driver.get_screenshot_as_file(image_name)
  driver.quit()
  os.system("ls -l")

def activity_posted(athlete_id, activity_id):
  # Check if an activity has been posted already
  gc = pygsheets.authorize(service_file='strava2hive.json')
  sh = gc.open("StravaActivity")
  wks = sh[1]
  row = []
  posted = False
  cells = wks.get_all_values(majdim='ROWS', include_tailing_empty=False, include_tailing_empty_rows=False)
  total_rows = len(cells)
  for i in range(total_rows):
    row = wks.get_row(i + 1)
    if str(row[1]) == str(activity_id):
      posted = True
      print("Activity has been found, now returning True")
      return posted
      break
  return posted

def record_post(athlete_id, activity_id, activity_type, activity_date):
  # Update the activity spreadsheet once activity has been posted to Hive
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
  # Add activity type
  cell_value = "C" + str(len(cells) + 1)
  wks.update_value(cell_value, activity_type)
  # Now add the activity date
  cell_value = "D" + str(len(cells) + 1)
  wks.update_value(cell_value, activity_date)
    
def refresh_access_token(athlete):
  # We need to update the access_token in strava every six hours
  try:
    response = requests.post("https://www.strava.com/api/v3/oauth/token",
                             params={'client_id': os.getenv('STRAVA_CLIENT_ID'), 'client_secret': os.getenv('STRAVA_SECRET'), 
                             'code': athlete[9], 'grant_type': 'refresh_token', 'refresh_token': athlete[13] })
    access_info = dict()
    activity_data = response.json()
    access_info['access_token'] = activity_data['access_token']
    access_info['expires_at'] = activity_data['expires_at']
    access_info['refresh_token'] = activity_data['refresh_token']
    hive_work.update_athlete(athlete[10], access_info['access_token'], 'L', "Strava2HiveNewUserSignUp")
    hive_work.update_athlete(athlete[10], access_info['expires_at'], 'M', "Strava2HiveNewUserSignUp")
    print(hive_work.update_athlete(athlete[10], access_info['refresh_token'], 'N', "Strava2HiveNewUserSignUp"))
    
  except:
    print("Log - An Error occurred trying to authenticate with the {} Strava token".format(athlete[6]))
    return False
  
def new_user_access_token(athlete):
  # New users have a different process for getting access tokens
  try:
    response = requests.post("https://www.strava.com/api/v3/oauth/token",
                             params={'client_id': os.getenv('STRAVA_CLIENT_ID'), 'client_secret': os.getenv('STRAVA_SECRET'),
                                     'code': athlete[9], 'grant_type': 'authorization_code'})
    access_info = dict()
    activity_data = response.json()
    access_info['access_token'] = activity_data['access_token']
    access_info['expires_at'] = activity_data['expires_at']
    access_info['refresh_token'] = activity_data['refresh_token']
    hive_work.update_athlete(athlete[10], access_info['access_token'], 'L', "Strava2HiveNewUserSignUp")
    hive_work.update_athlete(athlete[10], access_info['expires_at'], 'M', "Strava2HiveNewUserSignUp")
    print(hive_work.update_athlete(athlete[10], access_info['refresh_token'], 'N', "Strava2HiveNewUserSignUp"))
  except:
    print("Log - An Error occurred trying to authenticate with the Strava token")
    return False
  
def strava_activity_details(activity_id, bearer_header):
  strava_activity_url = "https://www.strava.com/api/v3/activities/" + str(activity_id)
  headers = {'Content-Type': 'application/json', 'Authorization': bearer_header}
  response = requests.get(strava_activity_url, headers=headers, )
  more_activity_data = response.json()
  activity_info = dict()
  activity_info['id'] = activity_id
  activity_info['name'] = more_activity_data['name']
  activity_info['distance'] = more_activity_data['distance']
  activity_info['duration'] = more_activity_data['elapsed_time']
  activity_info['type'] = more_activity_data['type']
  activity_info['start_date_local'] = more_activity_data['start_date_local']
  activity_info['location_country'] = more_activity_data['location_country']
  activity_info['description'] = more_activity_data['description']
  activity_info['calories'] = more_activity_data['calories']
  activity_info['photos'] = more_activity_data['photos']
  return activity_info 
    
def post_to_hive(athlete_id, activity_details):
  nodelist = NodeList()
  nodelist.update_nodes()
  nodes = nodelist.get_hive_nodes()
  #wif_post_key = getpass.getpass('Posting Key: ')
  # Get all the details including the posting keys
  athlete_details = hive_work.get_athlete(athlete_id, "Strava2HiveNewUserSignUp")
  #wif = os.getenv('POSTING_KEY')
  wif = athlete_details[6]
  hive = Hive(nodes=nodes, keys=[wif])
  author = athlete_details[1]
  distance = str(round(activity_details['distance'] * .001, 2))
  activity_type = activity_details['type'].lower()
  duration = str(round(activity_details['duration'] / 60))
  print("Log - Downloading images and getting details together")
  strava_screenshot(activity_details['id'])
  # Get athlete profile image
  if activity_details['photos']['primary'] == None:
    prof_image_path = '/home/circleci/project/S2HLogo.PNG'
    prof_image_name = 'S2HLogo.PNG'
    prof_image_uploader = ImageUploader(blockchain_instance=hive)
    prof_img_link = prof_image_uploader.upload(prof_image_path, author, image_name=prof_image_name)
    # Now set up the main image
    image_path = '/home/circleci/project/image_' + str(activity_details['id']) + '.png'
    image_name = 'image_' + str(activity_details['id']) + '.png'
    image_uploader = ImageUploader(blockchain_instance=hive)
    img_link = image_uploader.upload(image_path, author, image_name=image_name)
  else:
    profile_img = activity_details['photos']['primary']['urls']['600']
    command = 'wget ' + profile_img + ' -O prof_image_' + str(athlete_id) + '.png'
    os.system(command)
    image_path = '/home/circleci/project/prof_image_' + str(athlete_id) + '.png'
    image_name = 'prof_image_' + str(athlete_id) + '.png'
    image_uploader = ImageUploader(blockchain_instance=hive)
    img_link = image_uploader.upload(image_path, author, image_name=image_name)
    # The screen shot is now at the bottom of the page
    prof_image_path = '/home/circleci/project/image_' + str(activity_details['id']) + '.png'
    prof_image_name = 'image_' + str(activity_details['id']) + '.png'
    prof_image_uploader = ImageUploader(blockchain_instance=hive)
    prof_img_link = prof_image_uploader.upload(prof_image_path, author, image_name=prof_image_name)
  title = activity_details['name']
  hashtags, description =  hive_work.description_and_tags(activity_details['description'])
  body = f'''
  ![{image_name}]({img_link['url']})
  {author} just finished a {distance}km {activity_type}, that lasted for {duration} minutes.
  This {activity_type} helped {author} burn {activity_details['calories']} calories.
  
  Description from Strava: {description}
  
  If you would like to check out this activity on strava you can see it here:
  https://www.strava.com/activities/{activity_details['id']}
  
  About the Athlete: {athlete_details[2]}
  
  ![{prof_image_name}]({prof_img_link['url']})
  
  This is an automated post by @strava2hive and is currently in BETA.
  '''
  parse_body = True
  self_vote = False
  #tags = ['exhaust', 'test', 'beta', 'runningproject', 'sportstalk']
  tags = hashtags
  beneficiaries = [{'account': 'strava2hive', 'weight': 500},]
  print("Log - Posting to Hive")
  #hive.post(title, body, author=author, tags=tags, community="hive-176853", parse_body=parse_body, self_vote=self_vote, beneficiaries=beneficiaries)
  # This is the new work with Hivesigner
  c = Client(access_token=athlete_details[2],)
  permlink = ''.join(random.choices(string.digits, k=10))
  comment = Comment(
    author,
    permlink,
    body,
    title=title,
    parent_permlink="hive-176853",
    json_metadata=\{\"tags\":tags\}
  )
  comment_options = CommentOptions(
      allow_curation_rewards = True
      percent_hive_dollars = 5
  )
  c.broadcast([comment.to_operation_structure(),comment_options.to_operation_structure()])
  
def strava_activity(athlete_id):
  athlete_details = hive_work.get_athlete(athlete_id, "Strava2HiveNewUserSignUp")
  # activity bearer is needed as part of the data
  print("Log - Searching For New Activities")
  bearer_header = "Bearer " + athlete_details[11]
  headers = {'Content-Type': 'application/json', 'Authorization': bearer_header}
  t = datetime.now() - timedelta(days=1)
  parameters = {"after": int(t.strftime("%s"))}
  #response = requests.get("https://www.strava.com/api/v3/athlete/activities?per_page=3", headers=headers, params=parameters )
  response = requests.get("https://www.strava.com/api/v3/athlete/activities?per_page=3", headers=headers)
  activity_data = response.json()
  for i in range(len(activity_data)):
    activity = activity_data[i]
    print(activity['type'])
    if activity['type'] == 'Workout':
      print("Log - Activity is not a run or ride, so we can stop running this")
      continue
    print("Log - Activity is a run or ride, now can we see if it is already posted")
    posted_val = pipedream_modules.activity_posted_api(activity['id'])
    if posted_val:
      print("Log - Activity has been posted already, move on")
    else:
      print("Log - Activity has not been posted yet, ship it!!")
      print("Log - Now get some more detailed information")
      detailed_activity = strava_activity_details(activity['id'], bearer_header)
      print(detailed_activity)
      if detailed_activity['description'] == None:
        print("Log - Activity does not have a description, move on")
        #break
      elif detailed_activity['description'] == '':
        print("Log - Activity does not have a description, move on")
        #break
      else:
        post_to_hive(athlete_id, detailed_activity)
        print("Log - Add it now to the activity log")
        activity_date = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
        record_post(athlete_id, activity['id'], activity['type'], activity_date)
        # Work around for most recent post to be stored in HiveAthletes sheet
        hive_work.update_athlete(athlete_id, activity_date, "A", "Strava2HiveNewUserSignUp")
        print("Log - Activity posted so we only want one activity at a time for:", athlete_id)
        break

##################################################
# Workflow from scratch
##################################################

# Now we just have a list of Strava ID's but we will eventually make a list from our sheet
strava_athletes = hive_work.list_athletes(10, "Strava2HiveNewUserSignUp")
print(strava_athletes)

print("Log - Use athlete details to get activity from strava")
for i in strava_athletes:
  print("Log - When did the user post their last activity")
  activity_date = hive_work.get_latest_activity_date(i, "Strava2HiveNewUserSignUp", 10)
  print(f'Log - The last activity for the user {i} was on the date {activity_date}')
  date = datetime.strptime(activity_date, "%m/%d/%Y %H:%M:%S")
  act_timestamp = datetime.timestamp(date)
  current_time = time.time()
  NUMBER_OF_SECONDS = 86400 # seconds in 24 hours
  if (current_time - act_timestamp) > NUMBER_OF_SECONDS:
    print(f'Log - The last activity for the user {i} was more than 12 hours ago')
  else:
    print(f'Log - The last activity for the user {i} was NOT more than 12 hours ago')
    continue
  print("Log - First get athlete details from sheet so you can access strava")
  athlete_values = hive_work.get_athlete(i,"Strava2HiveNewUserSignUp")
  print("Log - Athlete Values: ", athlete_values)
  # Test if athlete bearer token is still valid by testing athlete_values[12]
  if athlete_values[12] == '':
    print("Log - Expire time is empty, so need to get auth from strava")
    new_user_access_token(athlete_values)
  else:
    print("Log - User is an existing user, so we need to check if we need to update the strava token")
    expire_time = int(athlete_values[12])
    current_time = time.time()
    expired_value = expire_time - int(current_time)
    if expired_value > 0:
      print("Log - Strava Token Still Valid")
    else:
      print("Log - Strava Token Needs To Be Updated")
      refresh_access_token(athlete_values)
      
  # Test if athlete hivesigner token is still valid by testing athlete_values[8]
  print("Log - User is an existing user, so we need to check if we need to update the hivesigner token")
  expire_time = int(athlete_values[8])
  current_time = time.time()
  expired_value = expire_time - int(current_time)
  if expired_value > 0:
    print("Log - Hivesigner Token Still Valid")
  else:
    print("Log - Hivesigner Token Needs To Be Updated")
    hive_work.refresh_hivesigner_token(athlete_values)

  print("Log - See what activity the athlete has")
  activity_details = strava_activity(i)
  print(activity_details)
  # Add a test to see if the activity was a run and then post if it is
  # we might need to also bring down all the activity for the day and not just the last

# Add details of the post to a new spreadsheet
# Hive - reblogging
# Refactor for more than one user
# Use the hive blocks explorer to help troubleshoot issues https://hiveblocks.com/@run.vince.run
