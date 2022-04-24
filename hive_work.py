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
