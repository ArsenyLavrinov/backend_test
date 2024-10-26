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
    if message.chat.id in weather_info:
        weather_info.pop(message.chat.id)

    if message.chat.id in user_intervals:
        user_intervals.pop(message.chat.id)

    bot.send_message(message.chat.id, "Привет!")
    get_city_msg = bot.send_message(
        message.chat.id, "Напиши название города для получения погоды"
    )
    bot.register_next_step_handler(get_city_msg, lambda msg: new_location(msg))
    bot.send_message(message.chat.id, "Введите /help для получения информации")


@bot.message_handler(commands=["help"])
def help_bot(message):
    bot.send_message(
        message.chat.id,
        """Что бы установить город напишите его название в чат! 
Команды:
/weather - получить погоду на сейчас
/location - изменить город
/interval - изменить интервал
/stop - остановить уведомления

""",
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
        msg = bot.send_message(chat_id, "Пришлите название города!")
        bot.register_next_step_handler(
            msg, lambda msg: update_weather_info(msg, chat_id)
        )


@bot.message_handler(commands=["interval"])
def new_interval(message):
    chat_id = message.chat.id
    if chat_id in user_intervals:
        markup = create_interval_keyboard()
        msg = bot.send_message(chat_id, "Выберите новый интервал", reply_markup=markup)
        bot.register_next_step_handler(
            msg, lambda msg: update_interval_info(msg, chat_id)
        )
    else:
        markup = create_interval_keyboard()
        msg = bot.send_message(chat_id, "Выберите интервал", reply_markup=markup)
        bot.register_next_step_handler(
            msg, lambda msg: update_interval_info(msg, chat_id)
        )


@bot.message_handler(commands=["stop"])
def stop_notifications(message):
    chat_id = message.chat.id
    if chat_id in user_intervals:
        user_intervals.pop(chat_id)
        weather_info.pop(chat_id)
        bot.send_message(chat_id, "Уведомления остановлены!")

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

            markup = create_interval_keyboard()
            bot.send_message(city.chat.id, "Выберите интервал:", reply_markup=markup)
        else:
            bot.send_message(city.chat.id, "Город не найден!")
            bot.send_message(city.chat.id, "Введите корректный город!")


def update_interval_info(message, chat_id):
    print(user_intervals[chat_id])
    # chat_id = message.chat.id
    interval = message.text
    isSuccess = True
    seconds = 3600
    if interval == "1 минута":
        seconds = 60
    elif interval == "1 час":
        seconds = 3600
    elif interval == "3 часа":
        seconds = 10800
    elif interval == "6 часов":
        seconds = 21600
    else:

        isSuccess = False

    user_intervals[chat_id] = seconds
    if isSuccess:
        bot.send_message(chat_id, "Интервал обновлен")
    else:
        bot.send_message(
            chat_id,
            "Введено некорректное значение интервала! Интервал установлен на 1 час",
        )
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


def create_interval_keyboard():
    markup = types.ReplyKeyboardMarkup()
    intervals = ["1 минута", "1 час", "3 часа", "6 часов"]
    for interval in intervals:
        markup.add(types.KeyboardButton(interval))
    return markup


bot.polling(none_stop=True, interval=0)
