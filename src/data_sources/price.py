"""
Gold Price Data Sources

Fetches XAUUSD price data from various sources:
- Yahoo Finance (free, no API key needed)
- Stooq (free, no API key needed)
- FRED (Federal Reserve Economic Data)
- Direct CSV/Excel import
"""

from typing import Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
import numpy as np
import requests
from functools import lru_cache


class PriceSource(Enum):
    YAHOO = "yahoo"
    STOOQ = "stooq"
    FRED = "fred"
    MOCK = "mock"


@dataclass
class GoldPriceData:
    """Container for gold price data."""
    symbol: str = "XAUUSD"
    source: str = "unknown"
    prices_df: pd.DataFrame = field(default_factory=pd.DataFrame)
    current_price: float = 0.0
    daily_change: float = 0.0
    daily_change_pct: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if not self.prices_df.empty:
            self.current_price = float(self.prices_df["close"].iloc[-1])
            if len(self.prices_df) > 1:
                prev_close = float(self.prices_df["close"].iloc[-2])
                self.daily_change = self.current_price - prev_close
                self.daily_change_pct = (self.daily_change / prev_close) * 100


def get_gold_prices(
    start_date: Union[str, datetime],
    end_date: Optional[Union[str, datetime]] = None,
    interval: str = "1d",
    source: str = "auto",
    symbol: str = "GC=F",
) -> GoldPriceData:
    """
    Fetch gold price data from specified source.
    
    Args:
        start_date: Start date (YYYY-MM-DD or datetime)
        end_date: End date (YYYY-MM-DD or datetime), defaults to today
        interval: Data interval (1d, 1h, 5m, etc.)
        source: Data source ("auto", "yahoo", "stooq", "fred", "mock")
                "auto" will try multiple sources until one works
        symbol: Trading symbol for the source
    
    Returns:
        GoldPriceData object with price DataFrame
    """
    # Parse dates
    if isinstance(start_date, str):
        start_date = pd.to_datetime(start_date)
    if end_date is None:
        end_date = datetime.now()
    elif isinstance(end_date, str):
        end_date = pd.to_datetime(end_date)
    
    # Auto-detect source
    if source == "auto":
        result = _fetch_auto(start_date, end_date)
        return result
    
    # Route to appropriate source
    if source == "yahoo":
        return _fetch_yahoo_gold(start_date, end_date, interval, symbol)
    elif source == "stooq":
        return _fetch_stooq_gold(start_date, end_date)
    elif source == "fred":
        return _fetch_fred_gold(start_date, end_date)
    elif source == "mock":
        return _generate_mock_gold_prices(start_date, end_date)
    else:
        raise ValueError(f"Unknown source: {source}")


def get_market_data(
    symbols: list[str] = None,
    start_date: str = None,
    end_date: str = None,
) -> dict[str, pd.DataFrame]:
    """
    Fetch market data for multiple symbols.
    
    Args:
        symbols: List of trading symbols
        start_date: Start date
        end_date: End date
    
    Returns:
        Dictionary mapping symbol to DataFrame
    """
    if symbols is None:
        symbols = [
            "GC=F",   # Gold Futures
            "DX-Y.NYB",  # US Dollar Index
            "^VIX",   # VIX
            "^TNX",   # 10-Year Treasury Yield
        ]
    
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    
    data = {}
    for symbol in symbols:
        try:
            price_data = get_gold_prices(
                start_date=start_date,
                end_date=end_date,
                source="auto",
                symbol=symbol,
            )
            data[symbol] = price_data.prices_df
        except Exception as e:
            print(f"Warning: Failed to fetch {symbol}: {e}")
            data[symbol] = pd.DataFrame()
    
    return data


def _fetch_auto(start_date: datetime, end_date: datetime) -> GoldPriceData:
    """
    Automatically try multiple sources until one works.
    
    Sources tried in order:
    1. Yahoo Finance (via yfinance)
    2. Stooq (public)
    3. FRED (Gold fixing price)
    4. Mock data (fallback)
    """
    from io import StringIO
    
    # Try Yahoo Finance first
    try:
        import yfinance as yf
        ticker = yf.Ticker("GC=F")
        df = ticker.history(start=start_date, end=end_date)
        if not df.empty:
            df = df.reset_index()
            df.columns = [c.lower() for c in df.columns]
            if "datetime" in df.columns:
                df["timestamp"] = pd.to_datetime(df["datetime"])
            elif "date" in df.columns:
                df["timestamp"] = pd.to_datetime(df["date"])
            return GoldPriceData(
                symbol="GC=F",
                source="yahoo_finance",
                prices_df=df,
            )
    except Exception as e:
        print(f"Yahoo Finance failed: {e}")
    
    # Try Stooq
    try:
        symbol = "GOLDD"
        start_str = start_date.strftime("%Y%m%d")
        end_str = end_date.strftime("%Y%m%d")
        url = f"https://stooq.com/q/d/l/?s={symbol.lower()}&d1={start_str}&d2={end_str}&i=d"
        
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        df = pd.read_csv(StringIO(response.text))
        if not df.empty:
            df.columns = [c.lower() for c in df.columns]
            df["timestamp"] = pd.to_datetime(df["date"])
            return GoldPriceData(
                symbol="XAUUSD",
                source="stooq",
                prices_df=df,
            )
    except Exception as e:
        print(f"Stooq failed: {e}")
    
    # Try FRED public data
    try:
        url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=GOLDAMGBD228NLBM"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        df = pd.read_csv(StringIO(response.text))
        if not df.empty:
            df.columns = ["timestamp", "close"]
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df["open"] = df["close"]
            df["high"] = df["close"] * 1.002
            df["low"] = df["close"] * 0.998
            df["volume"] = 0
            
            # Filter by date
            df = df[(df["timestamp"] >= start_date) & (df["timestamp"] <= end_date)]
            
            return GoldPriceData(
                symbol="XAUUSD",
                source="fred",
                prices_df=df,
            )
    except Exception as e:
        print(f"FRED failed: {e}")
    
    # Fallback to mock
    print("Using mock data (all sources failed)")
    return _generate_mock_gold_prices(start_date, end_date)


