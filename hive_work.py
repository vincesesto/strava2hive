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
  
def calc_calories(activity, duration):
  METS = 0.0
  weight = 75.0
  if activity == "Swim":
    METS = 8.3
  elif activity == "Run":
    METS = 11.5   
  elif activity == "Ride":
    METS = 7.5
  else:
    METS = 6
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
  response = requests.get("https://www.strava.com/api/v3/athlete/activities?per_page=3", headers=headers)
  activity_data = response.json()
  return activity_data
