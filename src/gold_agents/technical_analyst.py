"""
Gold Technical Analyst Agent

Performs comprehensive technical analysis on XAUUSD price charts.
Analyzes: trend, momentum, mean reversion, volatility, and chart patterns.
"""

from langchain_core.messages import HumanMessage
import pandas as pd
import numpy as np
import json
import math

from src.graph.state import AgentState, show_agent_reasoning
from src.gold_agents.models import GoldSignal
from src.utils.progress import progress


def safe_float(value, default=0.0):
    """Safely convert a value to float."""
    try:
        if pd.isna(value) or np.isnan(value):
            return default
        return float(value)
    except (ValueError, TypeError, OverflowError):
        return default


def gold_technical_analyst_agent(
    state: AgentState,
    agent_id: str = "gold_technical_analyst"
) -> dict:
    """
    Gold Technical Analyst Agent.
    
    Performs comprehensive technical analysis on XAUUSD including:
    - Trend Analysis (EMA crossovers, ADX)
    - Momentum Analysis (RSI, MACD, price momentum)
    - Mean Reversion (Bollinger Bands, Z-score)
    - Volatility Analysis (ATR, volatility regime)
    - Chart Patterns (support/resistance, golden ratio levels)
    """
    data = state["data"]
    prices_df = data.get("prices_df")
    symbol = data.get("symbol", "XAUUSD")
    
    progress.update_status(agent_id, symbol, "Performing technical analysis")
    
    if prices_df is None or len(prices_df) < 50:
        progress.update_status(agent_id, symbol, "Failed: Insufficient price data")
        return _create_empty_signal(agent_id, state)
    
    try:
        # Calculate all technical indicators
        trend_signals = calculate_trend_analysis(prices_df)
        momentum_signals = calculate_momentum_analysis(prices_df)
        mean_reversion_signals = calculate_mean_reversion(prices_df)
        volatility_signals = calculate_volatility_analysis(prices_df)
        pattern_signals = calculate_chart_patterns(prices_df)
        
        # Combine all signals with weights
        strategy_weights = {
            "trend": 0.30,
            "momentum": 0.25,
            "mean_reversion": 0.20,
            "volatility": 0.15,
            "patterns": 0.10,
        }
        
        combined = combine_signals(
            [trend_signals, momentum_signals, mean_reversion_signals, 
             volatility_signals, pattern_signals],
            strategy_weights
        )
        
        reasoning = {
            "trend": trend_signals,
            "momentum": momentum_signals,
            "mean_reversion": mean_reversion_signals,
            "volatility": volatility_signals,
            "patterns": pattern_signals,
            "weighted_combination": combined,
            "key_levels": calculate_key_levels(prices_df),
        }
        
        signal = GoldSignal(
            signal=combined["signal"],
            confidence=combined["confidence"],
            reasoning=reasoning,
            key_factors=_extract_key_factors(reasoning),
        )
        
        progress.update_status(agent_id, symbol, "Done", 
                             analysis=json.dumps(signal.reasoning, indent=2, default=str))
        
        if state["metadata"]["show_reasoning"]:
            show_agent_reasoning(signal.reasoning, "Gold Technical Analyst")
        
        state["data"]["analyst_signals"][agent_id] = signal.model_dump()
        
        return {
            "messages": state["messages"] + [HumanMessage(content=json.dumps(signal.model_dump()), name=agent_id)],
            "data": state["data"],
        }
        
    except Exception as e:
        progress.update_status(agent_id, symbol, f"Error: {str(e)}")
        return _create_empty_signal(agent_id, state, error=str(e))


