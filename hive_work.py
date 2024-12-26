#!/usr/bin/env python

import os
import pygsheets
import pandas as pd
import requests
import time
import re
import random
import string
import boto3
from boto3.dynamodb.conditions import Key
from selenium import webdriver
from selenium.webdriver.common.by import By
from time import sleep
from datetime import datetime, timedelta
from beem.imageuploader import ImageUploader
from beem import Hive
from beem.nodelist import NodeList

def test_module():
  print("This is a test module")
  
def dynamo_access():
  # Access the dynamo db to then do other stuff using it
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
  
def description_and_tags(description):
  community = re.findall("@([a-zA-Z0-9_]{1,50})", description)
  hashtags = re.findall("#([a-zA-Z0-9_]{1,50})", description)
  #new_description = re.sub("@[A-Za-z0-9_]+","", description)
  clean_description = re.sub("#[A-Za-z0-9_]+","", description)
  if "hikenz" in community:
    community = "hive-155184"
  elif "running" in community:
    community = "hive-107275"
  elif "cycling" in community:
    community = "hive-177745"
  else:
    community = "hive-176853"
  if not hashtags:
    hashtags = ["strava2hive", "runningproject", "sportstalk", "health", "fitness"]
  if not clean_description:
    clean_description = "Make sure you keep running and posting to Strava...Stay Strong Everyone!"
  print("Log - Community to post to: ", community)
  return hashtags[-5:], clean_description, community

def list_athletes(column, sheet_name):
  gc = pygsheets.authorize(service_file='strava2hive.json')
  sh = gc.open(sheet_name)
  wks = sh[0]
  row = []
  athletes = []
  cells = wks.get_all_values(majdim='ROWS', include_tailing_empty=False, include_tailing_empty_rows=False)
  print("Vince testing function")
  total_rows = len(cells)
  for i in range(total_rows):
    row = wks.get_row(i + 1)
    athletes.append(row[int(column)])
  # Drop the first value cause its 'Athlete ID'
  athletes.pop(0)
  return athletes

def get_latest_activity_date(athlete_id, sheet_name, column):
  # Get the last time this athlete has posted
  gc = pygsheets.authorize(service_file='strava2hive.json')
  sh = gc.open(sheet_name)
  wks = sh[0]
  row = []
  athlete_date = ""
  cells = wks.get_all_values(majdim='ROWS', include_tailing_empty=False, include_tailing_empty_rows=False)
  total_rows = len(cells)
  for i in range(total_rows):
    row = wks.get_row(i + 1)
    if row[int(column)] == athlete_id:
      athlete_date = row[0]

  return athlete_date

def get_athlete(athlete_id, sheet_name):
  gc = pygsheets.authorize(service_file='strava2hive.json')
  sh = gc.open(sheet_name)
  wks = sh[0]
  row = []
  athletes = 15
  cells = wks.get_all_values(majdim='ROWS', include_tailing_empty=False, include_tailing_empty_rows=False)
  total_rows = len(cells)
  for i in range(total_rows):
    row = wks.get_row(i + 1)
    if sheet_name == "HiveAthletes":
      if row[6] == athlete_id:
        break
    else:
      if row[10] == athlete_id:
        break
  return row

def update_athlete(athlete_id, change_val, column, sheet_name):
  # Update athlete in the spreadsheet with the changed cell value and column you need to change
  gc = pygsheets.authorize(service_file='strava2hive.json')
  sh = gc.open(sheet_name)
  wks = sh[0]
  row = []
  cells = wks.get_all_values(majdim='ROWS', include_tailing_empty=False, include_tailing_empty_rows=False)
  total_rows = len(cells)
  for i in range(total_rows):
    row = wks.get_row(i + 1)
    if sheet_name == "HiveAthletes":
      if row[6] == athlete_id:
        cell_value = column + str(i + 1)
        wks.update_value(cell_value, change_val)
        row = wks.get_row(i + 1)
        break
    else:
      if row[10] == athlete_id:
        cell_value = column + str(i + 1)
        wks.update_value(cell_value, change_val)
        row = wks.get_row(i + 1)
        break
  return row

def refresh_hivesigner_token(athlete):
  # We need to update the hivesigner token every six days
  hive_signer_info = dict()
  try:
    response = requests.post("https://hivesigner.com/api/oauth2/token?", 
                          params={'code': athlete[7], 'client_secret': os.getenv('HIVE_SIGN_SECRET')})
    hive_response_data = response.json()
    hive_signer_info['hive_signer_access_token'] = hive_response_data['access_token']
    hive_signer_info['hive_signer_expires'] = int(time.time()) + 604800
    update_athlete(athlete[10], hive_signer_info['hive_signer_access_token'], 'G', "Strava2HiveNewUserSignUp")
    update_athlete(athlete[10], hive_signer_info['hive_signer_expires'], 'I', "Strava2HiveNewUserSignUp")
  except:
    print("Log - An Error occurred trying to authenticate with the {} hive token".format(athlete[5]))
    return False
  
def create_permlink(activity_id):
  # Function to combine title with random number to create a permlink
  random_link = ''.join(random.choices(string.digits, k=10))
  permlink = str(activity_id) + "-" + random_link
  return permlink

def new_posts_list(permlink):
  # Create a list of permlinks posted in a text file
  f = open("post_list.txt","a")
  f.write(permlink + "\n")
  f.close()
  
