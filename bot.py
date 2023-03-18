# pip install pyTelegramBotAPI

from create_config import CONFIG_FILE, LEAGUES_FILE

import telebot
from telebot import types

from env_secret import TOKEN
from users_permissions import *

# Создаем экземпляр бота
bot = telebot.TeleBot(TOKEN)

users_for_allow = {}
admin_info = ""


def gen_markup_menu(list_btns):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    list_b = [types.KeyboardButton(btn) for btn in list_btns]
    markup.add(*list_b)
    return markup


def clear_markup():
    # для удаления кнопок
    return types.ReplyKeyboardRemove()


def main_menu(m):
    list_btns = ["Статус", "Подписчики", "Рестарт", "Настройки"]
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
        bot.register_next_step_handler(m, main_menu_choices)


def settings(m):
    list_btns = ["Список лиг", "Время матча", "Владение", "Удары", "Назад"]
    markup = gen_markup_menu(list_btns)
    bot.send_message(m.chat.id, 'Какие настройки интересуют?', reply_markup=markup)
    bot.register_next_step_handler(m, settings_actions)


def settings_actions(m):
    query = {"список лиг": league_menu, "время матча": time_event,
             "владение": passion, "удары": shoot_menu, "назад": start}
    try:
        query[m.text.lower()](m)
    except Exception as e:
        print(e)
        bot.send_message(m.chat.id, 'Неверный выбор, попробуй еще раз')
        bot.register_next_step_handler(m, settings_actions)


def league_menu(m):
    list_btns = ["Добавить", "Удалить", "Назад"]
    markup = gen_markup_menu(list_btns)
    leagues = "Список лиг для отбора:\n"
    if data := read_from(LEAGUES_FILE):
        leagues += "\n".join([f"{i} - {league}" for i, league in enumerate(leagues, 1)])
    else:
        leagues = f"Ошибка чтения списка лиг"
    bot.send_message(m.chat.id, leagues, reply_markup=markup)
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
    bot.send_message(m.chat.id, msg)
    leagues = read_from(LEAGUES_FILE).split("\n")
    if leagues:
        leagues.sort()
        msg = "\n".join([f"{i} - {league}" for i, league in enumerate(leagues, 1)])
    else:
        print(f"Ошибка чтения списка лиг")
        msg = "Ошибка чтения списка лиг"
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


def shoot_menu(m):
    bot.send_message(m.chat.id, 'Функция в разработке...')


def time_event(m):
    bot.send_message(m.chat.id, 'Функция в разработке...')


def passion(m):
    bot.send_message(m.chat.id, 'Функция в разработке...')


def get_status(m):
    bot.send_message(m.chat.id, 'Функция в разработке...')


def restart_pars(m):
    bot.send_message(m.chat.id, 'Функция в разработке...')


def subscribes(m):
    list_btns = ["Удалить", "Назад"]
    markup = gen_markup_menu(list_btns)
    subs = "Список подписчиков:\n"
    if data := read_from(ALLOW_FILENAME):
        subs += "\n".join([f"{i} - {user}" for i, user in enumerate(data.values(), 1)])
    bot.send_message(m.chat.id, subs, reply_markup=markup)
    bot.register_next_step_handler(m, subscribes_action)

def subscribes_action(m):
    if m.text.lower() == "удалить":
        choice_league(m)
    else:
        settings(m)

# Функция, обрабатывающая команду /start
@bot.message_handler(commands=["start", 'button'])
def start(m, res=False):
    global admin_info
    print(m.chat.id, m.text)
    if str(m.chat.id) == ADMIN:
        admin_info = f"@{m.from_user.username} - {m.from_user.first_name} {m.from_user.last_name}"
        print(admin_info)
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
        # bot.register_next_step_handler_by_chat_id(ADMIN, permission)
    elif str(m.chat.id) in allow_users:
        bot.send_message(m.chat.id, "Добро пожаловать, подписчик. Буду оповещать об интересных матчах.")
    else:
        bot.send_message(m.chat.id, "Доступ к сервису запрещен.")


@bot.callback_query_handler(func=lambda callback: True)
def permission(callback):
    msg_id = callback.message.message_id - 1
    if callback.data == "allow":
        add_user_to_allow(users_for_allow[msg_id])
        del users_for_allow[msg_id]
    elif callback.data == "ban":
        add_user_to_ban(users_for_allow[msg_id])
        del users_for_allow[msg_id]


# Получение сообщений не из меню
@bot.message_handler(content_types=["text"])
def message_reply(m):
    print(m.chat.id, m.text)
    if str(m.chat.id) == ADMIN:
        bot.reply_to(m, "Команда не распознана")
        bot.register_next_step_handler(m, main_menu)
    if str(m.chat.id) in allow_users:
        msg = f"По всем вопросам свяжитесь с админом - {admin_info}"
        bot.send_message(m.chat.id, msg)
    else:
        msg = "Доступ к данному бот-сервису запрещен!"
        bot.send_message(m.chat.id, msg,
                         reply_markup=clear_markup())


# Запускаем бота
bot.infinity_polling()
