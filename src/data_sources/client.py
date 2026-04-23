"""
Gold Data Client

Unified client for fetching and managing all gold-related data.
Combines price, macro, news, CFTC, and fundamental data.
"""

from typing import Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import pandas as pd

from src.data_sources.price import (
    get_gold_prices,
    get_market_data,
    GoldPriceData,
)
from src.data_sources.macro import (
    get_macro_data,
    MacroData,
)
from src.data_sources.news import (
    get_gold_news,
    NewsData,
)
from src.data_sources.cftc import (
    get_cftc_data,
    CftcData,
)
from src.data_sources.fundamentals import (
    get_gold_fundamentals,
    GoldFundamentals,
)


@dataclass
class GoldDataClient:
    """
    Unified data client for XAUUSD analysis.
    
    Provides a single interface to fetch all required data
    for the gold analysis framework.
    
    Example:
        client = GoldDataClient()
        
        # Fetch all data
        client.fetch_all()
        
        # Access data
        print(client.prices.prices_df)
        print(client.macro.cpi_yoy)
        print(client.news.positive_count)
        
        # Run analysis
        result = run_gold_analysis(
            prices_df=client.prices.prices_df,
            macro_data=client.macro.to_dict(),
            news_data=client.news.to_list(),
            fundamental_data=client.fundamentals.to_dict(),
            sentiment_data=client.sentiment_data,
        )
    """
    
    # Data containers
    prices: Optional[GoldPriceData] = None
    macro: Optional[MacroData] = None
    news: Optional[NewsData] = None
    cftc: Optional[CftcData] = None
    fundamentals: Optional[GoldFundamentals] = None
    
    # Sentiment data (derived from multiple sources)
    sentiment_data: dict = field(default_factory=dict)
    
    # Configuration
    start_date: str = ""
    end_date: str = ""
    price_source: str = "yahoo"
    
    # Metadata
    fetched_at: Optional[datetime] = None
    errors: list = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize with default dates."""
        if not self.end_date:
            self.end_date = datetime.now().strftime("%Y-%m-%d")
        if not self.start_date:
            self.start_date = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
    
    def fetch_all(
        self,
        fetch_prices: bool = True,
        fetch_macro: bool = True,
        fetch_news: bool = True,
        fetch_cftc: bool = True,
        fetch_fundamentals: bool = True,
    ) -> "GoldDataClient":
        """
        Fetch all data sources.
        
        Args:
            fetch_prices: Fetch price data
            fetch_macro: Fetch macro data
            fetch_news: Fetch news data
            fetch_cftc: Fetch CFTC data
            fetch_fundamentals: Fetch fundamental data
        
        Returns:
            Self for chaining
        """
        self.errors = []
        self.fetched_at = datetime.now()
        
        if fetch_prices:
            self.fetch_prices()
        
        if fetch_macro:
            self.fetch_macro()
        
        if fetch_news:
            self.fetch_news()
        
        if fetch_cftc:
            self.fetch_cftc()
        
        if fetch_fundamentals:
            self.fetch_fundamentals()
        
        # Build sentiment data from all sources
        self._build_sentiment_data()
        
        return self
    
    def fetch_prices(self) -> GoldPriceData:
        """Fetch price data."""
        try:
            self.prices = get_gold_prices(
                start_date=self.start_date,
                end_date=self.end_date,
                source=self.price_source,
            )
        except Exception as e:
            self.errors.append(f"Price fetch error: {e}")
            # Generate mock data as fallback
            from src.data_sources.price import _generate_mock_gold_prices
            self.prices = _generate_mock_gold_prices(
                start_date=pd.to_datetime(self.start_date),
                end_date=pd.to_datetime(self.end_date),
            )
        
        return self.prices
    
    def fetch_macro(self) -> MacroData:
        """Fetch macroeconomic data."""
        try:
            self.macro = get_macro_data(end_date=self.end_date)
        except Exception as e:
            self.errors.append(f"Macro fetch error: {e}")
            from src.data_sources.macro import _generate_mock_macro
            self.macro = _generate_mock_macro(self.end_date)
        
        return self.macro
    
    def fetch_news(
        self,
        days_back: int = 7,
        max_results: int = 100,
    ) -> NewsData:
        """Fetch news data."""
        try:
            self.news = get_gold_news(
                end_date=self.end_date,
                days_back=days_back,
                max_results=max_results,
            )
        except Exception as e:
            self.errors.append(f"News fetch error: {e}")
            from src.data_sources.news import _generate_mock_news
            self.news = _generate_mock_news(
                start_date=pd.to_datetime(self.end_date) - timedelta(days=days_back),
                end_date=pd.to_datetime(self.end_date),
                max_results=max_results,
            )
        
        return self.news
    
    def fetch_cftc(self) -> CftcData:
        """Fetch CFTC positioning data."""
        try:
            self.cftc = get_cftc_data(end_date=self.end_date)
        except Exception as e:
            self.errors.append(f"CFTC fetch error: {e}")
            from src.data_sources.cftc import _generate_mock_cftc
            self.cftc = _generate_mock_cftc(datetime.now())
        
        return self.cftc
    
    def fetch_fundamentals(self) -> GoldFundamentals:
        """Fetch fundamental data."""
        try:
            self.fundamentals = get_gold_fundamentals(end_date=self.end_date)
        except Exception as e:
            self.errors.append(f"Fundamentals fetch error: {e}")
            from src.data_sources.fundamentals import _generate_mock_fundamentals
            self.fundamentals = _generate_mock_fundamentals(datetime.now())
        
        return self.fundamentals
    
    def _build_sentiment_data(self):
        """Build consolidated sentiment data from all sources."""
        sentiment = {}
        
        # CFTC sentiment
        if self.cftc:
            sentiment["cftc"] = {
                "long_positions": self.cftc.long_positions,
                "short_positions": self.cftc.short_positions,
                "net_position": self.cftc.net_position,
                "open_interest": self.cftc.open_interest,
            }
        
        # News sentiment
        if self.news:
            sentiment["survey"] = {
                "bullish_pct": min(self.news.positive_count / max(len(self.news.news), 1) * 100 + 30, 70),
                "bearish_pct": min(self.news.negative_count / max(len(self.news.news), 1) * 100 + 20, 60),
                "neutral_pct": max(100 - (self.news.positive_count + self.news.negative_count) / max(len(self.news.news), 1) * 100, 20),
            }
        
        # Risk sentiment
        if self.macro:
            sentiment["risk"] = {
                "vix": self.macro.vix,
                "risk_score": 50 + (50 - self.macro.vix) if self.macro.vix else 50,
                "gold_sentiment": 50 + self.news.avg_sentiment * 50 if self.news else 50,
            }
        
        # ETF flows (from fundamentals)
        if self.fundamentals:
            sentiment["etf"] = {
                "holdings_change_pct": 1.0,  # Would need time-series data
                "inflow_7d": 0,
                "inflow_30d": 0,
            }
        
        # Technical consensus
        sentiment["consensus"] = {
            "analyst_bullish_pct": 50,
            "analyst_bearish_pct": 30,
            "recommendation": "neutral",
        }
        
        self.sentiment_data = sentiment
    
    def get_analysis_data(self) -> dict:
        """
        Get all data formatted for the gold analysis workflow.
        
        Returns:
            Dictionary with all data for analysis
        """
        return {
            "prices_df": self.prices.prices_df if self.prices else None,
            "macro_data": self.macro.to_dict() if self.macro else {},
            "news_data": self.news.to_list() if self.news else [],
            "fundamental_data": self.fundamentals.to_dict() if self.fundamentals else {},
            "sentiment_data": self.sentiment_data,
            "metadata": {
                "fetched_at": self.fetched_at.isoformat() if self.fetched_at else None,
                "start_date": self.start_date,
                "end_date": self.end_date,
                "errors": self.errors,
            }
        }
    
    def get_summary(self) -> str:
        """Get a human-readable summary of fetched data."""
        lines = ["Gold Data Summary", "=" * 50]
        
        if self.prices:
            lines.append(f"\nPrices:")
            lines.append(f"  Current: ${self.prices.current_price:.2f}")
            lines.append(f"  Daily Change: {self.prices.daily_change_pct:+.2f}%")
            lines.append(f"  Source: {self.prices.source}")
        
        if self.macro:
            lines.append(f"\nMacroeconomics:")
            lines.append(f"  Fed Funds: {self.macro.fed_funds_rate:.2f}%")
            lines.append(f"  Real Yield 10Y: {self.macro.real_yield_10y:.2f}%")
            lines.append(f"  CPI YoY: {self.macro.cpi_yoy:.1f}%")
            lines.append(f"  DXY: {self.macro.dollar_index_dxy:.2f}")
            lines.append(f"  VIX: {self.macro.vix:.1f}")
        
        if self.news:
            lines.append(f"\nNews:")
            lines.append(f"  Articles: {len(self.news.news)}")
            lines.append(f"  Positive: {self.news.positive_count}")
            lines.append(f"  Negative: {self.news.negative_count}")
            lines.append(f"  Neutral: {self.news.neutral_count}")
        
        if self.cftc:
            lines.append(f"\nCFTC Positioning:")
            lines.append(f"  Net Position: {self.cftc.net_position:,.0f}")
            lines.append(f"  Long/Short Ratio: {self.cftc.long_short_ratio:.2f}")
            lines.append(f"  Sentiment: {self.cftc.speculative_sentiment}")
        
        if self.fundamentals:
            lines.append(f"\nFundamentals:")
            lines.append(f"  Annual Demand: {self.fundamentals.total_demand_y:,.0f} tonnes")
            lines.append(f"  Annual Supply: {self.fundamentals.total_supply_y:,.0f} tonnes")
            lines.append(f"  CB Quarterly Purchase: {self.fundamentals.cb_quarterly_purchase:.0f} tonnes")
            lines.append(f"  AISC: ${self.fundamentals.aisc:.0f}/oz")
        
        if self.errors:
            lines.append(f"\nErrors:")
            for err in self.errors:
                lines.append(f"  - {err}")
        
        return "\n".join(lines)


def quick_analysis(
    symbol: str = "XAUUSD",
    days_back: int = 180,
    show_reasoning: bool = False,
) -> dict:
    """
    Quick analysis with automatic data fetching.
    
    Args:
        symbol: Trading symbol
        days_back: Days of historical data
        show_reasoning: Show detailed reasoning
    
    Returns:
        Analysis results
    """
    from src.gold_agents.workflow import run_gold_analysis
    
    # Create client and fetch data
    client = GoldDataClient(
        start_date=(datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d"),
        end_date=datetime.now().strftime("%Y-%m-%d"),
    )
    
    client.fetch_all()
    
    # Run analysis
    data = client.get_analysis_data()
    
    result = run_gold_analysis(
        symbol=symbol,
        prices_df=data["prices_df"],
        macro_data=data["macro_data"],
        news_data=data["news_data"],
        fundamental_data=data["fundamental_data"],
        sentiment_data=data["sentiment_data"],
        show_reasoning=show_reasoning,
    )
    
    # Add data info
    result["data_summary"] = client.get_summary()
    
    return result