def _fetch_yahoo_gold(
    start_date: datetime,
    end_date: datetime,
    interval: str,
    symbol: str,
) -> GoldPriceData:
    """Fetch gold data from Yahoo Finance."""
    import yfinance as yf
    
    # Use XAUUSD USD ETF proxy if futures not available
    proxy_symbols = ["GC=F", "XAUUSD=X", "GLD"]
    
    df = None
    used_symbol = symbol
    
    for sym in proxy_symbols:
        try:
            ticker = yf.Ticker(sym)
            df = ticker.history(
                start=start_date.strftime("%Y-%m-%d"),
                end=end_date.strftime("%Y-%m-%d"),
                interval=interval,
            )
            if not df.empty:
                used_symbol = sym
                break
        except Exception:
            continue
    
    if df is None or df.empty:
        # Fallback to mock data
        return _generate_mock_gold_prices(start_date, end_date)
    
    # Rename columns to standard format
    df = df.reset_index()
    df.columns = [c.lower() for c in df.columns]
    
    # Ensure datetime format
    if "datetime" in df.columns:
        df["timestamp"] = pd.to_datetime(df["datetime"])
    elif "date" in df.columns:
        df["timestamp"] = pd.to_datetime(df["date"])
    else:
        df["timestamp"] = df.index
    
    return GoldPriceData(
        symbol=used_symbol,
        source="yahoo_finance",
        prices_df=df,
    )


def _fetch_fred_gold(start_date: datetime, end_date: datetime) -> GoldPriceData:
    """Fetch gold data from FRED (Federal Reserve Economic Data)."""
    import os
    
    api_key = os.getenv("FRED_API_KEY")
    
    # FRED series IDs for gold
    gold_series = "GOLDAMGBD228NLBM"  # Gold Fixing Price in London
    
    if api_key is None:
        print("Warning: FRED_API_KEY not set, using mock data")
        return _generate_mock_gold_prices(start_date, end_date)
    
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": gold_series,
        "api_key": api_key,
        "file_type": "json",
        "observation_start": start_date.strftime("%Y-%m-%d"),
        "observation_end": end_date.strftime("%Y-%m-%d"),
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        observations = data.get("observations", [])
        
        if not observations:
            return _generate_mock_gold_prices(start_date, end_date)
        
        # Convert to DataFrame
        df = pd.DataFrame(observations)
        df = df.rename(columns={"date": "timestamp", "value": "close"})
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        
        # Fill missing values
        df["close"] = df["close"].ffill()
        
        # Add OHLC approximation (using close as all values)
        df["open"] = df["close"]
        df["high"] = df["close"] * 1.002  # Approximate
        df["low"] = df["close"] * 0.998
        df["volume"] = 0
        
        return GoldPriceData(
            symbol="XAUUSD",
            source="fred",
            prices_df=df,
        )
        
    except Exception as e:
        print(f"FRED fetch failed: {e}")
        return _generate_mock_gold_prices(start_date, end_date)


def _generate_mock_gold_prices(
    start_date: datetime,
    end_date: datetime,
    initial_price: float = 1950.0,
) -> GoldPriceData:
    """Generate realistic mock gold price data for testing."""
    np.random.seed(42)
    
    # Generate trading days
    date_range = pd.bdate_range(start=start_date, end=end_date)
    n_days = len(date_range)
    
    if n_days < 10:
        n_days = 180
        date_range = pd.bdate_range(end=end_date, periods=n_days)
    
    # Simulate gold price with realistic characteristics
    base_price = initial_price
    daily_volatility = 0.008  # ~0.8% daily vol
    
    # Price components
    trend = 0.0002  # Slight upward drift
    mean_reversion_strength = 0.1
    
    # Generate returns
    returns = np.random.normal(trend, daily_volatility, n_days)
    
    # Add some autocorrelation (momentum)
    for i in range(1, n_days):
        returns[i] += returns[i-1] * 0.1
    
    # Calculate prices
    prices = base_price * (1 + returns).cumprod()
    
    # Add a trend change mid-period
    mid = n_days // 2
    prices[mid:] *= 1.05  # 5% rally
    
    # Generate OHLC
    data = []
    for i, (date, close) in enumerate(zip(date_range, prices)):
        daily_range = close * daily_volatility * np.random.uniform(0.5, 1.5)
        
        open_price = close + np.random.uniform(-daily_range * 0.5, daily_range * 0.5)
        high = max(open_price, close) + abs(np.random.normal(0, daily_range * 0.5))
        low = min(open_price, close) - abs(np.random.normal(0, daily_range * 0.5))
        volume = int(np.random.lognormal(12, 0.5))  # Lognormal volume
        
        data.append({
            "timestamp": date,
            "open": open_price,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        })
    
    df = pd.DataFrame(data)
    
    return GoldPriceData(
        symbol="XAUUSD",
        source="mock",
        prices_df=df,
    )


# Cached price data for repeated queries
@lru_cache(maxsize=32)
def get_cached_gold_prices(
    start_date: str,
    end_date: str,
    source: str = "yahoo",
) -> GoldPriceData:
    """Get cached gold prices to reduce API calls."""
    return get_gold_prices(
        start_date=start_date,
        end_date=end_date,
        source=source,
    )
