# -*- coding: UTF-8 -*-

import os
import re
import time

import pandas as pd
from bs4 import BeautifulSoup
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver import Chrome
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By

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
                            "title": tit, "total price": price})

    return records


def honto(url, driver=None, csv="./honto.csv"):
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
        By.XPATH, '//*[@id="pbBlock2766835"]/div/div/ul/li[4]/a')
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
    df = df.sort_values(by=['date'])
    print(df)
    df.to_csv(csv)

    return df


def kinokuniya(url, driver=None, csv="./kinokuniya.csv"):
    sitecred = CRED[url]
    driver.get(url)

    user = driver.find_element(By.XPATH, '//*[@id="login_box"]/form/input[1]')
    password = driver.find_element(By.XPATH, '//*[@id="pwdright"]')
    user.send_keys(sitecred.get("user", ""))
    password.send_keys(sitecred.get("pass", ""))
    driver.find_element(
        By.XPATH, '//*[@id="login_box"]/form/input[3]').submit()

    driver.find_element(
        By.XPATH, '//*[@id="member_menu"]/a').click()

    driver.find_element(
        By.XPATH, '//*[@id="my_erea"]/div[2]/div[5]/a').click()

    driver.find_element(
        By.XPATH, '//*[@id="mypage_box"]/form[4]/div[1]/div/ul/li[3]/a').click()

    for i in range(1, 13):
        price = driver.find_element(
            By.XPATH, f'//*[@id="mypage_box"]/form[4]/div[3]/div[{i}]/div/div[2]/div[2]/span').get_attribute('innerText')
        price = int("".join(price.split(','))[1:])

        driver.find_element(
            By.XPATH,  f'//*[@id="mypage_box"]/form[4]/div[3]/div[{i}]/div/div[2]/h3/a').click()
        driver.back()

    # driver.find_element(
    #     By.XPATH, '//*[@id="main_contents"]/form/div/div[2]/h3/text()[1]')

    return None


def in_out(prefix_dir="C:/Users/kitty/Dropbox/My PC (DESKTOP-MT0S3I6)/Downloads/", prefix_files="収入・支出詳細_2020-"):
    file_list = []
    with os.scandir(prefix_dir) as itx:
        for entry in itx:
            if not entry.name.startswith('.') and entry.is_file() and entry.name.startswith(prefix_files):
                file_list.append(pd.read_csv(
                    prefix_dir + entry.name, header='infer', encoding='cp932'))

    return pd.concat(file_list).sort_values(by=['日付'])


with Chrome(executable_path=r'C:\Users\kitty\ChromeDriver\chromedriver.exe') as driver:
    # print(dir(driver))
    sites = list(CRED.keys())
    hont_df = honto(url=sites[0], driver=driver)
    kinokuniya_df = kinokuniya(url=sites[1], driver=driver)

    df_2020 = in_out()
    df_2020_nona = df_2020[df_2020.notna()['内容']]
    df_kinokuniya_mf = df_2020_nona[df_2020_nona['内容'].str.contains(
        '紀伊國屋') | df_2020_nona['内容'].str.contains('inokuniya') | df_2020_nona['内容'].str.contains('キノクニヤ')]
    print(df_kinokuniya_mf)
