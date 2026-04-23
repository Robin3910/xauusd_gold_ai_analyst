"""
Gold Risk Manager Agent

Manages risk and position sizing for XAUUSD trades.
Calculates: volatility-adjusted positions, correlation risks, stop-loss levels.
"""

from langchain_core.messages import HumanMessage
import json
import math
import pandas as pd
import numpy as np
from datetime import datetime

from src.graph.state import AgentState, show_agent_reasoning
from src.gold_agents.models import GoldSignal
from src.utils.progress import progress


def gold_risk_manager_agent(
    state: AgentState,
    agent_id: str = "gold_risk_manager"
) -> dict:
    """
    Gold Risk Manager Agent.
    
    Manages trading risk for XAUUSD:
    - Volatility-adjusted position sizing
    - Stop-loss level calculation
    - Risk/reward ratio assessment
    - Correlation analysis
    - Drawdown protection
    """
    data = state["data"]
    symbol = data.get("symbol", "XAUUSD")
    analyst_signals = state["data"].get("analyst_signals", {})
    
    progress.update_status(agent_id, symbol, "Analyzing risk factors")
    
    # Get price data for volatility calculation
    prices_df = data.get("prices_df")
    
    if prices_df is None or len(prices_df) < 20:
        progress.update_status(agent_id, symbol, "Insufficient data for risk analysis")
        return _create_default_risk_assessment(agent_id, state)
    
    # Calculate risk metrics
    volatility_analysis = calculate_volatility_risk(prices_df)
    support_resistance = calculate_support_resistance(prices_df)
    position_limits = calculate_position_limits(data, volatility_analysis)
    correlation_risk = calculate_correlation_risk(data)
    drawdown_risk = calculate_drawdown_risk(prices_df, data)
    
    # Aggregate risk assessment
    risk_assessment = aggregate_risk_assessment(
        volatility_analysis, position_limits, correlation_risk, drawdown_risk
    )
    
    # Create risk-adjusted signals
    risk_adjusted_signals = apply_risk_adjustments(analyst_signals, risk_assessment, support_resistance)
    
    reasoning = {
        "volatility_analysis": volatility_analysis,
        "support_resistance": support_resistance,
        "position_limits": position_limits,
        "correlation_risk": correlation_risk,
        "drawdown_risk": drawdown_risk,
        "overall_risk": risk_assessment,
        "risk_adjusted_signals": risk_adjusted_signals,
    }
    
    signal = GoldSignal(
        signal=risk_assessment["direction"],
        confidence=risk_assessment["confidence"],
        reasoning=reasoning,
        key_factors=_extract_risk_factors(reasoning),
        warnings=_extract_risk_warnings(reasoning),
    )
    
    progress.update_status(agent_id, symbol, "Done",
                         analysis=json.dumps(reasoning, indent=2, default=str))
    
    if state["metadata"]["show_reasoning"]:
        show_agent_reasoning(reasoning, "Gold Risk Manager")
    
    state["data"]["analyst_signals"][agent_id] = signal.model_dump()
    state["data"]["risk_assessment"] = risk_assessment
    
    return {
        "messages": state["messages"] + [HumanMessage(content=json.dumps(signal.model_dump()), name=agent_id)],
        "data": state["data"],
    }


def calculate_volatility_risk(prices_df: pd.DataFrame) -> dict:
    """Calculate volatility-based risk metrics."""
    returns = prices_df["close"].pct_change().dropna()
    
    # Historical volatility
    vol_20d = returns.rolling(20).std() * math.sqrt(252)
    vol_60d = returns.rolling(60).std() * math.sqrt(252)
    
    current_vol_20 = vol_20d.iloc[-1] if not vol_20d.empty else 0.15
    current_vol_60 = vol_60d.iloc[-1] if not vol_60d.empty else 0.15
    
    # Volatility regime
    vol_ratio = current_vol_20 / current_vol_60 if current_vol_60 > 0 else 1
    
    if vol_ratio > 1.3:
        regime = "expanding"  # Vol increasing
        risk_level = "high"
        confidence_adjustment = -0.15
    elif vol_ratio < 0.7:
        regime = "contracting"  # Vol decreasing
        risk_level = "low"
        confidence_adjustment = 0.1
    else:
        regime = "stable"
        risk_level = "medium"
        confidence_adjustment = 0
    
    # ATR for stop-loss
    atr = calculate_atr_risk(prices_df)
    atr_pct = atr / prices_df["close"].iloc[-1]
    
    return {
        "vol_20d": current_vol_20,
        "vol_60d": current_vol_60,
        "vol_ratio": vol_ratio,
        "regime": regime,
        "risk_level": risk_level,
        "atr": atr,
        "atr_pct": atr_pct,
        "confidence_adjustment": confidence_adjustment,
    }


