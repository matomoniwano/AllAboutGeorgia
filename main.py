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
#import gspread
from oauth2client.service_account import ServiceAccountCredentials
#from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
import heapq
import pickle



# def textclassification(a):
#     api_key   = "XGhjqzEtQylcOulQCSae3rgtB0iHau6qa4DlcYxLFNg"
#     paralleldots.set_api_key( api_key )
#     #print(a)
#     print(paralleldots.taxonomy( a ))
#     return paralleldots.taxonomy( a )

# def category_extractor(text):
#     api = textclassification(text)
#     print(api)
#     apiresult = api["taxonomy"]
#     apiresult_dic = {}
#     for i in apiresult:
#         apiresult_dic[i["tag"]] = float(i["confidence_score"])
#     category = heapq.nlargest(1, apiresult_dic, key=apiresult_dic.get)

#     return category[0]

def predict_category(text, classifier, tfidf_vectorizer):
    result = classifier.predict(tfidf_vectorizer.transform([text]))
    return(result[0])
    

def NLP_categorizer(txt):

    # Use pickle to load in the pre-trained model.
    with open('vector.pkl', 'rb') as file:
        tfidf_vectorizer = pickle.load(file)
        
    with open('class.pkl', 'rb') as file:
        classifier = pickle.load(file)

    return predict_category(txt, classifier, tfidf_vectorizer)



def process_article(soup, link):
    temp = []
    category = soup.find_all('div', class_='col-md-9')
    title_en = soup.find('h1', class_ = 'node-title').string
    
    url = title_en.replace(" ", "-")
    title_ja = GoogleTranslator(source='en', target='ja').translate(title_en).replace(".", "。").replace("グルジア", "ジョージア")

    body = soup.find_all('div', class_ = 'row bodytext')
    bodyall = soup.find('div', class_ = 'row bodytext').text
    index = int(len(bodyall)/2)
    print(index)
    #cat = category_extractor(bodyall[0:index])
    cat = NLP_categorizer(bodyall)
    #print(body[0])

    #print()
    #cat = category[0].find_all('img')[0]["src"].replace("/", " ").split()[1]

    for img in body[0].find_all('img'):
        #print(img["src"])
        img["src"] = "https://agenda.ge" + img["src"]

    #newbody = str(body[0])
    for pg in body[0].find_all('p'):
        if pg.string :
            pg.string.replace_with(GoogleTranslator(source='en', target='ja').translate(pg.string).replace(".", "。").replace("グルジア", "ジョージア"))
        else:
            pg.string = GoogleTranslator(source='en', target='ja').translate(pg.text).replace(".", "。").replace("グルジア", "ジョージア")
        #newbody = newbody.replace(pg.text, GoogleTranslator(source='en', target='ja').translate(pg.text))

    finalbody = "[blogcard url=" + link + "]"+ str(body[0])
    print("after process")
    #Title
    temp.append(title_ja)
    #url
    temp.append(url)
    #body
    temp.append(finalbody)
    #category
    temp.append(cat)
    return temp


def getcontents(driver):
    contents = []
    driver.get("https://agenda.ge/en/news/news")
    sleep(1)
    #should be 16
    print("front page about to get dates")
    dates = driver.find_elements_by_xpath( "//div[@class='node-teaser-time']")
    links = driver.find_elements_by_xpath( "//a[@class='node-teaser-title']")
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
    linkref = {}
    for link in pages:
        response = requests.get(link)
        soup = BeautifulSoup(response.text, 'html.parser')
        lentext = soup.find('div', class_ = 'row bodytext')
        linkref[link] = (len(lentext.text))


    print(linkref)

    top5 = heapq.nlargest(5, linkref, key=linkref.get)

    print(top5)

    for link in top5:
        response = requests.get(link)
        soup = BeautifulSoup(response.text, 'html.parser')     
        contents.append(process_article(soup, link))

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

    # driver = webdriver.Chrome(ChromeDriverManager().install())
    # driver.set_window_size(1280, 1696)
    contents = getcontents(driver)
    driver.get("https://00.ge/wp-admin/index.php")
    sleep(1)
    login = driver.find_element_by_id("user_login")
    login.send_keys("matomo.niwano@gmail.com")
    pwd = driver.find_element_by_id("user_pass")
    pwd.send_keys("@32jG5qqAyk4I#WuV3IOtN*q")
    submit = driver.find_element_by_id( "wp-submit")
    submit.click()

    for content in contents:
        print(content[1])
        driver.get("https://00.ge/wp-admin/post-new.php?post_type=custom&customize_changeset_uuid=")
        driver.save_screenshot('yahooooo.png')
        sleep(2)
        title = driver.find_element_by_name("post_title")
        title.send_keys(content[0])
        body = driver.find_element_by_xpath( "//textarea[@id='content']")
        body.click()
        sleep(1)
        body.send_keys(content[2])
        category_ML = content[3]

        if category_ML in ["ECONOMY-BUSINESS"]:
            category = driver.find_element_by_xpath("//input[@id='in-custom_category-14']")
        elif category_ML in ["POLITICS", "WORLDPOST"]:
            category = driver.find_element_by_xpath("//input[@id='in-custom_category-17']")
        elif category_ML in ["JUSTICE"]:
            category = driver.find_element_by_xpath("//input[@id='in-custom_category-20']")
        elif category_ML in ["CULTURE"]:
            category = driver.find_element_by_xpath("//input[@id='in-custom_category-19']")
        elif category_ML in ["SOCIETY-EDUCATION"]:
            category = driver.find_element_by_xpath("//input[@id='in-custom_category-16']")
        elif category_ML in ["SPORT"]:
            category = driver.find_element_by_xpath("//input[@id='in-custom_category-18']")
        else:
            category = driver.find_element_by_xpath("//input[@id='in-custom_category-23']")

        sleep(1)
        
        try:
            category.click()
        except:
            cat = driver.find_element_by_xpath("//div[@id='custom_categorydiv']//button[@class='handlediv']")
            cat.click()
            sleep(1)
            category.click()
        
        sleep(1)
        driver.execute_script("window.scrollTo(0, 0)")

        slug = driver.find_element_by_xpath("//button[@class='edit-slug button button-small hide-if-no-js']")
        slug.click()
        sleep(1)
        newslug = driver.find_element_by_xpath("//input[@id='new-post-slug']")
        newslug.send_keys(Keys.CONTROL + "a")
        newslug.send_keys(Keys.DELETE)
        sleep(1)
        newslug.send_keys(content[1])
        ok = driver.find_element_by_xpath( "//button[@class='save button button-small']")
        ok.click()
        sleep(1)


        
        #save = driver.find_element_by_xpath( "//input[@value='下書きとして保存']")
        publish = driver.find_element_by_xpath("//input[@class='button button-primary button-large']")
        publish.click()
        #save.click()
        sleep(3)



