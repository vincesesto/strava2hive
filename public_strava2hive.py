#!/usr/bin/env python

import os
import re
import pygsheets
import pandas as pd
import requests
import time
import glob
import hive_work
import pipedream_modules
import post_functions
from selenium import webdriver
from selenium.webdriver.common.by import By
from time import sleep
from datetime import datetime, timedelta
from beem.imageuploader import ImageUploader
from beem import Hive
from beem.account import Account
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

def record_post(athlete_id, activity_id, activity_type, activity_date, activity_distance, activity_calories, wcount, hive_name):
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
    print("Log - An Error occurred trying to authenticate with the {} Strava token".format(athlete[10]))
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
  wif = os.getenv('POSTING_KEY')
  #wif = athlete_details[6]
  hive = Hive(nodes=nodes, keys=[wif])
  author = athlete_details[1]
  distance = str(round(activity_details['distance'] * .001, 2))
  activity_type = activity_details['type'].lower()
  duration = str(round(activity_details['duration'] / 60))
  calories = activity_details['calories']
  if calories == 0:
    calories = hive_work.calc_calories(activity_type, duration)
  print("Log - Downloading images and getting details together")
  strava_screenshot(activity_details['id'])
  # Get athlete profile image
  if activity_details['photos']['primary'] == None:
    prof_image_path = '/home/circleci/project/S2HLogo.PNG'
    prof_image_name = 'S2HLogo.PNG'
    prof_image_uploader = ImageUploader(blockchain_instance=hive)
    prof_img_link = prof_image_uploader.upload(prof_image_path, "strava2hive", image_name=prof_image_name)
    # Now set up the main image
    image_path = '/home/circleci/project/image_' + str(activity_details['id']) + '.png'
    image_name = 'image_' + str(activity_details['id']) + '.png'
    image_uploader = ImageUploader(blockchain_instance=hive)
    img_link = image_uploader.upload(image_path, "strava2hive", image_name=image_name)
  else:
    profile_img = activity_details['photos']['primary']['urls']['600']
    command = 'wget ' + profile_img + ' -O prof_image_' + str(athlete_id) + '.png'
    os.system(command)
    image_path = '/home/circleci/project/prof_image_' + str(athlete_id) + '.png'
    image_name = 'prof_image_' + str(athlete_id) + '.png'
    image_uploader = ImageUploader(blockchain_instance=hive)
    #img_link = image_uploader.upload(image_path, author, image_name=image_name)
    img_link = image_uploader.upload(image_path, "strava2hive", image_name=image_name)
    # The screen shot is now at the bottom of the page
    prof_image_path = '/home/circleci/project/image_' + str(activity_details['id']) + '.png'
    prof_image_name = 'image_' + str(activity_details['id']) + '.png'
    prof_image_uploader = ImageUploader(blockchain_instance=hive)
    prof_img_link = prof_image_uploader.upload(prof_image_path, "strava2hive", image_name=prof_image_name)
  title = activity_details['name']
  hashtags, description, community =  hive_work.description_and_tags(activity_details['description'])
  body = f'''
  ![{image_name}]({img_link['url']})
  {author} just finished a {distance}km {activity_type}, that lasted for {duration} minutes.
  This {activity_type} helped {author} burn {calories} calories.
  ---
  
  **Description from Strava:**  {description}
  
  ---
  If you would like to check out this activity on strava you can see it here:
  https://www.strava.com/activities/{activity_details['id']}
  
  **About the Athlete:** *{athlete_details[2]}*
  
  ![{prof_image_name}]({prof_img_link['url']})
  
  ''' + post_functions.post_footer()
  parse_body = True
  self_vote = False
  #tags = ['exhaust', 'test', 'beta', 'runningproject', 'sportstalk']
  tags = hashtags
  beneficiaries = [{'account': 'strava2hive', 'weight': 500},]
  print("Log - Posting to Hive")
  #hive.post(title, body, author=author, tags=tags, community="hive-176853", parse_body=parse_body, self_vote=self_vote, beneficiaries=beneficiaries)
  # This is the new work with Hivesigner
  c = Client(access_token=athlete_details[6],)
  permlink = hive_work.create_permlink(activity_details['id'])
  comment = Comment(
    author,
    permlink,
    body,
    title=title,
    parent_permlink=community,
    json_metadata={"tags":tags},
  )
  comment_options = CommentOptions(
      author = author,
      permlink = permlink,
      allow_curation_rewards = True,
      allow_votes = True,
      extensions =  [[0,{"beneficiaries": [{"account": "strava2hive", "weight": 500}]}]])
  print("Log - Using Hivesigner to post")
  account_deets = Account(author, blockchain_instance=hive)
  auth = account_deets.get_blog(limit=5)
  
  broadcast_results = c.broadcast([comment.to_operation_structure(),comment_options.to_operation_structure()])
  #broadcast_results = c.broadcast([comment.to_operation_structure()])
  print(broadcast_results)
  if "error" in broadcast_results:
    print("Log - Something went wrong broadcasting with posting for:", author)
    exit()
  hive_work.new_posts_list("@" + author + "/" + permlink)
  
