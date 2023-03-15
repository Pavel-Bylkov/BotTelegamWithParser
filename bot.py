# pip install pyTelegramBotAPI
from yaml import safe_load, YAMLError, safe_dump

from create_config import CONFIG_FILE, LEAGUES_FILE


import telebot
from telebot import types

from env_secret import TOKEN, CHAT_ID

# Создаем экземпляр бота
bot = telebot.TeleBot(TOKEN)

active_users = {}


def gen_markup_menu():
    """Создает ряды кнопок по 4 в ряд"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    list_btns = ["Статус", "Подписчики", "Рестарт", "Настройки"]
    list_b = [types.KeyboardButton(btn) for btn in list_btns]
    markup.add(*list_b)
    return markup


# Функция, обрабатывающая команду /start
@bot.message_handler(commands=["start", 'button'])
def start(m, res=False):
    print(m.chat.id, m.text)
    if str(m.chat.id) in CHAT_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        list_btns = ["Статус", "Подписчики", "Рестарт", "Настройки"]
        list_b = [types.KeyboardButton(btn) for btn in list_btns]
        markup.add(*list_b)
        bot.send_message(m.chat.id, 'Помощник готов к работе))', reply_markup=markup)
        bot.register_next_step_handler(m, main_menu_choices)
    else:
        bot.send_message(m.chat.id, "Доступ к данному бот-сервису запрещен!")


def main_menu_choices(m):
    query = {"статус": get_status,
             "подписчики": subscribes,
             "рестарт": restart_pars,
             "настройки": settings}
    try:
        query[m.text.lower()](m)
    except Exception as e:
        print(e)
        bot.send_message(m.chat.id, 'Неверный выбор, попробуй еще раз')
        bot.register_next_step_handler(m, main_menu_choices)


def settings(m):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    list_btns = ["Список лиг", "Время матча", "Владение", "Удары", "Назад"]
    list_b = [types.KeyboardButton(btn) for btn in list_btns]
    markup.add(*list_b)
    bot.send_message(m.chat.id, 'Какие настройки интересуют?', reply_markup=markup)
    bot.register_next_step_handler(m, settings_actions)


def settings_actions(m):
    query = {"список лиг": league_menu,
             "время матча": time_event,
             "владение": passion,
             "удары": shot_menu,
             "назад": start}
    try:
        query[m.text.lower()](m)
    except Exception as e:
        print(e)
        bot.send_message(m.chat.id, 'Неверный выбор, попробуй еще раз')
        bot.register_next_step_handler(m, settings_actions)


def league_menu(m):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    list_btns = ["Добавить", "Удалить", "Назад"]
    list_b = [types.KeyboardButton(btn) for btn in list_btns]
    markup.add(*list_b)
    try:
        with open(LEAGUES_FILE, 'r') as f:
            leagues = f.read()
    except Exception as e:
        leagues = f"Ошибка чтения списка лиг - {e}"
    bot.send_message(m.chat.id, leagues, reply_markup=markup)
    bot.register_next_step_handler(m, league_action)

def league_action(m):
    query = {"добавить": input_league,
             "удалить": choice_league,
             "назад": settings}
    try:
        query[m.text.lower()](m)
    except Exception as e:
        print(e)
        bot.send_message(m.chat.id, 'Неверный выбор, попробуй еще раз')
        bot.register_next_step_handler(m, league_action)

def input_league(m):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    list_btns = ["Назад"]
    list_b = [types.KeyboardButton(btn) for btn in list_btns]
    markup.add(*list_b)
    bot.send_message(m.chat.id, "Напиши название лиги в формате - Страна: Лига", reply_markup=markup)
    bot.register_next_step_handler(m, add_league)

def add_league(m):
    if m.text.lower() == "назад":
        bot.send_message(m.chat.id, "Возврат")
    else:
        try:
            with open(LEAGUES_FILE, 'r') as f:
                leagues = f.read().split("\n")
            leagues.append(m.text)
            leagues.sort()
            with open(LEAGUES_FILE, "w") as f:
                f.write("\n".join(leagues))
            bot.send_message(m.chat.id, m.text + " добавлена")
        except Exception as e:
            print(f"Ошибка чтения списка лиг - {e}")
            bot.send_message(m.chat.id, f"{m.text} не добавлена, ошибка {e}")
    bot.register_next_step_handler(m, league_menu)


def choice_league(m):
    msg = "Укажите номер строки списка лиг для удаления или нажмите Назад:"
    bot.send_message(m.chat.id, msg)
    try:
        with open(LEAGUES_FILE, 'r') as f:
            leagues = f.read().split("\n")
        leagues.sort()
        msg = "\n".join([f"{i} - {league}" for i, league in enumerate(leagues, 1)])
        bot.send_message(m.chat.id, msg)
    except Exception as e:
        print(f"Ошибка чтения списка лиг - {e}")
        bot.send_message(m.chat.id, f"Ошибка {e}")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    list_btns = ["Назад"]
    list_b = [types.KeyboardButton(btn) for btn in list_btns]
    markup.add(*list_b)
    bot.send_message(m.chat.id, "Напиши название лиги в формате - Страна: Лига", reply_markup=markup)
    bot.register_next_step_handler(m, del_league)


def del_league(m):
    if m.text.lower() == "назад":
        bot.send_message(m.chat.id, "Возврат")
    elif not str(m.text).isdigit():
        bot.send_message(m.chat.id, f"{m.text} - не верный формат ввода")
    else:
        try:
            with open(LEAGUES_FILE, 'r') as f:
                leagues = f.read().split("\n")
            leagues.sort()
            league = leagues.pop(int(m.text) - 1)
            with open(LEAGUES_FILE, "w") as f:
                f.write("\n".join(leagues))
            bot.send_message(m.chat.id, league + " удалена")
        except Exception as e:
            print(f"Ошибка чтения списка лиг - {e}")
            bot.send_message(m.chat.id, f"{m.text} не удалена, ошибка {e}")
    bot.register_next_step_handler(m, league_menu)


def shot_menu(m):
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
    bot.send_message(m.chat.id, 'Функция в разработке...')


# Получение сообщений от юзера
@bot.message_handler(content_types=["text"])
def message_reply(message):
    print(message.chat.id, message.text)
    if str(message.chat.id) in CHAT_ID:
        bot.send_message(message.chat.id, message.text)
    else:
        msg = "Доступ к данному бот-сервису запрещен!"
        # для удаления кнопок
        reply_markup = types.ReplyKeyboardRemove()
        bot.send_message(message.chat.id, msg, reply_markup=reply_markup)


# Запускаем бота
# bot.polling(none_stop=True, timeout=123)
bot.infinity_polling()
