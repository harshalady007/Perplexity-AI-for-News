import trafilatura
import requests
from fastapi import FastAPI
from urllib.parse import urlparse
import google.generativeai as genai
import os
from dotenv import load_dotenv
load_dotenv()

NEWS_API_KEY = os.getenv("NEWS_API_KEY")

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')
app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Welcome to the News AI API"}

@app.get("/headlines")
def headlines():
    url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={NEWS_API_KEY}"
    response = requests.get(url)
    return response.json()
    

def extraction(article):
    downloaded = trafilatura.fetch_url(article)
    return trafilatura.extract(downloaded)

def summarize_text(out):
    response = model.generate_content(f"summarize the whole {out} in 100 words")
    return response

@app.get("/summarize")
def summarize(article: str):
    out = extraction(article)
    sum_out = summarize_text(out)
    return {'summary': sum_out.text}
article = "https://www.bbc.com/news/articles/c620ykrxedwo"
summary = summarize(article)

@app.get("/everything")
def fetch_articles_for_topic(topic):
    apiKey = NEWS_API_KEY
    url = f"https://newsapi.org/v2/everything?country=us&apiKey={NEWS_API_KEY}&q={topic}"
    response = requests.get(url)
    response.json()['articles'].sort(key=lambda articles: articles['publishedAt'])
    return response.json()

@app.get("/timeline")
def timeline(topic: str):
    # 1. Fetch and sort the articles
    data = fetch_articles_for_topic(topic)
    articles = data.get('articles', [])
    if not articles:
        return {"timeline": []} # Return empty if no articles found

    articles.sort(key=lambda x: x['publishedAt'])

    # 2. Create a clean context string for the AI
    context = ""
    for article in articles:
        title = article.get('title', '')
        description = article.get('description', '')
        if title and description:
            context += f"Title: {title}\nDescription: {description}\n\n"
    
    # 3. Create the prompt and call Gemini
    prompt = f"Based on the following news articles, create a timeline of the top 5 key events. For each event, provide the date and a single, concise sentence. Format the output as a JSON object with a key called 'timeline', which is a list of events. Each event should have 'date' and 'event' keys. Here is the context from the articles:\n\n{context}"
    
    response = model.generate_content(prompt)
    
    # 4. Return the AI's response
    return {"timeline": response.text}

bias_map = {'cnn.com':'Left','foxnews.com':'Right','reuters.com' : 'Center'}
def get_domain_from_url(url):
    catch = urlparse(url)
    return catch.netloc
bicall = get_domain_from_url(url)
bicall.replace('www.','')
@app.get("/bias")
def get_bias(bicall):
    bi = bicall.replace('www.','')
    if bi in bias_map:
        return bias_map[bi]
    else:
        return "unknown"
    
@app.get("/bias")
def bias(topic:str):
    fetched = fetch_articles_for_topic(topic)
    left_sources, center_sources, right_sources = [],[],[]
    for article in fetched['articles']:
        urls = article.get('url', '')



