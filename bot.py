import os
import telebot
from telebot import types
import time
import threading
import weatherAPI
from dotenv import load_dotenv

load_dotenv()
print(os.getenv("BOT_TOKEN"))
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = telebot.TeleBot(BOT_TOKEN)
weather_info = {}
user_intervals = {}


@bot.message_handler(commands=["start"])
def start_bot(message):
    bot.send_message(message.chat.id, "Привет!")
    bot.send_message(message.chat.id, "Напиши название города для получения погоды")
    bot.send_message(message.chat.id, "Введите /help для получения информации")


@bot.message_handler(commands=["help"])
def help_bot(message):
    bot.send_message(
        message.chat.id,
        """Что бы установить город напишите его название в чат! 
Команды:
/weather - получить погоду на сейчас
/location - изменить город
/interval - изменить интервал""",
    )


@bot.message_handler(commands=["weather"])
def send_weather(message):
    chat_id = message.chat.id
    if chat_id in weather_info:
        info = weather_info[chat_id]
        weather_now = weatherAPI.weather(info["lat"], info["lon"])
        bot.send_message(
            message.chat.id, f'Сейчас в {info["city_name"]}: {weather_now} °C'
        )
    else:
        bot.send_message(message.chat.id, "Сначала напишите название города!")


@bot.message_handler(commands=["location"])
def new_location(message):
    chat_id = message.chat.id
    if chat_id in weather_info:
        msg = bot.send_message(chat_id, "Пришлите название нового города!")
        bot.register_next_step_handler(
            msg, lambda msg: update_weather_info(msg, chat_id)
        )
    else:
        bot.send_message(chat_id, "Город еще не установлен!")


@bot.message_handler(commands=["interval"])
def new_interval(message):
    chat_id = message.chat.id
    if chat_id in user_intervals:
        markup = types.ReplyKeyboardMarkup()
        btn1 = types.KeyboardButton("1 минута")
        btn2 = types.KeyboardButton("1 час")
        btn3 = types.KeyboardButton("3 часа")
        btn4 = types.KeyboardButton("6 часов")
        markup.add(btn1, btn2, btn3, btn4)
        msg = bot.send_message(chat_id, "Выберите новый интервал", reply_markup=markup)
        bot.register_next_step_handler(
            msg, lambda msg: update_interval_info(msg, chat_id)
        )
    else:
        bot.send_message(chat_id, "Интервал еще не установлен!")


@bot.message_handler(commands=["stop"])
def stop_notifications(message):
    chat_id = message.chat.id
    if chat_id in user_intervals:
        is_empty = user_intervals.pop(chat_id)

        msg = bot.send_message(chat_id, "Уведомления остановлены!")

    else:
        bot.send_message(chat_id, "Интервал еще не установлен!")


@bot.message_handler(
    func=lambda message: message.text in ["1 минута", "1 час", "3 часа", "6 часов"]
)
def set_interval(message):
    chat_id = message.chat.id
    interval = message.text
    if chat_id in user_intervals:
        bot.send_message(chat_id, "Интервал уже установлен")
    else:
        if interval == "1 минута":
            seconds = 60
        elif interval == "1 час":
            seconds = 3600
        elif interval == "3 часа":
            seconds = 10800
        elif interval == "6 часов":
            seconds = 21600
        user_intervals[chat_id] = seconds
        bot.send_message(
            chat_id,
            f"Интервал установлен: {interval}. Погода будет отправляться с этим интервалом.",
        )
        threading.Thread(target=send_weather_periodically, args=(chat_id,)).start()


@bot.message_handler(content_types=["text"])
def get_city(city):
    chat_id = city.chat.id
    if chat_id in weather_info:
        bot.send_message(chat_id, "Город уже установлен!")
    else:
        arr_res = weatherAPI.get_city_coordinates(str(city.text))
        if arr_res:
            weather_info[city.chat.id] = {
                "lat": arr_res[0],
                "lon": arr_res[1],
                "city_name": arr_res[2],
            }
            bot.send_message(
                city.chat.id,
                f"Город установлен. Теперь выберите интервал для получения погоды.",
            )

            markup = types.ReplyKeyboardMarkup()
            btn1 = types.KeyboardButton("1 минута")
            btn2 = types.KeyboardButton("1 час")
            btn3 = types.KeyboardButton("3 часа")
            btn4 = types.KeyboardButton("6 часов")
            markup.add(btn1, btn2, btn3, btn4)
            bot.send_message(city.chat.id, "Выберите интервал:", reply_markup=markup)
        else:
            bot.send_message(city.chat.id, "Город не найден!")
            bot.send_message(city.chat.id, "Введите корректный город!")


def update_interval_info(message, chat_id):
    print(user_intervals[chat_id])
    chat_id = message.chat.id
    interval = message.text
    if interval == "1 минута":
        seconds = 60
    elif interval == "1 час":
        seconds = 3600
    elif interval == "3 часа":
        seconds = 10800
    elif interval == "6 часов":
        seconds = 21600
    user_intervals[chat_id] = seconds
    bot.send_message(chat_id, "Интервал обновлен")
    threading.Thread(target=send_weather_periodically, args=(chat_id,)).start()
    print(user_intervals[chat_id])


def update_weather_info(message, chat_id):
    arr_res = weatherAPI.get_city_coordinates(str(message.text))
    if arr_res:
        weather_info[chat_id] = {
            "lat": arr_res[0],
            "lon": arr_res[1],
            "city_name": arr_res[2],
        }
        bot.send_message(chat_id, "Город обновлен")
    else:
        bot.send_message(chat_id, "Город не найден")


def send_weather_periodically(chat_id):
    while chat_id in user_intervals:
        if chat_id in weather_info:
            info = weather_info[chat_id]
            weather_now = weatherAPI.weather(info["lat"], info["lon"])
            bot.send_message(chat_id, f'Сейчас в {info["city_name"]}: {weather_now} °C')
        time.sleep(user_intervals[chat_id])


bot.polling(none_stop=True, interval=0)
