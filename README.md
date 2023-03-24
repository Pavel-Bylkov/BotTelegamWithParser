# BotTelegamWithParser
Telebot + parser


# Настройка перед запуском

Установить необходимые библиотеки из requirements.txt

pip install -r requirements.txt


Создать папку chromedriver и скачать в нее версию соответствующую установленному Chrome

можно отсюда https://chromedriver.storage.googleapis.com/index.html

перед запуском нужно создать файл env_secret.py с переменными

TOKEN = "ваш токен" - взять у @BotFather

ADMIN = "ваш telegram ID"  - можно узнать через @IDBot

ALLOW_ID = []  - можно добавить подписчиков

BAN_ID = [] - можно добавить заблоченных пользователей

STRICT_SELECTION = False  - Строгий отбор - True


# Запуск бота

Для оптимизации и простоты принято решение разделить парсинг + оповещение и функционал бота по настройке парсинга.

Запускать необходимо два файла - bot.py и parser.py параллельно.

Они работают независимо друг от друга - синхронизация происходит через файлы конфигов.
