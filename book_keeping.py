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
from selenium import webdriver
from selenium.webdriver.common.by import By
from time import sleep
from datetime import datetime, timedelta
from beem.imageuploader import ImageUploader
from beem import Hive
from beem.nodelist import NodeList

# Script to run after posting to count up records and post to accounts


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
athletes = list_all_thletes()
for i in athletes:
  print(i)



