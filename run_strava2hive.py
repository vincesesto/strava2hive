#!/usr/bin/env python

import os
import re
import pygsheets
import pandas as pd
import requests
import time
import glob
import boto3
import hive_work
import pipedream_modules
import post_functions
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from time import sleep
from datetime import datetime, timedelta
from boto3.dynamodb.conditions import Key
from beem.imageuploader import ImageUploader
from beem import Hive
from beem.account import Account
from beem.nodelist import NodeList

# Functions

def dynamo_access():
  client = boto3.client('dynamodb', region_name='ap-southeast-2',
    aws_access_key_id=os.getenv('DB_ACCESS_KEY'),
    aws_secret_access_key=os.getenv('DB_SECRET_KEY'),
  )
  dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2',
    aws_access_key_id=os.getenv('DB_ACCESS_KEY'),
    aws_secret_access_key=os.getenv('DB_SECRET_KEY'),
  )
  ddb_exceptions = client.exceptions
  return dynamodb

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

def record_post(athlete_id, activity_id, activity_type, activity_date, activity_distance, activity_calories, wcount, hive_name, duration):
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
  # Now add the activity distance
  cell_value = "E" + str(len(cells) + 1)
  wks.update_value(cell_value, activity_distance)
  # Now add the activity calories
  cell_value = "F" + str(len(cells) + 1)
  wks.update_value(cell_value, activity_calories)
  # Now add the activity word count
  cell_value = "G" + str(len(cells) + 1)
  wks.update_value(cell_value, wcount)
  # Now add the activity hive user name
  cell_value = "H" + str(len(cells) + 1)
  wks.update_value(cell_value, hive_name)
  # Now add the activity duration
  cell_value = "I" + str(len(cells) + 1)
  wks.update_value(cell_value, duration)
    
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
    hive_work.update_athlete(athlete[6], access_info['access_token'], "H", "HiveAthletes")
    hive_work.update_athlete(athlete[6], access_info['expires_at'], "I", "HiveAthletes")
    print(hive_work.update_athlete(athlete[6], access_info['refresh_token'], "J", "HiveAthletes"))
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
    hive_work.update_athlete(athlete[6], access_info['access_token'], "H", "HiveAthletes")
    hive_work.update_athlete(athlete[6], access_info['expires_at'], "I", "HiveAthletes")
    print(hive_work.update_athlete(athlete[6], access_info['refresh_token'], "J", "HiveAthletes"))
  except:
    print("Log - An Error occurred trying to authenticate with the Strava token")
    return False
  
def strava_activity_details(activity_id, bearer_header):
  strava_activity_url = "https://www.strava.com/api/v3/activities/" + str(activity_id)
  headers = {'Content-Type': 'application/json', 'Authorization': bearer_header}
  response = requests.get(strava_activity_url, headers=headers, )
  more_activity_data = response.json()
  activity_info = dict()
  try:
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
    #activity_info['device_name'] = more_activity_data['device_name']
  except:
    print("Log - An Error occurred trying to get date from Strava")
    activity_info['description'] = None
  return activity_info
    
