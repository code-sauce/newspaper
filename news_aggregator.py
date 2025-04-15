import feedparser
import requests
from bs4 import BeautifulSoup
from newspaper import Article, ArticleException
import os
import time
import json
import random
from datetime import datetime
from typing import List, Dict, Any
import logging
import re

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Category keywords for improved detection
CATEGORY_KEYWORDS = {
    'world': ['world', 'international', 'global', 'foreign', 'europe', 'asia', 'africa', 'middle east', 'politics', 'diplomat', 'nation'],
    'business': ['business', 'economy', 'finance', 'market', 'stock', 'trade', 'economic', 'investment', 'startup', 'entrepreneur'],
    'technology': ['tech', 'technology', 'digital', 'software', 'hardware', 'app', 'ai', 'artificial intelligence', 'robot', 'computing', 'cyber'],
    'science': ['science', 'research', 'discovery', 'space', 'physics', 'biology', 'chemistry', 'environment', 'climate', 'nature'],
    'health': ['health', 'medical', 'medicine', 'disease', 'virus', 'pandemic', 'doctor', 'hospital', 'wellness', 'mental health'],
    'sports': ['sport', 'football', 'soccer', 'basketball', 'baseball', 'tennis', 'golf', 'hockey', 'olympics', 'athlete'],
    'entertainment': ['entertainment', 'art', 'film', 'movie', 'music', 'celebrity', 'culture', 'book', 'tv', 'television', 'theater']
}

class NewsSource:
    """Represents a news source with an RSS feed or API."""
    
    def __init__(self, name: str, url: str, source_type: str = 'rss', category: str = 'general'):
        self.name = name
        self.url = url
        self.source_type = source_type  # 'rss', 'api', etc.
        self.category = category.lower()  # world, tech, science, etc.
    
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
                    'category': self.category,
                    'published': entry.get('published', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                    'summary': entry.get('summary', ''),
                    'full_content': '',
                    'text': '',
                    'image': '',
                    'images': []
                }
                
                # Analyze title and summary for better category detection
                article_data = self._enhance_article_category(article_data)
                
                # Try to get the full article content
                try:
                    article = Article(entry.get('link', ''))
                    article.download()
                    article.parse()
                    
                    # Try to extract the full HTML content
                    article_data['full_content'] = article.article_html or ''
                    article_data['text'] = article.text
                    
                    # Get main image
                    article_data['image'] = article.top_image
                    
                    # Get all images - ensure it's a list, not a set
                    article_data['images'] = list(article.images) if article.images else []
                    
                    # Try to get authors
                    article_data['authors'] = list(article.authors) if article.authors else []
                    
                    # Get additional metadata
                    try:
                        article.nlp()
                        article_data['keywords'] = list(article.keywords) if article.keywords else []
                        article_data['summary'] = article.summary or article_data['summary']
                        
                        # Further enhance category using extracted keywords
                        if article_data['keywords']:
                            article_data = self._enhance_article_category(article_data, ' '.join(article_data['keywords']))
                    except:
                        pass
                        
                except Exception as e:
                    logger.warning(f"Error parsing article {entry.get('link', '')}: {e}")
                    # If we failed to get full content, use the summary
                    if not article_data['text']:
                        article_data['text'] = article_data['summary']
                    
                    # Try to extract content from the summary if it's HTML
                    if '<' in article_data['summary'] and '>' in article_data['summary']:
                        try:
                            soup = BeautifulSoup(article_data['summary'], 'html.parser')
                            # Use the summary HTML as the full content
                            article_data['full_content'] = article_data['summary']
                            # Try to extract text if we don't have it
                            if not article_data['text']:
                                article_data['text'] = soup.get_text()
                            # Try to find images
                            for img in soup.find_all('img'):
                                if img.get('src'):
                                    article_data['images'].append(img['src'])
                                    if not article_data['image']:
                                        article_data['image'] = img['src']
                        except Exception as e:
                            logger.warning(f"Error parsing summary HTML: {e}")
                
                articles.append(article_data)
        except Exception as e:
            logger.error(f"Error fetching from {self.name}: {e}")
        
        return articles
    
    def _enhance_article_category(self, article_data: Dict[str, Any], additional_text: str = '') -> Dict[str, Any]:
        """Analyze article content to potentially assign a more specific category."""
        if article_data['category'] != 'general':
            return article_data
            
        # Combine title and summary for analysis
        content_to_analyze = article_data['title'] + ' ' + article_data['summary'] + ' ' + additional_text
        content_to_analyze = content_to_analyze.lower()
        
        # Check for category keywords
        for category, keywords in CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in content_to_analyze:
                    article_data['category'] = category
                    return article_data
        
        return article_data

