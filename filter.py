import os
import sys

from yaml import safe_load, YAMLError

from create_config import create_config_file, CONFIG_FILE, LEAGUES_FILE, create_file_leagues

if not os.path.exists(CONFIG_FILE):
    create_config_file()
last_access = None
data = None

if not os.path.exists(LEAGUES_FILE):
    create_file_leagues()
last_access_league = None
leagues = None

def check_leagues():
    global last_access_league, leagues
    if last_access_league != os.path.getmtime(LEAGUES_FILE):
        with open(LEAGUES_FILE, 'r') as f:
            leagues = f.read().lower().split("\n")
            # print(*leagues, sep="\n")
        last_access_league = os.path.getmtime(LEAGUES_FILE)

def check_config():
    global last_access, data
    if last_access != os.path.getmtime(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            try:
                data = safe_load(f)
                # print(data['event_time'])
                # print(data['possession'])
                # print(data['leader_shoot'])
                # print(data['loser_shoot'])
                # print(data['leader_shoot_on_target'])
                # print(data['loser_shoot_on_target'])
            except YAMLError as exc:
                print(exc)
        last_access = os.path.getmtime(CONFIG_FILE)


def compare(elem, conf):
    if "-" in conf:
        min_, max_ = conf.split("-")
        return float(min_) <= float(elem) <= float(max_)
    elif ">" in conf or "<" in conf or "==" in conf:
        try:
            return eval(str(elem) + conf)
        except Exception as e:
            print("Error in compare:", e)
            raise Exception(f"Error in compare: {e}")
    raise Exception(f"Error in compare: don't made with {elem} and {conf}")


def filter_by_stat(match_stat):
    check_config()
    if data is not None:
        return {key: compare(match_stat[key], value)
                for key, value in data.items()}
    raise Exception("Error in filter: don't have config parameters")


def filter_by_league(league):
    check_leagues()
    if leagues is not None:
        return league in leagues
    raise Exception("Error in filter: don't have leagues list")


if __name__ == "__main__":
    match_stat = {'event_time': 27,
                  'possession': 61,
                  'leader_shoot': 5,
                  'loser_shoot': 2,
                  'leader_shoot_on_target': 3,
                  'loser_shoot_on_target': 0}
    x = filter_by_stat(match_stat)
    print("YES" if all(x.values()) else "NO" + str(x))
