import os 
import numpy as np 
from bs4 import BeautifulSoup 
import requests
from selenium import webdriver 
import time
from selenium.webdriver.common.by import By 
import pandas as pd 
import random 
import json 
from collections import defaultdict
import ast
import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


# manage json 
def write_json(data,fname,fpath=None):
    if fpath:
        loc = fpath + '/' + fname + '.json'
    else: 
        loc = os.getcwd()+"/" + fname + '.json'

    with open(loc, 'w') as json_file:
        json.dump(data, json_file)


def read_json(fname,fpath=None):
    if fpath:
        loc = fpath + '/' + fname + '.json'
    else: 
        loc = os.getcwd()+"/" + fname + '.json'

    try:
        with open(loc, 'r') as json_file:
            data = json.load(json_file)
            return data
    except FileNotFoundError:
        print(f"Error: The file {loc} does not exist.")
        return {}  # Return an empty dictionary
    


def scroll(driver):
    last_height = driver.execute_script("window.scrollTo(0,100);")
    
    while True:
        last_height = driver.execute_script("return window.scrollY")
        time.sleep(1)
    
        driver.execute_script("window.scrollBy(0,window.scrollY);")
        new_height = driver.execute_script("return window.scrollY")
        # print(f'new height = {new_height} , last_height = {last_height}')
    
        if new_height == last_height:
            break


# this function collects data from the tiles and accumulates in the tiles list

def collect_data(driver,tile_class):
    html_content = driver.page_source
    soup = BeautifulSoup(html_content,'lxml')
    tile = soup.find_all('div',attrs={"class":tile_class})
    return tile


# random wait 

def wait():
    wait = random.randint(1,5)
    print(f'Waiting for {wait} seconds')
    time.sleep(wait)


# finds the next button on naurki website and clicks it 

def click_next(driver,button_class):
    buttons = driver.find_elements(By.CLASS_NAME,button_class)

    if not buttons:
        return 'stop'

    next_button_found = 0
    for button in buttons:
        # print(button.text.lower())
        if 'next' in button.text.lower():
            next_button_found =1 

            is_disabled = button.get_attribute("disabled")
            if is_disabled:
                return 'stop'
            else:
                driver.execute_script("arguments[0].click()",button)

    if not next_button_found:
        return 'stop'
    
# convert text file to bs4 element

def file_to_list(file_path):
    with open(file_path, 'r') as file:
        # Read lines and strip newline characters
        lines = [line.strip() for line in file.readlines()]
    return lines


## Intialising the code 

urls = {'testing':'https://www.naukri.com/jobs-in-india?&wfhType=2&jobAge=2&experience=22'}

# urls = {'naukri : all jobs + no_filter + remote + 2 days + 10+ years': 'https://www.naukri.com/jobs-in-india?&wfhType=2&jobAge=2&experience=10',
#  'naukri : all jobs + no_filter + remote + 2 days + 12+ years': 'https://www.naukri.com/jobs-in-india?&wfhType=2&jobAge=2&experience=12',
#  'naukri : all jobs + no_filter + Delhi - all areas + 2 days + 10+ years': 'https://www.naukri.com/jobs-in-india?cityTypeGid=6&cityTypeGid=73&cityTypeGid=220&cityTypeGid=9508&jobAge=2&experience=10',
#  'naukri : all jobs + no_filter + Delhi - all areas + 2 days + 12+ years': 'https://www.naukri.com/jobs-in-india?cityTypeGid=6&cityTypeGid=73&cityTypeGid=220&cityTypeGid=9508&jobAge=2&experience=12'}

print(urls)
gui_flag = True

# current directory
cwd = os.getcwd()+"/"

# function to setup the chrome driver
def setup_chrome_driver(gui=False):
    if gui:
        """Set up Chrome driver for GUI operation"""
        chrome_options = webdriver.ChromeOptions()
        # chrome_options.add_argument("--headless")  # Uncomment this line if you want to run in headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    else:
        """Set up Chrome driver for headless operation in GitHub Actions"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver


# function to login into naurki 
def login_naukri(name='',password=''):
    driver = setup_chrome_driver(gui_flag)

    # driver = setup_chrome_driver()

    url = 'https://www.naukri.com/'
    driver.get(url)

    if not name and not password:  
        time.sleep(10)
        print('continue without login')
        return driver
      
    login_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, 'login_Layer')))

    login_button.click()

    time.sleep(4)

    input_fields = driver.find_elements(By.TAG_NAME, 'input')

    if input_fields:
        input_fields[0].send_keys(name)
        input_fields[1].send_keys(password)

    time.sleep(1)

    submit_buttons = driver.find_elements(By.CLASS_NAME, 'loginButton')
    # driver.execute_script("arguments[0].click()",submit_button)
    submit_buttons[0].click()
    
    time.sleep(2)

    errors = driver.find_elements(By.CLASS_NAME, 'server-err')
    if len(errors) > 0:
        print('login --> failed')
    else:
        print('login --> success')

    time.sleep(10)
    return driver


def create_job_1():
    
    driver = login_naukri()

    tiles_db = {}


    for url_id, url in urls.items():
        driver.get(url)
        wait()
        state = 'start'    
        tiles = []
        while state!='stop':
            scroll(driver)
            wait()
            tile = collect_data(driver,tile_class='srp-jobtuple-wrapper')
            if tile:
                tiles = tiles + tile
            wait()
            state = click_next(driver,'styles_btn-secondary__2AsIP')
            
        t_count = 0
        for tile in tiles:        
            key = url_id+'--tile_'+str(t_count)
            tiles_db[key] = str(tile)
            t_count+=1

    driver.close()

    write_json(tiles_db,'job_1')



def execute():
    create_job_1()

execute()