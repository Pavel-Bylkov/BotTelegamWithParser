import requests
import urllib.parse
from env_secret import TOKEN
from users_permissions import allow_users, update_allow

def bot_send_message(msg, parse_mode='html'):
    msg = urllib.parse.quote(msg)
    result = []
    update_allow()
    for chat_id in allow_users:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={chat_id}&text={msg}&parse_mode={parse_mode}"
        result.append(requests.get(url).json())
    return result


if __name__ == "__main__":
    url = "https://www.flashscore.com.ua/match/OphEJZ1i/#/match-summary/match-summary"
    bot_send_message(
        f'Test <a href="{url}">Игра</a> полностью удовлетворяет условиям!')
    # url = f"https://api.telegram.org/bot{TOKEN}/getMe"
    # print(requests.get(url).json())
