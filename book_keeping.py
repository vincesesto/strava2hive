#!/usr/bin/env python

import os
import pygsheets
import pandas as pd
import requests
import time
import re
import random
import string
import hive_work
import os.path
from time import sleep
from datetime import datetime, timedelta
from beem.imageuploader import ImageUploader
from beem import Hive
from beem.nodelist import NodeList
from beem.account import Account
from beem.comment import Comment

# Script to run after posting to count up records and post to accounts


# Function to get the last post from the user
def get_hive_posts(hive_user_name):
  nodelist = NodeList()
  nodelist.update_nodes()
  nodes = nodelist.get_hive_nodes()
  hive = Hive(node=nodelist.get_hive_nodes())
  account = Account(hive_user_name, blockchain_instance=hive)
  authorperm = account.get_blog(limit=1)
  return authorperm

# Function to donwload activity file as csv
def download_sheet_as_csv(sheet_name, sheet_number):
  gc = pygsheets.authorize(service_file='strava2hive.json')
  sh = gc.open(sheet_name)
  wks = sh[sheet_number]
  wks.export(pygsheets.ExportType.CSV)

# Function to get all users from both dev and prod sheets
def list_all_athletes():
  dev_athletes = hive_work.list_athletes(6, "HiveAthletes")
  prod_athletes = hive_work.list_athletes(10, "Strava2HiveNewUserSignUp")
  all_athletes = dev_athletes + prod_athletes
  return all_athletes

# Function to create the body of our comment
def comment_body():
  comment_body = f'''
  Thanks so much for using @strava2hive
  You're smashing your training at the
  moment and getting stronger every day.
  https://images.hive.blog/DQmNYafhCjpkKVmFD4os7BzV1F6hs4zDusvTtNiDDyGBz31/S2HLogo.PNG
  '''
  return comment_body
  
# Maybe set up a function to count from Hive



##################################################
# Workflow from scratch
##################################################

print("Book Keeping")
print("Log - Count/Record/Comment/Upvote")
print("Download the activity sheet to work directly with")
download_sheet_as_csv("StravaActivity", 1)
print(os.system("ls -l"))

print("Log - get all athletes and start working through them")
dev_athletes = hive_work.list_athletes(6, "HiveAthletes")
prod_athletes = hive_work.list_athletes(10, "Strava2HiveNewUserSignUp")

for i in dev_athletes:
  # get the hive username
  athlete_details = hive_work.get_athlete(i, "HiveAthletes")
  latest_post = get_hive_posts(athlete_details[1])
  print("Log - Latest post for user: ", i)
  print(latest_post)

# Test if posts have been made
file_exists = os.path.exists('post_list.txt')
if file_exists:
  f = open("post_list.txt", "r")
  for i in f.readlines():
    # We want to comment on a new post from strava2hive
    print(i)
    nodelist = NodeList()
    nodelist.update_nodes()
    nodes = nodelist.get_hive_nodes()    
    wif = os.getenv('POSTING_KEY')
    hive = Hive(nodes=nodes, keys=[wif])
    author = "strava2hive"
    authorperm = "@run.vince.run/7394608845-0066764884"
    body = comment_body()
    c = Comment(authorperm, hive_instance=hive)
    c.reply(body, author=author)
