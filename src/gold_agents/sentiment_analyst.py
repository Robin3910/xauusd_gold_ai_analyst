"""
Gold Market Sentiment Analyst Agent

Analyzes market sentiment and positioning for XAUUSD.
Focuses on: CFTC data, sentiment surveys, risk appetite, positioning indicators.
"""

from langchain_core.messages import HumanMessage
import pandas as pd
import numpy as np
import json
from datetime import datetime

from src.graph.state import AgentState, show_agent_reasoning
from src.gold_agents.models import GoldSignal, MarketSentimentData
from src.utils.progress import progress


def gold_sentiment_analyst_agent(
    state: AgentState,
    agent_id: str = "gold_sentiment_analyst"
) -> dict:
    """
    Gold Market Sentiment Analyst Agent.
    
    Analyzes market sentiment and positioning:
    - CFTC commitment of traders data
    - Sentiment surveys (bullish %)
    - Risk-on/Risk-off indicators
    - ETF flows and positioning
    - Technical sentiment consensus
    """
    data = state["data"]
    symbol = data.get("symbol", "XAUUSD")
    
    progress.update_status(agent_id, symbol, "Collecting sentiment data")
    
    # Get sentiment data from state or use provided
    sentiment_data = data.get("sentiment_data", {})
    
    if not sentiment_data:
        sentiment_data = _generate_mock_sentiment_data()
    
    # Analyze different sentiment dimensions
    cftc_analysis = analyze_cftc_data(sentiment_data)
    survey_analysis = analyze_survey_sentiment(sentiment_data)
    risk_analysis = analyze_risk_sentiment(sentiment_data)
    etf_analysis = analyze_etf_flows(sentiment_data)
    consensus_analysis = analyze_technical_consensus(sentiment_data)
    
    # Weighted combination
    weights = {
        "cftc": 0.25,
        "survey": 0.20,
        "risk": 0.20,
        "etf": 0.15,
        "consensus": 0.20,
    }
    
    combined = combine_sentiment_signals(
        [cftc_analysis, survey_analysis, risk_analysis, etf_analysis, consensus_analysis],
        weights
    )
    
    reasoning = {
        "cftc_analysis": cftc_analysis,
        "survey_analysis": survey_analysis,
        "risk_analysis": risk_analysis,
        "etf_analysis": etf_analysis,
        "consensus_analysis": consensus_analysis,
        "combined": combined,
        "overall_sentiment": _determine_overall_sentiment(combined),
    }
    
    signal = GoldSignal(
        signal=combined["signal"],
        confidence=combined["confidence"],
        reasoning=reasoning,
        key_factors=_extract_sentiment_factors(reasoning),
        warnings=_extract_sentiment_warnings(reasoning),
    )
    
    progress.update_status(agent_id, symbol, "Done",
                         analysis=json.dumps(reasoning, indent=2, default=str))
    
    if state["metadata"]["show_reasoning"]:
        show_agent_reasoning(reasoning, "Gold Market Sentiment Analyst")
    
    state["data"]["analyst_signals"][agent_id] = signal.model_dump()
    
    return {
        "messages": state["messages"] + [HumanMessage(content=json.dumps(signal.model_dump()), name=agent_id)],
        "data": state["data"],
    }


def analyze_cftc_data(sentiment_data: dict) -> dict:
    """Analyze CFTC Commitment of Traders data."""
    cftc = sentiment_data.get("cftc", {})
    
    long_positions = cftc.get("long_positions", 0)
    short_positions = cftc.get("short_positions", 0)
    
    if long_positions == 0 or short_positions == 0:
        return {
            "signal": "neutral",
            "confidence": 50,
            "metrics": {"cftc_data_available": False},
            "summary": "No CFTC data available"
        }
    
    net_position = long_positions - short_positions
    total_positions = long_positions + short_positions
    net_position_pct = (net_position / total_positions) * 100
    
    # Trading intensity (leverage ratio)
    leverage_ratio = total_positions / (long_positions - short_positions) if (long_positions - short_positions) != 0 else 0
    
    # Signal based on net positioning
    if net_position_pct > 30:  # Highly net long
        signal = "bullish"
        confidence = min(net_position_pct / 100 * 100, 80)
    elif net_position_pct < -30:  # Highly net short
        signal = "bearish"
        confidence = min(abs(net_position_pct) / 100 * 100, 80)
    elif net_position_pct > 15:
        signal = "bullish"
        confidence = 60
    elif net_position_pct < -15:
        signal = "bearish"
        confidence = 60
    else:
        signal = "neutral"
        confidence = 50
    
    # Crowding warning
    warnings = []
    if leverage_ratio > 3:
        warnings.append("High leverage - potential squeeze risk")
    
    return {
        "signal": signal,
        "confidence": confidence,
        "metrics": {
            "long_positions": long_positions,
            "short_positions": short_positions,
            "net_position": net_position,
            "net_position_pct": net_position_pct,
            "leverage_ratio": leverage_ratio,
        },
        "warnings": warnings,
        "summary": f"Net positioning: {net_position_pct:.1f}%"
    }


