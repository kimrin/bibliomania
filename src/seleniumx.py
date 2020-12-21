# -*- coding: UTF-8 -*-

import time
import re
import pandas as pd
from selenium.webdriver import Chrome
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from credentials import CRED


def get_handle():
    main_window_handle = driver.current_window_handle
    signin_window_handle = None
    while not signin_window_handle:
        for handle in driver.window_handles:
            if handle != main_window_handle:
                signin_window_handle = handle
                break
    return signin_window_handle


def get_date(datestr):
    # print(datestr)
    datestronly = re.sub("ご購入", "", datestr)
    return "-".join(datestronly.split("/"))


def extract_books_info(driver, books):
    records = []
    for idx in range(len(books)):
        book = books[idx]
        itemize = book.find_element_by_class_name('stItemize')

        title = [x.text for x in itemize.find_elements_by_tag_name('li')]

        datestr = book.find_elements_by_class_name('stHeading')[1].text

        date = get_date(datestr=datestr)

        store = book.find_element_by_class_name('stContents')
        store = re.sub(
            "店舗名：", "", store.find_elements_by_tag_name('em')[0].text)

        price = book.find_element_by_class_name('stPrice')
        price = price.find_element_by_class_name('stYen')
        price = price.find_elements_by_tag_name('span')[0].text

        for tit in title:
            records.append({"date": date, "store": store,
                            "title": tit, "price": price})

    return records


with Chrome(executable_path=r'C:\Users\kitty\ChromeDriver\chromedriver.exe') as driver:
    # print(dir(driver))
    sites = list(CRED.keys())
    for url in sites[:1]:
        sitecred = CRED[url]
        driver.get(url)
        acs = ActionChains(driver)

        el = driver.find_element_by_class_name("stHdLoginNav")
        logins = el.find_elements_by_tag_name('li')

        acs.click(logins[1])
        acs.perform()
        acs.reset_actions()

        user = driver.find_element_by_id("dy_lginId")
        passname = driver.find_element_by_id("dy_pw")
        user.send_keys(sitecred.get("user", ""))
        passname.send_keys(sitecred.get("pass", ""))
        driver.find_element_by_id("dy_btLgin").submit()

        mymenu = driver.find_element_by_class_name("stMyMenu")
        mymenu.find_elements_by_tag_name("em")[0].click()

        driver.get("https://honto.jp/my/account/history.html")

        pulldown = driver.find_element(
            By.XPATH, "/html/body/div[1]/div[2]/div[2]/div/div/div/div[2]/div")
        acs.move_to_element(pulldown)
        acs.click(pulldown)
        try:
            acs.perform()
        except StaleElementReferenceException:
            pulldown = driver.find_element(
                By.XPATH, "/html/body/div[1]/div[2]/div[2]/div/div/div/div[2]/div")
        acs.reset_actions()

        pulldown.click()

        oneyear = driver.find_element(
            By.XPATH, '//*[@id="pbBlock2766835"]/div/div/ul/li[3]/a')
        onclick = oneyear.get_attribute("onclick")
        driver.execute_script(onclick)

        driver.find_element(By.XPATH,
                            "/html/body/div[1]/div[2]/div[2]/div/div/div/div[3]/form/div[1]/div[1]/div/table/tbody/tr/td[2]/select/option[2]").click()

        records = []

        bot = driver.find_element(
            By.CLASS_NAME, "stNext").find_elements_by_tag_name('a')
        while len(bot) > 0:
            books = driver.find_elements_by_class_name("stAccount01")
            records.extend(extract_books_info(driver=driver, books=books))
            bot = driver.find_element(
                By.CLASS_NAME, "stNext").find_elements_by_tag_name('a')
            try:
                onclick = bot[0].get_attribute("onclick")
                driver.execute_script(onclick)
            except:
                break

        df = pd.DataFrame.from_records(records)

        print(df)
        df.to_csv('./honto.csv')
        time.sleep(5.0)
