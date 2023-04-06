"""
Главный файл для подписки на бота и изменения
настроек в работе парсера через бота
"""
import os
import signal
import logging
import sys
import time

logging.basicConfig(filename="bot.log")

from io import BytesIO
from PIL import ImageGrab
import psutil

from filter import get_config_stat, LEAGUES_FILE, update_config

import telebot
from telebot import types

from env_secret import TOKEN
from users_permissions import *
from functools import wraps


logger = logging.getLogger('Bot')

formatter = logging.Formatter(
    '%(asctime)s (%(filename)s:%(lineno)d %(threadName)s) %(levelname)s - %(name)s: "%(message)s"'
)

console_output_handler = logging.StreamHandler(sys.stderr)
console_output_handler.setFormatter(formatter)
logger.addHandler(console_output_handler)

logger.setLevel(logging.DEBUG)
logger_level = logging.DEBUG



# Создаем экземпляр бота
bot = telebot.TeleBot(TOKEN)

users_for_allow = {}
admin_info = ""


def clean_send_message(func):
    """Костыльный декоратор для исключения повтора сообщений"""
    last = {"msg": "",
            "id": "",
            "result": None}

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            if last["id"] != str(args[0]) or last["msg"] != args[1]:
                last["result"] = func(*args, **kwargs)
                last["id"] = str(args[0])
                last["msg"] = args[1]
            else:
                print(f"WARNING! Попытка повторного сообщения:\n{args}\n{kwargs}")
        except Exception as e:
            print("Error in decorator clean_send_message:", e)
        return last["result"]

    return wrapper


bot.send_message = clean_send_message(bot.send_message)


def gen_markup_menu(list_btns):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    list_b = [types.KeyboardButton(btn) for btn in list_btns]
    markup.add(*list_b)
    return markup


def clear_markup():
    # для удаления кнопок
    return types.ReplyKeyboardRemove()


def main_menu(m):
    list_btns = ["Подписчики", "Настройки", "Статус", "Рестарт"]
    markup = gen_markup_menu(list_btns)
    bot.send_message(m.chat.id, 'Помощник готов к работе))', reply_markup=markup)
    bot.register_next_step_handler(m, main_menu_choices)


def main_menu_choices(m):
    query = {"статус": get_status, "подписчики": subscribes,
             "рестарт": restart_pars, "настройки": settings}
    try:
        query[m.text.lower()](m)
    except Exception as e:
        print(e)
        bot.send_message(m.chat.id, 'Неверный выбор, попробуй еще раз')
        main_menu(m)


def settings(m):
    list_btns = ["Список лиг", "Условия отбора", "Назад"]
    markup = gen_markup_menu(list_btns)
    bot.send_message(m.chat.id, 'Какие настройки интересуют?', reply_markup=markup)
    bot.register_next_step_handler(m, settings_actions)


def settings_actions(m):
    query = {"список лиг": league_menu, "условия отбора": config_menu, "назад": start}
    try:
        query[m.text.lower()](m)
    except Exception:
        bot.register_next_step_handler(m, settings_actions)


def league_menu(m):
    list_btns = ["Добавить", "Удалить", "Назад"]
    markup = gen_markup_menu(list_btns)
    msg = "Список лиг для отбора:\n"
    leagues = read_from(LEAGUES_FILE).split("\n")
    if leagues:
        leagues.sort()
        msg += "\n".join([f"{i} - {league}" for i, league in enumerate(leagues, 1)])
    else:
        msg = f"Ошибка чтения списка лиг"
    bot.send_message(m.chat.id, msg, reply_markup=markup)
    bot.register_next_step_handler(m, league_action)


def league_action(m):
    if m.text.lower() == "добавить":
        input_league(m)
    elif m.text.lower() == "удалить":
        choice_league(m)
    else:
        settings(m)


def input_league(m):
    markup = gen_markup_menu(["Назад"])
    msg = "Напиши название лиги в формате - Страна: Лига"
    bot.send_message(m.chat.id, msg, reply_markup=markup)
    bot.register_next_step_handler(m, add_league)


def add_league(m):
    if m.text.lower() == "назад":
        bot.send_message(m.chat.id, "Возврат")
    elif ":" not in m.text:
        bot.reply_to(m, "Не верный формат")
    else:
        leagues = read_from(LEAGUES_FILE).split("\n")
        leagues.append(m.text)
        leagues.sort()
        write_to(LEAGUES_FILE, "\n".join(leagues))
        bot.send_message(m.chat.id, m.text + " добавлена")
    bot.register_next_step_handler(m, league_menu)


def choice_league(m):
    msg = "Укажите номер строки списка лиг для удаления или нажмите Назад:"
    list_btns = ["Назад"]
    markup = gen_markup_menu(list_btns)
    bot.send_message(m.chat.id, msg, reply_markup=markup)
    bot.register_next_step_handler(m, del_league)