def strava_activity(athlete_deets):
  #athlete_details = hive_work.get_athlete(athlete_id, "Strava2HiveNewUserSignUp")
  athlete_details = athlete_deets
  # activity bearer is needed as part of the data
  print("Log - Searching For New Activities")
  bearer_header = "Bearer " + athlete_details[11]
  headers = {'Content-Type': 'application/json', 'Authorization': bearer_header}
  t = datetime.now() - timedelta(days=1)
  parameters = {"after": int(t.strftime("%s"))}
  #response = requests.get("https://www.strava.com/api/v3/athlete/activities?per_page=3", headers=headers, params=parameters )
  response = requests.get("https://www.strava.com/api/v3/athlete/activities?per_page=3", headers=headers)
  activity_data = response.json()
  if type(activity_data) is dict:
    print(activity_data)
    print("Log - It looks like there is an issue with strava authentication")
    return None
  for i in range(len(activity_data)):
    activity = activity_data[i]
    print(activity['type'])
    if activity['type'] == 'Workout':
      print("Log - Activity is not a run or ride, so we can stop running this")
      continue
    print("Log - Activity is a run or ride, now can we it has a description")
    print("Log - Now get some more detailed information")
    detailed_activity = strava_activity_details(activity['id'], bearer_header)
    print(detailed_activity)
    
    # Testing if the CSV file can be used instead of checking the api
    activity_csv = glob.glob("*.csv")
    print(activity_csv)    
    with open(activity_csv[0], "r") as fp:
      s = fp.read()
    
    if detailed_activity['description'] == None:
      print("Log - Activity does not have a description, move on")
      #break
    elif detailed_activity['description'] == '':
      print("Log - Activity does not have a description, move on")
      #break
    elif str(activity['id']) in s:
      print(datetime.now().strftime("%d-%b-%Y %H:%M:%S"), "Log - Activity is in our CSV file as already posted, move on")
    else:
      posted_val = pipedream_modules.activity_posted_api(activity['id'])
      if posted_val:
        print("Log - Activity has been posted already, move on")
      elif posted_val is False:
        print(datetime.now().strftime("%d-%b-%Y %H:%M:%S"), "Log - There was an error connecting to pipedream")
      else:
        print("Log - Activity has not been posted yet, ship it!!")   
        new_dets = detailed_activity['description'].replace('\r','')
        detailed_activity['description'] = new_dets
        print(detailed_activity['description'])
        post_to_hive(athlete_details[10], detailed_activity)
        print("Log - Add it now to the activity log")
        activity_date = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
        word = detailed_activity['description'].split()
        wcount = len(word)
        record_distance = str(round(activity['distance'] * .001, 2))
        calories = detailed_activity['calories']
        duration = str(round(detailed_activity['duration'] / 60))
        if calories == 0:
          calories = hive_work.calc_calories(activity['type'], duration)
        record_post(athlete_details[10], activity['id'], activity['type'], activity_date, record_distance, calories, wcount, athlete_details[1])
        # Work around for most recent post to be stored in Strava2HiveNewUserSignUp sheet
        hive_work.update_athlete(athlete_details[10], activity_date, "A", "Strava2HiveNewUserSignUp")
        print("Log - Activity posted so we only want one activity at a time for:", athlete_details[10])
        break

##################################################
# Workflow from scratch
##################################################

# Now we just have a list of Strava ID's but we will eventually make a list from our sheet
strava_athletes = hive_work.list_athletes(10, "Strava2HiveNewUserSignUp")
print(strava_athletes)
dt = "%d-%b-%Y %H:%M:%S"
# Get a list of activities in CSV format
hive_work.download_sheet_as_csv("StravaActivity", 1)

