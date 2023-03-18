import os
from env_secret import ALLOW_ID, BAN_ID, ADMIN
from file_utils import write_to, read_from

allow_users = {}
ALLOW_FILENAME = "users_allow_list.json"
ban_users = {}
BAN_FILENAME = "users_ban_list.json"


def set_allow_users():
    allow_users.update(read_from(ALLOW_FILENAME))
    for id in ALLOW_ID:
        if str(id) not in allow_users:
            allow_users[str(id)] = {"id": id,
                                    "first_name": "",
                                    "last_name": "", "username": ""}
    if str(ADMIN) not in allow_users:
        allow_users[str(ADMIN)] = {"id": ADMIN,
                                   "first_name": "",
                                   "last_name": "", "username": ""}
    return os.path.getmtime(ALLOW_FILENAME)


def set_ban_users():
    ban_users.update(read_from(BAN_FILENAME))
    for id in BAN_ID:
        if str(id) not in ban_users:
            ban_users[str(id)] = {"id": id,
                                  "first_name": "",
                                  "last_name": "", "username": ""}
    return os.path.getmtime(BAN_FILENAME)


def add_user_to_allow(user):
    allow_users[str(user["id"])] = user
    write_to(ALLOW_FILENAME, allow_users)


def del_user_from_allow(user):
    if str(user["id"]) in allow_users:
        del allow_users[str(user["id"])]
        write_to(ALLOW_FILENAME, allow_users)


def add_user_to_ban(user):
    ban_users[str(user["id"])] = user
    write_to(BAN_FILENAME, allow_users)


def del_user_from_ban(user):
    if str(user["id"]) in ban_users:
        del ban_users[str(user["id"])]
        write_to(BAN_FILENAME, ban_users)


def update_allow():
    global last_access_allow, allow_users
    if last_access_allow != os.path.getmtime(ALLOW_FILENAME):
        allow_users = read_from(ALLOW_FILENAME)
        last_access_allow = os.path.getmtime(ALLOW_FILENAME)


last_access_allow = set_allow_users()
last_access_ban = set_ban_users()