def del_league(m):
    if m.text.lower() == "назад":
        bot.send_message(m.chat.id, "Возврат")
    elif not str(m.text).isdigit():
        bot.send_message(m.chat.id, f"{m.text} - не верный формат ввода")
    else:
        i = int(m.text) - 1
        leagues = read_from(LEAGUES_FILE).split("\n")
        if leagues and 0 <= i < len(leagues):
            leagues.sort()
            league = leagues.pop(i)
            write_to(LEAGUES_FILE, "\n".join(leagues))
            bot.send_message(m.chat.id, league + " удалена")
        else:
            bot.send_message(m.chat.id, f"{m.text} не удалена")
    bot.register_next_step_handler(m, league_menu)


def config_menu(m):
    match_stat = {'event_time': "Время матча",
                  'possession': "Владение мячом",
                  'leader_shoot': "C большим владением удары",
                  'loser_shoot': "С меньшим владением удары",
                  'leader_shoot_on_target': "С большим владением удары в створ",
                  'loser_shoot_on_target': "С меньшим владением удары в створ"}
    msg = "Настройки окружения env_secret.py:\n"
    msg += read_from("env_secret.py")
    bot.send_message(m.chat.id, msg)
    config = get_config_stat()
    for key in match_stat:
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("Изменить", callback_data="edit_" + key)
        markup.row(btn1)
        bot.send_message(ADMIN, f"{match_stat[key]}: {config[key]}", reply_markup=markup)
    settings(m)


def change_conf(key, m):
    print("change conf for", key, "to", m.text)
    match_stat = {'event_time': "Время матча",
                  'possession': "Владение мячом",
                  'leader_shoot': "C большим владением удары",
                  'loser_shoot': "С меньшим владением удары",
                  'leader_shoot_on_target': "С большим владением удары в створ",
                  'loser_shoot_on_target': "С меньшим владением удары в створ"}
    markup = gen_markup_menu(["Назад"])
    if update_config(key, m.text):
        msg = f"Новое значение для {match_stat[key]} записано"
    else:
        msg = f"Неверный формат значения для {match_stat[key]}"
    bot.reply_to(m, msg, reply_markup=markup)


def _get_parser_proc_info():
    pids = []
    for proc in psutil.process_iter():
        try:
            pinfo = proc.as_dict(attrs=['cmdline', 'pid', 'name', 'open_files', 'status'])
        except psutil.NoSuchProcess:
            pass
        else:
            if pinfo['name'] == "python.exe" and 'parser.py' in pinfo['cmdline']:
                pids.append(pinfo['pid'])
    if pids:
        return pids, "running"
    return None, "stopped"


def get_status(m):
    pid, status = _get_parser_proc_info()
    try:
        bio = BytesIO()
        bio.name = 'screenshot.png'
        myScreenshot = ImageGrab.grab(all_screens=True)
        myScreenshot.save(bio, 'PNG')
        bio.seek(0)
        bot.send_photo(m.chat.id, photo=bio)
    except Exception as e:
        print(e)
    bot.send_message(m.chat.id, f'Статус парсера: {status}')
    main_menu(m)


def restart_pars(m):
    pid, status = _get_parser_proc_info()
    try:
        if pid is not None:
            tmp_pid = pid[:]
            while tmp_pid:
                os.kill(tmp_pid.pop(), signal.SIGTERM)  # CTRL_C_EVENT or SIGTERM
            bot.send_message(m.chat.id, 'Перезапуск парсера...')
            time.sleep(4)
            pid2, status = _get_parser_proc_info()
            if pid2 is not None and pid != pid2:
                bot.send_message(m.chat.id, 'Парсер перезапущен!')
            else:
                bot.send_message(m.chat.id, 'Проблемы на сервере, парсер не перезапустился.')
        else:
            bot.send_message(m.chat.id, 'Проблемы на сервере, не найден PID процесса парсера.')
    except Exception as e:
        print(e)
        if logger_level and logger_level >= logging.ERROR:
            logger.error("Parser restart exception: %s", str(e))
    main_menu(m)


def subscribes(m):
    list_btns = ["Удалить", "Назад"]
    markup = gen_markup_menu(list_btns)
    subs = "Список подписчиков:\n"
    if data := read_from(ALLOW_FILENAME):
        data = sorted(data.values(), key=lambda user: int(user["id"]))
        subs += "\n".join([f"{i} - {user}" for i, user in enumerate(data, 1)])
    bot.send_message(m.chat.id, subs, reply_markup=markup)
    bot.register_next_step_handler(m, subscribes_action)


def subscribes_action(m):
    if m.text.lower() == "удалить":
        choice_allow_user(m)
    else:
        main_menu(m)