print("Log - Use athlete details to get activity from strava")
for i in strava_athletes:
  if i == '77830218' :
    continue
  print(f'Log - When did the user {i} post their last activity')
  athlete_values = hive_work.get_athlete(i,"Strava2HiveNewUserSignUp")
  #activity_date = hive_work.get_latest_activity_date(i, "Strava2HiveNewUserSignUp", 10)
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
  print("Log - First get athlete details from sheet so you can access strava")
  #athlete_values = hive_work.get_athlete(i,"Strava2HiveNewUserSignUp")
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
      athlete_values = hive_work.get_athlete(i,"Strava2HiveNewUserSignUp")
      
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
    athlete_values = hive_work.get_athlete(i,"Strava2HiveNewUserSignUp")

  print("Log - See what activity the athlete has")
  activity_details = strava_activity(athlete_values)
  print(activity_details)
  # Add a test to see if the activity was a run and then post if it is
  # we might need to also bring down all the activity for the day and not just the last

##############################################################33
# Move Processing to DynamoDB

dynamoTable = 'athletes'
sheetName = 'Strava2HiveNewUserSignUp'

dynamodb = hive_work.dynamo_access()
print("Scanning table")
response = dynamodb.Table(dynamoTable).scan()

for i in response['Items']:
    print(i)

athlete_values = hive_work.get_athlete("101635754", sheetName)   
print(athlete_values)

print("Testing and update post date")
dynamo_date = response['Items'][0]['last_post_date']
sheet_date = athlete_values[0]
if dynamo_date == sheet_date:
  print("It looks like the date is the same, so do not update")
else:
  print("Updating date on dynamo")
  table = dynamodb.Table(dynamoTable)
  response = table.update_item(
    Key={ 'athleteId': int(athlete_values[10])},
    UpdateExpression='SET last_post_date = :newDate',
    ExpressionAttributeValues={':newDate': sheet_date },
    ReturnValues="UPDATED_NEW"
  )
  
print("Testing HiveSigner Tokens are correct")
dynamo_hive_token = response['Items'][0]['hive_signer_access_token']
sheet_hive_token = athlete_values[6]
if dynamo_hive_token == sheet_hive_token:
  print("It looks like the hivesigner token is the same, so do not update")
else:
  print("Updating hivesigner token on dynamo")
  table = dynamodb.Table(dynamoTable)
  response = table.update_item(
    Key={ 'athleteId': int(athlete_values[10])},
    UpdateExpression='SET hive_signer_access_token = :newHiveToken',
    ExpressionAttributeValues={':newHiveToken': sheet_hive_token },
    ReturnValues="UPDATED_NEW"
  )
  print("And the token expire date")
  response = table.update_item(
    Key={ 'athleteId': int(athlete_values[10])},
    UpdateExpression='SET hive_signer_expires = :newHiveExpire',
    ExpressionAttributeValues={':newHiveExpire': athlete_values[8] },
    ReturnValues="UPDATED_NEW"
  )

print("Testing if Strava Tokens are correct")
dynamo_strava_token = response['Items'][0]['strava_access_token']
sheet_strava_token = athlete_values[11]
if dynamo_strava_token == sheet_strava_token:
  print("It looks like the strava token is the same, so do not update")
else:
  print("Updating strava token on dynamo")
  table = dynamodb.Table(dynamoTable)
  response = table.update_item(
    Key={ 'athleteId': int(athlete_values[10])},
    UpdateExpression='SET strava_access_token = :newStravaToken',
    ExpressionAttributeValues={':newStravaToken': sheet_strava_token },
    ReturnValues="UPDATED_NEW"
  )
  print("And the strava expire date")
  response = table.update_item(
    Key={ 'athleteId': int(athlete_values[10])},
    UpdateExpression='SET strava_token_expires = :newStravaExpire',
    ExpressionAttributeValues={':newHiveExpire': athlete_values[12] },
    ReturnValues="UPDATED_NEW"
  )  

#Start from scratch
#1. get a list of all the athleteId's
#2. loop through all the athleteId's
#	3. get the dynamo details for that athleteId
#	4. change the last_post_date is more that 12 hours old
#	5. check if strava token has expired, refresh if not
#	6. check if hivesigner token has expired, refresh if not
#	7. now see if the user has had any activities
#