class GoogleNewsSource(NewsSource):
    """Special handler for Google News RSS feeds."""
    
    def __init__(self, name: str, topic: str = '', category: str = 'general'):
        base_url = "https://news.google.com/rss"
        if topic:
            # Google News topic-specific feeds
            url = f"{base_url}/headlines/section/topic/{topic.upper()}"
        else:
            # General Google News feed
            url = base_url
        super().__init__(name, url, 'rss', category)

class NewsFeed:
    """Manages multiple news sources and aggregates their content."""
    
    def __init__(self):
        self.sources = self._initialize_sources()
        self.cache_file = 'article_cache.json'
        self.cache_duration = 3600  # Cache duration in seconds (1 hour)
    
    def _initialize_sources(self) -> List[NewsSource]:
        """Initialize list of news sources with quality sources for different categories."""
        sources = [
            # High-quality general news sources with fewer ads
            NewsSource('The Guardian', 'https://www.theguardian.com/world/rss', category='world'),
            NewsSource('Reuters', 'http://feeds.reuters.com/reuters/topNews', category='general'),
            NewsSource('PBS NewsHour', 'https://www.pbs.org/newshour/feeds/rss/headlines', category='general'),
            NewsSource('NPR News', 'https://feeds.npr.org/1001/rss.xml', category='general'),
            NewsSource('The Atlantic', 'https://www.theatlantic.com/feed/all/', category='general'),
            NewsSource('BBC World', 'http://feeds.bbci.co.uk/news/world/rss.xml', category='world'),
            
            # World news sources
            NewsSource('Foreign Policy', 'https://foreignpolicy.com/feed/', category='world'),
            NewsSource('Diplomatic Courier', 'https://www.diplomaticourier.com/feed/', category='world'),
            NewsSource('UN News', 'https://news.un.org/en/rss/all', category='world'),
            NewsSource('Al Jazeera', 'https://www.aljazeera.com/xml/rss/all.xml', category='world'),
            NewsSource('France 24', 'https://www.france24.com/en/rss', category='world'),
            NewsSource('Deutsche Welle', 'https://rss.dw.com/xml/rss-en-all', category='world'),
            
            # Technology sources with quality content and fewer ads
            NewsSource('Ars Technica', 'http://feeds.arstechnica.com/arstechnica/index', category='technology'),
            NewsSource('MIT Technology Review', 'https://www.technologyreview.com/feed/', category='technology'),
            NewsSource('Wired', 'https://www.wired.com/feed/rss', category='technology'),
            NewsSource('The Verge', 'https://www.theverge.com/rss/index.xml', category='technology'),
            NewsSource('Hacker News', 'https://news.ycombinator.com/rss', category='technology'),
            NewsSource('TechCrunch', 'https://techcrunch.com/feed/', category='technology'),
            NewsSource('Slashdot', 'http://rss.slashdot.org/Slashdot/slashdotMain', category='technology'),
            NewsSource('IEEE Spectrum', 'https://spectrum.ieee.org/feeds/feed.rss', category='technology'),
            
            # Science sources
            NewsSource('Nature News', 'http://feeds.nature.com/nature/rss/current', category='science'),
            NewsSource('Science Magazine', 'https://www.science.org/rss/news_current.xml', category='science'),
            NewsSource('Scientific American', 'http://rss.sciam.com/ScientificAmerican-Global', category='science'),
            NewsSource('Quanta Magazine', 'https://api.quantamagazine.org/feed/', category='science'),
            NewsSource('Space.com', 'https://www.space.com/feeds/all', category='science'),
            NewsSource('Live Science', 'https://www.livescience.com/feeds/all', category='science'),
            NewsSource('Physics World', 'https://physicsworld.com/feed/', category='science'),
            NewsSource('NASA', 'https://www.nasa.gov/rss/dyn/breaking_news.rss', category='science'),
            NewsSource('New Scientist', 'https://www.newscientist.com/feed/home/?cmpid=RSS', category='science'),
            
            # Business and Economics
            NewsSource('The Economist', 'https://www.economist.com/finance-and-economics/rss.xml', category='business'),
            NewsSource('Financial Times', 'https://www.ft.com/rss/home', category='business'),
            NewsSource('Harvard Business Review', 'https://hbr.org/rss/index.xml', category='business'),
            NewsSource('Bloomberg', 'https://news.google.com/rss/search?q=when:24h+allinurl:bloomberg.com', category='business'),
            NewsSource('CNBC', 'https://www.cnbc.com/id/10000664/device/rss/rss.html', category='business'),
            NewsSource('Market Watch', 'https://feeds.a.dj.com/rss/RSSMarketsMain.xml', category='business'),
            NewsSource('Business Insider', 'https://markets.businessinsider.com/rss/news', category='business'),
            NewsSource('Fortune', 'https://fortune.com/feed/', category='business'),
            
            # Culture and Arts
            NewsSource('The Paris Review', 'https://www.theparisreview.org/feed/', category='entertainment'),
            NewsSource('New Yorker Culture', 'https://www.newyorker.com/feed/culture', category='entertainment'),
            NewsSource('Pitchfork', 'https://pitchfork.com/rss/news/', category='entertainment'),
            NewsSource('Rolling Stone', 'https://www.rollingstone.com/feed/', category='entertainment'),
            NewsSource('Variety', 'https://variety.com/feed/', category='entertainment'),
            NewsSource('ArtNews', 'https://www.artnews.com/feed/', category='entertainment'),
            NewsSource('The Hollywood Reporter', 'https://www.hollywoodreporter.com/feed/', category='entertainment'),
            
            # Sports from quality sources
            NewsSource('The Athletic', 'https://theathletic.com/feeds/rss/', category='sports'),
            NewsSource('Sports Illustrated', 'https://www.si.com/rss/si_top_stories.rss', category='sports'),
            NewsSource('ESPN', 'https://www.espn.com/espn/rss/news', category='sports'),
            NewsSource('BBC Sport', 'https://feeds.bbci.co.uk/sport/rss.xml', category='sports'),
            NewsSource('The Ringer', 'https://www.theringer.com/rss/index.xml', category='sports'),
            NewsSource('SB Nation', 'https://www.sbnation.com/rss', category='sports'),
            NewsSource('Olympics', 'https://olympics.com/en/news/rss', category='sports'),
            
            # Health from medical sources with fewer ads
            NewsSource('Harvard Health', 'https://www.health.harvard.edu/blog/feed', category='health'),
            NewsSource('STAT News', 'https://www.statnews.com/feed', category='health'),
            NewsSource('Kaiser Health News', 'https://khn.org/feed/', category='health'),
            NewsSource('WebMD', 'https://rssfeeds.webmd.com/rss/rss.aspx?RSSSource=RSS_PUBLIC', category='health'),
            NewsSource('Medical News Today', 'https://www.medicalnewstoday.com/newsfeeds/medical.xml', category='health'),
            NewsSource('NIH News', 'https://www.nih.gov/news-events/feed.xml', category='health'),
            NewsSource('CDC', 'https://tools.cdc.gov/api/v2/resources/media/132608.rss', category='health'),
            NewsSource('Mayo Clinic', 'https://www.mayoclinic.org/rss/all-health-information-topics', category='health'),
            
            # Google News feeds for supplementary content
            GoogleNewsSource('Google News - World', 'WORLD', 'world'),
            GoogleNewsSource('Google News - Business', 'BUSINESS', 'business'),
            GoogleNewsSource('Google News - Technology', 'TECHNOLOGY', 'technology'),
            GoogleNewsSource('Google News - Science', 'SCIENCE', 'science'),
            GoogleNewsSource('Google News - Entertainment', 'ENTERTAINMENT', 'entertainment'),
            GoogleNewsSource('Google News - Sports', 'SPORTS', 'sports'),
            GoogleNewsSource('Google News - Health', 'HEALTH', 'health'),
        ]
        return sources
    
    def get_articles(self, category: str = None) -> List[Dict[str, Any]]:
        """Get articles from all sources or from cache if available.
        
        Args:
            category: Optional category to filter by
        """
        # Check if cache is valid
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    cache = json.load(f)
                    if time.time() - cache.get('timestamp', 0) < self.cache_duration:
                        articles = cache.get('articles', [])
                        # Filter by category if specified
                        if category:
                            # Enhanced category filtering with keywords
                            category_lower = category.lower()
                            category_keywords = CATEGORY_KEYWORDS.get(category_lower, [])
                            filtered_articles = []
                            
                            for article in articles:
                                # Direct category match
                                if category_lower == article.get('category', '').lower():
                                    filtered_articles.append(article)
                                    continue
                                    
                                # Title and text matching
                                title = article.get('title', '').lower()
                                text = article.get('text', '').lower()
                                summary = article.get('summary', '').lower()
                                
                                # Check if any category keyword is in title or text
                                if any(keyword in title or keyword in text or keyword in summary for keyword in category_keywords):
                                    # Clone article and set its category
                                    article_copy = article.copy()
                                    article_copy['category'] = category_lower
                                    filtered_articles.append(article_copy)
                                    
                            return filtered_articles
                        return articles
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error reading cache file: {e}")
        
        # Fetch new articles
        all_articles = []
        for source in self.sources:
            try:
                # If category is specified, focus on relevant sources first
                if category and category.lower() != source.category.lower() and source.category != 'general':
                    continue
                    
                articles = source.fetch_articles()
                all_articles.extend(articles)
                logger.info(f"Fetched {len(articles)} articles from {source.name}")
            except Exception as e:
                logger.error(f"Error fetching from source {source.name}: {e}")
        
        # If not enough category-specific articles found and category is specified, get from general sources too
        if category and len(all_articles) < 10:
            logger.info(f"Not enough {category} articles, fetching from general sources")
            for source in self.sources:
                try:
                    if source.category == 'general':
                        articles = source.fetch_articles()
                        all_articles.extend(articles)
                        logger.info(f"Fetched {len(articles)} general articles from {source.name}")
                except Exception as e:
                    logger.error(f"Error fetching from source {source.name}: {e}")
        
        # Sort by published date (newest first)
        all_articles.sort(key=lambda x: x.get('published', ''), reverse=True)
        
        # Remove duplicates (articles with similar titles)
        unique_articles = []
        titles_list = []  # Use a list instead of a set for better control
        for article in all_articles:
            title = article.get('title', '').lower()
            # Skip if we've seen a very similar title
            if any(self._similar_titles(title, existing) for existing in titles_list):
                continue
            titles_list.append(title)
            unique_articles.append(article)
        
        # Ensure all data is JSON serializable before caching
        json_safe_articles = []
        for article in unique_articles:
            json_safe_article = {}
            for key, value in article.items():
                # Convert sets to lists and handle other non-serializable types
                if isinstance(value, set):
                    json_safe_article[key] = list(value)
                elif isinstance(value, (str, int, float, bool, type(None))):
                    json_safe_article[key] = value
                elif isinstance(value, list):
                    # Recursively make lists serializable
                    json_safe_article[key] = self._make_json_serializable(value)
                elif isinstance(value, dict):
                    # Recursively make dicts serializable
                    json_safe_article[key] = self._make_json_serializable_dict(value)
                else:
                    # Convert other types to string
                    json_safe_article[key] = str(value)
            json_safe_articles.append(json_safe_article)
        
        # Cache all articles (not just the filtered ones)
        cache_data = {
            'timestamp': time.time(),
            'articles': json_safe_articles
        }
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f)
        except Exception as e:
            logger.error(f"Error writing cache file: {e}")
            # If caching fails, delete the cache file to prevent using corrupted data
            try:
                if os.path.exists(self.cache_file):
                    os.remove(self.cache_file)
            except:
                pass
        
        # Filter by category if specified
        if category:
            category_lower = category.lower()
            category_keywords = CATEGORY_KEYWORDS.get(category_lower, [])
            filtered_articles = []
            
            for article in unique_articles:
                # Direct category match
                if category_lower == article.get('category', '').lower():
                    filtered_articles.append(article)
                    continue
                
                # Title and text matching
                title = article.get('title', '').lower()
                text = article.get('text', '').lower()
                summary = article.get('summary', '').lower()
                
                # Check if any category keyword is in title or text
                if any(keyword in title or keyword in text or keyword in summary for keyword in category_keywords):
                    # Clone article and set its category
                    article_copy = article.copy()
                    article_copy['category'] = category_lower
                    filtered_articles.append(article_copy)
            
            return filtered_articles
        
        return unique_articles
    
    def _make_json_serializable(self, value: Any) -> Any:
        """Recursively convert data structures to JSON serializable types."""
        if isinstance(value, (str, int, float, bool, type(None))):
            return value
        elif isinstance(value, set):
            return list(value)
        elif isinstance(value, list):
            return [self._make_json_serializable(item) for item in value]
        elif isinstance(value, dict):
            return self._make_json_serializable_dict(value)
        else:
            return str(value)
    
    def _make_json_serializable_dict(self, d: Dict) -> Dict:
        """Convert a dictionary to a JSON serializable dictionary."""
        result = {}
        for key, value in d.items():
            result[key] = self._make_json_serializable(value)
        return result
    
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
    
    def get_article_by_id(self, article_id: int) -> Dict[str, Any]:
        """Get a specific article by its index in the list."""
        articles = self.get_articles()
        if 0 <= article_id < len(articles):
            return articles[article_id]
        return None

# For testing
if __name__ == "__main__":
    news_feed = NewsFeed()
    articles = news_feed.get_articles()
    for article in articles[:5]:  # Print first 5 articles
        print(f"Title: {article['title']}")
        print(f"Source: {article['source']}")
        print(f"Published: {article['published']}")
        print("---") 