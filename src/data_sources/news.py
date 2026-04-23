"""
Gold News Data Sources

Fetches news related to gold from:
- NewsAPI (free tier available)
- GDELT Project (free)
- Mock data for development
"""

from typing import Optional, Literal
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from dataclasses import asdict
import pandas as pd
import numpy as np
import requests
import json


@dataclass
class GoldNewsItem:
    """Single news item."""
    title: str
    description: str
    source: str
    url: str
    published_at: datetime
    sentiment: Literal["positive", "negative", "neutral"] = "neutral"
    sentiment_score: float = 0.0  # -1 to 1
    relevance_score: float = 0.5  # 0 to 1
    categories: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class NewsData:
    """Container for news data."""
    news: list[GoldNewsItem] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = "unknown"
    
    def to_list(self) -> list[dict]:
        return [item.to_dict() for item in self.news]
    
    @property
    def positive_count(self) -> int:
        return sum(1 for n in self.news if n.sentiment == "positive")
    
    @property
    def negative_count(self) -> int:
        return sum(1 for n in self.news if n.sentiment == "negative")
    
    @property
    def neutral_count(self) -> int:
        return sum(1 for n in self.news if n.sentiment == "neutral")
    
    @property
    def avg_sentiment(self) -> float:
        if not self.news:
            return 0.0
        return sum(n.sentiment_score for n in self.news) / len(self.news)


def get_gold_news(
    end_date: Optional[str] = None,
    days_back: int = 7,
    max_results: int = 100,
    language: str = "en",
) -> NewsData:
    """
    Fetch gold-related news from various sources.
    
    Args:
        end_date: End date for news search
        days_back: How many days back to search
        max_results: Maximum number of results
        language: Language filter
    
    Returns:
        NewsData object with news items
    """
    if end_date is None:
        end_date = datetime.now()
    elif isinstance(end_date, str):
        end_date = pd.to_datetime(end_date)
    
    start_date = end_date - timedelta(days=days_back)
    
    # Try newsapi first
    try:
        return _fetch_newsapi(start_date, end_date, max_results, language)
    except Exception as e:
        print(f"NewsAPI failed: {e}")
    
    # Try GDELT
    try:
        return _fetch_gdelt(start_date, end_date, max_results)
    except Exception as e:
        print(f"GDELT failed: {e}")
    
    # Fallback to mock
    return _generate_mock_news(start_date, end_date, max_results)