def calculate_support_resistance(prices_df: pd.DataFrame) -> dict:
    """Calculate support and resistance levels."""
    current_price = prices_df["close"].iloc[-1]
    high = prices_df["high"]
    low = prices_df["low"]
    
    # Recent swing high/low
    swing_high_20 = high.rolling(20).max().iloc[-1]
    swing_low_20 = low.rolling(20).min().iloc[-1]
    
    # Distance from levels
    dist_to_resistance = (swing_high_20 - current_price) / current_price
    dist_to_support = (current_price - swing_low_20) / current_price
    
    return {
        "current_price": current_price,
        "nearest_resistance": swing_high_20,
        "nearest_support": swing_low_20,
        "dist_to_resistance_pct": dist_to_resistance * 100,
        "dist_to_support_pct": dist_to_support * 100,
        "atr_stop_loss": calculate_atr_risk(prices_df),
    }


def calculate_position_limits(data: dict, volatility: dict) -> dict:
    """Calculate volatility-adjusted position limits."""
    portfolio = data.get("portfolio", {})
    cash = portfolio.get("cash", 100000)
    
    # Base risk per trade (1% of portfolio)
    base_risk = 0.01
    
    # Volatility adjustment
    vol_20d = volatility.get("vol_20d", 0.15)
    
    # Target volatility (gold typically 10-15%)
    target_vol = 0.12
    
    if vol_20d > target_vol * 1.5:
        # High volatility - reduce position
        vol_adjustment = 0.5
        max_position_pct = 0.15
    elif vol_20d > target_vol:
        vol_adjustment = 0.75
        max_position_pct = 0.20
    else:
        vol_adjustment = 1.0
        max_position_pct = 0.25
    
    # Calculate position size
    max_position_value = cash * max_position_pct
    risk_amount = cash * base_risk * vol_adjustment
    
    return {
        "max_position_pct": max_position_pct * 100,
        "max_position_value": max_position_value,
        "risk_amount": risk_amount,
        "vol_adjustment": vol_adjustment,
        "base_risk_pct": base_risk * 100,
        "vol_adjusted": vol_20d > target_vol,
    }


def calculate_correlation_risk(data: dict) -> dict:
    """Calculate correlation risk (for multi-asset scenarios)."""
    # In a single XAUUSD scenario, correlation risk is minimal
    # But we still track correlations with related assets
    
    correlations = data.get("correlations", {})
    
    # Key correlations for gold
    dxy_corr = correlations.get("dxy", -0.75)
    spx_corr = correlations.get("spx", 0.1)
    bonds_corr = correlations.get("bonds", 0.25)
    
    # Risk score based on correlations
    risk_score = 0
    
    if abs(dxy_corr) > 0.8:
        risk_score += 0.2
    if abs(spx_corr) > 0.5:
        risk_score += 0.15
    if abs(bonds_corr) > 0.5:
        risk_score += 0.1
    
    return {
        "dxy_correlation": dxy_corr,
        "spx_correlation": spx_corr,
        "bonds_correlation": bonds_corr,
        "correlation_risk_score": risk_score,
        "concentration_risk": "low",  # Single asset
    }


def calculate_drawdown_risk(prices_df: pd.DataFrame, data: dict) -> dict:
    """Calculate drawdown risk."""
    # Recent drawdown analysis
    rolling_max = prices_df["close"].rolling(window=20, min_periods=1).max()
    drawdown = (prices_df["close"] - rolling_max) / rolling_max
    
    current_drawdown = abs(drawdown.iloc[-1])
    max_drawdown_60d = abs(drawdown.rolling(60).min().iloc[-1]) if len(drawdown) >= 60 else 0
    
    # Recovery analysis
    recovery_days = 0
    if current_drawdown > 0.02:  # More than 2% drawdown
        recovery_days = estimate_recovery_days(drawdown)
    
    if max_drawdown_60d > 0.1:  # >10% drawdown in 60 days
        risk_level = "high"
        confidence = 80
    elif max_drawdown_60d > 0.05:  # >5% drawdown
        risk_level = "medium"
        confidence = 60
    else:
        risk_level = "low"
        confidence = 40
    
    return {
        "current_drawdown": current_drawdown,
        "max_drawdown_60d": max_drawdown_60d,
        "recovery_estimate_days": recovery_days,
        "risk_level": risk_level,
        "confidence": confidence,
    }


def calculate_atr_risk(prices_df: pd.DataFrame, period: int = 14) -> float:
    """Calculate ATR for stop-loss purposes."""
    high = prices_df["high"]
    low = prices_df["low"]
    close = prices_df["close"]
    
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()
    
    return atr.iloc[-1] if not atr.empty else prices_df["close"].iloc[-1] * 0.01


def estimate_recovery_days(drawdown: pd.Series) -> int:
    """Estimate days to recovery from drawdown."""
    # Simple estimation based on average recovery rate
    if abs(drawdown.iloc[-1]) < 0.01:
        return 0
    
    # Average daily return needed
    avg_return = 0.001  # ~0.1% per day
    required_return = abs(drawdown.iloc[-1])
    
    if avg_return > 0:
        return int(required_return / avg_return)
    
    return 30  # Default


