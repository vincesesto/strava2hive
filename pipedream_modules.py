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