def choice_allow_user(m):
    msg = "Укажите номер строки подписчика для удаления или нажмите Назад:"
    list_btns = ["Назад"]
    markup = gen_markup_menu(list_btns)
    bot.send_message(m.chat.id, msg, reply_markup=markup)
    bot.register_next_step_handler(m, del_allow_user)


def del_allow_user(m):
    if m.text.lower() == "назад":
        bot.send_message(m.chat.id, "Возврат")
    elif not str(m.text).isdigit():
        bot.send_message(m.chat.id, f"{m.text} - не верный формат ввода")
    else:
        i = int(m.text) - 1
        data = read_from(ALLOW_FILENAME)
        if data and 0 <= i < len(data):
            id = sorted(data.values(), key=lambda user: int(user["id"]))[i]["id"]
            del_user_from_allow(user := data[str(id)])
            bot.send_message(m.chat.id, f"{user} удален")
        else:
            bot.send_message(m.chat.id, f"{m.text} подписчик не удален, проверьте номер строки")
    bot.register_next_step_handler(m, subscribes)


# Функция, обрабатывающая команду /start
@bot.message_handler(commands=["start", 'button'])
def start(m, res=False):
    global admin_info
    print(m.chat.id, m.text)
    if str(m.chat.id) == ADMIN:
        admin_info = f"@{m.from_user.username} - {m.from_user.first_name} {m.from_user.last_name}"
        print(admin_info)
        add_user_to_allow({"id": m.from_user.id,
                           "first_name": m.from_user.first_name,
                           "last_name": m.from_user.last_name,
                           "username": m.from_user.username})
        main_menu(m)
    elif str(m.chat.id) not in allow_users and str(m.chat.id) not in ban_users:
        bot.send_message(m.chat.id, f"Ваш запрос на подписку рассматривается администратором {admin_info}.")
        user = {"id": m.from_user.id,
                "first_name": m.from_user.first_name,
                "last_name": m.from_user.last_name,
                "username": m.from_user.username}
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("В подписчики", callback_data="allow")
        btn2 = types.InlineKeyboardButton("В БАН", callback_data="ban")
        markup.row(btn1, btn2)
        msg = bot.send_message(ADMIN, f"Новый запрос на подписку от {user}", reply_markup=markup)
        users_for_allow[msg.id] = user
    elif str(m.chat.id) in allow_users:
        bot.send_message(m.chat.id, "Добро пожаловать, подписчик. Буду оповещать об интересных матчах.")
    else:
        bot.send_message(m.chat.id, "Доступ к сервису запрещен.")


@bot.callback_query_handler(func=lambda callback: True)
def callback_query_handler(callback):
    query = {
        'edit_event_time': lambda m: change_conf("event_time", m),
        'edit_possession': lambda m: change_conf("possession", m),
        'edit_leader_shoot': lambda m: change_conf("leader_shoot", m),
        'edit_loser_shoot': lambda m: change_conf("loser_shoot", m),
        'edit_leader_shoot_on_target': lambda m: change_conf("leader_shoot_on_target", m),
        'edit_loser_shoot_on_target': lambda m: change_conf("loser_shoot_on_target", m)}
    if callback.data in query:
        msg = 'Напиши новое значение (примеры: >5 | <=3 | ==3 | 20-30)'
        bot.reply_to(callback.message, msg, reply_markup=clear_markup())
        bot.register_next_step_handler_by_chat_id(int(ADMIN), query[callback.data])
    else:
        msg_id = callback.message.message_id
        try:
            user = users_for_allow[msg_id]
            if callback.data == "allow":
                add_user_to_allow(user)
                bot.send_message(user["id"], "Поздравляю! Вас добавили в подписчики.")
            elif callback.data == "ban":
                add_user_to_ban(user)
                bot.send_message(user["id"], "К сожалению, доступ к сервису для вас заблокирован.")
            del users_for_allow[msg_id]
            m = f'{user} добавлен в список'
        except Exception as e:
            print("Error in callback_query_handler:", e)
            m = "Что-то пошло не так, необходимо новому подписчику повторно отправить команду /start"
        bot.send_message(ADMIN, m)


# Получение сообщений не из меню
@bot.message_handler(content_types=["text"])
def message_reply(m):
    print(m.chat.id, m.text)
    if str(m.chat.id) == ADMIN:
        bot.reply_to(m, "Команда не распознана")
        bot.register_next_step_handler(m, main_menu)
    elif str(m.chat.id) in allow_users:
        msg = f"По всем вопросам свяжитесь с админом - {admin_info}"
        bot.send_message(m.chat.id, msg)
    else:
        msg = "Доступ к данному бот-сервису запрещен!"
        bot.send_message(m.chat.id, msg,
                         reply_markup=clear_markup())


# Запускаем бота
bot.infinity_polling()
