import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

API_YANDEX_KEY = os.getenv("API_YANDEX_KEY")


def get_city_coordinates(city_name):
    file_path = "city.csv"
    data = pd.read_csv(file_path)
    city_data = data[data["city"].str.lower() == city_name.lower()]
    if not city_data.empty:
        geo_lat = city_data.iloc[0]["geo_lat"]
        geo_lon = city_data.iloc[0]["geo_lon"]
        return geo_lat, geo_lon, city_name
    else:
        return False


def weather(lat, lon):
    access_key = API_YANDEX_KEY
    headers = {"X-Yandex-API-Key": access_key}
    response = requests.get(
        f"https://api.weather.yandex.ru/v2/forecast?lat={lat}&lon={lon}",
        headers=headers,
    )
    data = response.json()
    current_weather = data["fact"]
    print("Текущая температура:", current_weather["temp"], "°C")
    return current_weather["temp"]
