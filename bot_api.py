import requests
import urllib.parse
from env_secret import CHAT_ID, TOKEN


def bot_send_message(msg, parse_mode='html'):
    msg = urllib.parse.quote(msg)
    result = []
    for chat_id in CHAT_ID:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={chat_id}&text={msg}&parse_mode={parse_mode}"
        result.append(requests.get(url).json())
    return result


if __name__ == "__main__":
    url = "https://www.flashscore.com.ua/match/OphEJZ1i/#/match-summary/match-summary"
    bot_send_message(
        f'Test <a href="{url}">Игра</a> полностью удовлетворяет условиям!')
    # url = f"https://api.telegram.org/bot{TOKEN}/getMe"
    # print(requests.get(url).json())
