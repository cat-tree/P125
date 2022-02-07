import pandas as pd
import json
import requests


def retrieve_climate_data(lat, lon, api_key):
    url = f"https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude=minutely&appid={api_key}&units=metric"
    response = requests.get(url)
    data = json.loads(response.text)
    # weather = pd.json_normalize(data)
    hourly = pd.json_normalize(data['hourly'])

    return hourly