def post_to_hive(athlete_id, activity_details):
  nodelist = NodeList()
  nodelist.update_nodes()
  nodes = nodelist.get_hive_nodes()
  #wif_post_key = getpass.getpass('Posting Key: ')
  # Get all the details including the posting keys
  athlete_details = hive_work.get_athlete(athlete_id, "HiveAthletes")
  #wif = os.getenv('POSTING_KEY')
  wif = athlete_details[3]
  hive = Hive(nodes=nodes, keys=[wif])
  author = athlete_details[1]
  distance = str(round(activity_details['distance'] * .001, 2))
  activity_type = activity_details['type'].lower()
  duration = str(round(activity_details['duration'] / 60))
  calories = activity_details['calories']
  if calories == 0:
    calories = hive_work.calc_calories(activity_type, duration, distance)
  print("Log - Downloading images and getting details together")
  post_functions.strava_screenshot(activity_details['id'])
  # Testing to see if we can get multiple photos
  # For now using strava access token from user
  photo_data = hive_work.strava_photo_check(activity_details['id'], athlete_details[7])

  # Get athlete profile image
  if activity_details['photos']['primary'] == None:
    image_name, img_link, prof_image_name, prof_img_link = post_functions.zero_image_post(author, athlete_details[3], activity_details['id'])
    title_img = "https://images.hive.blog/DQme7eUjgkDvupcM7MvbarXtbkmA9bUufXwCdwJuGo7dVp1/ActivityStravaHive.png"
    title_img_alt = "Title_image.png"
  else:
    print("Not downloading screenshots from strava for now, but instead we will link it")
    title_img = activity_details['photos']['primary']['urls']['600']
    title_img_alt = "Title_image.png"
    #profile_img = activity_details['photos']['primary']['urls']['600']
    #command = '/usr/bin/wget "' + profile_img + '" -O prof_image_' + str(athlete_id) + '.png'
    #os.system(command)
    #image_path = '/home/circleci/project/prof_image_' + str(athlete_id) + '.png'
    #image_name = 'prof_image_' + str(athlete_id) + '.png'
    #image_uploader = ImageUploader(blockchain_instance=hive)
    #img_link = image_uploader.upload(image_path, author, image_name=image_name)
    ## The screen shot is now at the bottom of the page
    #prof_image_path = '/home/circleci/project/image_' + str(activity_details['id']) + '.png'
    #prof_image_name = 'image_' + str(activity_details['id']) + '.png'
    #prof_image_uploader = ImageUploader(blockchain_instance=hive)
    #prof_img_link = prof_image_uploader.upload(prof_image_path, author, image_name=prof_image_name)
  title = activity_details['name']
  hashtags, description, community =  hive_work.description_and_tags(activity_details['description'])

  #   <center><img src={title_img} alt={title_img_alt} srl_elementid="1"></center> 
  body = post_functions.post_header(title_img, distance, activity_type, duration, calories, activity_date) + f'''

  #![{image_name}]({img_link['url']})  
  #![{prof_image_name}]({prof_img_link['url']})

  <h3>We are currently experiencing some issues posting images on @strava2hive...Please bear with us</h3>

  @{author} just finished a {distance}km {activity_type}, that lasted for {duration} minutes.
  This {activity_type} helped {author} burn {calories} calories.
  ---
  
  **Description from Strava:** {description}
  
  ---
  If you would like to check out this activity on strava you can see it here:
  https://www.strava.com/activities/{activity_details['id']}
  
  **About the Athlete:** *{athlete_details[2]}*
  
  ''' + post_functions.post_footer()
  # REMOVED 28Nov2025 + post_functions.post_footer_and_image(photo_data, author, wif, activity_details['id'], athlete_id)
  parse_body = True
  self_vote = False
  #tags = ['exhaust', 'test', 'beta', 'runningproject', 'sportstalk']
  tags = hashtags
  beneficiaries = [{'account': 'strava2hive', 'weight': 600},]
  permlink = hive_work.create_permlink(activity_details['id'])
  print("Log - Posting to Hive")
  #account_deets = Account(author, blockchain_instance=hive)
  #auth = account_deets.get_blog(limit=5)
  if activity_type == "ride":
    community = "hive-177745"
  
  hive.post(title, body, author=author, tags=tags, community=community, parse_body=parse_body, self_vote=self_vote, beneficiaries=beneficiaries, permlink=permlink)
  hive_work.new_posts_list("@" + author + "/" + permlink)
  pipedream_modules.hive_post_api(author, distance)

