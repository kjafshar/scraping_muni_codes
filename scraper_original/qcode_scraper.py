import pandas as pd
import numpy as np
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import random
from bs4 import BeautifulSoup
import requests
import sys
import os
import scraper_tools
from time import sleep


def find_click_n_wait(driver, current_xpath, next_xpath, section_num, wait_time, extra_time):
    """find element click on it and wait till next xpath is present"""
    my_section = driver.find_elements_by_xpath(current_xpath)
    click_n_wait(driver, next_xpath, my_section, section_num, wait_time, extra_time)


def click_n_wait(driver, next_xpath, my_section, section_num, wait_time, extra_time):
    """click on current section and wait for next xpath to be present"""
    my_section[section_num].click()
    waiting_for_presence_of(driver, next_xpath, wait_time, extra_time)


def waiting_for_presence_of(driver, next_xpath, wait_time, extra_time):
    """wait till xpath is present, but usually needs a little extra time to load"""
    waiting = WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.XPATH, next_xpath)))
    time.sleep(extra_time)


def write_to_folder(base_loc, city, title, my_doc, update_date_messy):
    # save file to path
    path = scraper_tools.make_path(base_loc+'results', city.replace(" ", ""), update_date_messy)
    with open(f"{path}/{title}.txt", "w") as text_file:
        text_file.write('\n'.join(my_doc))
    print(f"{path}/{title}.txt")


def q_code_main(s3_bucket, s3_path, rs_table, base_loc, start_link):
    cwd = os.getcwd()
    chrome_options = webdriver.ChromeOptions()
    #set download folder
    #configure multiple file download and turn off prompt
    prefs = {'download.default_directory' : base_loc,
            'profile.default_content_setting_values.automatic_downloads': 1,
            'download.prompt_for_download': 'False'}
    chrome_options.add_experimental_option('prefs', prefs)
    missing_sections = 0
    keys_written = []
    my_xpath = "//div[@class='navChildren']//a"
    showall_xpath = "//a[@class='showAll']"
    high_title_xpath = "//div[@class='currentTopic']"
    low_title_xpath = "//div[@class='navTocHeading']"
    content_xpath = "//div[@class='content-fragment']"
    up_xpath = "//a[@accesskey='u']"
    city = start_link[0]
    links = start_link[1]
    print(city)
    for link in links:
        my_doc = [city]
        try:
            # level 1
            driver = webdriver.Chrome(f'{cwd}/chromedriver', options=chrome_options)
            print(link)
            driver.get(link)
            # get last updated date
            driver.switch_to.frame('LEFT')
            date_xpath = "//body[@class='preface']//p"
            scraper_tools.waiting_for_presence_of(driver, date_xpath, 3, 0.1)
            left_text = driver.find_elements_by_xpath(date_xpath)
            for p in left_text:
                if 'current' in p.text.lower():
                    update_date_messy = p.text
                    my_doc.append(update_date_messy)
            driver.switch_to.default_content()
            driver.switch_to.frame('RIGHT')
            scraper_tools.waiting_for_presence_of(driver, my_xpath, 3, 0.1)
            # level 2
            for h_sec_num in range(len(driver.find_elements_by_xpath(my_xpath))):
                h_sections = driver.find_elements_by_xpath(my_xpath)
                level2_title = h_sections[h_sec_num].text
                print(level2_title)
                my_doc.append(level2_title)
                if 'reserved' in level2_title.lower():
                    continue
                scraper_tools.click_n_wait(driver, my_xpath, h_sections, h_sec_num, 3, 0.1)
                # level 3
                for l_sec_num in range(len(driver.find_elements_by_xpath(my_xpath))):
                    try:
                        l_sections = driver.find_elements_by_xpath(my_xpath)
                        my_doc.append(l_sections[l_sec_num].text)
                        scraper_tools.click_n_wait(driver, showall_xpath, l_sections, l_sec_num, 3, 0.1)
                        scraper_tools.find_click_n_wait(driver, showall_xpath, high_title_xpath, 0, 3, 0.1)
                        h_title = driver.find_elements_by_xpath(high_title_xpath)
                        my_doc.append(h_title[0].text)
                        # get text
                        for content, l_title in zip(driver.find_elements_by_xpath(content_xpath), driver.find_elements_by_xpath(low_title_xpath)):
                            my_doc.append(l_title.text)
                            my_doc.append(content.text)
                        # go to previous page
                        find_click_n_wait(driver, up_xpath, my_xpath, 0, 3, 0.1)
                    except:
                        my_doc.append("-_-_-missing-_-_-")
                        missing_sections += 1
                        driver.get(link)
                        driver.switch_to.frame('RIGHT')
                        scraper_tools.find_click_n_wait(driver, my_xpath, my_xpath, h_sec_num, 3, 0.1)
                scraper_tools.find_click_n_wait(driver, up_xpath, my_xpath, 0, 3, 0.1)
                update_date = scraper_tools.extract_date(update_date_messy)
                key = scraper_tools.s3_file_writer(s3_bucket, s3_path, base_loc, city, update_date, level2_title, '\n'.join(my_doc))
                if key:
                    keys_written.append(key)
                my_doc = [city]
        except:
            return True, keys_written
    driver.close()
    driver.quit()
    print("-"*5)
    if missing_sections > 0:
        return True, keys_written
    return False, keys_written
