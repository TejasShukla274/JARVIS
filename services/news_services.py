import requests   #used to send internet requests to news api
import os   #used to access environment variables
from dotenv import load_dotenv   #used to load api keys from .env file


load_dotenv()   #loads variables from .env


#gets news api key from environment variables
API_KEY = os.getenv("NEWS_API_KEY")


def get_news(category="general"):

    #this function fetches category based news
    #example:
    #get_news("sports")

    try:

        #news api endpoint
        #country=in gives indian headlines
        #category can be sports, business, technology etc

        url = (
            f"https://newsapi.org/v2/top-headlines?"
            f"country=in&category={category}&apiKey={API_KEY}"
        )



        #sends internet request to news api server
        response = requests.get(url)



        #converts api response into python dictionary/json
        data = response.json()

        print(data)



        #if api fails or key invalid
        if data["status"] != "ok":
            return "News service is currently unavailable."



        #extracts list of articles
        articles = data["articles"]



        #if no articles found
        if len(articles) == 0:
            return "No news articles were found."



        #stores headlines
        headlines = []



        #gets first headline only
        for article in articles[:1]:

            #gets article title
            title = article["title"]

            headlines.append(title)



        #creates final spoken response
        final_news = "Latest news. "



        #adds headlines
        for headline in headlines:

            final_news += f"{headline}. "



        return final_news



    #if internet or api crashes
    except Exception as e:

        print("NEWS ERROR:", e)

        return "Unable to fetch news right now."





def search_news(topic):

    #this function searches news based on custom topic
    #example:
    #search_news("artificial intelligence")

    try:

        #everything endpoint searches articles matching topic

        url = (
            f"https://newsapi.org/v2/everything?"
            f"q={topic}&sortBy=publishedAt&apiKey={API_KEY}"
        )



        #sends request to news api
        response = requests.get(url)



        #converts response into python dictionary/json
        data = response.json()

        print(data)



        #if api fails
        if data["status"] != "ok":
            return "Unable to fetch topic news right now."



        #extracts articles list
        articles = data["articles"]



        #if no articles found
        if len(articles) == 0:
            return f"No recent news was found about {topic}."



        #stores top headlines
        headlines = []



        #gets first headline only
        for article in articles[:1]:

            title = article["title"]

            headlines.append(title)



        #creates final response sentence
        final_news = f"Latest news about {topic}. "



        #adds headlines
        for headline in headlines:

            final_news += f"{headline}. "



        return final_news



    #if internet/api crashes
    except Exception as e:

        print("NEWS ERROR:", e)

        return "Topic news service is currently unavailable."