def strava_activity(athlete_deets):
  #athlete_details = hive_work.get_athlete(athlete_id, "HiveAthletes")
  athlete_details = athlete_deets
  print("new change to strava_activity function: ", athlete_details)
  # activity bearer is needed as part of the data
  print(datetime.now().strftime("%d-%b-%Y %H:%M:%S"), "Log - Searching For New Activities")
  bearer_header = "Bearer " + athlete_details[7]
  headers = {'Content-Type': 'application/json', 'Authorization': bearer_header}
  t = datetime.now() - timedelta(days=7)
  parameters = {"after": int(t.strftime("%s"))}
  #url = "https://www.strava.com/api/v3/athlete/activities?after=" + t.strftime("%s") + "&per_page=3" 
  #print(url)
  response = requests.get("https://www.strava.com/api/v3/athlete/activities?per_page=3", headers=headers)
  #response = requests.get(url, headers=headers)
  activity_data = response.json()
  for i in range(len(activity_data)):
    activity = activity_data[i]
    print(activity)
    print(activity['type'])
    if activity['type'] == 'Workout':
      print(datetime.now().strftime("%d-%b-%Y %H:%M:%S"), "Log - Activity is not a run or ride, so we can stop running this")
      continue
    print(datetime.now().strftime("%d-%b-%Y %H:%M:%S"), "Log - Activity is a run or ride, now we can see if it has a discription")

    ### Put this in early to do less strava calls
    # Testing if the CSV file can be used instead of checking the api
    print("TESTING - Check if it is in the spreadsheet first")
    activity_csv = glob.glob("*.csv")
    print(activity_csv)    
    with open(activity_csv[0], "r") as fp:
      s = fp.read()
    if str(activity['id']) in s:
      print(datetime.now().strftime("%d-%b-%Y %H:%M:%S"), "Log - Activity is in our CSV file as already posted, move on")
      continue

    print(datetime.now().strftime("%d-%b-%Y %H:%M:%S"), "Log - Now get some more detailed information")
    detailed_activity = strava_activity_details(activity['id'], bearer_header)
    #print(detailed_activity)

    # Set up a test to see if the activity is older than 1 month
    # Details should be in detailed_activity as 'start_date_local': '2024-03-20T17:03:44Z'
    print(detailed_activity['start_date_local'])
    
    # Testing if the CSV file can be used instead of checking the api
    activity_csv = glob.glob("*.csv")
    print(activity_csv)    
    with open(activity_csv[0], "r") as fp:
      s = fp.read()
    if detailed_activity['description'] == None:
      print(datetime.now().strftime("%d-%b-%Y %H:%M:%S"), "Log - Activity does not have a description, move on")
      #break
    elif detailed_activity['description'] == '':
      print(datetime.now().strftime("%d-%b-%Y %H:%M:%S"), "Log - Activity does not have a description, move on")
      #break
    elif str(activity['id']) in s:
      print(datetime.now().strftime("%d-%b-%Y %H:%M:%S"), "Log - Activity is in our CSV file as already posted, move on")
    else:
      print(datetime.now().strftime("%d-%b-%Y %H:%M:%S"), "Log - Activity has a description, now can we see if it is already posted")
      posted_val = pipedream_modules.activity_posted_api(activity['id'])
      if posted_val > 0:
        print(datetime.now().strftime("%d-%b-%Y %H:%M:%S"), "Log - Activity has been posted already, move on")
      elif posted_val is False:
        print(datetime.now().strftime("%d-%b-%Y %H:%M:%S"), "Log - There was an error connecting to pipedream")  
      else:
        print(datetime.now().strftime("%d-%b-%Y %H:%M:%S"), "Log - Activity has not been posted yet, ship it!!")
        post_to_hive(athlete_details[6], detailed_activity)
        print(datetime.now().strftime("%d-%b-%Y %H:%M:%S"), "Log - Add it now to the activity log")
        activity_date = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
        word = detailed_activity['description'].split()
        wcount = len(word)
        record_distance = str(round(activity['distance'] * .001, 2))
        duration = str(round(detailed_activity['duration'] / 60))
        record_post(athlete_details[6], activity['id'], activity['type'], activity_date, record_distance, detailed_activity['calories'], wcount, athlete_details[1], duration)
        # Work around for most recent post to be stored in HiveAthletes sheet
        hive_work.update_athlete(athlete_details[6], activity_date, "A", "HiveAthletes")
        print(datetime.now().strftime("%d-%b-%Y %H:%M:%S"), "Log - Activity posted so we only want one activity at a time for:", athlete_details[6])
        break

##################################################
# Workflow from scratch
##################################################

# Now we just have a list of Strava ID's but we will eventually make a list from our sheet
strava_athletes = hive_work.list_athletes(6, "HiveAthletes")
print(strava_athletes)
dt = "%d-%b-%Y %H:%M:%S"
# Get a list of activities in CSV format
hive_work.download_sheet_as_csv("StravaActivity", 1)

print(datetime.now().strftime(dt), "Log - Use athlete details to get activity from strava")
for i in strava_athletes:
  print(datetime.now().strftime(dt), "Log - When did the user post their last activity")
  athlete_values = hive_work.get_athlete(i, "HiveAthletes")
  #activity_date = hive_work.get_latest_activity_date(i,"HiveAthletes", 6)
  activity_date = athlete_values[0]
  print(f'Log - The last activity for the user {i} was on the date {activity_date}')
  date = datetime.strptime(activity_date, "%m/%d/%Y %H:%M:%S")
  act_timestamp = datetime.timestamp(date)
  current_time = time.time()
  NUMBER_OF_SECONDS = 43200 # seconds in 12 hours
  if (current_time - act_timestamp) > NUMBER_OF_SECONDS:
    print(f'Log - The last activity for the user {i} was more than 12 hours ago')
  else:
    print(f'Log - The last activity for the user {i} was NOT more than 12 hours ago')
    continue
  print(datetime.now().strftime(dt), "Log - First get athlete details from sheet so you can access strava")
  #athlete_values = hive_work.get_athlete(i, "HiveAthletes")
  print(datetime.now().strftime(dt), "Log - Athlete Values: ", athlete_values)
  # Test if athlete bearer token is still valid by testing athlete_values[8]
  if athlete_values[8] == '':
    print(datetime.now().strftime(dt), "Log - Expire time is empty, so need to get auth from strava")
    new_user_access_token(athlete_values)
  else:
    print(datetime.now().strftime(dt), "Log - User is an existing user, so we need to check if we need to update the strava token")
    expire_time = int(athlete_values[8])
    current_time = time.time()
    expired_value = expire_time - int(current_time)
    if expired_value > 0:
      print(datetime.now().strftime(dt), "Log - Strava Token Still Valid")
    else:
      print(datetime.now().strftime(dt), "Log - Strava Token Needs To Be Updated")
      refresh_access_token(athlete_values)
      athlete_values = hive_work.get_athlete(i, "HiveAthletes")

  print(datetime.now().strftime(dt), "Log - See what activity the athlete has")
  #activity_details = strava_activity(i)
  activity_details = strava_activity(athlete_values)
  print(activity_details)
