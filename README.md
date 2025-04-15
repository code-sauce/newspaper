# The Daily Digest - News Aggregator

A Python-based newspaper-style news aggregator that pulls content from various free sources including Google News and presents it in a traditional newspaper layout.

## Features

- Aggregates news from multiple sources (BBC, CNN, Reuters, NPR, Washington Post, Google News)
- Generates a newspaper-style HTML layout
- Categorizes news articles (World, Business, Technology, etc.)
- Responsive design that works on desktop and mobile
- Caches articles to reduce API requests
- Removes duplicate stories
- Clean, print-friendly layout

## Installation

1. Clone this repository:
```
git clone <repository-url>
cd newspaper
```

2. Create a virtual environment (optional but recommended):
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```
pip install -r requirements.txt
```

## Usage

1. Run the Flask application:
```
python app.py
```

2. Open your browser and navigate to:
```
http://127.0.0.1:5000/
```

3. Browse news articles by category using the navigation menu.

## Customization

### Adding Custom News Sources

Edit the `_initialize_sources` method in the `NewsFeed` class in `news_aggregator.py` to add your own RSS feeds:

```python
def _initialize_sources(self) -> List[NewsSource]:
    """Initialize list of news sources."""
    sources = [
        # Your custom sources
        NewsSource('Custom Source Name', 'https://custom-source-url.com/rss'),
        # ...existing sources...
    ]
    return sources
```

### Modifying the Layout

The newspaper layout is defined in the HTML template (`templates/index.html`) and styled with CSS (`static/css/style.css`). You can modify these files to customize the appearance.

## Project Structure

```
newspaper/
├── app.py                  # Flask application
├── news_aggregator.py      # Core news aggregation logic
├── requirements.txt        # Python dependencies
├── article_cache.json      # Cache file (created on first run)
├── static/
│   ├── css/
│   │   └── style.css       # Newspaper styling
│   └── js/
│       └── script.js       # Client-side JavaScript
└── templates/
    └── index.html          # Main HTML template
```

## How It Works

1. The application fetches RSS feeds from various news sources.
2. It parses the feeds and extracts article information (title, summary, etc.).
3. For each article, it attempts to fetch the full content and images.
4. It removes duplicate articles and sorts by publication date.
5. The Flask app renders the articles in a newspaper-style layout.
6. Articles are cached to avoid repeated API requests.

## Dependencies

- Flask: Web framework
- Feedparser: RSS feed parsing
- Newspaper3k: Article extraction and parsing
- BeautifulSoup4: HTML parsing
- Requests: HTTP requests

## License

MIT