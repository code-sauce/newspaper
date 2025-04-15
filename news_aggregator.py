import feedparser
import requests
from bs4 import BeautifulSoup
from newspaper import Article
import os
import time
import json
import random
from datetime import datetime
from typing import List, Dict, Any

class NewsSource:
    """Represents a news source with an RSS feed or API."""
    
    def __init__(self, name: str, url: str, source_type: str = 'rss'):
        self.name = name
        self.url = url
        self.source_type = source_type  # 'rss', 'api', etc.
    
    def fetch_articles(self) -> List[Dict[str, Any]]:
        """Fetch articles from the source."""
        if self.source_type == 'rss':
            return self._fetch_from_rss()
        else:
            # Placeholder for other source types
            return []
    
    def _fetch_from_rss(self) -> List[Dict[str, Any]]:
        """Fetch articles from RSS feed."""
        articles = []
        try:
            feed = feedparser.parse(self.url)
            for entry in feed.entries[:10]:  # Limit to 10 articles per source
                article_data = {
                    'title': entry.get('title', 'No title'),
                    'url': entry.get('link', ''),
                    'source': self.name,
                    'published': entry.get('published', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                    'summary': entry.get('summary', ''),
                }
                
                # Try to get the full article content
                try:
                    article = Article(entry.get('link', ''))
                    article.download()
                    article.parse()
                    article_data['text'] = article.text
                    article_data['image'] = article.top_image
                except Exception as e:
                    article_data['text'] = article_data['summary']
                    article_data['image'] = ''
                
                articles.append(article_data)
        except Exception as e:
            print(f"Error fetching from {self.name}: {e}")
        
        return articles

class GoogleNewsSource(NewsSource):
    """Special handler for Google News RSS feeds."""
    
    def __init__(self, name: str, topic: str = ''):
        base_url = "https://news.google.com/rss"
        if topic:
            # Google News topic-specific feeds
            url = f"{base_url}/headlines/section/topic/{topic.upper()}"
        else:
            # General Google News feed
            url = base_url
        super().__init__(name, url, 'rss')

class NewsFeed:
    """Manages multiple news sources and aggregates their content."""
    
    def __init__(self):
        self.sources = self._initialize_sources()
        self.cache_file = 'article_cache.json'
        self.cache_duration = 3600  # Cache duration in seconds (1 hour)
    
    def _initialize_sources(self) -> List[NewsSource]:
        """Initialize list of news sources."""
        sources = [
            # Standard RSS feeds
            NewsSource('BBC', 'http://feeds.bbci.co.uk/news/world/rss.xml'),
            NewsSource('CNN', 'http://rss.cnn.com/rss/edition.rss'),
            NewsSource('Reuters', 'http://feeds.reuters.com/reuters/topNews'),
            NewsSource('NPR', 'https://feeds.npr.org/1001/rss.xml'),
            NewsSource('Washington Post', 'http://feeds.washingtonpost.com/rss/world'),
            
            # Google News feeds
            GoogleNewsSource('Google News - Top Stories'),
            GoogleNewsSource('Google News - World', 'WORLD'),
            GoogleNewsSource('Google News - Business', 'BUSINESS'),
            GoogleNewsSource('Google News - Technology', 'TECHNOLOGY'),
            GoogleNewsSource('Google News - Entertainment', 'ENTERTAINMENT'),
            GoogleNewsSource('Google News - Sports', 'SPORTS'),
            GoogleNewsSource('Google News - Science', 'SCIENCE'),
            GoogleNewsSource('Google News - Health', 'HEALTH'),
        ]
        return sources
    
    def get_articles(self) -> List[Dict[str, Any]]:
        """Get articles from all sources or from cache if available."""
        # Check if cache is valid
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r') as f:
                cache = json.load(f)
                if time.time() - cache.get('timestamp', 0) < self.cache_duration:
                    return cache.get('articles', [])
        
        # Fetch new articles
        all_articles = []
        for source in self.sources:
            articles = source.fetch_articles()
            all_articles.extend(articles)
        
        # Sort by published date (newest first)
        all_articles.sort(key=lambda x: x.get('published', ''), reverse=True)
        
        # Remove duplicates (articles with similar titles)
        unique_articles = []
        titles = set()
        for article in all_articles:
            title = article.get('title', '').lower()
            # Skip if we've seen a very similar title
            if any(self._similar_titles(title, existing) for existing in titles):
                continue
            titles.add(title)
            unique_articles.append(article)
        
        # Cache the results
        cache_data = {
            'timestamp': time.time(),
            'articles': unique_articles
        }
        with open(self.cache_file, 'w') as f:
            json.dump(cache_data, f)
        
        return unique_articles
    
    def _similar_titles(self, title1: str, title2: str, threshold: float = 0.8) -> bool:
        """Check if two titles are very similar."""
        # Simple version: check if one is contained in the other
        if len(title1) > 20 and len(title2) > 20:
            return title1 in title2 or title2 in title1
        return False
    
    def search_articles(self, query: str) -> List[Dict[str, Any]]:
        """Search articles by query."""
        articles = self.get_articles()
        return [
            article for article in articles
            if query.lower() in article.get('title', '').lower() or
               query.lower() in article.get('text', '').lower()
        ]

# For testing
if __name__ == "__main__":
    news_feed = NewsFeed()
    articles = news_feed.get_articles()
    for article in articles[:5]:  # Print first 5 articles
        print(f"Title: {article['title']}")
        print(f"Source: {article['source']}")
        print(f"Published: {article['published']}")
        print("---") 