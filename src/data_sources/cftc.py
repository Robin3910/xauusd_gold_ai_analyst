"""
CFTC Commitment of Traders Data Source

Fetches gold futures positioning data from CFTC.
Data shows non-commercial (speculative) and commercial positioning.
"""

from typing import Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import pandas as pd
import numpy as np
import requests


@dataclass
class CftcData:
    """Container for CFTC positioning data."""
    # Position data
    long_positions: float = 0.0
    short_positions: float = 0.0
    net_position: float = 0.0
    open_interest: float = 0.0
    
    # Changes
    change_long: float = 0.0
    change_short: float = 0.0
    change_net: float = 0.0
    
    # Ratios
    long_short_ratio: float = 1.0
    net_as_pct_oi: float = 0.0
    
    # Derived metrics
    speculative_sentiment: str = "neutral"  # "bullish", "bearish", "neutral"
    crowding_indicator: float = 0.5  # 0-1, higher = more crowded
    
    # Metadata
    report_date: datetime = field(default_factory=datetime.now)
    contract: str = "Gold Futures"
    source: str = "unknown"
    
    def to_dict(self) -> dict:
        return {
            "long_positions": self.long_positions,
            "short_positions": self.short_positions,
            "net_position": self.net_position,
            "open_interest": self.open_interest,
            "change_long": self.change_long,
            "change_short": self.change_short,
            "change_net": self.change_net,
            "long_short_ratio": self.long_short_ratio,
            "net_as_pct_oi": self.net_as_pct_oi,
            "speculative_sentiment": self.speculative_sentiment,
            "crowding_indicator": self.crowding_indicator,
            "report_date": self.report_date.isoformat(),
        }


def get_cftc_data(
    end_date: Optional[str] = None,
    use_cache: bool = True,
) -> CftcData:
    """
    Fetch CFTC gold positioning data.
    
    Args:
        end_date: Reference date
        use_cache: Whether to use cached data
    
    Returns:
        CftcData object with positioning information
    """
    if end_date is None:
        end_date = datetime.now()
    elif isinstance(end_date, str):
        end_date = pd.to_datetime(end_date)
    
    # Try CFTC API
    try:
        return _fetch_cftc_gold(end_date)
    except Exception as e:
        print(f"CFTC fetch failed: {e}")
        return _generate_mock_cftc(end_date)


def _fetch_cftc_gold(report_date: datetime) -> CftcData:
    """Fetch CFTC data from their data API."""
    
    # CFTC publishes data every Friday, with a ~3 day lag
    # Find the most recent report date
    days_since_friday = (report_date.weekday() - 4) % 7
    report_dt = report_date - timedelta(days=days_since_friday + 2)
    
    # CFTC Historical Data API
    # Gold futures (GC) = 100 oz
    # Using the legacy format API
    
    url = "https://www.cftc.gov/dea/futures/financial_fut.htm"
    
    try:
        # Parse HTML table from CFTC website
        tables = pd.read_html(url, skiprows=1)
        
        # Find gold table (Gold = GC)
        for table in tables:
            if "Gold" in str(table) or "GC" in str(table):
                return _parse_cftc_table(table, report_dt)
        
    except Exception as e:
        print(f"CFTC HTML parse failed: {e}")
    
    # Try JSON API
    try:
        return _fetch_cftc_json(report_dt)
    except Exception:
        pass
    
    return _generate_mock_cftc(report_dt)


def _fetch_cftc_json(report_date: datetime) -> CftcData:
    """Fetch CFTC data from their JSON API."""
    
    # CFTC provide a JSON endpoint
    url = "https://api.cftc.gov/v1/reports/futures"
    
    # Gold futures market (disaggregated)
    # Markets: Gold (100 oz) = 088691
    params = {
        "marketCode": "088691",
        "reportDate": report_date.strftime("%Y-%m-%d"),
        "outputType": "json",
    }
    
    response = requests.get(url, params=params, timeout=30)
    
    if response.status_code != 200:
        raise ValueError(f"CFTC API error: {response.status_code}")
    
    data = response.json()
    
    # Parse positions
    return _parse_cftc_response(data, report_date)


