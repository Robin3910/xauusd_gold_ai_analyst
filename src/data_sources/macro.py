"""
Macroeconomic Data Sources

Fetches macroeconomic data relevant to gold analysis from:
- FRED (Federal Reserve Economic Data)
- Yahoo Finance (for market data)
- Mock data for development
"""

from typing import Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import pandas as pd
import numpy as np
import requests


@dataclass
class MacroData:
    """Container for macroeconomic data."""
    # Interest rates
    fed_funds_rate: float = 5.25
    real_yield_10y: float = 1.8
    nominal_yield_10y: float = 4.5
    yield_curve: str = "normal"  # "inverted", "normal", "flat"
    
    # USD metrics
    dollar_index_dxy: float = 104.5
    dollar_change_1m: float = 0.0
    dollar_change_3m: float = 0.0
    
    # Inflation
    cpi_yoy: float = 3.2
    core_cpi: float = 3.8
    ppi_yoy: float = 2.1
    breakeven_inflation_10y: float = 2.3
    inflation_trend: str = "falling"  # "rising", "falling", "stable"
    
    # Risk metrics
    vix: float = 18.0
    hy_spread: float = 380.0  # High yield credit spread
    fear_greed_index: float = 50.0
    recession_probability: float = 20.0
    
    # Correlations
    gold_dxy_corr: float = -0.75
    gold_bonds_corr: float = 0.25
    gold_stocks_corr: float = 0.05
    correlation_regime: str = "normal"
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = "unknown"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for workflow."""
        return {
            "interest_rates": {
                "fed_funds_rate": self.fed_funds_rate,
                "real_yield_10y": self.real_yield_10y,
                "nominal_yield_10y": self.nominal_yield_10y,
                "yield_curve": self.yield_curve,
            },
            "dollar": {
                "dxy": self.dollar_index_dxy,
                "dxy_change_1m": self.dollar_change_1m,
                "dxy_change_3m": self.dollar_change_3m,
            },
            "inflation": {
                "cpi_yoy": self.cpi_yoy,
                "core_cpi": self.core_cpi,
                "ppi_yoy": self.ppi_yoy,
                "breakeven_10y": self.breakeven_inflation_10y,
                "trend": self.inflation_trend,
            },
            "risk": {
                "vix": self.vix,
                "hy_spread": self.hy_spread,
                "fear_greed_index": self.fear_greed_index,
                "recession_prob": self.recession_probability,
            },
            "correlations": {
                "gold_dxy_corr": self.gold_dxy_corr,
                "gold_bonds_corr": self.gold_bonds_corr,
                "gold_stocks_corr": self.gold_stocks_corr,
                "regime": self.correlation_regime,
            },
        }


def get_macro_data(
    end_date: Optional[str] = None,
    use_cache: bool = True,
) -> MacroData:
    """
    Fetch macroeconomic data from multiple sources.
    
    Args:
        end_date: Reference date for data (defaults to today)
        use_cache: Whether to use cached data
    
    Returns:
        MacroData object with all macro indicators
    """
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    # Try to fetch from FRED first
    try:
        return _fetch_fred_macro(end_date)
    except Exception as e:
        print(f"FRED fetch failed: {e}, using mock data")
        return _generate_mock_macro(end_date)


def get_fred_data(
    series_id: str,
    start_date: str,
    end_date: str,
    api_key: Optional[str] = None,
) -> pd.Series:
    """
    Fetch specific series from FRED.
    
    Args:
        series_id: FRED series ID
        start_date: Start date
        end_date: End date
        api_key: FRED API key
    
    Returns:
        pandas Series with the data
    """
    import os
    
    if api_key is None:
        api_key = os.getenv("FRED_API_KEY")
    
    if api_key is None:
        raise ValueError("FRED_API_KEY required")
    
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "observation_start": start_date,
        "observation_end": end_date,
    }
    
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    
    observations = data.get("observations", [])
    if not observations:
        raise ValueError(f"No data for series {series_id}")
    
    df = pd.DataFrame(observations)
    series = pd.to_numeric(df["value"], errors="coerce")
    series.index = pd.to_datetime(df["date"])
    
    return series


def _fetch_fred_macro(end_date: str) -> MacroData:
    """Fetch macro data from FRED API."""
    import os
    
    api_key = os.getenv("FRED_API_KEY")
    
    if api_key is None:
        return _generate_mock_macro(end_date)
    
    # FRED series IDs
    series_map = {
        "fed_funds": "FEDFUNDS",
        "yield_10y": "DGS10",
        "yield_2y": "DGS2",
        "ti10y": "TIP10Y",
        "dxy": "DTWEXBGS",
        "vix": "VIXCLS",
        "cpi": "CPIAUCSL",
        "core_cpi": "CPILFESL",
        "ppi": "PPIACO",
        "recession_prob": "REALTIME",  # We'll use other indicators
    }
    
    # Try to fetch each series
    data = {}
    end_dt = pd.to_datetime(end_date)
    start_dt = end_dt - timedelta(days=90)
    
    for name, series_id in series_map.items():
        try:
            series = get_fred_data(
                series_id=series_id,
                start_date=start_dt.strftime("%Y-%m-%d"),
                end_date=end_dt.strftime("%Y-%m-%d"),
                api_key=api_key,
            )
            data[name] = series.iloc[-1]
        except Exception:
            data[name] = None
    
    # Build macro data
    macro = MacroData(
        fed_funds_rate=data.get("fed_funds") or 5.25,
        nominal_yield_10y=data.get("yield_10y") or 4.5,
        dollar_index_dxy=_calculate_dxy(data.get("dxy")),
        vix=data.get("vix") or 18.0,
        source="fred",
    )
    
    # Calculate derived values
    if data.get("ti10y"):
        macro.real_yield_10y = macro.nominal_yield_10y - data["ti10y"]
    
    if data.get("yield_2y") and data.get("yield_10y"):
        macro.yield_curve = _get_yield_curve_shape(
            data["yield_2y"], 
            data["yield_10y"]
        )
    
    if data.get("cpi") and data.get("core_cpi"):
        macro.cpi_yoy = _calculate_yoy_change(data["cpi"])
        macro.core_cpi = _calculate_yoy_change(data["core_cpi"])
        macro.ppi_yoy = _calculate_yoy_change(data["ppi"]) if data.get("ppi") else 2.1
        macro.breakeven_inflation_10y = macro.nominal_yield_10y - macro.real_yield_10y
        macro.inflation_trend = _get_inflation_trend(macro.cpi_yoy)
    
    return macro


def _calculate_dxy(dxy_value: float) -> float:
    """Calculate USD Index value."""
    # DXY is already the index value
    return dxy_value if dxy_value else 104.5


def _get_yield_curve_shape(yield_2y: float, yield_10y: float) -> str:
    """Determine yield curve shape."""
    spread = yield_10y - yield_2y
    if spread > 0.5:
        return "normal"
    elif spread > 0:
        return "flat"
    else:
        return "inverted"


def _calculate_yoy_change(series: float) -> float:
    """Calculate year-over-year change (simplified)."""
    # In real implementation, would compare to 12-month ago value
    return 3.2  # Default


def _get_inflation_trend(cpi: float) -> str:
    """Determine inflation trend."""
    if cpi > 4:
        return "rising"
    elif cpi < 2:
        return "falling"
    else:
        return "stable"


def _generate_mock_macro(end_date: str) -> MacroData:
    """Generate realistic mock macro data."""
    np.random.seed(42)
    
    return MacroData(
        fed_funds_rate=5.25,
        real_yield_10y=1.8,
        nominal_yield_10y=4.5,
        yield_curve="inverted",
        dollar_index_dxy=104.5 + np.random.uniform(-2, 2),
        dollar_change_1m=np.random.uniform(-2, 2),
        dollar_change_3m=np.random.uniform(-5, 5),
        cpi_yoy=3.2 + np.random.uniform(-0.5, 0.5),
        core_cpi=3.8 + np.random.uniform(-0.3, 0.3),
        ppi_yoy=2.1 + np.random.uniform(-0.5, 0.5),
        breakeven_inflation_10y=2.3 + np.random.uniform(-0.3, 0.3),
        inflation_trend="falling",
        vix=18 + np.random.uniform(-5, 10),
        hy_spread=380 + np.random.uniform(-50, 100),
        fear_greed_index=55 + np.random.uniform(-20, 30),
        recession_probability=20 + np.random.uniform(-10, 15),
        gold_dxy_corr=-0.75,
        gold_bonds_corr=0.25,
        gold_stocks_corr=0.05,
        correlation_regime="normal",
        source="mock",
    )


# Common FRED series IDs for reference
FRED_SERIES = {
    # Interest rates
    "FEDFUNDS": "Federal Funds Rate",
    "DGS10": "10-Year Treasury Rate",
    "DGS2": "2-Year Treasury Rate",
    "DGS5": "5-Year Treasury Rate",
    "DGS30": "30-Year Fixed Rate Mortgage",
    "MORTGAGE30US": "30-Year Mortgage Rate",
    
    # Inflation
    "CPIAUCSL": "Consumer Price Index (CPI)",
    "CPILFESL": "Core CPI",
    "PPIACO": "Producer Price Index",
    "PCECTPI": "PCE Price Index",
    "TIP10Y": "10-Year Breakeven Inflation Rate",
    "TIPS10Y": "10-Year TIPS Yield",
    
    # Currency
    "DTWEXBGS": "Trade Weighted USD Index (Broad)",
    "DTWEXM": "Trade Weighted USD Index (Major)",
    
    # Risk
    "VIXCLS": "CBOE Volatility Index",
    "BAMLM0A0CM": "Option-Adjusted Spread (Corporate Bonds)",
    
    # Gold
    "GOLDAMGBD228NLBM": "Gold Fixing Price (London)",
    "GOLDPMGBD228NLBM": "Gold Fixing Price (PM)",
    
    # Economic indicators
    "UNRATE": "Unemployment Rate",
    "NROU": "Natural Rate of Unemployment",
    "GDP": "Real GDP",
    "INDPRO": "Industrial Production",
    "RETAILMRKT": "Retail and Food Services Sales",
    
    # Consumer
    "PCE": "Personal Consumption Expenditures",
    "MICH": "University of Michigan Consumer Sentiment",
}
