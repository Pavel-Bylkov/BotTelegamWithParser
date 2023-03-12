import asyncio

import concurrent.futures
import time
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import Select
import xml

from multiprocessing import Pool

from filter import filter_by_stat, filter_by_league
from bot_api import bot_send_message

# Строгий отбор
STRICT_SELECTION = True

def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument('--ignore-certificate-errors-spki-list')
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36\
                            (KHTML, like Gecko) Chrome/106.0.0.0 YaBrowser/22.11.5.715 Yowser/2.5 Safari/537.36")
    driver = webdriver.Chrome(executable_path='chromedriver/chromedriver.exe', options=chrome_options)
    driver.maximize_window()
    return driver

def get_stats(id):
    def driver_close():
        driver.close()
        driver.quit()
        return False
    url = f'https://www.flashscore.com.ua/match/{id}/#/match-summary/match-statistics/0'
    driver = get_driver()
    driver.get(url)
    time.sleep(1)
    # print(url)
    t = driver.find_element(By.CLASS_NAME, 'tournamentHeader__country')
    t = t.text.split(" -")
    league = t[0]
    match_stat = {}
    if filter_by_league(league.lower()):
        time_event = None
        print(league)
        for i in driver.find_elements(By.CLASS_NAME, 'detailScore__status'):
            if i.text in ("ПЕРЕРЫВ", "ЗАВЕРШЕН"):
                return driver_close()
            print(url)
            time_event = i.text.split("ТАЙМ")
            print(time_event)
            if ":" in time_event[1]:
                time_event[1] = time_event[1].split(":")
            elif "+" in time_event[1]:
                time_event[1] = time_event[1].split("+")
            match_stat['event_time'] = time_event[1][0]
            home = [i.text for i in driver.find_elements(By.CLASS_NAME, 'stat__homeValue')]
            away = [i.text for i in driver.find_elements(By.CLASS_NAME, 'stat__awayValue')]
            match_stat['possession'] = home[0][:2]
            match_stat['leader_shoot'] = home[1]
            match_stat['loser_shoot'] = away[1]
            match_stat['leader_shoot_on_target'] = home[2]
            match_stat['loser_shoot_on_target'] = away[2]
            x = filter_by_stat(match_stat)
            if all(x.values()):
                driver_close()
                return bot_send_message(
                    f'<a href="{url}">Игра</a> из лиги {league} полностью удовлетворяет условиям!')
            team1 = {key: value for key, value in match_stat.items() if not x[key]}
            match_stat['possession'] = away[0][:2]
            match_stat['leader_shoot'] = away[1]
            match_stat['loser_shoot'] = home[1]
            match_stat['leader_shoot_on_target'] = away[2]
            match_stat['loser_shoot_on_target'] = home[2]
            y = filter_by_stat(match_stat)
            if all(y.values()):
                driver_close()
                return bot_send_message(
                    f'<a href="{url}">Игра</a> из лиги {league} полностью удовлетворяет условиям!')
            team2 = {key: value for key, value in match_stat.items() if not y[key]}
            msg = f'<a href="{url}">Игра</a> из лиги {league} близко к условиям!'
            if not STRICT_SELECTION and len(team1) == 1:
                msg += '\nдля 1 команды не подходит ' + str(team1)
            if not STRICT_SELECTION and len(team2) == 1:
                msg += '\nдля 2 команды не подходит ' + str(team2)
            if not STRICT_SELECTION and (len(team1) == 1 or len(team2) == 1):
                driver_close()
                return bot_send_message(msg)
    return driver_close()


def parser(url='https://www.flashscore.com.ua'):
    driver = get_driver()
    driver.get(url)
    time.sleep(1)
    for i in driver.find_elements(By.CLASS_NAME, 'filters__tab'):
        if i.text == "LIVE":
            i.click()
    names_leagues = []
    pageSource = driver.page_source
    fileToWrite = open("page_source.html", "w", encoding="utf-8")
    fileToWrite.write(pageSource)
    fileToWrite.close()
    for i in driver.find_elements(By.CLASS_NAME, 'event__match'):
        print(i.text)
        names_leagues.append(i.get_attribute("id"))
    for i in range(0, len(names_leagues)):
        names_leagues[i] = names_leagues[i].replace("g_1_", "")
    driver.close()
    driver.quit()
    print(names_leagues)
    # for url in names_leagues:
    #     get_stats(url)


def check_stat():
    # while True:
        parser()
        # time.sleep(20)


if __name__ == "__main__":
    check_stat()


# links = None
# matches_info = []
# links = get_listing('https://www.olx.com.pk/cars/')
#
# with Pool(10) as p:
#     records = p.map(parse, cars_links)
#
# if len(records) > 0:
#     with open('data_parallel.csv', 'a+') as f:
#         f.write('\n'.join(records))