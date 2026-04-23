"""
Gold Market Data Models

Data structures for XAUUSD analysis framework.
"""

from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class GoldPrice(BaseModel):
    """Gold price data point."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: Optional[float] = None


class GoldMetrics(BaseModel):
    """Fundamental metrics for gold analysis."""
    # Price metrics
    current_price: float
    spot_price: float
    futures_price: float
    premium_discount: Optional[float] = None  # Spot-Futures spread
    
    # Market metrics
    open_interest: Optional[float] = None
    comex_inventory: Optional[float] = None
    etf_holdings: Optional[float] = None
    
    # Volatility
    historical_volatility_20d: Optional[float] = None
    implied_volatility: Optional[float] = None


class MacroIndicators(BaseModel):
    """Macroeconomic indicators relevant to gold."""
    # Interest rates
    fed_funds_rate: Optional[float] = None
    real_yield_10y: Optional[float] = None
    nominal_yield_10y: Optional[float] = None
    
    # USD metrics
    dollar_index_dxy: Optional[float] = None
    dollar_index_change: Optional[float] = None
    
    # Inflation
    cpi_yoy: Optional[float] = None
    ppi_yoy: Optional[float] = None
    core_inflation: Optional[float] = None
    
    # Risk metrics
    vix: Optional[float] = None
    credit_spread_high_yield: Optional[float] = None


class SupplyDemandData(BaseModel):
    """Gold supply and demand data."""
    # Supply
    mining_production_q: Optional[float] = None
    scrap_supply: Optional[float] = None
    net_central_bank_purchase: Optional[float] = None
    
    # Demand
    jewelry_demand: Optional[float] = None
    technology_demand: Optional[float] = None
    investment_demand: Optional[float] = None
    etf_inflow_outflow: Optional[float] = None
    
    # Central banks
    cb_gold_reserves_change: Optional[float] = None


class GeopoliticalEvent(BaseModel):
    """Geopolitical risk event."""
    event_type: str
    region: str
    severity: float = Field(ge=0, le=1)  # 0-1 scale
    timestamp: datetime
    description: str


class GoldNews(BaseModel):
    """News item relevant to gold."""
    title: str
    source: str
    timestamp: datetime
    sentiment: str  # "positive", "negative", "neutral"
    sentiment_score: float = Field(ge=-1, le=1)
    relevance_to_gold: float = Field(ge=0, le=1)
    categories: list[str] = []  # e.g., ["Fed", "Inflation", "Geopolitics"]


class MarketSentimentData(BaseModel):
    """Market sentiment indicators for gold."""
    # Positioning
    cftc_long_positions: Optional[float] = None
    cftc_short_positions: Optional[float] = None
    net_positioning: Optional[float] = None
    
    # Sentiment surveys
    gold_sentiment_index: Optional[float] = None  # Bullish %
    
    # Risk-on/Risk-off
    risk_sentiment: str = "neutral"  # "risk_on", "risk_off", "neutral"
    risk_appetite_score: Optional[float] = None
    
    # Technical sentiment
    analyst_consensus: str = "neutral"
    analyst_bullish_pct: Optional[float] = None


class SeasonalPattern(BaseModel):
    """Historical seasonal patterns for gold."""
    month: int
    avg_return: float
    win_rate: float
    best_periods: list[str] = []
    worst_periods: list[str] = []


class TechnicalIndicators(BaseModel):
    """Technical analysis indicators for gold."""
    # Trend
    ema_8: float
    ema_21: float
    ema_55: float
    ema_200: float
    adx: float
    trend_direction: str
    
    # Momentum
    rsi_14: float
    rsi_28: float
    macd: float
    macd_signal: float
    momentum_score: float
    
    # Mean reversion
    bollinger_position: float  # 0-1, where 0.5 is middle
    z_score_50d: float
    
    # Volatility
    atr_14: float
    atr_ratio: float  # ATR as % of price
    volatility_regime: str  # "low", "normal", "high"
    
    # Support/Resistance
    nearest_support: float
    nearest_resistance: float


class GoldSignal(BaseModel):
    """Output signal from any gold analyst agent."""
    signal: str  # "bullish", "bearish", "neutral"
    confidence: float = Field(ge=0, le=100)
    reasoning: dict
    key_factors: list[str] = []
    warnings: list[str] = []


class AnalystOutput(BaseModel):
    """Standard output from any analyst agent."""
    agent_name: str
    signal: GoldSignal
    supporting_data: dict = {}
    timestamp: datetime = Field(default_factory=datetime.now)


class PortfolioRecommendation(BaseModel):
    """Final trading recommendation."""
    action: str  # "buy", "sell", "hold", "strong_buy", "strong_sell"
    quantity: Optional[float] = None
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    risk_reward_ratio: Optional[float] = None
    confidence: float = Field(ge=0, le=100)
    reasoning: dict
    risk_assessment: dict
