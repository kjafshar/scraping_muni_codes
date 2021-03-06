from selenium import webdriver
from time import sleep
import os
from scraper_tools import *
from datetime import datetime
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import sys
import getpass

user = getpass.getuser()
sys.dont_write_bytecode = True

sys.path.insert(0, '/Users/{}/Box/Utility Code'.format(user))

from utils_io import *


class wait_for_text_to_start_with:

    """
    This class functions as a condition which can be used by the WebDriverWait method
    It will cause the driver to wait until the text given to it is present in the element

    It includes text replacement methods to modify the text string extracted from the element
    """

    def __init__(self, locator, text_):
        self.locator = locator
        self.text = text_

    def __call__(self, driver):
        try:
            element_text = EC._find_element(driver, self.locator).text.replace(" modified", '')\
                                                                        .replace(" Modified", '')\
                                                                        .replace(" Amended", '')\
                                                                        .replace(" amended", '')\
                                                                        .replace(" New", '') \
                                                                        .replace(" new", '')
            return element_text.startswith(self.text)
        except StaleElementReferenceException:
            return False


def generate_municode_links():

    """
    Using the list of names below, this function will find the municode link corresponding to the page of each given muni

    """





    city_county = 'Alameda County,Contra Costa County,Marin County,Napa County,City and County of San Francisco,San Mateo County,' \
                  'Santa Clara County,' \
                  'Solano County,Sonoma County,Alameda,Albany,Berkeley,Dublin,Emeryville,Fremont,Hayward,Livermore,Newark,Oakland,Piedmont,' \
                  'Pleasanton,' \
                  'San Leandro,Union City,Antioch,Brentwood,Clayton,Concord,Danville,El Cerrito,Hercules,Lafayette,Martinez,Moraga,Oakley,Orinda,' \
                  'Pinole,' \
                  'Pittsburg,Pleasant Hill,Richmond,San Pablo,San Ramon,Walnut Creek,Belvedere,Fairfax,Larkspur,Mill Valley,Novato,Ross,' \
                  'San Anselmo,' \
                  'San Rafael,Sausalito,Tiburon,American Canyon,Calistoga,Napa,St. Helena,Yountville,Atherton,Belmont,Brisbane,Burlingame,' \
                  'Colma,Daly City,East Palo Alto,Foster City,Half Moon Bay,Hillsborough,Menlo Park,Millbrae,Pacifica,Portola Valley,Redwood City,' \
                  'San Bruno,San Carlos,San Mateo,South San Francisco,Woodside,Campbell,Cupertino,Gilroy,Los Altos,Los Altos Hills,Los Gatos,' \
                  'Milpitas,' \
                  'Monte Sereno,Morgan Hill,Mountain View,Palo Alto,San Jose,Santa Clara,Saratoga,Sunnyvale,Benicia,Dixon,Fairfield,Rio Vista,' \
                  'Suisun City,Vacaville,Vallejo,Cloverdale,Cotati,Healdsburg,Petaluma,Rohnert Park,Santa Rosa,Sebastopol,Sonoma,Windsor'

    city_county = city_county.split(",")

    cwd = os.getcwd()
    driver = webdriver.Chrome(f'{cwd}/chromedriver')
    driver.get('https://library.municode.com/ca')

    element = WebDriverWait(driver, 30) \
        .until(EC.element_to_be_clickable((By.CSS_SELECTOR, "li[ng-repeat='client in letterGroup.clients']")))

    ca_links = driver.find_elements_by_tag_name("li")

    # filter to desired municipalities
    muni_links = [link for link in ca_links if link.text in city_county]
    muni_links = [(link.text, link.find_element_by_tag_name("a").get_attribute("href")) for link in muni_links]
    driver.quit()

    return muni_links


def extract_text(driver):
    """
    Given a driver point at a page with "chunk" partitioned text, extract the text
    """

    filler_text = "\nSHARE LINK TO SECTION\nPRINT SECTION\nDOWNLOAD (DOCX) OF SECTIONS\nEMAIL SECTION"
    element = WebDriverWait(driver, 120).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[ng-switch-when='CHUNKS']")))
    doc = driver.find_element_by_css_selector('ul[class="chunks list-unstyled small-padding"]').text
    doc = doc.replace(filler_text, '')
    return doc


