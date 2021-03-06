#!/usr/bin/env python

import os
import glob
import pygsheets
import pandas as pd
import requests
import time
import re
import random
import string
import hive_work
import csv
import os.path
from time import sleep
from collections import Counter
from datetime import datetime, timedelta
from beem.imageuploader import ImageUploader
from beem import Hive
from beem.nodelist import NodeList
from beem.account import Account
from beem.comment import Comment
from hivesigner.client import Client
from hivesigner.operations import Reblog

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

# Function to get all users from both dev and prod sheets
def list_all_athletes():
  dev_athletes = hive_work.list_athletes(6, "HiveAthletes")
  prod_athletes = hive_work.list_athletes(10, "Strava2HiveNewUserSignUp")
  all_athletes = dev_athletes + prod_athletes
  return all_athletes

# Function to create the body of our comment
def comment_body():
  comment_body = f'''
  You're smashing your training at the moment and getting stronger every day.
  Did you know you can now post your activity to the Running community New Zealand community.
  Simply start your activity description with the \@running or \@hikenz tag at the start of your post.
  Of course, you can still leave it blank to have your posts delivered to the Exhaust community by default.
  https://images.hive.blog/DQmNYafhCjpkKVmFD4os7BzV1F6hs4zDusvTtNiDDyGBz31/S2HLogo.PNG
  '''
  return comment_body

# Function to create a leaderboard to add to the body comment
def create_leader_board(high):
  if high[0][0] == '8764738':
    top1 = ['8764738', 'run.kirsty.run']
  elif high[0][0] == '1778778':
    top1 = ['1778778', 'run.vince.run']
  else:
    top1 = hive_work.get_athlete(high[0][0], "Strava2HiveNewUserSignUp")
  if high[1][0] == '8764738':
    top2 = ['8764738', 'run.kirsty.run']
  elif high[1][0] == '1778778':
    top2 = ['1778778', 'run.vince.run']
  else:
    top2 = hive_work.get_athlete(high[1][0], "Strava2HiveNewUserSignUp")
  if high[2][0] == '8764738':
    top3 = ['8764738', 'run.kirsty.run']
  elif high[2][0] == '1778778':
    top3 = ['1778778', 'run.vince.run']
  else:
    top3 = hive_work.get_athlete(high[2][0], "Strava2HiveNewUserSignUp")
  leader_comment = f'''
  This Weeks Leader Board(Top 3):
  1. @{top1[1]} - {high[0][1]} Posted Activity(s)
  2. @{top2[1]} - {high[1][1]} Posted Activity(s)
  3. @{top3[1]} - {high[2][1]} Posted Activity(s)
  '''
  return leader_comment
  
# Function to reblog a post
def reblog_strava2hive(permlink):
  athlete_values = hive_work.get_athlete('101635754', "Strava2HiveNewUserSignUp")
  c = Client(access_token=athlete_values[6], )
  reblog = Reblog("strava2hive", "strava2hive", permlink)
  print(c.broadcast([reblog.to_operation_structure()]))


##################################################
# Workflow from scratch
##################################################

print("Book Keeping")
print("Log - Count/Record/Comment/Upvote")
print("Download the activity sheet to work directly with")
hive_work.download_sheet_as_csv("StravaActivity", 1)

print("Log - get all athletes to work through")
#dev_athletes = hive_work.list_athletes(6, "HiveAthletes")
dev_athletes = ['8764738', '1778778']
prod_athletes = hive_work.list_athletes(10, "Strava2HiveNewUserSignUp")
all_athletes = dev_athletes + prod_athletes

leader_board = {}
new_leader_board = {}
activity_calories = {}
total_activity_count = 0

new_week_row = 172

print("Log - Tally up top athletes")
for i in all_athletes:
  # get the hive username
  #athlete_details = hive_work.get_athlete(i, "HiveAthletes")
  #latest_post = get_hive_posts(athlete_details[1])
  #print("Log - Latest post for user: ", i)
  
  activity_csv = glob.glob("*.csv")
  #print(activity_csv)
  activity_total = 0
  new_activity_total = 0.0
  activity_calories_total = 0.0
  with open(activity_csv[0], "r") as fp:
    reader = csv.reader(fp)
    row_count = 0
    for row in reader:
      row_count += 1
      if row_count > new_week_row:
        if(row[0] == i ):
          total_activity_count = total_activity_count + 1
          activity_total = activity_total + 1
          new_activity_total = new_activity_total + float(row[5]) + float(row[6])
          activity_calories_total = activity_calories_total + float(row[5])
          # print(row)
  leader_board[i] = activity_total
  new_leader_board[i] = new_activity_total
  activity_calories[i] = activity_calories_total
  #print("Athlete: " + str(i) + " Activities: " + str(activity_total))

print(new_leader_board)
print(activity_calories)
print(total_activity_count)

k = Counter(leader_board)
top10 = k.most_common(15)
high = k.most_common(3)
print(top10)
print(high)
leaders = create_leader_board(high)
print(leaders)

reblog_count = 0

# Test if posts have been made
file_exists = os.path.exists('post_list.txt')
if file_exists:
  f = open("post_list.txt", "r")
  for i in f.readlines():
    # We want to comment on a new post from strava2hive
    print("Log - S2H Comment On Post: ", i)
    nodelist = NodeList()
    nodelist.update_nodes()
    nodes = nodelist.get_hive_nodes()    
    wif = os.getenv('POSTING_KEY')
    hive = Hive(nodes=nodes, keys=[wif])
    author = "strava2hive"
    authorperm = i
    body = comment_body() + leaders
    c = Comment(authorperm, hive_instance=hive)
    c.reply(body, author=author)
    if reblog_count == 0:
      reblog_strava2hive(i)
      reblog_count = reblog_count + 1
    sleep(10)
    
    #print("Log - Test if values are in spreadsheet")
    #url_val = i.split("/")
    #activity_test = url_val[1].split("-")
    #print(activity_test)
    