def calculate_trend_analysis(df: pd.DataFrame) -> dict:
    """Analyze trend using EMAs and ADX."""
    close = df["close"]
    
    # EMAs
    ema_8 = close.ewm(span=8, adjust=False).mean()
    ema_21 = close.ewm(span=21, adjust=False).mean()
    ema_55 = close.ewm(span=55, adjust=False).mean()
    ema_200 = close.ewm(span=200, adjust=False).mean()
    
    # ADX
    adx_value = calculate_adx(df, 14)
    
    # Trend determination
    short_trend = ema_8.iloc[-1] > ema_21.iloc[-1]
    medium_trend = ema_21.iloc[-1] > ema_55.iloc[-1]
    long_trend = ema_55.iloc[-1] > ema_200.iloc[-1]
    
    price_vs_ema200 = (close.iloc[-1] - ema_200.iloc[-1]) / ema_200.iloc[-1] * 100
    adx_strength = adx_value["adx"].iloc[-1] / 100
    
    # Trend signal
    bullish_count = sum([short_trend, medium_trend, long_trend, price_vs_ema200 > 0])
    
    if bullish_count >= 3:
        signal = "bullish"
        confidence = min(0.5 + adx_strength * 0.5, 0.95)
    elif bullish_count <= 1:
        signal = "bearish"
        confidence = min(0.5 + adx_strength * 0.5, 0.95)
    else:
        signal = "neutral"
        confidence = 0.5
    
    return {
        "signal": signal,
        "confidence": confidence,
        "metrics": {
            "ema_8": safe_float(ema_8.iloc[-1]),
            "ema_21": safe_float(ema_21.iloc[-1]),
            "ema_55": safe_float(ema_55.iloc[-1]),
            "ema_200": safe_float(ema_200.iloc[-1]),
            "adx": safe_float(adx_value["adx"].iloc[-1]),
            "adx_trend_strength": adx_strength,
            "price_vs_ema200_pct": safe_float(price_vs_ema200),
            "short_trend_bullish": short_trend,
            "medium_trend_bullish": medium_trend,
            "long_trend_bullish": long_trend,
        }
    }


def calculate_momentum_analysis(df: pd.DataFrame) -> dict:
    """Analyze momentum using RSI, MACD, and price returns."""
    close = df["close"]
    returns = close.pct_change()
    
    # RSI
    rsi_14 = calculate_rsi(close, 14)
    rsi_28 = calculate_rsi(close, 28)
    
    # MACD
    ema_12 = close.ewm(span=12, adjust=False).mean()
    ema_26 = close.ewm(span=26, adjust=False).mean()
    macd_line = ema_12 - ema_26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    macd_histogram = macd_line - signal_line
    
    # Price momentum
    mom_1w = returns.rolling(5).sum()
    mom_1m = returns.rolling(21).sum()
    mom_3m = returns.rolling(63).sum()
    
    # Momentum score
    momentum_score = (mom_1w.iloc[-1] * 4 + mom_1m.iloc[-1] + mom_3m.iloc[-1] * 0.5)
    
    # RSI signals
    rsi_bullish = rsi_14.iloc[-1] < 70 and rsi_14.iloc[-1] > 50
    rsi_bearish = rsi_14.iloc[-1] > 30 and rsi_14.iloc[-1] < 50
    rsi_overbought = rsi_14.iloc[-1] >= 70
    rsi_oversold = rsi_14.iloc[-1] <= 30
    
    # MACD signals
    macd_bullish = macd_histogram.iloc[-1] > 0 and macd_histogram.iloc[-1] > macd_histogram.iloc[-2]
    macd_bearish = macd_histogram.iloc[-1] < 0 and macd_histogram.iloc[-1] < macd_histogram.iloc[-2]
    
    # Combine
    bullish_signals = sum([rsi_bullish, macd_bullish, momentum_score > 0])
    bearish_signals = sum([rsi_bearish, macd_bearish, momentum_score < 0])
    
    if bullish_signals > bearish_signals:
        signal = "bullish"
        confidence = min(bullish_signals / 4, 0.9)
    elif bearish_signals > bullish_signals:
        signal = "bearish"
        confidence = min(bearish_signals / 4, 0.9)
    else:
        signal = "neutral"
        confidence = 0.5
    
    # Warnings
    warnings = []
    if rsi_overbought:
        warnings.append("RSI overbought - potential reversal")
    if rsi_oversold:
        warnings.append("RSI oversold - potential bounce")
    
    return {
        "signal": signal,
        "confidence": confidence,
        "metrics": {
            "rsi_14": safe_float(rsi_14.iloc[-1]),
            "rsi_28": safe_float(rsi_28.iloc[-1]),
            "macd": safe_float(macd_line.iloc[-1]),
            "macd_signal": safe_float(signal_line.iloc[-1]),
            "macd_histogram": safe_float(macd_histogram.iloc[-1]),
            "momentum_1w": safe_float(mom_1w.iloc[-1]),
            "momentum_1m": safe_float(mom_1m.iloc[-1]),
            "momentum_3m": safe_float(mom_3m.iloc[-1]),
            "rsi_overbought": rsi_overbought,
            "rsi_oversold": rsi_oversold,
        },
        "warnings": warnings
    }