def _fetch_newsapi(
    start_date: datetime,
    end_date: datetime,
    max_results: int,
    language: str,
) -> NewsData:
    """Fetch news from NewsAPI.org."""
    import os
    
    api_key = os.getenv("NEWS_API_KEY")
    
    if api_key is None:
        raise ValueError("NEWS_API_KEY required")
    
    # Search terms for gold
    queries = [
        "gold price XAUUSD",
        "Federal Reserve gold",
        "gold market outlook",
        "central bank gold",
    ]
    
    all_news = []
    
    for query in queries:
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "from": start_date.strftime("%Y-%m-%d"),
            "to": end_date.strftime("%Y-%m-%d"),
            "language": language,
            "sortBy": "relevancy",
            "pageSize": min(max_results // len(queries), 25),
            "apiKey": api_key,
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            articles = data.get("articles", [])
            
            for article in articles:
                news_item = GoldNewsItem(
                    title=article.get("title", ""),
                    description=article.get("description", ""),
                    source=article.get("source", {}).get("name", "Unknown"),
                    url=article.get("url", ""),
                    published_at=pd.to_datetime(article.get("publishedAt")),
                    categories=_categorize_news(article.get("title", "")),
                )
                
                # Simple sentiment based on keywords
                news_item.sentiment, news_item.sentiment_score = _analyze_sentiment(
                    article.get("title", "") + " " + article.get("description", "")
                )
                
                all_news.append(news_item)
                
        except Exception as e:
            print(f"NewsAPI query failed: {e}")
    
    # Remove duplicates
    seen = set()
    unique_news = []
    for item in all_news:
        if item.url not in seen:
            seen.add(item.url)
            unique_news.append(item)
    
    # Sort by date
    unique_news.sort(key=lambda x: x.published_at, reverse=True)
    
    return NewsData(
        news=unique_news[:max_results],
        source="newsapi",
    )


def _fetch_gdelt(
    start_date: datetime,
    end_date: datetime,
    max_results: int,
) -> NewsData:
    """Fetch news from GDELT Project (free, no API key needed)."""
    # GDELT Global Graph API
    # Returns news articles matching queries
    
    queries = [
        "gold price",
        "Federal Reserve",
        "XAUUSD",
        "central bank gold",
    ]
    
    all_news = []
    
    for query in queries:
        url = "https://api.gdeltproject.org/api/v2/doc/doc"
        params = {
            "format": "json",
            "mode": "artlist",
            "query": f"{query} sourcelang:english",
            "maxrecords": min(max_results // len(queries), 50),
            "sort": "DateDesc",
        }
        
        try:
            response = requests.get(url, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()
            
            articles = data.get("articles", [])
            
            for article in articles:
                if article.get("url"):
                    news_item = GoldNewsItem(
                        title=article.get("title", ""),
                        description=article.get("seendate", ""),
                        source=article.get("domain", ""),
                        url=article.get("url", ""),
                        published_at=pd.to_datetime(article.get("seendate"), format="%Y%m%dT%H%M%SZ"),
                        categories=_categorize_news(article.get("title", "")),
                    )
                    
                    news_item.sentiment, news_item.sentiment_score = _analyze_sentiment(
                        article.get("title", "")
                    )
                    
                    all_news.append(news_item)
                    
        except Exception as e:
            print(f"GDELT query failed: {e}")
    
    # Remove duplicates and sort
    seen = set()
    unique_news = []
    for item in all_news:
        if item.url not in seen:
            seen.add(item.url)
            unique_news.append(item)
    
    unique_news.sort(key=lambda x: x.published_at, reverse=True)
    
    return NewsData(
        news=unique_news[:max_results],
        source="gdelt",
    )


def _categorize_news(text: str) -> list[str]:
    """Categorize news based on keywords."""
    text_lower = text.lower()
    categories = []
    
    category_keywords = {
        "Fed": ["fed", "federal reserve", "powell", "fomc", " Jerome Powell"],
        "Inflation": ["inflation", "cpi", "ppi", "price", "cost", "pcE"],
        "Geopolitical": ["war", "conflict", "sanction", "tension", "crisis", "russia", "china", "ukraine"],
        "Central Bank": ["central bank", "reserve", "imf", "world bank"],
        "Gold Demand": ["demand", "purchase", "jewelry", "investment", "etf"],
        "Technical": ["resistance", "support", "breakout", "trend", "technical"],
        "USD": ["dollar", "usd", "dxy"],
        "Rates": ["interest rate", "yield", "bond", "treasury"],
    }
    
    for category, keywords in category_keywords.items():
        if any(kw in text_lower for kw in keywords):
            categories.append(category)
    
    return categories


def _analyze_sentiment(text: str) -> tuple[str, float]:
    """
    Simple keyword-based sentiment analysis.
    In production, use a proper ML model or API.
    """
    text_lower = text.lower()
    
    positive_words = [
        "bullish", "rally", "surge", "gain", "rise", "up", "higher",
        "support", "breakout", "growth", "strong", "positive", "buy",
        "soar", "jump", "advance", "improve", "optimistic"
    ]
    
    negative_words = [
        "bearish", "fall", "drop", "decline", "down", "lower", "sell",
        "resistance", "correction", "weak", "negative", "concern",
        "plunge", "slump", "retreat", "worsen", "pessimistic"
    ]
    
    gold_positive = [
        "gold up", "gold price", "safe haven", "inflation hedge",
        "central bank buys", "demand rises", "bullion"
    ]
    
    gold_negative = [
        "gold down", "dollar strength", "risk on", "profit taking",
        "selling pressure", "headwinds"
    ]
    
    score = 0.0
    
    for word in positive_words:
        if word in text_lower:
            score += 0.1
    
    for word in negative_words:
        if word in text_lower:
            score -= 0.1
    
    for phrase in gold_positive:
        if phrase in text_lower:
            score += 0.15
    
    for phrase in gold_negative:
        if phrase in text_lower:
            score -= 0.15
    
    # Clamp score
    score = max(-1.0, min(1.0, score))
    
    if score > 0.1:
        sentiment = "positive"
    elif score < -0.1:
        sentiment = "negative"
    else:
        sentiment = "neutral"
    
    return sentiment, score


def _generate_mock_news(
    start_date: datetime,
    end_date: datetime,
    max_results: int,
) -> NewsData:
    """Generate realistic mock news data for testing."""
    np.random.seed(42)
    
    # Sample news templates
    news_templates = [
        {
            "title": "Gold Prices Rally on Weaker Dollar, Fed Rate Cut Expectations",
            "categories": ["Fed", "USD", "Gold Demand"],
            "sentiment": "positive",
            "score": 0.6,
        },
        {
            "title": "Federal Reserve Signals Potential Rate Cuts in Coming Months",
            "categories": ["Fed", "Inflation"],
            "sentiment": "positive",
            "score": 0.5,
        },
        {
            "title": "Central Banks Continue Gold Buying Spree Amid Geopolitical Uncertainty",
            "categories": ["Central Bank", "Geopolitical"],
            "sentiment": "positive",
            "score": 0.7,
        },
        {
            "title": "Gold Falls as Strong US Jobs Data Supports Dollar",
            "categories": ["USD", "Fed"],
            "sentiment": "negative",
            "score": -0.5,
        },
        {
            "title": "Inflation Data Shows Cooling Prices, Gold Retreats",
            "categories": ["Inflation"],
            "sentiment": "negative",
            "score": -0.4,
        },
        {
            "title": "Technical Analysis: Gold Testing Key Resistance at $2000",
            "categories": ["Technical"],
            "sentiment": "neutral",
            "score": 0.0,
        },
        {
            "title": "Rising Treasury Yields Pressure Gold Prices",
            "categories": ["Rates", "USD"],
            "sentiment": "negative",
            "score": -0.3,
        },
        {
            "title": "Geopolitical Tensions Drive Safe Haven Demand for Gold",
            "categories": ["Geopolitical", "Gold Demand"],
            "sentiment": "positive",
            "score": 0.8,
        },
        {
            "title": "Gold ETFs See Inflows as Market Volatility Increases",
            "categories": ["Gold Demand", "Geopolitical"],
            "sentiment": "positive",
            "score": 0.4,
        },
        {
            "title": "Market Outlook: Mixed Signals for Gold Amid Dollar Strength",
            "categories": ["USD"],
            "sentiment": "neutral",
            "score": 0.0,
        },
    ]
    
    sources = [
        "Reuters", "Bloomberg", "CNBC", "Kitco", "Gold-Eagle",
        "FX Street", "Investing.com", "MarketWatch"
    ]
    
    news_items = []
    date_range = pd.date_range(start=start_date, end=end_date, freq="h")
    
    for i in range(min(max_results, len(news_templates) * 3)):
        template = news_templates[i % len(news_templates)]
        
        # Vary the sentiment slightly
        score = template["score"] + np.random.uniform(-0.1, 0.1)
        score = max(-1.0, min(1.0, score))
        
        sentiment = "neutral"
        if score > 0.1:
            sentiment = "positive"
        elif score < -0.1:
            sentiment = "negative"
        
        news_item = GoldNewsItem(
            title=template["title"],
            description=f"Analysis and market commentary on gold price action and market dynamics.",
            source=np.random.choice(sources),
            url=f"https://example.com/news/{i}",
            published_at=date_range[i % len(date_range)] if i < len(date_range) else datetime.now(),
            sentiment=sentiment,
            sentiment_score=score,
            relevance_score=np.random.uniform(0.5, 1.0),
            categories=template["categories"],
        )
        
        news_items.append(news_item)
    
    # Sort by date
    news_items.sort(key=lambda x: x.published_at, reverse=True)
    
    return NewsData(
        news=news_items,
        source="mock",
    )


# News API endpoint helpers
NEWS_API_SOURCES = {
    "major": [
        "reuters", "bloomberg", "associated-press", "cnbc",
        "the-wall-street-journal", "financial-times",
    ],
    "financial": [
        "marketwatch", "investing-com", "fx-street", "kitco",
        "gold-eagle", "mineweb",
    ],
    "business": [
        "business-insider", "fortune", "forbes", "economist",
    ],
}