def toc_crawler(driver):

    """
    this code is run for situations where the level 2  or further docs are broken into further chunks that aren't visible on the landing page
    """

    two_toc = driver.find_elements_by_css_selector("li[depth='-1']")
    l_2_doc = []

    for level_3_heading in two_toc:
        level_3_heading.click()

        title = level_3_heading.text.split("\n")[0].replace(" modified", '')\
            .replace(" Modified", '')\
            .replace(" Amended", '')\
            .replace(" amended", '')\
            .replace(" New", '') \
            .replace(" new", '')

        try:
            element = WebDriverWait(driver, 120).until(wait_for_text_to_start_with((By.CSS_SELECTOR, "div[class='chunk-title-wrapper']"), title))
        except:
            return True

        # if the level 3 doc is visible from the toc link, extract text, else begin another table of content crawl

        if driver.find_elements_by_css_selector("div[ng-switch-when='CHUNKS']"):
            l_2_doc.append(extract_text(driver))
        elif driver.find_elements_by_css_selector("div[ng-switch-when='TOC']"):
            level_3_doc = []
            three_toc = level_3_heading.find_elements_by_css_selector("li[depth='-1']")

            for level_4_heading in three_toc:
                level_4_heading.click()

                title = level_4_heading.text.split("\n")[0].replace(" modified", '')\
                                                           .replace(" Modified", '')\
                                                           .replace(" Amended", '')\
                                                           .replace(" amended", '')\
                                                           .replace(" New", '')\
                                                           .replace(" new", '')

                try:
                    element = WebDriverWait(driver, 120).until(wait_for_text_to_start_with((By.CSS_SELECTOR, "div[class='chunk-title-wrapper']"), title))
                except:
                    return True

                # if the level 4 doc is visible from the toc link, extract text, else begin another table of content crawl

                if driver.find_elements_by_css_selector("div[ng-switch-when='CHUNKS']"):
                    level_3_doc.append(extract_text(driver))
                elif driver.find_elements_by_css_selector("div[ng-switch-when='TOC']"):
                    level_4_doc = []
                    four_toc = level_4_heading.find_elements_by_css_selector("li[depth='-1']")
                    for level_5_heading in four_toc:
                        level_5_heading.click()

                        title = level_5_heading.text.split("\n")[0].replace(" modified", '')\
                                                                        .replace(" Modified", '')\
                                                                        .replace(" Amended", '')\
                                                                        .replace(" amended", '')\
                                                                        .replace(" New", '') \
                                                                        .replace(" new", '')

                        try:
                            element = WebDriverWait(driver, 120).until(
                            wait_for_text_to_start_with((By.CSS_SELECTOR, "div[class='chunk-title-wrapper']"), title))
                        except:
                            return True
                        level_4_doc.append(extract_text(driver))
                level_3_doc.append(extract_text(driver))
            l_2_doc.append("\n".join(level_3_doc))

    return "\n".join(l_2_doc)


def page_crawler(driver, s3_bucket, s3_path, rs_table, base_loc, muni, date_str):
    # this is the code which runs after the driver reaches the muni landing
    # it will call extraction and toc crawler as needed

    element = WebDriverWait(driver, 120).until(EC.presence_of_element_located((By.CSS_SELECTOR, "section[id='toc']")))
    toc = [link for link in driver.find_element_by_css_selector("section[id='toc']").find_elements_by_tag_name("li")]
    keys_written = []
    for level_2_heading in toc:

        # this check and similar ones during the toc_crawler are to ensure the driver has reached the particular page
        # after clicking on the table of contents link
        # the toc title needs to be stripped of additional tags added to it

        title = level_2_heading.text.split("\n")[0].replace(" modified", '')\
                                    .replace(" Modified", '')\
                                    .replace(" Amended", '')\
                                    .replace(" amended", '') \
                                    .replace(" New", '') \
                                    .replace(" new", '')

        print(title)
        level_2_heading.click()
        try:
            element = WebDriverWait(driver, 120).until(wait_for_text_to_start_with((By.CSS_SELECTOR, "div[class='chunk-title-wrapper']"), title))
        except:
            print(2)
            return True, keys_written

        if driver.find_elements_by_css_selector("div[ng-switch-when='CHUNKS']"):
            key = s3_file_writer(s3_bucket, s3_path, base_loc, muni, date_str, title, extract_text(driver))
            if key:
                keys_written.append(key)
        elif driver.find_elements_by_css_selector("div[ng-switch-when='TOC']"):
            key = s3_file_writer(s3_bucket, s3_path, base_loc, muni, date_str, title, toc_crawler(driver))
            if key:
                keys_written.append(key)
        else:
            print(f'{muni}-{title} failed')
            return True, keys_written

        close_button = driver.find_elements_by_css_selector('i[class="fa-fw fa fa-chevron-down"]')
        if close_button:
            close_button[0].click()

    return False, keys_written


def municode_scraper(s3_bucket, s3_path, rs_table, base_loc, muni_tuple):

    cwd = os.getcwd()
    driver = webdriver.Chrome(f'{cwd}/chromedriver')
    driver.get(muni_tuple[1])
    element = WebDriverWait(driver, 120) \
                .until(EC.element_to_be_clickable((By.CSS_SELECTOR, "i[class='fa fa-home']")))

    keys_written = []

    try:

        sleep(1)

        # check municipality name
        muni = driver.current_url.split('/')[4]
        print(muni)
        print('')
        sleep(3)
        # check for a division first before exposing docs

        try:
            # update_date = driver.find_element_by_class_name("product-date").text  # update data only visible on actual code page, works as a check

            update_date = WebDriverWait(driver, 5) \
                .until(EC.element_to_be_clickable((By.CLASS_NAME, "product-date"))).text

        except:
            x = ([link for link in driver.find_elements_by_tag_name("li")
                  if "municipal" in link.text.lower() or "ordinance" in link.text.lower()])[0]

            x.find_elements_by_tag_name("a")[0].click()
            update_date = WebDriverWait(driver, 10) \
                .until(EC.element_to_be_clickable((By.CLASS_NAME, "product-date"))).text

        # format update date

        update_date = update_date.split(' ')[-3:]

        update_date = datetime.strptime("-".join(update_date), '%B-%d,-%Y').date()
        date_str = update_date.strftime("%m-%d-%y")

        if len(rs_table) > 0:
            if not check_for_update(update_date, muni, rs_table):
                print(f'{muni} not updated')
                return False, keys_written

        # check for popup-window

        try:
            popup_button = WebDriverWait(driver, 20) \
                .until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[class='hopscotch-bubble-close hopscotch-close']")))

            popup_button.click()
        except:
            pass

        failed_crawl, keys_written = page_crawler(driver, s3_bucket, s3_path, rs_table, base_loc, muni, date_str)

        if failed_crawl:
            driver.quit()
            print(1)
            return True, keys_written

        driver.quit()

        return False, keys_written

    except:

        driver.quit()

        return True, keys_written