def aggregate_risk_assessment(
    volatility: dict, 
    positions: dict, 
    correlation: dict,
    drawdown: dict
) -> dict:
    """Aggregate all risk factors into overall assessment."""
    # Risk scores
    risk_scores = []
    
    # Volatility risk
    vol_risk = 1.0 if volatility["risk_level"] == "high" else 0.5 if volatility["risk_level"] == "medium" else 0.2
    risk_scores.append(("volatility", vol_risk, 0.30))
    
    # Drawdown risk
    dd_risk = 1.0 if drawdown["risk_level"] == "high" else 0.5 if drawdown["risk_level"] == "medium" else 0.2
    risk_scores.append(("drawdown", dd_risk, 0.25))
    
    # Correlation risk
    corr_risk = correlation["correlation_risk_score"]
    risk_scores.append(("correlation", corr_risk, 0.20))
    
    # Position limit risk
    pos_risk = 1.0 if positions["vol_adjusted"] else 0.5
    risk_scores.append(("position", pos_risk, 0.25))
    
    # Calculate weighted risk
    total_risk = sum(risk * weight for _, risk, weight in risk_scores)
    
    # Determine direction and confidence
    if total_risk > 0.7:
        direction = "neutral"  # High risk = be cautious
        confidence = 40
    elif total_risk < 0.4:
        direction = "neutral"  # Low risk alone doesn't indicate direction
        confidence = 60
    else:
        direction = "neutral"
        confidence = 50
    
    return {
        "overall_risk_score": total_risk,
        "risk_level": "high" if total_risk > 0.7 else "medium" if total_risk > 0.4 else "low",
        "direction": direction,
        "confidence": confidence,
        "component_risks": {name: risk for name, risk, _ in risk_scores},
        "stop_loss_pct": 2.0 if volatility["risk_level"] == "high" else 1.5,
        "take_profit_min_ratio": 2.0,
    }


def apply_risk_adjustments(
    analyst_signals: dict, 
    risk_assessment: dict,
    levels: dict
) -> dict:
    """Apply risk adjustments to analyst signals."""
    adjusted = {}
    
    for agent_name, signal_data in analyst_signals.items():
        if isinstance(signal_data, dict) and "signal" in signal_data:
            # Reduce confidence if risk is high
            if risk_assessment["risk_level"] == "high":
                adjusted[agent_name] = {
                    **signal_data,
                    "confidence": signal_data.get("confidence", 50) * 0.7,
                    "risk_warning": "High market risk - reduced confidence"
                }
            else:
                adjusted[agent_name] = signal_data.copy()
    
    # Add stop-loss levels
    adjusted["stop_loss"] = {
        "nearest_support": levels["nearest_support"],
        "atr_based": levels.get("atr_stop_loss", 0),
        "recommend_stop_pct": risk_assessment.get("stop_loss_pct", 1.5)
    }
    
    return adjusted


def _extract_risk_factors(reasoning: dict) -> list:
    """Extract key risk factors."""
    factors = []
    
    vol = reasoning.get("volatility_analysis", {})
    if vol.get("regime") == "contracting":
        factors.append("Volatility contracting - potential breakout setup")
    elif vol.get("regime") == "expanding":
        factors.append("Volatility expanding - increased risk")
    
    pos = reasoning.get("position_limits", {})
    if pos.get("vol_adjusted"):
        factors.append("Volatility-adjusted position sizing active")
    
    return factors


def _extract_risk_warnings(reasoning: dict) -> list:
    """Extract risk warnings."""
    warnings = []
    
    risk = reasoning.get("overall_risk", {})
    if risk.get("risk_level") == "high":
        warnings.append("High overall risk - consider reduced position or no trade")
    
    vol = reasoning.get("volatility_analysis", {})
    if vol.get("regime") == "expanding":
        warnings.append("Volatility expanding - wider stops needed")
    
    dd = reasoning.get("drawdown_risk", {})
    if dd.get("max_drawdown_60d", 0) > 0.05:
        warnings.append(f"Recent drawdown: {dd['max_drawdown_60d']*100:.1f}%")
    
    return warnings


def _create_default_risk_assessment(agent_id: str, state: dict) -> dict:
    """Create default risk assessment when data is insufficient."""
    default_signal = GoldSignal(
        signal="neutral",
        confidence=50,
        reasoning={"error": "Insufficient data for risk analysis"},
        warnings=["Unable to calculate risk metrics - trade cautiously"],
    ).model_dump()
    
    state["data"]["analyst_signals"][agent_id] = default_signal
    state["data"]["risk_assessment"] = {
        "risk_level": "unknown",
        "direction": "neutral",
        "confidence": 50,
    }
    
    return {
        "messages": state["messages"] + [HumanMessage(content=json.dumps(default_signal), name=agent_id)],
        "data": state["data"],
    }
