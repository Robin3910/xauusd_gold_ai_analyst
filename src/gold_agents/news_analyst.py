"""
Gold News Analyst Agent

Analyzes news and macroeconomic events affecting XAUUSD.
Focuses on: Fed policy, inflation data, geopolitical events, central bank actions.
"""

from langchain_core.messages import HumanMessage
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta

from src.graph.state import AgentState, show_agent_reasoning
from src.gold_agents.models import GoldSignal, GoldNews
from src.utils.progress import progress


def gold_news_analyst_agent(
    state: AgentState,
    agent_id: str = "gold_news_analyst"
) -> dict:
    """
    Gold News Analyst Agent.
    
    Analyzes news and events affecting gold prices:
    - Fed policy announcements and statements
    - Inflation data (CPI, PPI, PCE)
    - Geopolitical events and risk
    - Central bank gold purchases/sales
    - Economic data releases
    """
    data = state["data"]
    symbol = data.get("symbol", "XAUUSD")
    
    progress.update_status(agent_id, symbol, "Collecting news data")
    
    # Get news from state or mock for now
    news_data = data.get("news_data", [])
    macro_data = data.get("macro_data", {})
    
    if not news_data:
        news_data = _generate_mock_news_analysis(symbol)
    
    progress.update_status(agent_id, symbol, "Analyzing sentiment")
    
    # Analyze each news category
    fed_analysis = analyze_fed_news(news_data)
    inflation_analysis = analyze_inflation_news(news_data)
    geopolitical_analysis = analyze_geopolitical_news(news_data)
    cb_analysis = analyze_central_bank_news(news_data)
    economic_analysis = analyze_economic_data(macro_data)
    
    # Weighted combination
    weights = {
        "fed": 0.30,
        "inflation": 0.25,
        "geopolitical": 0.20,
        "central_bank": 0.15,
        "economic": 0.10,
    }
    
    combined = combine_news_signals(
        [fed_analysis, inflation_analysis, geopolitical_analysis, cb_analysis, economic_analysis],
        weights
    )
    
    reasoning = {
        "fed_analysis": fed_analysis,
        "inflation_analysis": inflation_analysis,
        "geopolitical_analysis": geopolitical_analysis,
        "central_bank_analysis": cb_analysis,
        "economic_analysis": economic_analysis,
        "combined": combined,
        "news_count": len(news_data),
        "relevance_scores": _calculate_relevance(news_data),
    }
    
    signal = GoldSignal(
        signal=combined["signal"],
        confidence=combined["confidence"],
        reasoning=reasoning,
        key_factors=_extract_news_factors(reasoning),
        warnings=_extract_news_warnings(reasoning),
    )
    
    progress.update_status(agent_id, symbol, "Done",
                         analysis=json.dumps(reasoning, indent=2, default=str))
    
    if state["metadata"]["show_reasoning"]:
        show_agent_reasoning(reasoning, "Gold News Analyst")
    
    state["data"]["analyst_signals"][agent_id] = signal.model_dump()
    
    return {
        "messages": state["messages"] + [HumanMessage(content=json.dumps(signal.model_dump()), name=agent_id)],
        "data": state["data"],
    }


def analyze_fed_news(news_data: list) -> dict:
    """Analyze Fed-related news impact on gold."""
    fed_keywords = ["fed", "federal reserve", "powell", "fomc", "interest rate", 
                    "monetary policy", "federal funds"]
    
    fed_news = [n for n in news_data if _matches_keywords(n, fed_keywords)]
    
    if not fed_news:
        return {
            "signal": "neutral",
            "confidence": 50,
            "metrics": {"fed_news_count": 0, "impact": "unknown"},
            "summary": "No significant Fed news"
        }
    
    bullish_count = 0
    bearish_count = 0
    
    for news in fed_news:
        sentiment = news.get("sentiment", "neutral")
        if sentiment == "positive":
            bullish_count += 1  # Hawkish Fed = bearish for gold
        elif sentiment == "negative":
            bearish_count += 1  # Dovish Fed = bullish for gold
    
    if bearish_count > bullish_count:
        signal = "bullish"
        confidence = min(bearish_count / len(fed_news) * 100, 85)
    elif bullish_count > bearish_count:
        signal = "bearish"
        confidence = min(bullish_count / len(fed_news) * 100, 85)
    else:
        signal = "neutral"
        confidence = 50
    
    return {
        "signal": signal,
        "confidence": confidence,
        "metrics": {
            "fed_news_count": len(fed_news),
            "bullish_signals": bullish_count,
            "bearish_signals": bearish_count,
            "impact": "high" if len(fed_news) >= 3 else "medium" if len(fed_news) >= 1 else "low"
        },
        "summary": f"Found {len(fed_news)} Fed-related news items"
    }


