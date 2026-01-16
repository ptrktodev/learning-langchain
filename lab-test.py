import os
import requests
from dotenv import load_dotenv
from rich.pretty import pprint
load_dotenv()

api_weather = os.getenv("WEATHER_API_KEY")
city = "toronto"

url = f"https://api.tomorrow.io/v4/weather/realtime?location={city}&apikey={api_weather}"
headers = {
    "accept": "application/json",
    "accept-encoding": "deflate, gzip, br"
}
response = requests.get(url, headers=headers)
pprint(response.json())
