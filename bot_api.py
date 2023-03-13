import requests
import urllib.parse
from env_secret import TOKEN, CHAT_ID


def bot_send_message(msg, chat_id=CHAT_ID, parse_mode='html'):
    msg = urllib.parse.quote(msg)
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={chat_id}&text={msg}&parse_mode={parse_mode}"
    return requests.get(url).json()


if __name__ == "__main__":
    url = "https://www.flashscore.com.ua/match/OphEJZ1i/#/match-summary/match-summary"
    bot_send_message(
        f'<a href="{url}">Игра</a> полностью удовлетворяет условиям!')
