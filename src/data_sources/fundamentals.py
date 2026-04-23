"""
Gold Fundamentals Data Source

Fetches gold supply, demand, and fundamental data from:
- World Gold Council (WGC)
- Metals Focus
- GFMS (Refinitiv)
- USGS (geological data)
- Mock data for development
"""

from typing import Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import pandas as pd
import numpy as np
import requests


@dataclass
class GoldFundamentals:
    """Container for gold fundamental data."""
    
    # Supply data (annual tonnes)
    mining_production_y: float = 3650.0
    scrap_supply_y: float = 1100.0
    total_supply_y: float = 4750.0
    
    # Supply trends
    mining_trend: str = "stable"  # "increasing", "stable", "decreasing"
    scrap_trend: str = "stable"
    supply_disruption_risk: str = "low"  # "low", "medium", "high"
    
    # Demand data (annual tonnes)
    jewelry_demand_y: float = 2200.0
    investment_demand_y: float = 1200.0
    cb_purchase_y: float = 1100.0
    tech_demand_y: float = 400.0
    total_demand_y: float = 4900.0
    
    # Demand trends
    jewelry_trend: str = "stable"
    investment_trend: str = "stable"
    
    # Central bank data
    cb_reserves_pct: float = 12.0  # % of total reserves
    cb_quarterly_purchase: float = 150.0  # tonnes
    cb_diversification: str = "buying"  # "buying", "selling", "neutral"
    
    # Market structure
    comex_inventory: float = 700.0  # tonnes
    etf_holdings: float = 3000.0  # tonnes
    open_interest_contracts: float = 450000.0
    spot_futures_premium: float = 0.0  # $/oz
    inventory_trend: str = "stable"
    
    # Production costs ($/oz)
    aisc: float = 1250.0  # All-in sustaining costs
    marginal_cost: float = 1400.0
    high_cost_producers_pct: float = 15.0  # % operating at loss
    
    # Seasonal patterns
    best_months: list[str] = field(default_factory=lambda: ["Sep", "Oct", "Jan"])
    worst_months: list[str] = field(default_factory=lambda: ["Mar", "Apr", "May"])
    
    # Metadata
    report_date: datetime = field(default_factory=datetime.now)
    source: str = "unknown"
    last_updated: str = "unknown"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for workflow."""
        return {
            "supply": {
                "mining_production_y": self.mining_production_y,
                "scrap_supply_y": self.scrap_supply_y,
                "total_supply_y": self.total_supply_y,
                "mining_trend": self.mining_trend,
                "scrap_trend": self.scrap_trend,
                "supply_disruption_risk": self.supply_disruption_risk,
            },
            "demand": {
                "jewelry_y": self.jewelry_demand_y,
                "investment_y": self.investment_demand_y,
                "cb_purchase_y": self.cb_purchase_y,
                "tech_y": self.tech_demand_y,
                "total_demand_y": self.total_demand_y,
                "jewelry_trend": self.jewelry_trend,
                "investment_trend": self.investment_trend,
            },
            "central_bank": {
                "purchase_q": self.cb_quarterly_purchase,
                "reserves_pct": self.cb_reserves_pct,
                "diversification_trend": self.cb_diversification,
            },
            "market_structure": {
                "comex_inventory": self.comex_inventory,
                "etf_holdings": self.etf_holdings,
                "open_interest": self.open_interest_contracts,
                "spot_futures_premium": self.spot_futures_premium,
                "inventory_trend": self.inventory_trend,
            },
            "production_costs": {
                "aisc": self.aisc,
                "current_price": 1950.0,  # Will be filled from price data
                "marginal_cost": self.marginal_cost,
                "high_cost_producers_pct": self.high_cost_producers_pct,
            }
        }
    
    @property
    def supply_demand_balance(self) -> dict:
        """Calculate supply-demand balance."""
        balance = self.total_demand_y - self.total_supply_y
        return {
            "deficit": balance > 0,
            "surplus": balance < 0,
            "balance": balance,
            "balance_pct": (balance / self.total_supply_y) * 100 if self.total_supply_y > 0 else 0,
        }


def get_gold_fundamentals(
    end_date: Optional[str] = None,
    use_cache: bool = True,
) -> GoldFundamentals:
    """
    Fetch gold fundamental data.
    
    Args:
        end_date: Reference date
        use_cache: Whether to use cached data
    
    Returns:
        GoldFundamentals object with supply/demand data
    """
    if end_date is None:
        end_date = datetime.now()
    elif isinstance(end_date, str):
        end_date = pd.to_datetime(end_date)
    
    # Try WGC/GFMS data
    try:
        return _fetch_wgc_data(end_date)
    except Exception as e:
        print(f"WGC fetch failed: {e}")
    
    return _generate_mock_fundamentals(end_date)


def _fetch_wgc_data(report_date: datetime) -> GoldFundamentals:
    """
    Fetch data from World Gold Council.
    
    Note: WGC provides quarterly demand reports.
    For real-time data, you'd need a subscription or scrape their reports.
    """
    
    # WGC publishes quarterly Gold Demand Trends report
    # Key datasets: demand by category, central bank purchases
    
    # For now, we'll try to fetch from their public API if available
    # Or fall back to the most recent known values
    
    # Example: Try WGC data endpoint
    url = "https://api.gold.org/v1/demand"
    
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            data = response.json()
            return _parse_wgc_response(data, report_date)
    except Exception:
        pass
    
    # Try USGS for production data
    try:
        return _fetch_usgs_data(report_date)
    except Exception:
        pass
    
    return _generate_mock_fundamentals(report_date)


def _fetch_usgs_data(report_date: datetime) -> GoldFundamentals:
    """Fetch production data from USGS (US Geological Survey)."""
    
    # USGS publishes annual mineral yearbooks
    url = "https://www.usgs.gov/centers/national-minerals-information-center/gold-statistics-and-information"
    
    # For now, use known global production data
    # World gold production is approximately 3,600-3,700 tonnes annually
    
    return _generate_mock_fundamentals(report_date)


def _parse_wgc_response(data: dict, report_date: datetime) -> GoldFundamentals:
    """Parse World Gold Council response."""
    
    # This would parse the actual WGC data structure
    # For now, return mock
    
    return _generate_mock_fundamentals(report_date)


def _generate_mock_fundamentals(report_date: datetime) -> GoldFundamentals:
    """Generate realistic mock fundamental data."""
    np.random.seed(42)
    
    # Based on WGC Gold Demand Trends Q3 2024
    return GoldFundamentals(
        # Supply
        mining_production_y=3650.0 + np.random.uniform(-100, 150),
        scrap_supply_y=1100.0 + np.random.uniform(-100, 100),
        total_supply_y=4750.0 + np.random.uniform(-200, 250),
        mining_trend="stable",
        scrap_trend="increasing",
        supply_disruption_risk="low",
        
        # Demand
        jewelry_demand_y=2200.0 + np.random.uniform(-200, 200),
        investment_demand_y=1200.0 + np.random.uniform(-150, 200),
        cb_purchase_y=1100.0 + np.random.uniform(-100, 150),
        tech_demand_y=400.0 + np.random.uniform(-30, 30),
        total_demand_y=4900.0 + np.random.uniform(-300, 350),
        jewelry_trend="stable",
        investment_trend="increasing",
        
        # Central banks
        cb_reserves_pct=12.0 + np.random.uniform(-2, 3),
        cb_quarterly_purchase=150.0 + np.random.uniform(-30, 50),
        cb_diversification="buying",
        
        # Market structure
        comex_inventory=700.0 + np.random.uniform(-100, 150),
        etf_holdings=3000.0 + np.random.uniform(-200, 300),
        open_interest_contracts=450000.0 + np.random.uniform(-50000, 60000),
        spot_futures_premium=np.random.uniform(-10, 15),
        inventory_trend="stable",
        
        # Production costs (typical AISC for gold miners)
        aisc=1250.0 + np.random.uniform(-50, 100),
        marginal_cost=1400.0 + np.random.uniform(-50, 100),
        high_cost_producers_pct=15.0 + np.random.uniform(-5, 8),
        
        # Seasonal (historical patterns)
        best_months=["Sep", "Oct", "Jan", "Nov"],
        worst_months=["Mar", "Apr", "May", "Jun"],
        
        report_date=report_date,
        source="mock",
        last_updated=datetime.now().strftime("%Y-%m-%d"),
    )


def get_seasonal_patterns() -> dict:
    """
    Get historical seasonal patterns for gold.
    
    Returns monthly average returns and win rates.
    """
    # Historical gold seasonal patterns (approximate)
    # Based on 20+ years of data
    
    patterns = {
        "January": {"avg_return": 2.5, "win_rate": 0.65, "description": "Strong month, Chinese New Year demand"},
        "February": {"avg_return": 1.2, "win_rate": 0.58, "description": "Good month, post-Lunar New Year"},
        "March": {"avg_return": -0.8, "win_rate": 0.45, "description": "Weak month, profit taking"},
        "April": {"avg_return": -0.5, "win_rate": 0.48, "description": "Below average"},
        "May": {"avg_return": -0.3, "win_rate": 0.50, "description": "Mixed performance"},
        "June": {"avg_return": 0.5, "win_rate": 0.52, "description": "Slight positive bias"},
        "July": {"avg_return": 1.0, "win_rate": 0.55, "description": "Improving"},
        "August": {"avg_return": 1.5, "win_rate": 0.58, "description": "Good month, monsoon season"},
        "September": {"avg_return": 2.8, "win_rate": 0.68, "description": "Best month, festival season"},
        "October": {"avg_return": 2.2, "win_rate": 0.65, "description": "Very strong, Diwali demand"},
        "November": {"avg_return": 1.8, "win_rate": 0.62, "description": "Strong, holiday season"},
        "December": {"avg_return": 0.8, "win_rate": 0.55, "description": "Moderate, profit taking"},
    }
    
    return patterns


def calculate_supply_demand_forecast(
    fundamentals: GoldFundamentals,
    months_ahead: int = 12,
) -> pd.DataFrame:
    """
    Create supply-demand forecast based on fundamentals.
    
    Args:
        fundamentals: Current fundamental data
        months_ahead: Forecast horizon
    
    Returns:
        DataFrame with monthly forecasts
    """
    dates = pd.date_range(
        start=datetime.now(),
        periods=months_ahead,
        freq="ME"
    )
    
    data = []
    for date in dates:
        month_name = date.strftime("%B")
        seasonal = get_seasonal_patterns().get(month_name, {"avg_return": 0})
        
        # Simple forecast based on trend and seasonality
        row = {
            "date": date,
            "month": month_name,
            "expected_return": seasonal["avg_return"] / 100,
            "confidence": 0.5 + (1 / months_ahead) * 0.3,  # Confidence decreases with horizon
        }
        data.append(row)
    
    return pd.DataFrame(data)


# Data source URLs for reference
DATA_SOURCES = {
    "wgc": {
        "name": "World Gold Council",
        "url": "https://www.gold.org",
        "reports": [
            "Gold Demand Trends (quarterly)",
            "Gold Investment Outlook (quarterly)",
            "Central Bank Gold Reserves (monthly)",
        ],
    },
    "usgs": {
        "name": "US Geological Survey",
        "url": "https://www.usgs.gov/centers/national-minerals-information-center/gold-statistics-and-information",
        "reports": ["Mineral Commodity Summaries", "Mineral Yearbook"],
    },
    "cme": {
        "name": "CME Group",
        "url": "https://www.cmegroup.com",
        "data": ["COMEX Gold Futures", "Warehouse Stocks"],
    },
    "lbma": {
        "name": "London Bullion Market Association",
        "url": "https://www.lbma.org.uk",
        "data": ["Gold Fixing", "Warehouse Stocks"],
    },
    "metals_focus": {
        "name": "Metals Focus",
        "url": "https://www.metalsfocus.com",
        "reports": ["Gold Focus (annual)", "Gold Leaf (monthly)"],
    },
}
