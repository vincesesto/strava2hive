#!/usr/bin/env python

# This function has been set up to break out the body of the post

import os
import re
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from beem.imageuploader import ImageUploader
from beem import Hive
from beem.account import Account
from beem.nodelist import NodeList

# Functions
def strava_screenshot(activity):
  # Create the command to run on chrome
  activity_url = "https://www.strava.com/activities/" + str(activity)
  image_name = "image_" + str(activity) + ".png"
  s = Service('/bin/chromedriver')
  driver = webdriver.Chrome(service=s)  
  driver.get(activity_url)
  time.sleep(6)
  if driver.find_element(By.ID, "CybotCookiebotDialogBodyLevelButtonAccept"):
    driver.find_element(By.ID, "CybotCookiebotDialogBodyLevelButtonAccept").click()
    time.sleep(3)
  if "/activities/" in driver.current_url:
    if driver.find_element(By.CSS_SELECTOR, '[data-cy="sign-up-modal-close-button"]'):
      print("Element exists!")
      driver.find_element(By.CSS_SELECTOR, '[data-cy="sign-up-modal-close-button"]').click()
      time.sleep(1)
  #if driver.find_elements("xpath", "/html/body/div[1]/div/div[4]/div[1]/div/div[2]/button[4]"):
    #print("Element exists!")
    #driver.find_element("xpath", "/html/body/div[1]/div/div[4]/div[1]/div/div[2]/button[4]").click()
  driver.get_screenshot_as_file(image_name)
  driver.quit()
  os.system("ls -l")
  
def top_image(image_name, image_link):
  # Create the top image for the post
  top_image = f'''
  ![{image_name}]({image_link})
  '''
  return top_image

def activity_summary(author, distance, activity_type, duration, calories):
  # Create the top summary for the post
  act_summary = f'''
  {author} just finished a {distance}km {activity_type}, that lasted for {duration} minutes.
  This {activity_type} helped {author} burn {calories} calories.
  '''
  return act_summary


def monthly_totals(athlete_id, total_runs, total_kms, total_calories, activity_type):
  # Create a table for the monthly totals for the user
  monthly_totals_table = f'''  
  
  | <h1>Four Weeks Totals</h1> | <h1></h1> |
  |---|---|
  | Strava User | {athlete_id} |
  | Total {activity_type}s | {total_runs} |
  | Total Kms | {total_kms} |
  | Total Calories | {total_calories} kcal |

  '''
  return monthly_totals_table
  

def post_header(header_image, distance, activity_type, duration, calories, activity_date):
  # Create header with
  ## Header image
  ## Activity icon, type, date
  ## Activity distance, duration, calories
  # Get icon type
  activity_icon = ""
  print(activity_type)
  if activity_type == "swim":
    activity_icon = "🏊"
  elif activity_type == "ride":
    activity_icon = "🚴"
  elif activity_type == "run":
    activity_icon = "🏃"
  elif activity_type == "walk":
    activity_icon = "🚶"
  else:
    activity_icon = "🏋"
  
  act_header = f''' 
  <center><img src={header_image} alt="Title_image.png" srl_elementid="1"></center>
 
  | <h1>{activity_icon}</h1> | <h1></h1> | <h1>{calories} kcal</h1> |
  |:--------|:-----:|------:|

  '''
  return act_header
  
def post_header_image(author, user_wif, distance, activity_type, duration, calories, activity_date, activity_id, header_image="no_image"):
  # Create header with
  ## Header image
  # Get icon type
  activity_icon = ""
  print(activity_type)
  if activity_type == "swim":
    activity_icon = "🏊"
  elif activity_type == "ride":
    activity_icon = "🚴"
  elif activity_type == "run":
    activity_icon = "🏃"
  elif activity_type == "walk":
    activity_icon = "🚶"
  else:
    activity_icon = "🏋"

  wif = os.getenv('POSTING_KEY')

  # Create the screehshot image name
  print("Testing: ", wif)
  #image_name, img_link, prof_image_name, prof_img_link = zero_image_post(author, wif, activity_id)

  header = ''

  # Unable to post images to Hive at the moment
  header_image = "no_image"
  
  #![{image_name}]({img_link['url']})  - Add back to line 131
  if header_image == "no_image":
    post_header_screenshot = f''' 


  <center><img src="https://images.hive.blog/DQmNYafhCjpkKVmFD4os7BzV1F6hs4zDusvTtNiDDyGBz31/S2HLogo.PNG" alt="S2HLogo.PNG" srl_elementid="1"></center>
  
  There are issues posting images to Hive at the moment...please bare with us.
 
  | <h1>{activity_icon}</h1> | <h1></h1> | <h1>{calories} kcal</h1> |
  |:--------|:-----:|------:|

  @{author} just finished a {distance}km {activity_type}, that lasted for {duration} minutes.
  This {activity_type} helped {author} burn {calories} calories.  

  '''
    header = post_header_screenshot
  else:
    post_header_image_screenshot = f''' 
  <center><img src={header_image} alt="Title_image.png" srl_elementid="1"></center>
 
  | <h1>{activity_icon}</h1> | <h1></h1> | <h1>{calories} kcal</h1> |
  |:--------|:-----:|------:|

  ![{image_name}]({img_link['url']})   

  @{author} just finished a {distance}km {activity_type}, that lasted for {duration} minutes.
  This {activity_type} helped {author} burn {calories} calories.  

  '''
    header = post_header_image_screenshot
  return header


