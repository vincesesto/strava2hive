#!/usr/bin/env python

from selenium import webdriver
#from webdriver_manager.firefox import GeckoDriverManager
from time import sleep

print("Running Strava 2 Hive")

def strava_screenshot(activity_url):
  driver = webdriver.Firefox() 
  #driver = webdriver.Firefox(executable_path=GeckoDriverManager().install())
  driver.get(activity_url)
  sleep(1)
  driver.get_screenshot_as_file("screenshot.png")
  driver.quit()
  print("end...")
  
print("Take screenshot of activity")  
strava_screenshot("https://www.strava.com/activities/6790387629")
