from flask import Flask, render_template, request, redirect, url_for, jsonify
from dotenv import load_dotenv
import os
from news_aggregator import NewsFeed
from datetime import datetime
import html
from bs4 import BeautifulSoup
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__)

@app.route('/')
def home():
    """Render the home page with news articles."""
    # Get category filter from query params
    category = request.args.get('category', '')
    
    # Get force_refresh parameter
    force_refresh = request.args.get('refresh', '').lower() == 'true'
    
    # Get current date
    current_date = datetime.now().strftime('%A, %B %d, %Y')
    current_year = datetime.now().year
    
    articles = []
    error_message = None
    
    try:
        # Get news articles
        news_feed = NewsFeed()
        
        # Clear cache if refresh requested
        if force_refresh and os.path.exists(news_feed.cache_file):
            try:
                os.remove(news_feed.cache_file)
            except Exception as e:
                logger.error(f"Error removing cache file: {e}")
        
        # Get articles with category filter
        try:
            articles = news_feed.get_articles(category=category if category else None)
        except Exception as e:
            logger.error(f"Error getting articles: {e}")
            # Delete corrupt cache file if it exists
            if os.path.exists(news_feed.cache_file):
                try:
                    os.remove(news_feed.cache_file)
                    # Try again without the cache
                    articles = news_feed.get_articles(category=category if category else None)
                except Exception as new_e:
                    logger.error(f"Error retrying after cache deletion: {new_e}")
        
        # Handle empty category
        if not articles and category:
            # Try clearing the cache and fetch again
            if os.path.exists(news_feed.cache_file):
                try:
                    os.remove(news_feed.cache_file)
                    articles = news_feed.get_articles(category=category)
                except Exception as e:
                    logger.error(f"Error fetching category after cache removal: {e}")
                    # Fallback to general articles if category is empty
                    try:
                        articles = news_feed.get_articles()
                    except Exception as fallback_e:
                        logger.error(f"Error fetching fallback articles: {fallback_e}")
        
        # Add index to each article for routing to full view
        for i, article in enumerate(articles):
            article['id'] = i
            
            # Process article text for better readability
            if article.get('text'):
                # Split into paragraphs and keep only non-empty ones
                paragraphs = [p.strip() for p in article['text'].split('\n') if p.strip()]
                article['paragraphs'] = paragraphs[:5]  # Limit to first 5 paragraphs for preview
            else:
                article['paragraphs'] = []
    
    except Exception as e:
        logger.error(f"Unhandled error in home route: {e}")
        error_message = f"An error occurred while loading the news. Please try refreshing the page."
    
    return render_template('index.html', 
                          articles=articles, 
                          current_date=current_date,
                          current_year=current_year,
                          current_category=category,
                          error_message=error_message)

@app.route('/article/<int:article_id>')
def article(article_id):
    """Render a single article page."""
    news_feed = NewsFeed()
    article = news_feed.get_article_by_id(article_id)
    
    if not article:
        return redirect(url_for('home'))
    
    # Get current date
    current_date = datetime.now().strftime('%A, %B %d, %Y')
    current_year = datetime.now().year
    
    # Process article text for better readability
    if article.get('text'):
        # Split into paragraphs and keep only non-empty ones
        paragraphs = [p.strip() for p in article['text'].split('\n') if p.strip()]
        article['paragraphs'] = paragraphs
    else:
        article['paragraphs'] = []
    
    # Process full content if available
    if article.get('full_content'):
        try:
            # Clean the HTML content
            soup = BeautifulSoup(article['full_content'], 'html.parser')
            
            # Remove potentially harmful elements
            for s in soup(['script', 'style', 'iframe', 'form']):
                s.decompose()
                
            # Only keep the content HTML
            article['content_html'] = str(soup)
        except Exception as e:
            article['content_html'] = ''
    
    return render_template('article.html', 
                          article=article, 
                          current_date=current_date,
                          current_year=current_year)

@app.route('/api/article/<int:article_id>')
def api_article(article_id):
    """API endpoint to get article data for modal display."""
    try:
        news_feed = NewsFeed()
        article = news_feed.get_article_by_id(article_id)
        
        if not article:
            return jsonify({'error': 'Article not found'}), 404
        
        # Process article text for better readability
        if article.get('text'):
            paragraphs = [p.strip() for p in article['text'].split('\n') if p.strip()]
            article['paragraphs'] = paragraphs
        else:
            article['paragraphs'] = []
        
        # Process full content if available
        if article.get('full_content'):
            try:
                # Clean the HTML content
                soup = BeautifulSoup(article['full_content'], 'html.parser')
                
                # Remove potentially harmful elements
                for s in soup(['script', 'style', 'iframe', 'form']):
                    s.decompose()
                    
                # Only keep the content HTML
                article['content_html'] = str(soup)
            except Exception as e:
                article['content_html'] = ''
        
        # Compile the article data for JSON response
        article_data = {
            'id': article.get('id'),
            'title': article.get('title'),
            'source': article.get('source'),
            'published': article.get('published'),
            'authors': article.get('authors', []),
            'url': article.get('url'),
            'image': article.get('image'),
            'images': article.get('images', []),
            'summary': article.get('summary'),
            'paragraphs': article.get('paragraphs', []),
            'content_html': article.get('content_html', ''),
            'keywords': article.get('keywords', [])
        }
        
        return jsonify(article_data)
    except Exception as e:
        logger.error(f"Error in API article endpoint: {e}")
        return jsonify({'error': 'An error occurred while processing the article'}), 500

@app.route('/refresh')
def refresh_news():
    """Force refresh the news by clearing the cache."""
    category = request.args.get('category', '')
    news_feed = NewsFeed()
    
    # Clear the cache
    if os.path.exists(news_feed.cache_file):
        try:
            os.remove(news_feed.cache_file)
        except Exception as e:
            logger.error(f"Error removing cache file: {e}")
    
    # Redirect back to homepage or category page
    if category:
        return redirect(url_for('home', category=category))
    else:
        return redirect(url_for('home'))

@app.errorhandler(500)
def internal_error(error):
    return render_template('index.html', 
                          articles=[], 
                          current_date=datetime.now().strftime('%A, %B %d, %Y'),
                          current_year=datetime.now().year,
                          error_message="An error occurred while processing your request. Please try again later.")

if __name__ == '__main__':
    app.run(debug=True) 