def calculate_mean_reversion(df: pd.DataFrame) -> dict:
    """Analyze mean reversion using Bollinger Bands and Z-score."""
    close = df["close"]
    
    # Bollinger Bands
    bb_ma = close.rolling(20).mean()
    bb_std = close.rolling(20).std()
    bb_upper = bb_ma + 2 * bb_std
    bb_lower = bb_ma - 2 * bb_std
    
    # Bollinger position (0-1, where 0.5 is middle)
    bb_position = (close.iloc[-1] - bb_lower.iloc[-1]) / (bb_upper.iloc[-1] - bb_lower.iloc[-1])
    
    # Z-score
    ma_50 = close.rolling(50).mean()
    std_50 = close.rolling(50).std()
    z_score = (close - ma_50) / std_50
    
    # Signals
    if z_score.iloc[-1] < -2 and bb_position < 0.2:
        signal = "bullish"
        confidence = min(abs(z_score.iloc[-1]) / 4, 0.9)
    elif z_score.iloc[-1] > 2 and bb_position > 0.8:
        signal = "bearish"
        confidence = min(abs(z_score.iloc[-1]) / 4, 0.9)
    elif z_score.iloc[-1] < -1:
        signal = "bullish"
        confidence = 0.6
    elif z_score.iloc[-1] > 1:
        signal = "bearish"
        confidence = 0.6
    else:
        signal = "neutral"
        confidence = 0.5
    
    return {
        "signal": signal,
        "confidence": confidence,
        "metrics": {
            "bollinger_position": safe_float(bb_position),
            "bollinger_upper": safe_float(bb_upper.iloc[-1]),
            "bollinger_middle": safe_float(bb_ma.iloc[-1]),
            "bollinger_lower": safe_float(bb_lower.iloc[-1]),
            "z_score_50d": safe_float(z_score.iloc[-1]),
            "deviation_from_mean": safe_float(z_score.iloc[-1] * std_50.iloc[-1]),
        }
    }


def calculate_volatility_analysis(df: pd.DataFrame) -> dict:
    """Analyze volatility conditions."""
    returns = df["close"].pct_change()
    
    # Historical volatility
    hist_vol_20 = returns.rolling(20).std() * math.sqrt(252)
    hist_vol_60 = returns.rolling(60).std() * math.sqrt(252)
    
    # ATR
    atr = calculate_atr(df, 14)
    atr_ratio = atr.iloc[-1] / df["close"].iloc[-1]
    
    # Volatility regime
    vol_ma = hist_vol_60.rolling(60).mean().iloc[-1]
    vol_ratio = hist_vol_20.iloc[-1] / vol_ma if vol_ma > 0 else 1
    
    if vol_ratio < 0.8:
        regime = "low"
        signal = "bullish"  # Low vol often precedes moves
        confidence = min((0.8 - vol_ratio) * 2, 0.7)
    elif vol_ratio > 1.2:
        regime = "high"
        signal = "neutral"  # High vol - uncertain direction
        confidence = 0.5
    else:
        regime = "normal"
        signal = "neutral"
        confidence = 0.5
    
    return {
        "signal": signal,
        "confidence": confidence,
        "metrics": {
            "hist_vol_20d": safe_float(hist_vol_20.iloc[-1]),
            "hist_vol_60d": safe_float(hist_vol_60.iloc[-1]),
            "atr_14": safe_float(atr.iloc[-1]),
            "atr_ratio": safe_float(atr_ratio),
            "volatility_regime": regime,
            "vol_ratio": safe_float(vol_ratio),
        }
    }


def calculate_chart_patterns(df: pd.DataFrame) -> dict:
    """Identify common chart patterns in gold."""
    close = df["close"]
    high = df["high"]
    low = df["low"]
    
    patterns_found = []
    signal = "neutral"
    confidence = 0.5
    
    # Golden ratio levels
    current_price = close.iloc[-1]
    high_52w = high.rolling(252).max().iloc[-1]
    low_52w = low.rolling(252).min().iloc[-1]
    range_52w = high_52w - low_52w
    
    golden_levels = [
        low_52w + range_52w * 0.382,  # 38.2% retracement
        low_52w + range_52w * 0.500,  # 50% retracement
        low_52w + range_52w * 0.618,  # 61.8% Golden ratio
        low_52w + range_52w * 0.786,  # 78.6% retracement
    ]
    
    # Check proximity to golden levels
    for level in golden_levels:
        distance = abs(current_price - level) / current_price
        if distance < 0.01:  # Within 1%
            patterns_found.append(f"Near golden level {level:.2f}")
    
    # Recent swing high/low detection
    swing_high = high.rolling(20).max().iloc[-1]
    swing_low = low.rolling(20).min().iloc[-1]
    
    if abs(current_price - swing_high) / current_price < 0.02:
        patterns_found.append("Near swing high resistance")
    if abs(current_price - swing_low) / current_price < 0.02:
        patterns_found.append("Near swing low support")
    
    return {
        "signal": signal,
        "confidence": confidence,
        "metrics": {
            "patterns_found": patterns_found,
            "swing_high_20d": safe_float(swing_high),
            "swing_low_20d": safe_float(swing_low),
            "high_52w": safe_float(high_52w),
            "low_52w": safe_float(low_52w),
            "golden_levels": [safe_float(l) for l in golden_levels],
        }
    }


