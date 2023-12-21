#!/usr/bin/env python

# This is what we are basically doing to get our data
# curl https://eojaaqdfrkizbyb.m.pipedream.net/1778778

import requests
import json

athlete_id = "1778778"
url = "https://eojaaqdfrkizbyb.m.pipedream.net/" + athlete_id

response_API = requests.get(url)
print(response_API.status_code)

data = response_API.text
parse_json = json.loads(data)
weeks = int(parse_json['$return_value'][2][0])
newline = "\n"
activities = []
for i in range(7,(7+weeks)):
  activities.append(parse_json['$return_value'][i])

weekly_summary = '''
<h2>Weekly Training Summary</h2>
Enter details from user here
'''


body = f'''
<h2>Weekly Strava2Hive Training Report</h2>
<table>
  <tr>
    <th></th>
    <th>Total Activities</th>
    <th>Total Kilometres</th>
    <th>Total Calories</th>
  </tr>
  <tr>
    <td></td>
    <td style="text-align:center">{parse_json['$return_value'][2][0]}</td>
    <td style="text-align:center">{parse_json['$return_value'][3][0]}</td>
    <td style="text-align:center">{parse_json['$return_value'][4][0]}</td>
  </tr>
</table>

{weekly_summary}

<h2>Strava2Hive Activities For The Week</h2>

{newline.join(f"{vals[1]}: {vals[2]} {vals[3]}km {vals[4]}mins [Link]({vals[5]})   " for vals in activities)}

'''
print(body)
