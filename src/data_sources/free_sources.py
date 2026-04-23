"""
Additional Free Data Sources for Gold

This module provides alternative data sources that don't require API keys:
- Direct CSV/Excel import
- Central Bank websites
- Public data repositories
"""

from typing import Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import pandas as pd
import requests


@dataclass
class DataSourceResult:
    """Result from a data source."""
    success: bool
    data: pd.DataFrame = None
    message: str = ""
    source_name: str = ""


def fetch_gold_from_stooq(start_date: str, end_date: str, symbol: str = "XAUUSD") -> DataSourceResult:
    """
    Fetch gold data from Stooq (requires free API key now).
    
    Stooq provides free daily data but requires registration.
    Sign up at: https://stooq.com/q/d/?s=goldd&get_apikey
    
    Args:
        start_date: Start date YYYY-MM-DD
        end_date: End date YYYY-MM-DD
        symbol: Symbol to fetch (not used, kept for compatibility)
    
    Returns:
        DataSourceResult with DataFrame
    """
    # Stooq now requires API key registration
    # For now, return a helpful message
    return DataSourceResult(
        success=False,
        message=(
            "Stooq now requires free API key registration. "
            "Sign up at: https://stooq.com/q/d/?s=goldd&get_apikey "
            "For immediate use, the system will fall back to mock data."
        ),
        source_name="stooq"
    )


def fetch_gold_from_yahoo_finance(symbol: str = "GC=F") -> DataSourceResult:
    """
    Fetch gold data from Yahoo Finance (uses yfinance package).
    
    Args:
        symbol: Yahoo Finance symbol (GC=F for Gold Futures, GLD for ETF)
    
    Returns:
        DataSourceResult with DataFrame
    """
    try:
        import yfinance as yf
        
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="max")
        
        if df.empty:
            return DataSourceResult(
                success=False,
                message="No data returned from Yahoo Finance",
                source_name="yahoo"
            )
        
        df = df.reset_index()
        df.columns = [c.lower() for c in df.columns]
        
        # Rename datetime column
        if "datetime" in df.columns:
            df["timestamp"] = df["datetime"]
        elif "date" in df.columns:
            df["timestamp"] = df["date"]
        
        return DataSourceResult(
            success=True,
            data=df,
            message=f"Fetched {len(df)} records",
            source_name="yahoo"
        )
        
    except ImportError:
        return DataSourceResult(
            success=False,
            message="yfinance not installed. Run: pip install yfinance",
            source_name="yahoo"
        )
    except Exception as e:
        return DataSourceResult(
            success=False,
            message=f"Yahoo Finance error: {str(e)}",
            source_name="yahoo"
        )


def fetch_fred_public_data(series_id: str, start_date: str, end_date: str) -> DataSourceResult:
    """
    Fetch data from FRED without API key (limited access).
    
    Some FRED series are available without authentication.
    
    Args:
        series_id: FRED series ID
        start_date: Start date
        end_date: End date
    
    Returns:
        DataSourceResult with DataFrame
    """
    try:
        # FRED public CSV endpoint (no API key needed)
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
        
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        from io import StringIO
        df = pd.read_csv(StringIO(response.text))
        
        if df.empty:
            return DataSourceResult(
                success=False,
                message="No data returned",
                source_name="fred_public"
            )
        
        df.columns = ["timestamp", "value"]
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        
        # Filter by date
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        df = df[(df["timestamp"] >= start_dt) & (df["timestamp"] <= end_dt)]
        
        return DataSourceResult(
            success=True,
            data=df,
            message=f"Fetched {len(df)} records",
            source_name="fred_public"
        )
        
    except Exception as e:
        return DataSourceResult(
            success=False,
            message=f"FRED public error: {str(e)}",
            source_name="fred_public"
        )


def import_csv(file_path: str) -> DataSourceResult:
    """
    Import gold data from a CSV file.
    
    Expected format:
    timestamp, open, high, low, close, volume
    
    Args:
        file_path: Path to CSV file
    
    Returns:
        DataSourceResult with DataFrame
    """
    try:
        df = pd.read_csv(file_path)
        
        # Standardize column names
        df.columns = [c.lower().strip() for c in df.columns]
        
        # Try to find timestamp column
        timestamp_cols = ["timestamp", "date", "datetime", "time"]
        for col in timestamp_cols:
            if col in df.columns:
                df["timestamp"] = pd.to_datetime(df[col])
                break
        
        # Try to standardize price columns
        rename_map = {
            "open": "open",
            "high": "high", 
            "low": "low",
            "close": "close",
            "volume": "volume",
        }
        
        for old, new in rename_map.items():
            if old in df.columns and new not in df.columns:
                df[new] = df[old]
        
        return DataSourceResult(
            success=True,
            data=df,
            message=f"Imported {len(df)} records from {file_path}",
            source_name="csv"
        )
        
    except Exception as e:
        return DataSourceResult(
            success=False,
            message=f"CSV import error: {str(e)}",
            source_name="csv"
        )


