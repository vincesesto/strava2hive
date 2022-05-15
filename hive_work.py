#!/usr/bin/env python

import os
import pygsheets
import pandas as pd
import requests
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from time import sleep
from datetime import datetime, timedelta
from beem.imageuploader import ImageUploader
from beem import Hive
from beem.nodelist import NodeList

def test_module():
  print("This is a test module")
  
def description_and_tags(description):
  hashtags = re.findall("#([a-zA-Z0-9_]{1,50})", description)
  clean_description = re.sub("#[A-Za-z0-9_]+","", description)
  if not hashtags:
    hashtags = ["hive", "strava2hive", "runningproject", "sportstalk", "health"]
  if not clean_description:
    clean_description = "Make sure you keep running and posting to Strava...Stay Strong Everyone!"
  return hashtags[-5:], clean_description

def list_athletes(sheet_name):
  gc = pygsheets.authorize(service_file='strava2hive.json')
  sh = gc.open(sheet_name)
  wks = sh[0]
  row = []
  athletes = []
  cells = wks.get_all_values(majdim='ROWS', include_tailing_empty=False, include_tailing_empty_rows=False)
  total_rows = len(cells)
  for i in range(total_rows):
    row = wks.get_row(i + 1)
    athletes.append(row[6])
  # Drop the first value cause its 'Athlete ID'
  athletes.pop(0)
  return athletes

def get_latest_activity_date(athlete_id, sheet_name):
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
    if row[6] == athlete_id:
      athlete_date = row[0]

  return athlete_date

def get_athlete(athlete_id, sheet_name):
  gc = pygsheets.authorize(service_file='strava2hive.json')
  sh = gc.open(sheet_name)
  wks = sh[0]
  row = []
  athletes = 15
  for i in range(athletes):
    row = wks.get_row(i + 1)
    if row[6] == athlete_id:
      break
  return row

def update_athlete(athlete_id, change_val, column, sheet_name):
  # Update athlete in the spreadsheet with the changed cell value and column you need to change
  gc = pygsheets.authorize(service_file='strava2hive.json')
  sh = gc.open(sheet_name)
  wks = sh[0]
  row = []
  athletes = 5
  for i in range(athletes):
    row = wks.get_row(i + 1)
    if row[6] == athlete_id:
      cell_value = column + str(i + 1)
      wks.update_value(cell_value, change_val)
      row = wks.get_row(i + 1)
      break
  return row
