from flask import Flask, render_template, request
from dotenv import load_dotenv
import os
from news_aggregator import NewsFeed
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)

@app.route('/')
def home():
    """Render the home page with news articles."""
    # Get category filter from query params
    category = request.args.get('category', '')
    
    # Get current date
    current_date = datetime.now().strftime('%A, %B %d, %Y')
    current_year = datetime.now().year
    
    # Get news articles
    news_feed = NewsFeed()
    articles = news_feed.get_articles()
    
    # Filter by category if specified
    if category:
        articles = [article for article in articles if category.lower() in article.get('title', '').lower() or 
                                                     category.lower() in article.get('text', '').lower()]
    
    return render_template('index.html', 
                          articles=articles, 
                          current_date=current_date,
                          current_year=current_year)

if __name__ == '__main__':
    app.run(debug=True) 