def analyze_inflation_news(news_data: list) -> dict:
    """Analyze inflation-related news impact on gold."""
    inflation_keywords = ["inflation", "cpi", "ppi", "pce", "price", "cost", 
                         "commodity prices", "energy prices", "food prices"]
    
    inflation_news = [n for n in news_data if _matches_keywords(n, inflation_keywords)]
    
    if not inflation_news:
        return {
            "signal": "neutral",
            "confidence": 50,
            "metrics": {"inflation_news_count": 0},
            "summary": "No significant inflation news"
        }
    
    # Higher inflation = bullish for gold
    bullish_count = 0
    bearish_count = 0
    
    for news in inflation_news:
        sentiment = news.get("sentiment", "neutral")
        # "positive" sentiment usually means higher prices/inflation
        if sentiment == "positive":
            bullish_count += 1
        elif sentiment == "negative":
            bearish_count += 1
    
    if bullish_count > bearish_count:
        signal = "bullish"
        confidence = min(bullish_count / len(inflation_news) * 100, 80)
    elif bearish_count > bullish_count:
        signal = "bearish"
        confidence = min(bearish_count / len(inflation_news) * 100, 80)
    else:
        signal = "neutral"
        confidence = 50
    
    return {
        "signal": signal,
        "confidence": confidence,
        "metrics": {
            "inflation_news_count": len(inflation_news),
            "bullish_signals": bullish_count,
            "bearish_signals": bearish_count
        },
        "summary": f"Found {len(inflation_news)} inflation-related news items"
    }


def analyze_geopolitical_news(news_data: list) -> dict:
    """Analyze geopolitical events impact on gold."""
    geo_keywords = ["war", "conflict", "sanction", "tension", "crisis", "election",
                   "geopolitical", "trade war", "military", "terrorism", "brexit", "recession"]
    
    geo_news = [n for n in news_data if _matches_keywords(n, geo_keywords)]
    
    if not geo_news:
        return {
            "signal": "neutral",
            "confidence": 50,
            "metrics": {"geo_news_count": 0, "risk_level": "normal"},
            "summary": "No major geopolitical risks"
        }
    
    # Geopolitical risk is generally bullish for gold (safe haven)
    severity = sum(n.get("severity", 0.5) for n in geo_news) / len(geo_news)
    
    signal = "bullish"
    confidence = min(50 + severity * 40, 90)
    
    return {
        "signal": signal,
        "confidence": confidence,
        "metrics": {
            "geo_news_count": len(geo_news),
            "average_severity": severity,
            "risk_level": "high" if severity > 0.7 else "medium" if severity > 0.4 else "low"
        },
        "summary": f"Found {len(geo_news)} geopolitical events, risk level: {'high' if severity > 0.6 else 'medium'}"
    }


def analyze_central_bank_news(news_data: list) -> dict:
    """Analyze central bank gold-related news."""
    cb_keywords = ["central bank", "reserve", "gold purchase", "gold sale", 
                  "world gold council", "imf", "bIS"]
    
    cb_news = [n for n in news_data if _matches_keywords(n, cb_keywords)]
    
    if not cb_news:
        return {
            "signal": "neutral",
            "confidence": 50,
            "metrics": {"cb_news_count": 0},
            "summary": "No central bank gold news"
        }
    
    # Central bank purchases = bullish for gold
    purchase_count = sum(1 for n in cb_news if "purchase" in n.get("title", "").lower())
    sale_count = sum(1 for n in cb_news if "sale" in n.get("title", "").lower())
    
    if purchase_count > sale_count:
        signal = "bullish"
        confidence = 70
    elif sale_count > purchase_count:
        signal = "bearish"
        confidence = 70
    else:
        signal = "neutral"
        confidence = 50
    
    return {
        "signal": signal,
        "confidence": confidence,
        "metrics": {
            "cb_news_count": len(cb_news),
            "purchase_signals": purchase_count,
            "sale_signals": sale_count
        },
        "summary": f"Found {len(cb_news)} central bank news items"
    }


