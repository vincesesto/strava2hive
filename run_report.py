#!/usr/bin/env python

import requests
import json
import random
import string
import os
#from beem.imageuploader import ImageUploader
#from beem import Hive
#from beem.account import Account
#from beem.nodelist import NodeList


# Whats going on here

# 1. Check to see if there  are values in the spreadsheet. The first row will be the values used for the report - DONE

# 2. Get the values from the first rows - DONE(But need to set up another spreadsheet)

# 3. Check to see if the user is a valid user...maybe have a map with athlete id and hive user - DONE

# 4. Get the hive access details to post the report for the user

# 5. Run the report and create the html - DONE

# 6. Generate the report and post to hive

# 7. Remove the values from the original report so it does not generate the weekly report again


def check_for_weekly_reports():
  # 1. Check if there are values in the sheet
  weekly_report_url = "https://eonjvmkqs6po2lt.m.pipedream.net"
  
  response_API = requests.get(weekly_report_url)
  #print(response_API.status_code)

  weekly_report_data = response_API.text
  parse_json = json.loads(weekly_report_data)

  if len(parse_json) == 0:
    print("The dictionary is empty")
    parse_json = {"$return_value":[["empty","empty"]]}
  else:
    print("The dictionary is not empty")

  return parse_json['$return_value']

def check_for_valid_user(list_of_users, report_user):
  # 3. Check to see if user is valid and return hive user name
  if report_user in list_of_users.values():
    print("%s is valid" % report_user)
  else:
    print("%s is not valid - Kill script" % report_user)
    # Add in extra details to kill the report
  
  return list(list_of_users.keys())[list(list_of_users.values()).index(report_user)]

def upload_image(url, athlete):
  # Add ability to add images to hive post
  post_img = url
  command = '/usr/bin/wget "' + post_img + '" -O post_image_' + str(athlete) + '.png'
  os.system(command)
  image_path = str(os.getcwd()) +  '/post_image_' + str(athlete) + '.png'
  image_name = 'post_image_' + str(athlete) + '.png'
  image_uploader = ImageUploader(blockchain_instance=hive)
  img_link = image_uploader.upload(image_path, "strava2hive", image_name=image_name)
  return image_name, img_link

def previous_weeks_data(athlete):
  # Download the data from the previous week for comparison
  athlete_id = athlete
  url = "https://eou6w2gk79gwb4s.m.pipedream.net/" + athlete_id
  response_API = requests.get(url)
  print(response_API.status_code)
  data = response_API.text
  parse_json = json.loads(data)
  return parse_json
  #return int(parse_json['$return_value'][2][0])

def this_weeks_data(athlete):
  # 5. Run the report and create the html
  athlete_id = athlete
  url = "https://eojaaqdfrkizbyb.m.pipedream.net/" + athlete_id
  response_API = requests.get(url)
  print(response_API.status_code)
  data = response_API.text
  parse_json = json.loads(data)
  return parse_json

def weekly_report_generator(this_weeks_data, previous_weeks_data, athlete):
  # 5. Run the report and create the html
  athlete_id = athlete
  weeks = int(this_weeks_data['$return_value'][2][0])
  newline = "\n"
  activities = []
  top = [0, '0.0', '0.0', '0.0', '0.0', '0.0']
  for i in range(7,(7+weeks)):
    #print(top)
    activities.append(this_weeks_data['$return_value'][i])
    if float(top[4]) < float(this_weeks_data['$return_value'][i][4]):
      top = this_weeks_data['$return_value'][i]
    else:
      print(top)
  print("Top value is ", top)

  weekly_summary = '''
  <h2>Weekly Training Summary</h2>
  Enter details from user here
  '''
  body = f'''
  <h2>Weekly Strava2Hive Training Report</h2>
  <table>
    <tr>
      <th></th>
      <th></th>
      <th>Total Activities</th>
      <th>Total Kilometres</th>
      <th>Total Calories</th>
    </tr>
    <tr>
      <td></td>
      <td style="text-align:center">This Week</td>
      <td style="text-align:center">{this_weeks_data['$return_value'][2][0]}</td>
      <td style="text-align:center">{this_weeks_data['$return_value'][3][0]}</td>
      <td style="text-align:center">{this_weeks_data['$return_value'][4][0]}</td>
    </tr>
    <tr>
      <td></td>
      <td style="text-align:center">Last Week</td>
      <td style="text-align:center">{previous_weeks_data['$return_value'][2][0]}</td>
      <td style="text-align:center">{previous_weeks_data['$return_value'][3][0]}</td>
      <td style="text-align:center">{previous_weeks_data['$return_value'][4][0]}</td>
    </tr>
  </table>

  {this_weeks_data['$return_value'][5][1]}

  <h2>Strava2Hive Activities For The Week</h2>

  {newline.join(f"{vals[3]}: {vals[2]} - {vals[4]}km, with {vals[5]} calories burnt:[Link](https://www.strava.com/activities/{vals[1]})" for vals in activities)}

  <h2>Top Training Session For The Week</h2>
  Your top training session for the week was on {top[3]}.
  On that day, you did a {top[2]} for {top[4]}km, buring {top[5]} calories on that one training session.

  The Strava link to this training session is [here](https://www.strava.com/activities/{top[1]})

  We need to get a screen shot of this training session...

  '''
  return body

def post_to_hive(post_athlete, post_title, post_body):
  nodelist = NodeList()
  nodelist.update_nodes()
  nodes = nodelist.get_hive_nodes()
  wif = os.getenv('POSTING_KEY')
  hive = Hive(nodes=nodes, keys=[wif])
  author = "strava2hive"
  title = post_title
  community = "hive-107275"
  body = post_body
  parse_body = True
  self_vote = False
  tags = ['exhaust', 'test', 'beta', 'runningproject', 'sportstalk']
  beneficiaries = [{'account': 'run.vince.run', 'weight': 1000},]
  random_link = ''.join(random.choices(string.digits, k=10))
  permlink = "testingweeklyreport-" + "-" + random_link
  hive.post(title, body, author=author, tags=tags, community=community, parse_body=parse_body, self_vote=self_vote, beneficiaries=beneficiaries, permlink=permlink)

def create_post_title(user):
  title = "Weekly Report For Strava2Hive User " + user
  return title

# Main function of the program
user = check_for_weekly_reports()[0][0]

valid_users = {
  "run.vince.run": "1778778",
  "run.kirsy.run": "8764738"
}

hive_user =  check_for_valid_user(valid_users, user)
weeks_data = this_weeks_data(user)
previous_data = previous_weeks_data(user)
html_body = weekly_report_generator(weeks_data, previous_data, user)
post_title = create_post_title(hive_user)
#image_name, img_link = upload_image(url, user)
# All we need to do is add ![{image_name}]({img_link['url']}) to the body of the post

print(previous_data)
print(html_body)
print(post_title)
print(hive_user)


#post_to_hive(hive_user, post_title, html_body)