def analyze_survey_sentiment(sentiment_data: dict) -> dict:
    """Analyze sentiment survey data."""
    survey = sentiment_data.get("survey", {})
    
    bullish_pct = survey.get("bullish_pct", 50)
    bearish_pct = survey.get("bearish_pct", 25)
    neutral_pct = survey.get("neutral_pct", 25)
    
    # Fear and Greed interpretation
    if bullish_pct > 60:
        signal = "bullish"
        confidence = min((bullish_pct - 50) * 2, 80)
    elif bullish_pct < 40:
        signal = "bearish"
        confidence = min((50 - bullish_pct) * 2, 80)
    else:
        signal = "neutral"
        confidence = 50
    
    # Bull-Bear spread
    spread = bullish_pct - bearish_pct
    
    return {
        "signal": signal,
        "confidence": confidence,
        "metrics": {
            "bullish_pct": bullish_pct,
            "bearish_pct": bearish_pct,
            "neutral_pct": neutral_pct,
            "bull_bear_spread": spread,
            "crowding_risk": "high" if bullish_pct > 70 or bearish_pct > 60 else "medium" if bullish_pct > 60 else "low"
        },
        "summary": f"Bullish: {bullish_pct}%, Bearish: {bearish_pct}%, Spread: {spread}%"
    }


def analyze_risk_sentiment(sentiment_data: dict) -> dict:
    """Analyze risk-on/risk-off sentiment."""
    risk = sentiment_data.get("risk", {})
    
    vix = risk.get("vix", 20)
    gold_sentiment = risk.get("gold_sentiment", 50)  # Typically inverse to risk appetite
    risk_score = risk.get("risk_score", 50)  # 0 = risk off, 100 = risk on
    
    # Determine risk regime
    if vix > 25 or risk_score < 30:
        risk_regime = "risk_off"
        signal = "bullish"  # Gold benefits from risk-off
        confidence = min((vix - 20) / 2 + (50 - risk_score) / 2, 80)
    elif vix < 15 or risk_score > 70:
        risk_regime = "risk_on"
        signal = "bearish"  # Gold struggles in risk-on
        confidence = min((20 - vix) + (risk_score - 50), 80)
    else:
        risk_regime = "neutral"
        signal = "neutral"
        confidence = 50
    
    return {
        "signal": signal,
        "confidence": confidence,
        "metrics": {
            "vix": vix,
            "risk_score": risk_score,
            "gold_sentiment": gold_sentiment,
            "risk_regime": risk_regime,
            "fear_greed": "fear" if vix > 25 else "greed" if vix < 15 else "neutral"
        },
        "summary": f"Risk regime: {risk_regime}, VIX: {vix}"
    }


def analyze_etf_flows(sentiment_data: dict) -> dict:
    """Analyze ETF flows and holdings changes."""
    etf = sentiment_data.get("etf", {})
    
    holdings_change = etf.get("holdings_change_pct", 0)
    inflow_7d = etf.get("inflow_7d", 0)  # in tonnes
    inflow_30d = etf.get("inflow_30d", 0)
    
    if abs(holdings_change) < 0.5:
        signal = "neutral"
        confidence = 50
    elif holdings_change > 0:
        signal = "bullish"
        confidence = min(abs(holdings_change) * 3, 80)
    else:
        signal = "bearish"
        confidence = min(abs(holdings_change) * 3, 80)
    
    return {
        "signal": signal,
        "confidence": confidence,
        "metrics": {
            "holdings_change_pct": holdings_change,
            "inflow_7d": inflow_7d,
            "inflow_30d": inflow_30d,
            "trend": "increasing" if inflow_7d > 0 else "decreasing"
        },
        "summary": f"ETF holdings {'up' if holdings_change > 0 else 'down'} {abs(holdings_change):.2f}%"
    }