def import_excel(file_path: str, sheet_name: str = 0) -> DataSourceResult:
    """
    Import gold data from an Excel file.
    
    Args:
        file_path: Path to Excel file
        sheet_name: Sheet name or index
    
    Returns:
        DataSourceResult with DataFrame
    """
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        
        # Standardize
        df.columns = [c.lower().strip() if isinstance(c, str) else c for c in df.columns]
        
        return DataSourceResult(
            success=True,
            data=df,
            message=f"Imported {len(df)} records from {file_path}",
            source_name="excel"
        )
        
    except Exception as e:
        return DataSourceResult(
            success=False,
            message=f"Excel import error: {str(e)}",
            source_name="excel"
        )


# Common FRED series IDs for gold analysis (public access)
PUBLIC_FRED_SERIES = {
    "gold_price": "GOLDAMGBD228NLBM",
    "gold_pmm": "GOLDPMGBD228NLBM",
    "vix": "VIXCLS",
    "dxy": "DTWEXBGS",
    "fed_funds": "FEDFUNDS",
    "yield_10y": "DGS10",
    "yield_2y": "DGS2",
    "cpi": "CPIAUCSL",
    "core_cpi": "CPILFESL",
    "ppi": "PPIACO",
    "unemployment": "UNRATE",
    "sp500": "SP500",
}


def fetch_multiple_fred_series(
    series_ids: list[str],
    start_date: str,
    end_date: str
) -> dict[str, DataSourceResult]:
    """
    Fetch multiple FRED series at once.
    
    Args:
        series_ids: List of FRED series IDs
        start_date: Start date
        end_date: End date
    
    Returns:
        Dictionary mapping series_id to DataSourceResult
    """
    results = {}
    
    for series_id in series_ids:
        result = fetch_fred_public_data(series_id, start_date, end_date)
        results[series_id] = result
    
    return results


class MultiSourceFetcher:
    """
    Try multiple data sources in order until one succeeds.
    
    Example:
        fetcher = MultiSourceFetcher()
        result = fetcher.fetch_gold_prices("2024-01-01", "2024-04-23")
        
        if result.success:
            print(result.data)
        else:
            print(f"Failed: {result.message}")
    """
    
    def __init__(self):
        self.last_successful_source = None
    
    def fetch_gold_prices(
        self,
        start_date: str,
        end_date: str,
        symbols: list[str] = None
    ) -> DataSourceResult:
        """
        Try multiple sources to fetch gold prices.
        
        Sources tried in order:
        1. Yahoo Finance (yfinance)
        2. Stooq
        3. FRED (public)
        """
        # Yahoo Finance symbols to try
        if symbols is None:
            symbols = ["GC=F", "XAUUSD=X", "GLD", "IAU"]
        
        # Try Yahoo Finance
        print("Trying Yahoo Finance...")
        for symbol in symbols:
            result = fetch_gold_from_yahoo_finance(symbol)
            if result.success:
                self.last_successful_source = "yahoo"
                # Filter by date
                if result.data is not None:
                    result.data = result.data[
                        (result.data["timestamp"] >= pd.to_datetime(start_date)) &
                        (result.data["timestamp"] <= pd.to_datetime(end_date))
                    ]
                return result
        
        # Try Stooq
        print("Trying Stooq...")
        result = fetch_gold_from_stooq(start_date, end_date)
        if result.success:
            self.last_successful_source = "stooq"
            return result
        
        # Try FRED (gold price)
        print("Trying FRED public data...")
        result = fetch_fred_public_data("GOLDAMGBD228NLBM", start_date, end_date)
        if result.success:
            self.last_successful_source = "fred_public"
            # Convert to standard format
            if result.data is not None:
                result.data["open"] = result.data["value"]
                result.data["high"] = result.data["value"]
                result.data["low"] = result.data["value"]
                result.data["close"] = result.data["value"]
                result.data["volume"] = 0
            return result
        
        return DataSourceResult(
            success=False,
            message="All sources failed",
            source_name="none"
        )
    
    def fetch_macro_data(
        self,
        start_date: str,
        end_date: str
    ) -> dict[str, pd.DataFrame]:
        """
        Fetch macro data from public sources.
        
        Returns:
            Dictionary of DataFrames for each series
        """
        results = fetch_multiple_fred_series(
            series_ids=list(PUBLIC_FRED_SERIES.values()),
            start_date=start_date,
            end_date=end_date
        )
        
        data = {}
        for series_id, result in results.items():
            if result.success:
                data[series_id] = result.data
        
        return data


# Quick test function
def test_data_sources():
    """Test all available data sources."""
    print("Testing data sources...")
    print("=" * 50)
    
    fetcher = MultiSourceFetcher()
    
    # Test gold prices
    print("\n1. Testing gold price fetch...")
    result = fetcher.fetch_gold_prices("2024-01-01", "2024-04-23")
    print(f"   Source: {result.source_name}")
    print(f"   Success: {result.success}")
    print(f"   Message: {result.message}")
    if result.success and result.data is not None:
        print(f"   Records: {len(result.data)}")
        print(f"   Sample:\n{result.data.tail(3)}")
    
    # Test macro data
    print("\n2. Testing macro data fetch...")
    macro = fetcher.fetch_macro_data("2024-01-01", "2024-04-23")
    print(f"   Sources found: {len(macro)}")
    for series, df in macro.items():
        print(f"   - {series}: {len(df)} records")
    
    print("\n" + "=" * 50)
    print("Test complete!")


if __name__ == "__main__":
    test_data_sources()
