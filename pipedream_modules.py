#!/usr/bin/env python

import requests
import json

def activity_posted_api(activity_id):
  url = 'https://eoe0c053dx0czcp.m.pipedream.net'
  activity_query = {'activity_id': activity_id}
  header_vals = {'Content-Type': 'application/json' }
  # Use the pipedream api to test if activity has been posted
  try:
    response = requests.post(url, data=json.dumps(activity_query), headers=header_vals)
    return_data = response.json()
  except:
    print("Log - An Error occurred trying to authenticate with pipedream")
    return_data = False

  return return_data

def hive_post_api(hive_user, distance):
  # Add details to the user store in pipedream after posting to hive
  url = 'https://eovp49jyklnn22n.m.pipedream.net'
  hive_post_details = {"user": hive_user, "distance": distance }
  print(hive_post_details)
  header_vals = {'Content-Type': 'application/json' }
  try:
    response = requests.post(url, data=json.dumps(hive_post_details), headers=header_vals)
    return_data = response.json()
  except:
    print("Log - An Error occurred trying to authenticate with pipedream")
    return_data = False

  return return_data    