def _parse_cftc_table(table: pd.DataFrame, report_date: datetime) -> CftcData:
    """Parse CFTC HTML table data."""
    # This is a simplified parser
    # In production, you'd need more robust parsing
    
    # Find the gold row
    gold_row = None
    for idx, row in table.iterrows():
        if "Gold" in str(row.values):
            gold_row = row
            break
    
    if gold_row is None:
        return _generate_mock_cftc(report_date)
    
    # Extract values (column positions vary by report format)
    # Typical columns: Market, Long, Short, Open Interest, etc.
    
    try:
        long_pos = float(gold_row.iloc[1]) if len(gold_row) > 1 else 0
        short_pos = float(gold_row.iloc[2]) if len(gold_row) > 2 else 0
        oi = float(gold_row.iloc[5]) if len(gold_row) > 5 else long_pos + short_pos
    except (ValueError, IndexError):
        return _generate_mock_cftc(report_date)
    
    return _build_cftc_data(long_pos, short_pos, oi, report_date)


def _parse_cftc_response(data: dict, report_date: datetime) -> CftcData:
    """Parse CFTC JSON response."""
    
    # Extract positions from JSON structure
    positions = data.get("positions", {})
    
    long_pos = positions.get("nonCommLong", 0)
    short_pos = positions.get("nonCommShort", 0)
    oi = positions.get("openInterest", long_pos + short_pos)
    
    return _build_cftc_data(long_pos, short_pos, oi, report_date)


def _build_cftc_data(
    long_positions: float,
    short_positions: float,
    open_interest: float,
    report_date: datetime,
) -> CftcData:
    """Build CftcData object from raw values."""
    
    net_position = long_positions - short_positions
    
    # Calculate ratios
    long_short_ratio = long_positions / short_positions if short_positions > 0 else 1.0
    net_as_pct_oi = (net_position / open_interest * 100) if open_interest > 0 else 0
    
    # Speculative sentiment
    if net_as_pct_oi > 20:
        sentiment = "bullish"
    elif net_as_pct_oi < -20:
        sentiment = "bearish"
    else:
        sentiment = "neutral"
    
    # Crowding indicator (based on concentration)
    # High net position relative to OI = crowded trade
    crowding = min(abs(net_as_pct_oi) / 30, 1.0)
    
    return CftcData(
        long_positions=long_positions,
        short_positions=short_positions,
        net_position=net_position,
        open_interest=open_interest,
        long_short_ratio=long_short_ratio,
        net_as_pct_oi=net_as_pct_oi,
        speculative_sentiment=sentiment,
        crowding_indicator=crowding,
        report_date=report_date,
        source="cftc",
    )


def _generate_mock_cftc(report_date: datetime) -> CftcData:
    """Generate realistic mock CFTC data."""
    np.random.seed(42)
    
    # Typical gold futures positioning
    base_long = 180000
    base_short = 80000
    
    # Add some variation
    long_positions = base_long + np.random.randint(-20000, 30000)
    short_positions = base_short + np.random.randint(-15000, 20000)
    open_interest = long_positions + short_positions + np.random.randint(20000, 40000)
    
    net_position = long_positions - short_positions
    
    return CftcData(
        long_positions=long_positions,
        short_positions=short_positions,
        net_position=net_position,
        open_interest=open_interest,
        change_long=np.random.randint(-10000, 15000),
        change_short=np.random.randint(-8000, 10000),
        change_net=np.random.randint(-20000, 25000),
        long_short_ratio=long_positions / short_positions if short_positions > 0 else 1.0,
        net_as_pct_oi=(net_position / open_interest * 100) if open_interest > 0 else 0,
        speculative_sentiment="bullish" if net_position > 50000 else "neutral",
        crowding_indicator=min(net_position / 150000, 1.0),
        report_date=report_date,
        source="mock",
    )


def get_historical_cftc(
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    """
    Get historical CFTC data as a DataFrame.
    
    Args:
        start_date: Start date
        end_date: End date
    
    Returns:
        DataFrame with historical positioning data
    """
    dates = pd.date_range(start=start_date, end=end_date, freq="W-FRI")
    
    data = []
    for date in dates:
        cftc = get_cftc_data(date)
        data.append({
            "date": date,
            "long_positions": cftc.long_positions,
            "short_positions": cftc.short_positions,
            "net_position": cftc.net_position,
            "open_interest": cftc.open_interest,
            "long_short_ratio": cftc.long_short_ratio,
            "net_as_pct_oi": cftc.net_as_pct_oi,
        })
    
    return pd.DataFrame(data)


# CFTC Market Codes for commodities
CFTC_MARKET_CODES = {
    "gold": "088691",      # Gold (100 oz)
    "silver": "084691",    # Silver (5000 oz)
    "copper": "085692",    # Copper
    "platinum": "076651",  # Platinum
    "palladium": "075651", # Palladium
    "crude_oil": "067651", # WTI Crude Oil
    "natural_gas": "023651", # Natural Gas
}