def analyze_technical_consensus(sentiment_data: dict) -> dict:
    """Analyze technical analyst consensus."""
    consensus = sentiment_data.get("consensus", {})
    
    analyst_bullish = consensus.get("analyst_bullish_pct", 50)
    analyst_bearish = consensus.get("analyst_bearish_pct", 25)
    
    # Signal
    if analyst_bullish > 60:
        signal = "bullish"
        confidence = min((analyst_bullish - 50) * 2, 75)
    elif analyst_bullish < 40:
        signal = "bearish"
        confidence = min((50 - analyst_bullish) * 2, 75)
    else:
        signal = "neutral"
        confidence = 50
    
    return {
        "signal": signal,
        "confidence": confidence,
        "metrics": {
            "analyst_bullish_pct": analyst_bullish,
            "analyst_bearish_pct": analyst_bearish,
            "recommendation": consensus.get("recommendation", "neutral")
        },
        "summary": f"{analyst_bullish}% of analysts are bullish"
    }


def combine_sentiment_signals(signals: list, weights: dict) -> dict:
    """Combine sentiment signals with weighted averaging."""
    signal_values = {"bullish": 1, "neutral": 0, "bearish": -1}
    
    keys = list(weights.keys())
    weighted_sum = 0
    total_weight = 0
    
    for i, signal_data in enumerate(signals):
        key = keys[i]
        weight = weights[key]
        confidence = signal_data["confidence"] / 100
        numeric_signal = signal_values[signal_data["signal"]]
        
        weighted_sum += numeric_signal * weight * confidence
        total_weight += weight * confidence
    
    final_score = weighted_sum / total_weight if total_weight > 0 else 0
    
    if final_score > 0.2:
        signal = "bullish"
    elif final_score < -0.2:
        signal = "bearish"
    else:
        signal = "neutral"
    
    return {
        "signal": signal,
        "confidence": min(abs(final_score) * 100, 100),
        "raw_score": final_score
    }


def _determine_overall_sentiment(combined: dict) -> str:
    """Determine overall market sentiment."""
    if combined["confidence"] > 70:
        if combined["signal"] == "bullish":
            return "strongly_bullish"
        elif combined["signal"] == "bearish":
            return "strongly_bearish"
    
    return combined["signal"]


def _extract_sentiment_factors(reasoning: dict) -> list:
    """Extract key factors from sentiment analysis."""
    factors = []
    
    cftc = reasoning.get("cftc_analysis", {}).get("metrics", {})
    if cftc.get("net_position_pct", 0) > 20:
        factors.append("Smart money is net long gold")
    elif cftc.get("net_position_pct", 0) < -20:
        factors.append("Smart money is net short gold")
    
    risk = reasoning.get("risk_analysis", {})
    if risk.get("metrics", {}).get("risk_regime") == "risk_off":
        factors.append("Risk-off environment supporting gold")
    elif risk.get("metrics", {}).get("risk_regime") == "risk_on":
        factors.append("Risk-on environment pressuring gold")
    
    if reasoning.get("etf_analysis", {}).get("metrics", {}).get("inflow_7d", 0) > 10:
        factors.append("Strong ETF inflows into gold")
    
    return factors


def _extract_sentiment_warnings(reasoning: dict) -> list:
    """Extract warnings from sentiment analysis."""
    warnings = []
    
    cftc = reasoning.get("cftc_analysis", {})
    if cftc.get("warnings"):
        warnings.extend(cftc["warnings"])
    
    survey = reasoning.get("survey_analysis", {}).get("metrics", {})
    if survey.get("crowding_risk") == "high":
        warnings.append("High crowd positioning - reversal risk")
    
    return warnings


def _generate_mock_sentiment_data() -> dict:
    """Generate mock sentiment data for testing."""
    return {
        "cftc": {
            "long_positions": 180000,
            "short_positions": 80000,
        },
        "survey": {
            "bullish_pct": 55,
            "bearish_pct": 25,
            "neutral_pct": 20,
        },
        "risk": {
            "vix": 18,
            "risk_score": 60,
        },
        "etf": {
            "holdings_change_pct": 1.5,
            "inflow_7d": 15,
            "inflow_30d": 45,
        },
        "consensus": {
            "analyst_bullish_pct": 52,
            "analyst_bearish_pct": 28,
        }
    }