def calculate_key_levels(df: pd.DataFrame) -> dict:
    """Calculate key support and resistance levels."""
    close = df["close"]
    high = df["high"]
    low = df["low"]
    
    current = close.iloc[-1]
    
    # Fibonacci levels based on recent range
    recent_high = high.rolling(20).max().iloc[-1]
    recent_low = low.rolling(20).min().iloc[-1]
    range_size = recent_high - recent_low
    
    return {
        "current_price": safe_float(current),
        "resistance_1": safe_float(recent_high),
        "resistance_2": safe_float(recent_high + range_size * 0.382),
        "support_1": safe_float(recent_low),
        "support_2": safe_float(recent_low - range_size * 0.382),
        "pivot": safe_float((recent_high + recent_low + close.rolling(1).mean().iloc[-1]) / 3),
    }


def combine_signals(signals: list, weights: dict) -> dict:
    """Combine multiple signals with weighted averaging."""
    signal_values = {"bullish": 1, "neutral": 0, "bearish": -1}
    
    keys = list(weights.keys())
    weighted_sum = 0
    total_confidence = 0
    
    for i, signal_data in enumerate(signals):
        key = keys[i]
        weight = weights[key]
        confidence = signal_data["confidence"]
        numeric_signal = signal_values[signal_data["signal"]]
        
        weighted_sum += numeric_signal * weight * confidence
        total_confidence += weight * confidence
    
    final_score = weighted_sum / total_confidence if total_confidence > 0 else 0
    
    if final_score > 0.2:
        signal = "bullish"
    elif final_score < -0.2:
        signal = "bearish"
    else:
        signal = "neutral"
    
    return {
        "signal": signal,
        "confidence": min(abs(final_score), 1.0) * 100,
        "raw_score": final_score
    }


def _extract_key_factors(reasoning: dict) -> list:
    """Extract key factors from reasoning."""
    factors = []
    
    if reasoning.get("trend", {}).get("signal") == "bullish":
        factors.append("Strong uptrend")
    elif reasoning.get("trend", {}).get("signal") == "bearish":
        factors.append("Weak downtrend")
    
    if reasoning.get("momentum", {}).get("metrics", {}).get("rsi_overbought"):
        factors.append("RSI overbought warning")
    if reasoning.get("momentum", {}).get("metrics", {}).get("rsi_oversold"):
        factors.append("RSI oversold opportunity")
    
    return factors


def _create_empty_signal(agent_id: str, state: dict, error: str = None) -> dict:
    """Create empty signal on error."""
    empty_signal = GoldSignal(
        signal="neutral",
        confidence=50,
        reasoning={"error": error or "No price data available"},
    ).model_dump()
    
    state["data"]["analyst_signals"][agent_id] = empty_signal
    
    return {
        "messages": state["messages"] + [HumanMessage(content=json.dumps(empty_signal), name=agent_id)],
        "data": state["data"],
    }


# Helper functions
def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Calculate RSI indicator."""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """Calculate ADX indicator."""
    df = df.copy()
    
    high_low = df["high"] - df["low"]
    high_close = abs(df["high"] - df["close"].shift())
    low_close = abs(df["low"] - df["close"].shift())
    df["tr"] = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    
    df["up_move"] = df["high"] - df["high"].shift()
    df["down_move"] = df["low"].shift() - df["low"]
    
    df["plus_dm"] = np.where(
        (df["up_move"] > df["down_move"]) & (df["up_move"] > 0), df["up_move"], 0
    )
    df["minus_dm"] = np.where(
        (df["down_move"] > df["up_move"]) & (df["down_move"] > 0), df["down_move"], 0
    )
    
    df["+di"] = 100 * (df["plus_dm"].ewm(span=period).mean() / df["tr"].ewm(span=period).mean())
    df["-di"] = 100 * (df["minus_dm"].ewm(span=period).mean() / df["tr"].ewm(span=period).mean())
    df["dx"] = 100 * abs(df["+di"] - df["-di"]) / (df["+di"] + df["-di"])
    df["adx"] = df["dx"].ewm(span=period).mean()
    
    return df[["adx", "+di", "-di"]]


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate ATR indicator."""
    high_low = df["high"] - df["low"]
    high_close = abs(df["high"] - df["close"].shift())
    low_close = abs(df["low"] - df["close"].shift())
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return true_range.rolling(period).mean()
