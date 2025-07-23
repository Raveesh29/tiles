#!/usr/bin/env python3
"""
Naukri Job Scraper - Automated daily job collection
"""

import os
import numpy as np
from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from selenium.webdriver.common.by import By
import pandas as pd
import random
import json
from collections import defaultdict
import datetime
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def setup_chrome_driver():
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

# JSON management functions
def write_json(data, fname, fpath=None):
    if fpath:
        loc = fpath + '/' + fname + '.json'
    else:
        loc = os.getcwd() + "/" + fname + '.json'

    with open(loc, 'w') as json_file:
        json.dump(data, json_file)

def read_json(fname, fpath=None):
    if fpath:
        loc = fpath + '/' + fname + '.json'
    else:
        loc = os.getcwd() + "/" + fname + '.json'

    try:
        with open(loc, 'r') as json_file:
            data = json.load(json_file)
            return data
    except FileNotFoundError:
        print(f"Error: The file {loc} does not exist.")
        return {}

def scroll(driver):
    """Scroll to the end of the page"""
    last_height = driver.execute_script("window.scrollTo(0,100);")
    
    while True:
        last_height = driver.execute_script("return window.scrollY")
        time.sleep(1)
        
        driver.execute_script("window.scrollBy(0,window.scrollY);")
        new_height = driver.execute_script("return window.scrollY")
        
        if new_height == last_height:
            break

def collect_data(driver, tile_class):
    """Collect data from the tiles"""
    html_content = driver.page_source
    soup = BeautifulSoup(html_content, 'lxml')
    tile = soup.find_all('div', attrs={"class": tile_class})
    return tile

def wait():
    """Random wait between requests"""
    wait_time = random.randint(1, 5)
    time.sleep(wait_time)

def click_next(driver, button_class):
    """Find and click the next button"""
    buttons = driver.find_elements(By.CLASS_NAME, button_class)

    if not buttons:
        return 'stop'

    next_button_found = 0
    for button in buttons:
        if 'next' in button.text.lower():
            next_button_found = 1
            is_disabled = button.get_attribute("disabled")
            if is_disabled:
                return 'stop'
            else:
                driver.execute_script("arguments[0].click()", button)

    if not next_button_found:
        return 'stop'

def login_naukri(driver, name='', password=''):
    """Login to Naukri (optional - can run without login)"""
    url = 'https://www.naukri.com/'
    driver.get(url)

    if not name and not password:
        time.sleep(5)
        print('Continuing without login')
        return driver

    try:
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
        submit_buttons[0].click()
        time.sleep(2)

        errors = driver.find_elements(By.CLASS_NAME, 'server-err')
        if len(errors) > 0:
            print('Login failed - continuing without login')
        else:
            print('Login successful')
    except Exception as e:
        print(f'Login failed: {e} - continuing without login')

    time.sleep(5)
    return driver

def extract_tag_data_to_dict_and_df(ele):
    """Extract element data and convert to dictionary"""
    ele_data = defaultdict(list)

    current_ele = ele
    c = '0'
    while current_ele is not None:
        c = current_ele.get('class', c) if hasattr(current_ele, 'get') else c
        tag = current_ele.name if hasattr(current_ele, 'name') else '0'
        
        key = (str(c), str(tag), 'text')
        text = current_ele.text if current_ele.text is not None else ''
        ele_data[key].append(text)
        current_ele = current_ele.next_element

    # Remove duplicates
    for k, v in ele_data.items():
        ele_data[k] = list(dict.fromkeys(v))

    ele_data_str = {k: "--".join(str(item) for item in v if item) for k, v in ele_data.items()}
    ele_data_df = pd.DataFrame.from_dict(ele_data_str, orient='index', columns=['text'])

    return ele_data_str, ele_data_df