def download_sheet_as_csv(sheet_name, sheet_number):
  # Function to donwload activity file as csv
  gc = pygsheets.authorize(service_file='strava2hive.json')
  sh = gc.open(sheet_name)
  wks = sh[sheet_number]
  print(wks)
  wks.export(pygsheets.ExportType.CSV)
  wks.export(filename="testingcsv")
  
def calc_calories(activity, duration, distance):
  test_vals = "Calculating Calories for " + activity + " " + str(duration) + " " + str(distance)
  print(test_vals)
  hours = float(duration)/60.0
  speed = float(distance)/hours
  print("Speed for this activity is " + str(speed))
  METS = 0.0
  weight = 70.0
  if activity == "Swim":
    METS = 6.3
  elif activity == "Run":
    METS = 8.5   
  elif activity == "Ride":
    METS = 4.5
  else:
    METS = 4
  per_minute = (METS * weight * 3.5) / 200
  calories = float(per_minute) * float(duration)
  return str(round(calories, 1))
  
def check_last_post_date(athleteId, last_post_date):
  # Check if the last post date is older than 12 hours old
  print(f'Log - The last activity for the user {athleteId} was on the date {last_post_date}')
  date = datetime.strptime(last_post_date, "%m/%d/%Y %H:%M:%S")
  act_timestamp = datetime.timestamp(date)
  current_time = time.time()
  NUMBER_OF_SECONDS = 43200 # seconds in 12 hours
  if (current_time - act_timestamp) > NUMBER_OF_SECONDS:
    return True
  else:
    return False

def strava_activity_check(strava_access_token):
  bearer_header = "Bearer " + str(strava_access_token)
  headers = {'Content-Type': 'application/json', 'Authorization': bearer_header}
  response = requests.get("https://www.strava.com/api/v3/athlete/activities?per_page=2", headers=headers)
  activity_data = response.json()
  return activity_data

def strava_photo_check(activity_id, strava_access_token):
  print("TESTING - Seeing if we can get more than one image")
  bearer_header = "Bearer " + str(strava_access_token)
  headers = {'Content-Type': 'application/json', 'Authorization': bearer_header}
  strava_activity_url = "https://www.strava.com/api/v3/activities/" + str(activity_id) + "/photos?size=5000"
  response = requests.get(strava_activity_url, headers=headers)
  photo_data = response.json()
  print(len(photo_data))
  p_count = 0
  for i in photo_data:
    p_count = p_count + 1
    print(i['urls'])
    if p_count == 3:
      break
  return photo_data[0]
  
def strava_activity_details(activity_id, strava_access_token):
  bearer_header = "Bearer " + str(strava_access_token)
  strava_activity_url = "https://www.strava.com/api/v3/activities/" + str(activity_id)
  headers = {'Content-Type': 'application/json', 'Authorization': bearer_header}
  response = requests.get(strava_activity_url, headers=headers, )
  more_activity_data = response.json()
  print(more_activity_data)
  activity_info = dict()
  activity_info['id'] = activity_id
  activity_info['name'] = more_activity_data['name']
  activity_info['distance'] = more_activity_data['distance']
  activity_info['old_duration'] = more_activity_data['elapsed_time']
  activity_info['duration'] = more_activity_data['moving_time']
  activity_info['type'] = more_activity_data['type']
  activity_info['start_date_local'] = more_activity_data['start_date_local']
  activity_info['location_country'] = more_activity_data['location_country']
  activity_info['description'] = more_activity_data['description']
  activity_info['calories'] = more_activity_data['calories']
  activity_info['photos'] = more_activity_data['photos']
  return activity_info 

def refresh_dynamo_access_token(athlete):
  # We need to update the access_token in strava every six hours
  # This one is specific for the dynamo DB's
  athlete_vals = athlete[0]
  print(type(athlete_vals))
  code_val = athlete_vals['strava_one_time']
  print(type(code_val))
  print(code_val)
  try:
    response = requests.post("https://www.strava.com/api/v3/oauth/token",
                             params={'client_id': os.getenv('STRAVA_CLIENT_ID'), 'client_secret': os.getenv('STRAVA_SECRET'), 
                             'code': code_val, 'grant_type': 'refresh_token', 'refresh_token': athlete_vals['strava_refresh_token'] })
    access_info = dict()
    activity_data = response.json()
    access_info['access_token'] = activity_data['access_token']
    access_info['expires_at'] = activity_data['expires_at']
    access_info['refresh_token'] = activity_data['refresh_token']
    return access_info['access_token'], access_info['expires_at']
  except:
    print("Log - An Error occurred trying to authenticate with the {} Strava token".format(athlete[10]))
    return False 
  
def refresh_dynamo_hivesigner_token(athlete):
  # We need to update the hivesigner token every six days
  # This is for the dynamoDB as well
  athlete_vals = athlete[0]
  code_val = athlete_vals['hive_signer_refresh_token']
  hive_signer_info = dict()
  try:
    response = requests.post("https://hivesigner.com/api/oauth2/token?", 
                          params={'code': code_val, 'client_secret': os.getenv('HIVE_SIGN_SECRET')})
    hive_response_data = response.json()
    hive_signer_info['hive_signer_access_token'] = hive_response_data['access_token']
    hive_signer_info['hive_signer_expires'] = int(time.time()) + 604800
    return hive_signer_info['hive_signer_access_token'], hive_signer_info['hive_signer_expires']
  except:
    print("Log - An Error occurred trying to authenticate with the {} hive token".format(athlete[5]))
    return False
