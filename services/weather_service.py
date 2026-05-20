import requests   #used to send internet requests to weather api
import os   #used to access environment variables
from dotenv import load_dotenv   #used to load hidden api keys from env file


load_dotenv()   #loads all variables from .env file


#gets weather api key from env file
API_KEY = os.getenv("WEATHER_API_KEY")


def get_weather(city):

    #this function receives city name from jarvis command
    #example:
    #get_weather("delhi")

    try:

        #this is the actual weather api url
        #q={city} inserts city name dynamically
        #appid sends our secret api key
        #units=metric gives temperature in celsius

        url = (
            f"https://api.openweathermap.org/data/2.5/weather?"
            f"q={city}&appid={API_KEY}&units=metric"
        )



        #requests.get() sends internet request to api server
        #api then returns live weather data

        response = requests.get(url)



        #converts api response into python dictionary/json format
        #so python can read values easily

        data = response.json()
        print(data)
        


        #if city name is wrong api sends error code
        #200 means success

        if data["cod"] != 200:
            return "I could not find that city."



        # ---------------- EXTRACTING WEATHER DATA ----------------

        #main contains temperature related information
        temperature = data["main"]["temp"]

        #feels like temperature
        feels_like = data["main"]["feels_like"]

        #humidity percentage
        humidity = data["main"]["humidity"]

        #weather condition text
        #weather is a list so [0] gets first item

        condition = data["weather"][0]["description"]



        #returns final sentence back to jarvis

        return (
            f"The current temperature in {city} is {temperature} degrees Celsius "
            f"with {condition}. "
            f"It feels like {feels_like} degrees "
            f"and humidity is {humidity} percent."
        )



    #if internet fails or api crashes this runs
    except:
        return "Weather service is currently unavailable."