import time
import sys
import logging
import traceback

from itertools import repeat
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

from multiprocessing import Manager

from filter import filter_by_stat, filter_by_league
from bot_api import bot_send_message
from env_secret import STRICT_SELECTION

logging.basicConfig(filename="parser.log")
logger = logging.getLogger('Parser')

formatter = logging.Formatter(
    '%(asctime)s (%(filename)s:%(lineno)d %(threadName)s) %(levelname)s - %(name)s: "%(message)s"'
)

console_output_handler = logging.StreamHandler(sys.stderr)
console_output_handler.setFormatter(formatter)
logger.addHandler(console_output_handler)

logger.setLevel(logging.DEBUG)
logger_level = logging.DEBUG


TIME_OUT_IN_CACHE = 90
TIME_OUT_IN_CACHE_NEAR = 5
BASE_URL = 'https://www.flashscore.com.ua'
MATCH_URL = 'https://www.flashscore.com.ua/match/{}/#/match-summary/match-statistics/0'
GOOD_MSG = '<a href="{}">Игра</a> из лиги {} полностью удовлетворяет условиям!'
GOOD_MSG2 = '<a href="{}">Игра</a> из лиги {} близко к условиям!'
STAT_KEYS = {'event_time': "Время матча",
             'possession': "Владение мячом",
             'leader_shoot': "C большим владением удары",
             'loser_shoot': "С меньшим владением удары",
             'leader_shoot_on_target': "С большим владением удары в створ",
             'loser_shoot_on_target': "С меньшим владением удары в створ"}

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument('--ignore-certificate-errors-spki-list')
chrome_options.add_argument("--disable-gpu")
# chrome_options.add_argument("start-maximized")
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
    #  executable_path='chromedriver/chromedriver.exe'
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.maximize_window()
    driver.execute_cdp_cmd("Network.setCacheDisabled", {"cacheDisabled": True})
    return driver


def get_stats(id, cache):
    if id in cache:
        return {}
    driver = get_driver()
    url = MATCH_URL.format(id)
    debag_msg = ""
    try:
        driver.get(url)
        time.sleep(3)
        # print(url)
        t = driver.find_element(By.CLASS_NAME, 'tournamentHeader__country')
        t = t.text.split(" -")
        league = t[0]
        match_stat = {}
        if filter_by_league(league.lower()):
            debag_msg += f"{league}\n"
            for i in driver.find_elements(By.CLASS_NAME, 'detailScore__status'):
                if i.text == "ЗАВЕРШЕН":
                    print(debag_msg, i.text)
                    return {}
                if i.text == "ПЕРЕРЫВ":
                    match_stat['event_time'] = "45"
                else:
                    time_event = i.text.split("ТАЙМ")
                    debag_msg += f"{time_event}\n"
                    time_event[1] = time_event[1].strip("\n")
                    if ":" in time_event[1]:
                        time_event[1] = time_event[1].split(":")
                    elif "+" in time_event[1]:
                        time_event[1] = time_event[1].split("+")
                    match_stat['event_time'] = time_event[1][0]
                # debag_msg += f"{url}\n"
                home = [i.text for i in driver.find_elements(By.CLASS_NAME, 'stat__homeValue')]
                away = [i.text for i in driver.find_elements(By.CLASS_NAME, 'stat__awayValue')]
                # debag_msg += f"{"#"*20} Отладка статистики {"#"*20}\n"
                # debag_msg += f"{' '.join(home)}\n"
                # debag_msg += f"{' '.join(away)}\n"
                # debag_msg += f"{"#" * 20} Отладка статистики {"#" * 20}\n"
                start_index = 0 if "%" in home[0] else 1
                match_stat['possession'] = home[start_index][:home[start_index].find("%")]
                match_stat['leader_shoot'] = home[start_index + 1]
                match_stat['loser_shoot'] = away[start_index + 1]
                match_stat['leader_shoot_on_target'] = home[start_index + 2]
                match_stat['loser_shoot_on_target'] = away[start_index + 2]
                debag_msg += f"1 team:\n{match_stat}"
                x = filter_by_stat(match_stat)
                if all(x.values()):
                    print("GOOD RESULT:\n", debag_msg)
                    return msg_send(GOOD_MSG.format(url, league), id, cache)
                team1 = {key: value for key, value in match_stat.items() if not x[key] and key != 'possession'}
                match_stat['possession'] = away[start_index][:away[start_index].find("%")]
                match_stat['leader_shoot'] = away[start_index + 1]
                match_stat['loser_shoot'] = home[start_index + 1]
                match_stat['leader_shoot_on_target'] = away[start_index + 2]
                match_stat['loser_shoot_on_target'] = home[start_index + 2]
                debag_msg += f"2 team:\n{match_stat}"
                y = filter_by_stat(match_stat)
                if all(y.values()):
                    print("GOOD RESULT:\n", debag_msg)
                    return msg_send(GOOD_MSG.format(url, league), id, cache)
                team2 = {key: value for key, value in match_stat.items() if not y[key] and key != 'possession'}
                m = GOOD_MSG2.format(url, league)
                if not STRICT_SELECTION and len(team1) == 1:
                    m += f'\nдля 1 команды не подходит:\n {STAT_KEYS[list(team1.keys())[0]]} - {list(team1.values())[0]}'
                if not STRICT_SELECTION and len(team2) == 1:
                    m += f'\nдля 2 команды не подходит:\n {STAT_KEYS[list(team2.keys())[0]]} - {list(team2.values())[0]}'
                if not STRICT_SELECTION and (len(team1) == 1 or len(team2) == 1):
                    if id + "temp" in cache:
                        return {}
                    print("NEAR RESULT:\n", debag_msg)
                    return msg_send(m, id, cache)
                logger.debug(f"DEBAG INFO:\n {debag_msg}")
    except Exception as e:
        logger.error(f"DEBAG INFO:\n{debag_msg}\nError in get_stat: {e}")
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
        logger.error("Error in parser: %s", str(e))
    finally:
        driver.close()
        driver.quit()
    print(names_leagues)
    return names_leagues


def check_stat():
    cache = {}
    start = time.time()
    while True:
        try:
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
        except Exception as e:
            if logger_level and logger_level >= logging.ERROR:
                logger.error("Parser exception: %s", str(e))
            if logger_level and logger_level >= logging.DEBUG:
                logger.error("Exception traceback:\n%s", traceback.format_exc())
            time.sleep(5)
            continue
        if logger_level and logger_level >= logging.INFO:
            logger.error("Parser: loop exited")


if __name__ == "__main__":
    while True:
        try:
            check_stat()
        except Exception as e:
            if logger_level and logger_level >= logging.ERROR:
                logger.error("Parser exception: %s", str(e))
            if logger_level and logger_level >= logging.DEBUG:
                logger.error("Exception traceback:\n%s", traceback.format_exc())
            time.sleep(3)
            continue
        if logger_level and logger_level >= logging.INFO:
            logger.error("Parser: loop exited")
    if logger_level and logger_level >= logging.INFO:
        logger.error("Break parser")