def analyze_economic_data(macro_data: dict) -> dict:
    """Analyze macroeconomic data impact."""
    if not macro_data:
        return {
            "signal": "neutral",
            "confidence": 50,
            "metrics": {},
            "summary": "No macro data available"
        }
    
    signals = []
    
    # USD strength (negative correlation with gold)
    if "dollar_index" in macro_data:
        dxy = macro_data["dollar_index"]
        if dxy > 105:  # Strong dollar
            signals.append("bearish")
        elif dxy < 95:  # Weak dollar
            signals.append("bullish")
    
    # Real yields (negative correlation)
    if "real_yield_10y" in macro_data:
        real_yield = macro_data["real_yield_10y"]
        if real_yield < 0:  # Negative real yields = bullish for gold
            signals.append("bullish")
        elif real_yield > 1:
            signals.append("bearish")
    
    # VIX (fear index - positive correlation)
    if "vix" in macro_data:
        vix = macro_data["vix"]
        if vix > 25:
            signals.append("bullish")
        elif vix < 15:
            signals.append("bearish")
    
    bullish_count = signals.count("bullish")
    bearish_count = signals.count("bearish")
    
    if bullish_count > bearish_count:
        signal = "bullish"
        confidence = min(50 + bullish_count * 10, 80)
    elif bearish_count > bullish_count:
        signal = "bearish"
        confidence = min(50 + bearish_count * 10, 80)
    else:
        signal = "neutral"
        confidence = 50
    
    return {
        "signal": signal,
        "confidence": confidence,
        "metrics": macro_data,
        "summary": f"Analyzed {len(signals)} macro indicators"
    }


def combine_news_signals(signals: list, weights: dict) -> dict:
    """Combine news signals with weighted averaging."""
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


def _matches_keywords(news: dict, keywords: list) -> bool:
    """Check if news matches any keywords."""
    text = (news.get("title", "") + " " + news.get("content", "")).lower()
    return any(kw.lower() in text for kw in keywords)


def _calculate_relevance(news_data: list) -> dict:
    """Calculate relevance scores for different categories."""
    categories = {
        "fed": 0,
        "inflation": 0,
        "geopolitical": 0,
        "central_bank": 0,
        "economic": 0,
    }
    
    for news in news_data:
        cat = news.get("category", "")
        if cat in categories:
            categories[cat] += 1
    
    return categories


def _extract_news_factors(reasoning: dict) -> list:
    """Extract key factors from news analysis."""
    factors = []
    
    combined = reasoning.get("combined", {})
    
    if reasoning.get("geopolitical_analysis", {}).get("metrics", {}).get("risk_level") == "high":
        factors.append("High geopolitical risk - safe haven demand")
    
    if reasoning.get("fed_analysis", {}).get("signal") == "bullish":
        factors.append("Dovish Fed stance supporting gold")
    elif reasoning.get("fed_analysis", {}).get("signal") == "bearish":
        factors.append("Hawkish Fed pressuring gold")
    
    if reasoning.get("inflation_analysis", {}).get("signal") == "bullish":
        factors.append("Inflation concerns boosting gold")
    
    return factors


def _extract_news_warnings(reasoning: dict) -> list:
    """Extract warnings from news analysis."""
    warnings = []
    
    if reasoning.get("fed_analysis", {}).get("metrics", {}).get("impact") == "high":
        warnings.append("Major Fed news expected - watch for volatility")
    
    return warnings


def _generate_mock_news_analysis(symbol: str) -> list:
    """Generate mock news for testing."""
    return [
        {
            "title": "Fed signals potential rate cuts in 2024",
            "sentiment": "negative",  # Dovish = positive for gold
            "category": "fed",
            "severity": 0.7
        },
        {
            "title": "CPI data shows inflation cooling",
            "sentiment": "negative",  # Lower inflation
            "category": "inflation",
            "severity": 0.5
        },
    ]
