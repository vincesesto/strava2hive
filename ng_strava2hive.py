#!/usr/bin/env python

import os
import re
import pygsheets
import pandas as pd
import requests
import time
import glob
import hive_work
import boto3
import pipedream_modules
import post_functions
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from boto3.dynamodb.conditions import Key
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
  s = Service('/bin/chromedriver')
  #driver = webdriver.Chrome('/bin/chromedriver')
  driver = webdriver.Chrome(service=s)  
  driver.get(activity_url)
  sleep(3)
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
  # activity_info['duration'] = more_activity_data['elapsed_time']
  activity_info['duration'] = more_activity_data['moving_time']
  activity_info['type'] = more_activity_data['type']
  activity_info['start_date_local'] = more_activity_data['start_date_local']
  activity_info['location_country'] = more_activity_data['location_country']
  activity_info['description'] = more_activity_data['description']
  activity_info['calories'] = more_activity_data['calories']
  activity_info['photos'] = more_activity_data['photos']
  return activity_info 
    
def post_to_hive(athlete_id, activity_details, strava_access_token):
  print("Posting to Hive")
  nodelist = NodeList()
  nodelist.update_nodes()
  nodes = nodelist.get_hive_nodes()
  #wif_post_key = getpass.getpass('Posting Key: ')
  # Get all the details including the posting keys
  # athlete_details = hive_work.get_athlete(athlete_id, "Strava2HiveNewUserSignUp")
  dynamodb = hive_work.dynamo_access()
  table = dynamodb.Table(dynamoTable)
  athlete_details = table.query(
    KeyConditionExpression=Key('athleteId').eq(athlete_id)
  )
  print(athlete_details['Items'])
  wif = os.getenv('POSTING_KEY')
  #wif = athlete_details[6]
  hive = Hive(nodes=nodes, keys=[wif])
  ##### athlete_details['Items'][0]['hive_user']
  author = athlete_details['Items'][0]['hive_user']
  distance = str(round(activity_details['distance'] * .001, 2))
  activity_type = activity_details['type'].lower()
  duration = str(round(activity_details['duration'] / 60))
  print("Duration")
  print(detailed_activity)
  calories = activity_details['calories']
  if calories == 0:
    calories = hive_work.calc_calories(activity_type, duration, distance)
  print("Log - Downloading images and getting details together")
  strava_screenshot(activity_details['id'])

  # Testing to see if we can get multiple photos
  # For now using strava access token from user
  photo_data = hive_work.strava_photo_check(activity_details['id'], strava_access_token)

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
    command = '/usr/bin/wget "' + profile_img + '" -O prof_image_' + str(athlete_id) + '.png'
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
  
  **About the Athlete:** *{athlete_details['Items'][0]['about_me']}*
  
  ![{prof_image_name}]({prof_img_link['url']})
  
  ''' + post_functions.post_footer_and_image(photo_data, author, wif, activity_details['id'], athlete_id)
  parse_body = True
  self_vote = False
  #tags = ['exhaust', 'test', 'beta', 'runningproject', 'sportstalk']
  tags = hashtags
  beneficiaries = [{'account': 'strava2hive', 'weight': 500},]
  print("Log - Posting to Hive")
  #hive.post(title, body, author=author, tags=tags, community="hive-176853", parse_body=parse_body, self_vote=self_vote, beneficiaries=beneficiaries)
  # This is the new work with Hivesigner
  c = Client(access_token=athlete_details['Items'][0]['hive_signer_access_token'],)
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
      percent_hive_dollars = 5000,
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
  pipedream_modules.hive_post_api(author, activity_details['id'])
  
  
## Function to post more than one image
## Activity details looks like this notice "'total_photo_count': 3"
## {'resource_state': 2, 'athlete': {'id': 1778778, 'resource_state': 1}, 'name': 'Afternoon Swim - Between Two Runs', 'distance': 1500.0, 'moving_time': 1985, 'elapsed_time': 1985, 'total_elevation_gain': 0, 'type': 'Swim', 'sport_type': 'Swim', 'id': 8305092413, 'start_date': '2022-12-29T02:55:09Z', 'start_date_local': '2022-12-29T15:55:09Z', 'timezone': '(GMT+12:00) Pacific/Auckland', 'utc_offset': 46800.0, 'location_city': None, 'location_state': None, 'location_country': 'New Zealand', 'achievement_count': 0, 'kudos_count': 7, 'comment_count': 0, 'athlete_count': 1, 'photo_count': 0, 'map': {'id': 'a8305092413', 'summary_polyline': '', 'resource_state': 2}, 'trainer': True, 'commute': False, 'manual': False, 'private': False, 'visibility': 'everyone', 'flagged': False, 'gear_id': None, 'start_latlng': [], 'end_latlng': [], 'average_speed': 0.756, 'max_speed': 0.0, 'has_heartrate': True, 'average_heartrate': 169.4, 'max_heartrate': 194.0, 'heartrate_opt_out': False, 'display_hide_heartrate_option': True, 'upload_id': 8903746600, 'upload_id_str': '8903746600', 'external_id': '5013379158-1672282509-swim.tcx', 'from_accepted_tag': False, 'pr_count': 0, 'total_photo_count': 3, 'has_kudoed': False}
## hive_work.strava_activity_details needs to be extended to include extra images

##################################################
# NG Strava2Hive Processing
##############################################################33
# Move Processing to DynamoDB

dynamoTable = 'athletes'
sheetName = 'Strava2HiveNewUserSignUp'

dynamodb = hive_work.dynamo_access()
print("Scanning table")
response = dynamodb.Table(dynamoTable).scan()

#Start from scratch again
#1. get a list of all the athleteId's(we are doing this the easy way for now)
athlete_list = [101635754, 105596627, 105808129, 15403365, 107153228, 18345670, 30471548, 10864136, 
                63571991, 24013473, 105691374, 27627544, 27092562, 12057602, 26385836, 110525401, 100382865, 
                3811369, 107301925, 88497473, 119363780, 113681541, 23333253, 123893901,114524958, 127129915,
                126411877, 130326653, 2622268, 131361374, 107003849, 133962447, 8061069, 132763906, 135751007,
                48844017, 124098314]
#2. loop through all the athleteId's
for i in athlete_list:
  if i == 27092562 :
    continue
  print(f'Log - Working throuh the next set of activity for the user {i}')
  #	3. get the dynamo details for that athleteId
  dynamodb = hive_work.dynamo_access()
  table = dynamodb.Table(dynamoTable)
  athletedb_response = table.query(
    KeyConditionExpression=Key('athleteId').eq(i)
  )
  #	4. check the last_post_date is more that 12 hours old
  last_activity_date = athletedb_response['Items'][0]['last_post_date']
  post_val = hive_work.check_last_post_date(i, last_activity_date)
  if post_val:
    print(f'Log - The last activity for the user {i} was more than 12 hours ago')
  else:
    print(f'Log - The last activity for the user {i} was NOT more than 12 hours ago')
    continue
  #	5. check if strava token has expired, refresh if not
  strava_expire_date = athletedb_response['Items'][0]['strava_token_expires']
  expire_time = int(strava_expire_date)
  current_time = time.time()
  expired_value = expire_time - int(current_time)
  if expired_value > 0:
    print("Log - Strava Token Still Valid")
  else:
    print("Log - Strava Token Needs To Be Updated")
    new_strava_access_token, new_strava_expires = hive_work.refresh_dynamo_access_token(athletedb_response['Items'])  
    print("Updating strava token on dynamo")
    table = dynamodb.Table(dynamoTable)
    response = table.update_item(
      Key={ 'athleteId': int(i)},
      UpdateExpression='SET strava_access_token = :newStravaToken',
      ExpressionAttributeValues={':newStravaToken': new_strava_access_token },
      ReturnValues="UPDATED_NEW"
    )
    print("And the strava expire date")
    response = table.update_item(
      Key={ 'athleteId': int(i)},
      UpdateExpression='SET strava_token_expires = :newStravaExpire',
      ExpressionAttributeValues={':newStravaExpire': new_strava_expires },
      ReturnValues="UPDATED_NEW"
    )  
    print("Log - New strava expires: ", new_strava_expires)
    print("Log - We need to get the new details for the athlete now")
    dynamodb = hive_work.dynamo_access()
    table = dynamodb.Table(dynamoTable)
    athletedb_response = table.query(KeyConditionExpression=Key('athleteId').eq(i))
    print("Log - New strava expires in the db: ", athletedb_response['Items'][0]['strava_token_expires'])
    
  #	6. check if hivesigner token has expired, refresh if not
  hive_expire_date = athletedb_response['Items'][0]['hive_signer_expires']
  expire_time = int(hive_expire_date)
  current_time = time.time()
  expired_value = expire_time - int(current_time)
  if expired_value > 0:
    print("Log - Hivesigner Token Still Valid")
  else:
    print("Log - Hivesigner Token Needs To Be Updated")
    new_hive_signer_access_token, new_hive_signer_expires = hive_work.refresh_dynamo_hivesigner_token(athletedb_response['Items'])
    print("Updating hivesigner token on dynamo")
    table = dynamodb.Table(dynamoTable)
    response = table.update_item(
      Key={ 'athleteId': int(i)},
      UpdateExpression='SET hive_signer_access_token = :newHiveToken',
      ExpressionAttributeValues={':newHiveToken': new_hive_signer_access_token },
      ReturnValues="UPDATED_NEW"
    )
    print("And the token expire date")
    response = table.update_item(
      Key={ 'athleteId': int(i)},
      UpdateExpression='SET hive_signer_expires = :newHiveExpire',
      ExpressionAttributeValues={':newHiveExpire': new_hive_signer_expires },
      ReturnValues="UPDATED_NEW"
    )
    print("Log - New hivesigner expires: ", new_hive_signer_expires)
    print("Log - We need to get the new details for the athlete now")
    dynamodb = hive_work.dynamo_access()
    table = dynamodb.Table(dynamoTable)
    athletedb_response = table.query(KeyConditionExpression=Key('athleteId').eq(i))
    print("Log - New strava expires in the db: ", athletedb_response['Items'][0]['hive_signer_expires'])
    
    
  # ############################################# 
  #	7. now see if the user has had any activities
  
  print(f'Log - Searching For New Activities for user {i}')
  activity_data = hive_work.strava_activity_check(athletedb_response['Items'][0]['strava_access_token'])
  if type(activity_data) is dict:
    print("Log - It looks like there is an issue with strava authentication")
    break
  
  
  for j in range(len(activity_data)):
    activity = activity_data[j]
    print(activity)
    # a. Check if activity is a run or a ride...not a workout
    print(activity['type'])
    if activity['type'] == 'Workout':
      print("Log - Activity is not a run or ride, so we can stop running this")
      continue
    print("Log - Activity is a run or ride, now can we it has a description")
    detailed_activity = hive_work.strava_activity_details(activity['id'], athletedb_response['Items'][0]['strava_access_token'])
    print(detailed_activity)
    # Testing if the CSV file can be used instead of checking the api
    activity_csv = glob.glob("*.csv")
    with open(activity_csv[0], "r") as fp:
      s = fp.read()
    
    if detailed_activity['description'] == None:
      print("Log - Activity does not have a description, move on")
    elif detailed_activity['description'] == '':
      print("Log - Activity does not have a description, move on")
    elif str(activity['id']) in s:
      print("Log - Activity is in our CSV file as already posted, move on")
    else:
      posted_val = pipedream_modules.activity_posted_api(activity['id'])
      if posted_val:
        print("Log - Activity has been posted already, move on")
      elif posted_val is False:
        print("Log - There was an error connecting to pipedream")
      else:
        print("Log - Activity has not been posted yet, ship it!!") 
        new_dets = detailed_activity['description'].replace('\r','')
        detailed_activity['description'] = new_dets
        post_to_hive(i, detailed_activity, athletedb_response['Items'][0]['strava_access_token'])
        print("Log - Add it now to the activity log")
        activity_date = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
        word = detailed_activity['description'].split()
        wcount = len(word)
        record_distance = str(round(activity['distance'] * .001, 2))
        calories = detailed_activity['calories']
        duration = str(round(detailed_activity['duration'] / 60))
        if calories == 0:
          calories = hive_work.calc_calories(activity['type'], duration, record_distance)
        record_post(i, activity['id'], activity['type'], activity_date, record_distance, calories, wcount, athletedb_response['Items'][0]['hive_user'], duration)
        # Work around for most recent post to be stored in Strava2HiveNewUserSignUp sheet
        last_log = athletedb_response['Items'][0]['last_post_date']
        print("Log - finially we need to update dynamodb's last post data, which is currently:", last_log)
        response = table.update_item(
          Key={ 'athleteId': int(i)},
          UpdateExpression='SET last_post_date = :newLastPost',
          ExpressionAttributeValues={':newLastPost': activity_date },
          ReturnValues="UPDATED_NEW"
        )
        #hive_work.update_athlete(i, activity_date, "A", "Strava2HiveNewUserSignUp")
        print("Log - Activity posted so we only want one activity at a time for:", i)
        break
        
        
