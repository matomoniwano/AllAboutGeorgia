import os
from pickletools import unicodestring4
from idna import uts46_remap
from selenium import webdriver
import json
import requests
from pytz import timezone
from six import string_types
from six.moves.urllib.parse import urlencode, urlunparse  # noqa
from selenium.webdriver.common.keys import Keys
from time import sleep, strftime
from selenium.webdriver.support.ui import Select
from datetime import date, timedelta, datetime
import time
from selenium.webdriver.chrome.options import Options
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator



def getcontents(driver):
    contents = []
    driver.get("https://agenda.ge/en/news/news")
    sleep(3)

    #should be 16
    print("checking here")
    dates = driver.find_elements_by_xpath("//div[@class='node-teaser-time']")
    print("dates", len(dates))
    links = driver.find_elements_by_xpath("//a[@class='node-teaser-title']")
    pages = []
    
    # Check dates for today
    for i in range(len(dates)):
        #insert - before d when GCP
        posteddate = datetime.strptime(dates[i].text, '%d %b %Y - %H:%M')
        print("hhihih", posteddate, datetime.now(timezone('Asia/Tbilisi')))
        if posteddate.strftime('%Y-%m-%d') == datetime.now(timezone('Asia/Tbilisi')).strftime('%Y-%m-%d'):
            print(posteddate)
            pages.append(links[i].get_attribute("href"))

    # Done getting all the URLs now moving to each page

    for link in pages:
        temp = []
        response = requests.get(link)
        soup = BeautifulSoup(response.text, 'html.parser')
        category = soup.find_all('div', class_='col-md-9')
        title_en = soup.find('h1', class_ = 'node-title').string
        url = title_en.replace(" ", "-")
        title_ja = GoogleTranslator(source='en', target='ja').translate(title_en).replace("グルジア", "ジョージア").replace(".", "。")

        body = soup.find_all('div', class_ = 'row bodytext')

        #print(body[0])

        print()
        cat = category[0].find_all('img')[0]["src"].replace("/", " ").split()[1]

        for img in body[0].find_all('img'):
            #print(img["src"])
            img["src"] = "https://agenda.ge" + img["src"]

        #newbody = str(body[0])
        for pg in body[0].find_all('p'):
            if pg.string :
                pg.string.replace_with(GoogleTranslator(source='en', target='ja').translate(pg.string).replace("グルジア", "ジョージア").replace(".", "。"))
            else:
                pg.string = GoogleTranslator(source='en', target='ja').translate(pg.text).replace("グルジア", "ジョージア").replace(".", "。")
            #newbody = newbody.replace(pg.text, GoogleTranslator(source='en', target='ja').translate(pg.text))

        finalbody = "[blogcard url=" + link + "]"+ str(body[0])

        #Title
        temp.append(title_ja)
        #url
        temp.append(url)
        #body
        temp.append(finalbody)
        #category
        temp.append(cat)

        contents.append(temp)

    return contents

## TOdo transger texts to the wordpress and publish

def AAG(requests):
    chrome_options = webdriver.ChromeOptions()

    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1280x1696')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--hide-scrollbars')
    chrome_options.add_argument('--enable-logging')
    chrome_options.add_argument('--log-level=0')
    chrome_options.add_argument('--v=99')
    chrome_options.add_argument('--single-process')
    chrome_options.add_argument('--ignore-certificate-errors')

    chrome_options.binary_location = os.getcwd() + "/headless-chromium"    
    driver = webdriver.Chrome(os.getcwd() + "/chromedriver",chrome_options=chrome_options)


    contents = getcontents(driver)
    driver.set_window_size(1024, 600)
    driver.maximize_window()
    # Scraping

    driver.get("https://00.ge/wp-admin/index.php")
    sleep(1)
    login = driver.find_element_by_id("user_login")
    login.send_keys("matomo.niwano@gmail.com")
    pwd = driver.find_element_by_id("user_pass")
    pwd.send_keys("@32jG5qqAyk4I#WuV3IOtN*q")
    submit = driver.find_element_by_id("wp-submit")
    submit.click()
    sleep(1)
    print("content: ", len(contents))
    for content in contents:

        driver.get("https://00.ge/wp-admin/post-new.php?post_type=custom&customize_changeset_uuid=")

        sleep(2)
        title = driver.find_element_by_name("post_title")
        title.send_keys(content[0])
        sleep(1)


        body = driver.find_element_by_xpath("//textarea[@id='content']")
        body.click()
        sleep(2)
        body.send_keys(content[2])

        sleep(3)
        driver.execute_script("window.scrollTo(0, 220)")
        sleep(1)
        slug = driver.find_element_by_xpath("//button[@class='edit-slug button button-small hide-if-no-js']")
        slug.click()
        sleep(3)
        newslug = driver.find_element_by_xpath("//input[@id='new-post-slug']")
        newslug.send_keys(Keys.CONTROL + "a")
        newslug.send_keys(Keys.DELETE)
        sleep(2)
        newslug.send_keys(content[1])
        ok = driver.find_element_by_xpath("//button[@class='save button button-small']")
        ok.click()
        sleep(3)

        cat = driver.find_element_by_xpath("//div[@id='custom_categorydiv']//button[@class='handlediv']")
        cat.click()
        sleep(2)
        if content[3] == "sport":
            category = driver.find_element_by_xpath("//input[@id='in-custom_category-18']")
        elif content[3] == "grants" or content[3] == "parliament" or content[3] == "congress" or content[3] == "EU" or content[3] == "government" or content[3] == "politics":
            category = driver.find_element_by_xpath("//input[@id='in-custom_category-17']")
        elif content[3] == "ArtNCulture2":
            category = driver.find_element_by_xpath("//input[@id='in-custom_category-19']")
        elif content[3] == "justice" or content[3] == "Crime" or content[3] == "police":
            category = driver.find_element_by_xpath("//input[@id='in-custom_category-20']")
        elif content[3] == "society":
            category = driver.find_element_by_xpath("//input[@id='in-custom_category-16']")
        elif content[3] == "Economy":
            category = driver.find_element_by_xpath("//input[@id='in-custom_category-14']")
        else:
            category = driver.find_element_by_xpath("//input[@id='in-custom_category-23']")


        sleep(3)
        try:
            category.click()
        except:
            cat.click()
            category.click()
        
        sleep(3)
        save = driver.find_element_by_xpath("//input[@value='下書きとして保存']")
        save.click()
        sleep(3)



