import time
from itertools import repeat
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from multiprocessing import Pool, Manager

from filter import filter_by_stat, filter_by_league
from bot_api import bot_send_message
from env_secret import STRICT_SELECTION

TIME_OUT_IN_CACHE = 90
TIME_OUT_IN_CACHE_NEAR = 5
BASE_URL = 'https://www.flashscore.com.ua'
MATCH_URL = 'https://www.flashscore.com.ua/match/{}/#/match-summary/match-statistics/0'
GOOD_MSG = '<a href="{}">Игра</a> из лиги {} полностью удовлетворяет условиям!'
GOOD_MSG2 = '<a href="{}">Игра</a> из лиги {} близко к условиям!'

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument('--ignore-certificate-errors-spki-list')
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36\
                        (KHTML, like Gecko) Chrome/106.0.0.0 YaBrowser/22.11.5.715 Yowser/2.5 Safari/537.36")


def update_cache(cache):
    key_for_del = []
    for match_id in cache:
        cache[match_id] -= 1
        if cache[match_id] <= 0:
            key_for_del.append(match_id)
    for key in key_for_del:
        del cache[key]


def msg_send(msg, id, cache):
    if "полностью" in msg:
        cache[id] = TIME_OUT_IN_CACHE
    else:
        cache[id + "temp"] = TIME_OUT_IN_CACHE_NEAR
    print(msg)
    return bot_send_message(msg)


def get_driver():
    driver = webdriver.Chrome(executable_path='chromedriver/chromedriver.exe', options=chrome_options)
    driver.maximize_window()
    driver.execute_cdp_cmd("Network.setCacheDisabled", {"cacheDisabled": True})
    return driver


def get_stats(id, cache):
    if id in cache:
        return {}
    driver = get_driver()
    url = MATCH_URL.format(id)
    try:
        driver.get(url)
        time.sleep(1)
        # print(url)
        t = driver.find_element(By.CLASS_NAME, 'tournamentHeader__country')
        t = t.text.split(" -")
        league = t[0]
        match_stat = {}
        if filter_by_league(league.lower()):
            print(league)
            for i in driver.find_elements(By.CLASS_NAME, 'detailScore__status'):
                if i.text == "ЗАВЕРШЕН":
                    print(i.text)
                    return {}
                if i.text == "ПЕРЕРЫВ":
                    match_stat['event_time'] = "45"
                else:
                    time_event = i.text.split("ТАЙМ")
                    print(time_event)
                    if ":" in time_event[1]:
                        time_event[1] = time_event[1].split(":")
                    elif "+" in time_event[1]:
                        time_event[1] = time_event[1].split("+")
                    match_stat['event_time'] = time_event[1][0]
                print(url)
                home = [i.text for i in driver.find_elements(By.CLASS_NAME, 'stat__homeValue')]
                away = [i.text for i in driver.find_elements(By.CLASS_NAME, 'stat__awayValue')]
                match_stat['possession'] = home[0][:2]
                match_stat['leader_shoot'] = home[1]
                match_stat['loser_shoot'] = away[1]
                match_stat['leader_shoot_on_target'] = home[2]
                match_stat['loser_shoot_on_target'] = away[2]
                x = filter_by_stat(match_stat)
                if all(x.values()):
                    return msg_send(GOOD_MSG.format(url, league), id, cache)
                team1 = {key: value for key, value in match_stat.items() if not x[key]}
                match_stat['possession'] = away[0][:2]
                match_stat['leader_shoot'] = away[1]
                match_stat['loser_shoot'] = home[1]
                match_stat['leader_shoot_on_target'] = away[2]
                match_stat['loser_shoot_on_target'] = home[2]
                y = filter_by_stat(match_stat)
                if all(y.values()):
                    return msg_send(GOOD_MSG.format(url, league), id, cache)
                team2 = {key: value for key, value in match_stat.items() if not y[key]}
                msg = GOOD_MSG2.format(url, league)
                if not STRICT_SELECTION and len(team1) == 1:
                    msg += '\nдля 1 команды не подходит ' + str(team1)
                if not STRICT_SELECTION and len(team2) == 1:
                    msg += '\nдля 2 команды не подходит ' + str(team2)
                if not STRICT_SELECTION and (len(team1) == 1 or len(team2) == 1):
                    if id + "temp" in cache:
                        return {}
                    return msg_send(msg, id, cache)
    except Exception as e:
        print("Error in get_stat:", e.__traceback__)
    finally:
        driver.close()
        driver.quit()
    return {}


def parser(url):
    driver: webdriver = get_driver()
    names_leagues = []
    try:
        driver.get(url)
        time.sleep(1)
        for i in driver.find_elements(By.CLASS_NAME, 'filters__tab'):
            if i.text == "LIVE":
                i.click()
                time.sleep(1)
                break
        # pageSource = driver.page_source
        # fileToWrite = open("page_source.html", "w", encoding="utf-8")
        # fileToWrite.write(pageSource)
        # fileToWrite.close()
        for i in driver.find_elements(By.CLASS_NAME, 'event__match'):
            id = i.get_attribute("id").replace("g_1_", "")
            names_leagues.append(id)
    except Exception as e:
        print("Error in parser:", e)
    finally:
        driver.close()
        driver.quit()
    print(names_leagues)
    return names_leagues


def check_stat():
    cache = {}
    start = time.time()
    while True:
        match_ids = parser(BASE_URL)
        with Manager() as manager:
            d = manager.dict(cache)
            with manager.Pool() as pool:
                pool.starmap(get_stats, zip(match_ids, repeat(d, len(match_ids))))
            cache = dict(d)
        time.sleep(20)
        if time.time() - start > 60:
            update_cache(cache)
            start = time.time()


if __name__ == "__main__":
    check_stat()
