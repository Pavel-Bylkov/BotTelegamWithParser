# pip install pyTelegramBotAPI
import socket

import telebot
from telebot import types

from env_secret import TOKEN, CHAT_ID


# Создаем экземпляр бота
bot = telebot.TeleBot(TOKEN)

active_users = {}

def gen_markup(list_btns):
    """Создает ряды кнопок по 4 в ряд"""
    n = len(list_btns)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if n > 4:
        markup.row_width = n // 2
        list_b = [types.KeyboardButton(btn) for btn in list_btns]
        half_list_b = list_b[:len(list_b) // 2 + 1]
        markup.add(*half_list_b)
        markup.add(*list_b[len(list_b) // 2 + 1:])
    else:
        markup.row_width = n
        list_b = [types.KeyboardButton(btn) for btn in list_btns]
        markup.add(*list_b)
    return markup


# Функция, обрабатывающая команду /start
@bot.message_handler(commands=["start", 'button'])
def start(m, res=False):
    print(m.chat.id, m.text)
    if str(m.chat.id) in CHAT_ID:
        bot.send_message(m.chat.id, 'Помощник готов к работе))')
    else:
        bot.send_message(m.chat.id, "Доступ к данному бот-сервису запрещен!")


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
