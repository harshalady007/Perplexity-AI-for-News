
import os
import google.generativeai as genai
import requests
import trafilatura
from urllib.parse import urlparse
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

app = FastAPI()

origins = ["*"] 

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DATA ---
BIAS_MAP = {
    # Left
    'abcnews.go.com': 'Left',
    'alternet.org': 'Left',
    'axios.com': 'Left',
    'bloomberg.com': 'Left',
    'buzzfeednews.com': 'Left',
    'cbsnews.com': 'Left',
    'cnn.com': 'Left',
    'crooksandliars.com': 'Left',
    'dailykos.com': 'Left',
    'democracynow.org': 'Left',
    'huffpost.com': 'Left',
    'msnbc.com': 'Left',
    'nbcnews.com': 'Left',
    'newrepublic.com': 'Left',
    'newyorker.com': 'Left',
    'nytimes.com': 'Left',
    'politico.com': 'Left',
    'slate.com': 'Left',
    'theatlantic.com': 'Left',
    'theguardian.com': 'Left',
    'theintercept.com': 'Left',
    'thenation.com': 'Left',
    'thinkprogress.org': 'Left',
    'vox.com': 'Left',
    'washingtonpost.com': 'Left',

    # Lean Left
    'afr.com': 'Left',
    'aljazeera.com': 'Left',
    'apnews.com': 'Left',
    'businessinsider.com': 'Left',
    'cnbc.com': 'Left',
    'fortune.com': 'Left',
    'insider.com': 'Left',
    'latimes.com': 'Left',
    'npr.org': 'Left',
    'pbs.org': 'Left',
    'propublica.org': 'Left',
    'time.com': 'Left',
    'usatoday.com': 'Left',
    'vanityfair.com': 'Left',
    'wired.com': 'Left',

    # Center
    'ap.org': 'Center',
    'bbc.com': 'Center',
    'csmonitor.com': 'Center',
    'forbes.com': 'Center',
    'marketwatch.com': 'Center',
    'news.yahoo.com': 'Center',
    'newsweek.com': 'Center',
    'realclearpolitics.com': 'Center',
    'reuters.com': 'Center',
    'thehill.com': 'Center',
    'thestreet.com': 'Center',
    'usnews.com': 'Center',
    'wsj.com': 'Center',
    'yahoo.com': 'Center',

    # Lean Right
    'americanaffairsjournal.org': 'Right',
    'christianpost.com': 'Right',
    'commentarymagazine.com': 'Right',
    'dailymail.co.uk': 'Right',
    'foxbusiness.com': 'Right',
    'nationalreview.com': 'Right',
    'nypost.com': 'Right',
    'spectator.org': 'Right',
    'theadvocate.com': 'Right',
    'thedispatch.com': 'Right',
    'theepochtimes.com': 'Right',
    'thefederalist.com': 'Right',
    'thetimes.co.uk': 'Right',
    'washingtontimes.com': 'Right',

    # Right
    'americanthinker.com': 'Right',
    'breitbart.com': 'Right',
    'cbn.com': 'Right',
    'dailycaller.com': 'Right',
    'dailywire.com': 'Right',
    'foxnews.com': 'Right',
    'freebeacon.com': 'Right',
    'infowars.com': 'Right',
    'judicialwatch.org': 'Right',
    'newsmax.com': 'Right',
    'redstate.com': 'Right',
    'theblaze.com': 'Right',
    'townhall.com': 'Right',
    'washingtonexaminer.com': 'Right',
    'wnd.com': 'Right',

    # International (various biases)
    'cbc.ca': 'Left',             # Canada
    'dw.com': 'Center',           # Germany
    'economist.com': 'Left',      # UK
    'ft.com': 'Center',           # UK
    'indiatimes.com': 'Center',   # India
    'japantimes.co.jp': 'Center', # Japan
    'lemonde.fr': 'Left',         # France
    'reuters.co.jp': 'Center',    # Japan
    'scmp.com': 'Center',         # Hong Kong
    'smh.com.au': 'Left',         # Australia
    'spiegel.de': 'Left',         # Germany
    'theage.com.au': 'Left',      # Australia
    'theglobeandmail.com': 'Center', # Canada
    'timesofindia.indiatimes.com': 'Center', # India
    'torontosun.com': 'Right'     # Canada
}

def get_domain_from_url(url: str) -> str:
    """Extracts the domain from a full URL."""
    return urlparse(url).netloc

def lookup_bias(domain: str) -> str:
    """Looks up the bias of a domain from our BIAS_MAP."""
    cleaned_domain = domain.replace('www.', '')
    return BIAS_MAP.get(cleaned_domain, 'Unknown')

@app.get("/")
def read_root():
    """Root endpoint to welcome users."""
    return {"message": "Welcome to the News AI API"}

@app.get("/everything")
def fetch_articles_for_topic(topic: str):
    """Fetches and sorts articles for a given topic from NewsAPI."""
    url = f"https://newsapi.org/v2/everything?q={topic}&apiKey={NEWS_API_KEY}"
    response = requests.get(url)
    data = response.json()
    
    articles = data.get('articles', [])

    articles.sort(key=lambda article: article.get('publishedAt', ''))
    
    data['articles'] = articles
    return data

@app.get("/summarize")
def summarize(article_url: str):
    """Extracts text from a URL and generates a 100-word summary."""
    extracted_text = trafilatura.fetch_url(article_url)
    clean_text = trafilatura.extract(extracted_text)
    
    prompt = f"Summarize the following news article into a concise 100-word digest: {clean_text}"
    response = model.generate_content(prompt)
    
    return {'summary': response.text}

@app.get("/timeline")
def timeline(topic: str):
    """Generates a historical timeline of key events for a topic."""
    data = fetch_articles_for_topic(topic)
    articles = data.get('articles', [])

    if not articles:
        return {"timeline": "[]"} 

    context = ""
    for article in articles[:10]: 
        title = article.get('title', '')
        description = article.get('description', '')
        if title and description:
            context += f"Title: {title}\nDescription: {description}\n\n"

    prompt = f"Based on the following news articles, create a timeline of the top 5 key events. For each event, provide the date and a single, concise sentence. Format the output as a JSON object with a key called 'timeline', which is a list of events. Each event should have 'date' and 'event' keys. Here is the context:\n\n{context}"
    
    response = model.generate_content(prompt)
    return {"timeline": response.text}

@app.get("/bias")
def get_bias_analysis(topic: str):
    """Analyzes the political bias of news sources for a given topic."""
    data = fetch_articles_for_topic(topic)
    articles = data.get('articles', [])
    
    left_sources, center_sources, right_sources = [], [], []

    for article in articles:
        url = article.get('url')
        title = article.get('title')
        if not url or not title:
            continue

        domain = get_domain_from_url(url)
        bias = lookup_bias(domain) 

        if bias == 'Left':
            left_sources.append(title)
        elif bias == 'Right':
            right_sources.append(title)
        else: 
            center_sources.append(title)
    
    return {
        "Left": left_sources,
        "Center": center_sources,
        "Right": right_sources
    }