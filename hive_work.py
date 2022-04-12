#!/usr/bin/env python

import os
import pygsheets
import pandas as pd
import requests
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from time import sleep
from datetime import datetime, timedelta
from beem.imageuploader import ImageUploader
from beem import Hive
from beem.nodelist import NodeList

def test_module():
  print("This is a test module")
  
def post_to_hive(athlete_id, activity_details):
  nodelist = NodeList()
  nodelist.update_nodes()
  nodes = nodelist.get_hive_nodes()
  #wif_post_key = getpass.getpass('Posting Key: ')
  # Get all the details including the posting keys
  athlete_details = get_athlete(athlete_id)
  #wif = os.getenv('POSTING_KEY')
  wif = athlete_details[3]
  hive = Hive(nodes=nodes, keys=[wif])
  author = athlete_details[1]
  distance = str(round(activity_details['distance'] * .001, 2))
  activity_type = activity_details['type'].lower()
  duration = str(round(activity_details['duration'] / 60, 2))
  print("Log - Downloading images and getting details together")
  strava_screenshot(activity_details['id'])
  image_path = '/home/circleci/project/image_' + str(activity_details['id']) + '.png'
  #os.system('wget https://drive.google.com/open?id=16y8dMM0DupVASUj8VOq-72ZcLyFodz6q -O activity_image.png')
  #image_path = '/home/circleci/project/activity_image.png'
  image_name = 'image_' + str(activity_details['id']) + '.png'
  image_uploader = ImageUploader(blockchain_instance=hive)
  img_link = image_uploader.upload(image_path, author, image_name=image_name)
  title = activity_details['name']
  body = f'''
  ![{image_name}]({img_link['url']})
  {author} just finished a {distance}km {activity_type}, that lasted for {duration} minutes.
  This {activity_type} helped {author} burn {activity_details['calories']} calories.
  
  Discription from Strava: {activity_details['description']}
  
  If you would like to check out this activity on strava you can see it here:
  https://www.strava.com/activities/{activity_details['id']}
  
  About the Athlete: {athlete_details[2]}
  
  This is an automated post by @strava2hive and is currently in BETA.
  '''
  parse_body = True
  self_vote = False
  tags = ['exhaust', 'test', 'beta', 'runningproject', 'sportstalk']
  beneficiaries = [{'account': 'strava2hive', 'weight': 500},]
  print("Log - Posting to Hive")
  hive.post(title, body, author=author, tags=tags, community="hive-176853", parse_body=parse_body, self_vote=self_vote, beneficiaries=beneficiaries)