def create_job_1():
    """Scrape job listings from Naukri"""
    print("Starting job scraping...")
    
    # URLs to scrape
    # urls = {
    #     'naukri : all jobs + no_filter + remote + 2 days + 10+ years': 'https://www.naukri.com/jobs-in-india?&wfhType=2&jobAge=2&experience=10',
    #     'naukri : all jobs + no_filter + remote + 2 days + 12+ years': 'https://www.naukri.com/jobs-in-india?&wfhType=2&jobAge=2&experience=12',
    #     'naukri : all jobs + no_filter + Delhi - all areas + 2 days + 10+ years': 'https://www.naukri.com/jobs-in-india?cityTypeGid=6&cityTypeGid=73&cityTypeGid=220&cityTypeGid=9508&jobAge=2&experience=10',
    #     'naukri : all jobs + no_filter + Delhi - all areas + 2 days + 12+ years': 'https://www.naukri.com/jobs-in-india?cityTypeGid=6&cityTypeGid=73&cityTypeGid=220&cityTypeGid=9508&jobAge=2&experience=12'
    # }

    urls = {'testing':'https://www.naukri.com/jobs-in-india?&wfhType=2&jobAge=2&experience=22'}
    
    driver = setup_chrome_driver()
    login_naukri(driver)  # Login without credentials
    
    tiles_db = {}

    try:
        for url_id, url in urls.items():
            print(f"Processing: {url_id}")
            driver.get(url)
            wait()
            state = 'start'
            tiles = []
            page_count = 0
            
            while state != 'stop' and page_count < 5:  # Limit pages to avoid long runs
                scroll(driver)
                wait()
                tile = collect_data(driver, tile_class='srp-jobtuple-wrapper')
                if tile:
                    tiles = tiles + tile
                wait()
                state = click_next(driver, 'styles_btn-secondary__2AsIP')
                page_count += 1
                print(f"Processed page {page_count}")

            t_count = 0
            for tile in tiles:
                key = url_id + '--tile_' + str(t_count)
                tiles_db[key] = str(tile)
                t_count += 1
                
            print(f"Collected {len(tiles)} tiles from {url_id}")

    finally:
        driver.quit()

    write_json(tiles_db, 'job_1')
    print(f"Saved {len(tiles_db)} job tiles to job_1.json")

def process_job_data():
    """Process the scraped job data into CSV format"""
    print("Processing job data...")
    
    # Read job data
    job_1 = read_json('job_1')
    
    if not job_1:
        print("No job data found!")
        return

    # Convert to BeautifulSoup elements
    for tile_id, tile in job_1.items():
        job_1[tile_id] = BeautifulSoup(tile, 'lxml').find('div')

    # Create DataFrame
    df_job_1 = pd.DataFrame(columns=['job_id', 'company_name', 'job_title', 'job_url'])

    for tile_id, tile in job_1.items():
        try:
            job_id = tile.get('data-job-id')
            title_elem = tile.find('a', class_='title')
            company_elem = tile.find('a', class_='comp-name')
            
            if title_elem and company_elem:
                title = title_elem.text.strip()
                href = title_elem.get('href', '')
                company = company_elem.text.strip()

                data = {
                    'job_id': str(job_id) if job_id else '',
                    'company_name': company,
                    'job_title': title,
                    'job_url': href
                }

                df_job_1.loc[len(df_job_1)] = data
        except Exception as e:
            print(f"Error processing tile {tile_id}: {e}")
            continue

    # Remove duplicates
    df_job_1['tile_duplicates'] = df_job_1.groupby(df_job_1.columns.tolist()).transform('size')
    df_job_1 = df_job_1.drop_duplicates()

    # Calculate keyword scores
    keyword_terms = [
        "SQL", "Python", "Analytics", "Business Analysis", "Data Visualization",
        "Reporting", "Insights", "Stakeholder Management", "Product Management",
        "Program Management", "Project Management", "Advanced Excel",
        "Data Governance", "Data Management", "Business Strategy", "strategy",
        "analyst", "data", "manager", "report", "agile"
    ]

    def calculate_score(text):
        if pd.isna(text):
            return 0
        score = 0
        for k in keyword_terms:
            score += text.lower().count(k.lower())
        return score

    df_job_1['keyword_score'] = df_job_1['job_title'].apply(calculate_score)
    
    # Sort by keyword score
    df_job_1 = df_job_1.sort_values(by=['keyword_score'], ascending=False)

    # Save results
    cwd = os.getcwd() + "/"
    df_job_1.to_csv(cwd + 'job_1.csv', index=False)
    df_job_1.to_json('n.json', orient='records')
    
    print(f'Processed {len(df_job_1)} jobs and saved to job_1.csv and n.json')

def main():
    """Main function"""
    print(f"Starting job scraper at {datetime.datetime.now()}")
    
    cwd = os.getcwd() + "/"
    
    # Check if we need to scrape new data
    should_scrape = True
    if os.path.exists(cwd + "job_1.json"):
        job_1_mtime = os.path.getmtime(cwd + "job_1.json")
        job_1_mdate = datetime.datetime.fromtimestamp(job_1_mtime).date()
        print(f"Last scrape date: {job_1_mdate}")
        print(f"Today's date: {datetime.date.today()}")
        
        if job_1_mdate == datetime.date.today():
            should_scrape = False
            print("Data already scraped today, skipping scrape...")

    if should_scrape:
        create_job_1()
    
    # Always process the data
    process_job_data()
    
    print(f"Job scraper completed at {datetime.datetime.now()}")

if __name__ == "__main__":
    main()