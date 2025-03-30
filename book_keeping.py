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
import boto3
import pipedream_modules
from boto3.dynamodb.conditions import Key, Attr
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
from hivesigner.operations import Vote

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
  Keep going, you're smashing your training at the moment and getting stronger every day.
  To see the full Weekly Leader Board, [click here.](https://cypress-anorak-da8.notion.site/Leader-Board-Updated-Mon-Feb-6-23-45-03-UTC-2023-bf9e87e4106e446fb627abff356ce675)
  https://images.hive.blog/DQmNYafhCjpkKVmFD4os7BzV1F6hs4zDusvTtNiDDyGBz31/S2HLogo.PNG
  '''
  return comment_body

# Function to create a leaderboard to add to the body comment
def create_leader_board(high):
  leader_comment = f'''
  This Weeks Leader Board(Top 5):
  1. @{high[0][0]} - {high[0][1]} Calories Burned
  2. @{high[1][0]} - {high[1][1]} Calories Burned
  3. @{high[2][0]} - {high[2][1]} Calories Burned
  4. @{high[3][0]} - {high[3][1]} Calories Burned
  5. @{high[4][0]} - {high[4][1]} Calories Burned
  '''
  return leader_comment
  
# Function to reblog a post
def reblog_strava2hive(permlink, hive_token):
  c = Client(access_token=hive_token, )
  #reblog = Reblog("strava2hive", "strava2hive", permlink)
  author_from_pl = permlink.split("/")[0]
  reblog = Reblog("strava2hive", author_from_pl.split("@")[1] , permlink.split("/")[1])
  print("Repost from strava2hive")
  print(c.broadcast([reblog.to_operation_structure()]))
  sleep(3)
  
# Function to work out weekly top 10
def create_top_10(top_10):
  total_hbd = 5
  tot_cal = 0
  for i in range(len(top_10)):
    tot_cal = tot_cal + top_10[i][1]
  print(tot_cal)
  top_10 = f'''
  This Weeks Leader Board of {tot_cal} total calories burned:
  1. @{top_10[0][0]} - {top_10[0][1]} Calories Burned - {round((top_10[0][1]/tot_cal)*total_hbd,3)} HBD
  2. @{top_10[1][0]} - {top_10[1][1]} Calories Burned - {round((top_10[1][1]/tot_cal)*total_hbd,3)} HBD
  3. @{top_10[2][0]} - {top_10[2][1]} Calories Burned - {round((top_10[2][1]/tot_cal)*total_hbd,3)} HBD 
  4. @{top_10[3][0]} - {top_10[3][1]} Calories Burned - {round((top_10[3][1]/tot_cal)*total_hbd,3)} HBD
  5. @{top_10[4][0]} - {top_10[4][1]} Calories Burned - {round((top_10[4][1]/tot_cal)*total_hbd,3)} HBD
  6. @{top_10[5][0]} - {top_10[5][1]} Calories Burned - {round((top_10[5][1]/tot_cal)*total_hbd,3)} HBD
  7. @{top_10[6][0]} - {top_10[6][1]} Calories Burned - {round((top_10[6][1]/tot_cal)*total_hbd,3)} HBD
  8. @{top_10[7][0]} - {top_10[7][1]} Calories Burned - {round((top_10[7][1]/tot_cal)*total_hbd,3)} HBD
  9. @{top_10[8][0]} - {top_10[8][1]} Calories Burned - {round((top_10[8][1]/tot_cal)*total_hbd,3)} HBD 
  10. @{top_10[9][0]} - {top_10[9][1]} Calories Burned - {round((top_10[9][1]/tot_cal)*total_hbd,3)} HBD
  11. @{top_10[10][0]} - {top_10[10][1]} Calories Burned - {round((top_10[10][1]/tot_cal)*total_hbd,3)} HBD
  12. @{top_10[11][0]} - {top_10[11][1]} Calories Burned - {round((top_10[11][1]/tot_cal)*total_hbd,3)} HBD
  13. @{top_10[12][0]} - {top_10[12][1]} Calories Burned - {round((top_10[12][1]/tot_cal)*total_hbd,3)} HBD
  14. @{top_10[13][0]} - {top_10[13][1]} Calories Burned - {round((top_10[13][1]/tot_cal)*total_hbd,3)} HBD
  15. @{top_10[14][0]} - {top_10[14][1]} Calories Burned - {round((top_10[14][1]/tot_cal)*total_hbd,3)} HBD
  16. @{top_10[15][0]} - {top_10[15][1]} Calories Burned - {round((top_10[15][1]/tot_cal)*total_hbd,3)} HBD
  17. @{top_10[16][0]} - {top_10[16][1]} Calories Burned - {round((top_10[16][1]/tot_cal)*total_hbd,3)} HBD
  18. @{top_10[17][0]} - {top_10[17][1]} Calories Burned - {round((top_10[17][1]/tot_cal)*total_hbd,3)} HBD
  19. @{top_10[18][0]} - {top_10[18][1]} Calories Burned - {round((top_10[18][1]/tot_cal)*total_hbd,3)} HBD
  20. @{top_10[19][0]} - {top_10[19][1]} Calories Burned - {round((top_10[19][1]/tot_cal)*total_hbd,3)} HBD
  21. @{top_10[20][0]} - {top_10[20][1]} Calories Burned - {round((top_10[20][1]/tot_cal)*total_hbd,3)} HBD
  22. @{top_10[21][0]} - {top_10[21][1]} Calories Burned - {round((top_10[21][1]/tot_cal)*total_hbd,3)} HBD
  23. @{top_10[22][0]} - {top_10[22][1]} Calories Burned - {round((top_10[22][1]/tot_cal)*total_hbd,3)} HBD
  24. @{top_10[23][0]} - {top_10[23][1]} Calories Burned - {round((top_10[23][1]/tot_cal)*total_hbd,3)} HBD
  25. @{top_10[24][0]} - {top_10[24][1]} Calories Burned - {round((top_10[24][1]/tot_cal)*total_hbd,3)} HBD
  26. @{top_10[25][0]} - {top_10[25][1]} Calories Burned - {round((top_10[25][1]/tot_cal)*total_hbd,3)} HBD
  27. @{top_10[26][0]} - {top_10[26][1]} Calories Burned - {round((top_10[26][1]/tot_cal)*total_hbd,3)} HBD
  28. @{top_10[27][0]} - {top_10[27][1]} Calories Burned - {round((top_10[27][1]/tot_cal)*total_hbd,3)} HBD
  29. @{top_10[28][0]} - {top_10[28][1]} Calories Burned - {round((top_10[28][1]/tot_cal)*total_hbd,3)} HBD
  30. @{top_10[29][0]} - {top_10[29][1]} Calories Burned - {round((top_10[29][1]/tot_cal)*total_hbd,3)} HBD
  '''
  return top_10

# Function to upvote new posts
def post_upvote(post_permlink):
  # This is going to be a bit more involved
  # Details here: https://hivesigner-python-client.readthedocs.io/en/latest/gettingstarted.html
  # This is what post_permlink will look like "@run.vince.run/8300095141-2696039387"
  list_of_upvoters = [101635754, 1778778, 105596627]
  # 1 - loop through all the users
  for j in list_of_upvoters:
    # 2 - For each user get the hivesigner token from dynamodb
    dynamoTable = 'athletes'
    dynamodb = hive_work.dynamo_access()
    table = dynamodb.Table(dynamoTable)
    athletedb_response = table.query(
      KeyConditionExpression=Key('athleteId').eq(j)
    )
    hive_signer_token = athletedb_response['Items'][0]['hive_signer_access_token']
    # If strava2hive, reblog the post
    if j == 101635754:
      #reblog_strava2hive(post_permlink, hive_signer_token)
      print("Taking reblog out for now")
    # 3 - Create the client with the hivesigner token
    v = Client(access_token=hive_signer_token,)
    # 4 - Create the upvote details
    # - Need to get the voter name from dynamodb
    voter = athletedb_response['Items'][0]['hive_user']
    # - Need to split the permlink to get the auther name
    print(post_permlink)
    full_name = post_permlink.split("/")[0]
    name = full_name.split("@")[1]
    print(name)
    author=""
    #vote = Vote(voter, str(name), post_permlink.split("/")[1], 30)
    vote = Vote(str(name), voter, post_permlink, 30)
    # 5 - Broadcast the vote
    print(v.broadcast([vote.to_operation_structure()]))
    print("Log - upvote for user: ", voter)
    print("Log - upvote for permlink: ", post_permlink)
  

##################################################
# Workflow from scratch
##################################################

print("Book Keeping")
print("Log - Count/Record/Comment/Upvote")
print("Download the activity sheet to work directly with")
hive_work.download_sheet_as_csv("StravaActivity", 1)

print("Log - get all athletes to work through")
#dev_athletes = hive_work.list_athletes(6, "HiveAthletes")
dev_athletes = ['run.kirsty.run', 'run.vince.run']
prod_athletes = hive_work.list_athletes(1, "Strava2HiveNewUserSignUp")
ng_athletes = [ 'nicklewis', 'masoom', 'budapestguide', 'bostonadventures', 'thishuman', 'mervinthepogi', 'dennnmarc', 'valerianis', 'crysis', 'ataliba', 
               'rmsadkri', 'neuerko', 'fortune1m', 'ingi1976', 'anna-newkey', 'sabajfa', 'matthewbox', 
               'kam5iz', 'sodom-lv', 'pinkhub', 'maccazftw', 'amico.sports', 'sandralopes', 'chris-uk',
               'itravelrox22', 'crackyup', 'buzzgoblin', 'taushifahamed', 'alfazmalek02', 'akb01',
               'kingtanu', 'itz.inno', 'disgustoid88', 'nabbas0786', 'giorgakis', 'gunting', 'bobinson',
               'hasaanazam', 'captainman', 'kiwibloke', 'chris-uk', 'tom45p', 'vardatarmaion88', 
               'alessandrawhite', 'borniet', 'jaytone', 'tipy', 'mirzaiqi', 'fizz0', 'Ismaelcastillo']
all_athletes = dev_athletes + prod_athletes + ng_athletes

leader_board = {}
new_leader_board = {}
activity_calories = {}
total_activity_count = 0

new_week_row = 1607

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
      if row_count >= new_week_row:
        if(row[7] == i ):
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

k = Counter(activity_calories)
top10 = k.most_common(30)
high = k.most_common(5)
print(top10)
print(high)
leaders = create_leader_board(high)
print(leaders)

#print(create_top_10(top10))
reblog_count = 0
print("Personal Best 135 blog posts")

print("Update the leader board page")
pipedream_modules.board_update()


# Test if posts have been made
file_exists = os.path.exists('post_list.txt')
#file_exists = False
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
    # Now we want to get upvotes for the new post
    print("Log - Now Upvote On Post: ", i)
    #post_upvote(i)
    if reblog_count == 0:
      #reblog_strava2hive(i)
      reblog_count = reblog_count + 1
    sleep(10)
    
    print("Log - Test if values are in spreadsheet")
    url_val = i.split("/")
    activity_test = url_val[1].split("-")
    print(activity_test)
      
    