def post_footer():
  # Create a footer for our posts
  footer = f'''
  
  <center><img src="https://images.hive.blog/DQmNYafhCjpkKVmFD4os7BzV1F6hs4zDusvTtNiDDyGBz31/S2HLogo.PNG" alt="S2HLogo.PNG" srl_elementid="1"></center>
  
  This is an automated post by @strava2hive and is currently in BETA.
  
  If you would like to know more about the @strava2hive service, you can checkout our [Frequently Asked Questions.](https://hive.blog/hive-176853/@strava2hive/strava2hive-frequently-asked-questions)
  
  '''
  return footer

def post_footer_and_image(photo_data, author, user_wif, activity_id, athlete_id):
  # Create a footer for our posts
  # Add in second image to post, if it is available

  # This can sometimes fail due to an issue with strava uploads
  # to fix this change line 69 to   if len(photo_data) >= 20:

  footer = ''
  
  if len(photo_data) >= 20:
    # Download the image from strava
    footer_img = photo_data[1]['urls']['5000']
    command = '/usr/bin/wget "' + footer_img + '" -O footer_image_' + str(activity_id) + '.png'
    os.system(command)

    # Connect to hive
    nodelist = NodeList()
    nodelist.update_nodes()
    nodes = nodelist.get_hive_nodes()
    wif = user_wif
    hive = Hive(nodes=nodes, keys=[wif])

    # Upload image from strava
    footer_image_path = '/home/circleci/project/footer_image_' + str(activity_id) + '.png'  
    footer_image_name = 'footer_image_' + str(activity_id) + '.png'
    image_uploader = ImageUploader(blockchain_instance=hive)

    if author == "run.kirsty.run" or author == "run.vince.run":
      footer_img_link = image_uploader.upload(footer_image_path, author, image_name=footer_image_name)
    else:
      footer_img_link = image_uploader.upload(footer_image_path, "strava2hive", image_name=footer_image_name)

    footer_with_image = f'''
![{footer_image_name}]({footer_img_link['url']})

This is an automated post by @strava2hive and is currently in BETA.
  
If you would like to know more about the @strava2hive service, you can checkout our [Frequently Asked Questions.](https://hive.blog/hive-176853/@strava2hive/strava2hive-frequently-asked-questions)

'''
    
    footer = footer_with_image
  else:
    footer_no_image = f'''
This is an automated post by @strava2hive and is currently in BETA.
  
If you would like to know more about the @strava2hive service, you can checkout our [Frequently Asked Questions.](https://hive.blog/hive-176853/@strava2hive/strava2hive-frequently-asked-questions)
  
'''
    
    footer = footer_no_image
  
  return footer

def zero_image_post(author, user_wif, activity_id):
  # Create images for a post with zero photos provided by user
  
  #if author == "run.kirsty.run" or author == "run.vince.run":
  #    print("Dont do anything with the author")
  #else:
  author = "strava2hive"

  nodelist = NodeList()
  nodelist.update_nodes()
  nodes = nodelist.get_hive_nodes()
  wif = user_wif
  hive = Hive(nodes=nodes, keys=[wif])
  prof_image_path = '/home/circleci/project/S2HLogo.PNG'
  prof_image_name = 'S2HLogo.PNG'
  prof_image_uploader = ImageUploader(blockchain_instance=hive)
  prof_img_link = prof_image_uploader.upload(prof_image_path, author, image_name=prof_image_name)
  print(prof_img_link)
  # Now set up the main image
  image_path = '/home/circleci/project/image_' + str(activity_id) + '.png'
  image_name = 'image_' + str(activity_id) + '.png'
  image_uploader = ImageUploader(blockchain_instance=hive)
  img_link = image_uploader.upload(image_path, author, image_name=image_name)
  return image_name, img_link, prof_image_name, prof_img_link
  
def one_image_post(author, user_wif, activity_id, athlete_id, image_url):
  # Create images for a post with one image taken from strava

  # 1. Download the image from strava - image_url
  # 2. Connect to hive
  # 3. Upload the image from strava
  # 4. upload the activity screenshot

  # Download the image from strava
  profile_img = image_url
  command = '/usr/bin/wget "' + profile_img + '" -O prof_image_' + str(activity_id) + '.png'
  os.system(command)

  # Connect to hive
  nodelist = NodeList()
  nodelist.update_nodes()
  nodes = nodelist.get_hive_nodes()
  wif = user_wif
  hive = Hive(nodes=nodes, keys=[wif])

  # Upload image from strava
  image_path = '/home/circleci/project/prof_image_' + str(activity_id) + '.png'  
  image_name = 'prof_image_' + str(activity_id) + '.png'
  image_uploader = ImageUploader(blockchain_instance=hive)
  img_link = image_uploader.upload(image_path, author, image_name=image_name)

  # Upload activity screenshot
  prof_image_path = '/home/circleci/project/image_' + str(activity_id) + '.png'
  prof_image_name = 'image_' + str(activity_id) + '.png'
  prof_image_uploader = ImageUploader(blockchain_instance=hive)
  prof_img_link = prof_image_uploader.upload(prof_image_path, author, image_name=prof_image_name)

  # Return values
  return image_name, img_link, prof_image_name, prof_img_link

