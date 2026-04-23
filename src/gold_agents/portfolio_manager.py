"""
Gold Portfolio Manager Agent

Final decision-making agent that synthesizes all analyst signals
and generates trading recommendations for XAUUSD.
"""

from langchain_core.messages import HumanMessage
import json
from datetime import datetime

from src.graph.state import AgentState, show_agent_reasoning
from src.gold_agents.models import GoldSignal, PortfolioRecommendation
from src.utils.progress import progress


def gold_portfolio_manager_agent(
    state: AgentState,
    agent_id: str = "gold_portfolio_manager"
) -> dict:
    """
    Gold Portfolio Manager Agent.
    
    Synthesizes all analyst signals to generate trading recommendations:
    - Aggregates signals from all analysts
    - Calculates weighted consensus
    - Generates specific trading actions
    - Provides entry, stop-loss, and take-profit levels
    """
    data = state["data"]
    symbol = data.get("symbol", "XAUUSD")
    analyst_signals = state["data"].get("analyst_signals", {})
    risk_assessment = state["data"].get("risk_assessment", {})
    support_resistance = risk_assessment.get("support_resistance", {})
    
    progress.update_status(agent_id, symbol, "Synthesizing analyst signals")
    
    # Extract signals from all analysts
    analyst_scores = aggregate_analyst_signals(analyst_signals)
    
    # Calculate consensus
    consensus = calculate_consensus(analyst_scores, risk_assessment)
    
    # Generate trading recommendation
    recommendation = generate_recommendation(
        consensus, 
        risk_assessment, 
        support_resistance,
        data
    )
    
    # Create final signal
    final_signal = GoldSignal(
        signal=recommendation.action,
        confidence=recommendation.confidence,
        reasoning={
            "analyst_scores": analyst_scores,
            "consensus": consensus,
            "recommendation": recommendation.model_dump(),
        },
        key_factors=_extract_decision_factors(analyst_scores, consensus),
        warnings=_extract_decision_warnings(consensus, risk_assessment),
    )
    
    progress.update_status(agent_id, symbol, "Done",
                         analysis=json.dumps(consensus, indent=2, default=str))
    
    if state["metadata"]["show_reasoning"]:
        show_agent_reasoning(consensus, "Gold Portfolio Manager")
    
    state["data"]["analyst_signals"][agent_id] = final_signal.model_dump()
    state["data"]["recommendation"] = recommendation.model_dump()
    
    return {
        "messages": state["messages"] + [HumanMessage(content=json.dumps(final_signal.model_dump()), name=agent_id)],
        "data": state["data"],
    }


def aggregate_analyst_signals(analyst_signals: dict) -> dict:
    """Aggregate signals from all analysts."""
    scores = {
        "bullish": 0,
        "neutral": 0,
        "bearish": 0,
        "total_confidence": 0,
        "analysts": {},
        "count": 0,
    }
    
    # Agent weights (can be configured)
    agent_weights = {
        "gold_technical_analyst": 0.20,
        "gold_news_analyst": 0.15,
        "gold_sentiment_analyst": 0.15,
        "gold_fundamental_analyst": 0.20,
        "gold_macro_analyst": 0.20,
        "gold_risk_manager": 0.10,
    }
    
    for agent_name, signal_data in analyst_signals.items():
        if not isinstance(signal_data, dict):
            continue
        
        signal = signal_data.get("signal", "neutral")
        confidence = signal_data.get("confidence", 50) / 100
        
        # Get weight for this agent
        weight = agent_weights.get(agent_name, 0.1)
        
        # Record individual score
        scores["analysts"][agent_name] = {
            "signal": signal,
            "confidence": confidence * 100,
            "weight": weight,
            "weighted_score": _signal_to_score(signal) * confidence * weight,
        }
        
        # Aggregate
        if signal == "bullish":
            scores["bullish"] += 1
            scores["total_confidence"] += confidence
        elif signal == "bearish":
            scores["bearish"] += 1
            scores["total_confidence"] += confidence
        else:
            scores["neutral"] += 1
        
        scores["count"] += 1
    
    # Calculate weighted score
    total_weight = sum(a["weight"] for a in scores["analysts"].values())
    weighted_score = sum(a["weighted_score"] for a in scores["analysts"].values())
    
    if total_weight > 0:
        scores["weighted_score"] = weighted_score / total_weight
    else:
        scores["weighted_score"] = 0
    
    return scores


def calculate_consensus(analyst_scores: dict, risk_assessment: dict) -> dict:
    """Calculate consensus from analyst scores."""
    # Determine consensus signal
    bullish = analyst_scores["bullish"]
    bearish = analyst_scores["bearish"]
    neutral = analyst_scores["neutral"]
    total = analyst_scores["count"]
    
    if total == 0:
        return {
            "signal": "neutral",
            "confidence": 50,
            "bullish_pct": 33.3,
            "bearish_pct": 33.3,
            "neutral_pct": 33.3,
            "strength": "none",
        }
    
    bullish_pct = (bullish / total) * 100
    bearish_pct = (bearish / total) * 100
    neutral_pct = (neutral / total) * 100
    
    # Determine signal
    if bullish >= bearish * 1.5 and bullish >= 3:
        consensus_signal = "bullish"
        strength = "strong" if bullish >= 4 else "moderate"
    elif bearish >= bullish * 1.5 and bearish >= 3:
        consensus_signal = "bearish"
        strength = "strong" if bearish >= 4 else "moderate"
    elif bullish > bearish + 1:
        consensus_signal = "bullish"
        strength = "mild"
    elif bearish > bullish + 1:
        consensus_signal = "bearish"
        strength = "mild"
    elif bullish == bearish:
        consensus_signal = "neutral"
        strength = "none"
    else:
        consensus_signal = "neutral"
        strength = "mixed"
    
    # Adjust confidence based on consensus strength
    if strength == "strong":
        base_confidence = 80
    elif strength == "moderate":
        base_confidence = 70
    elif strength == "mild":
        base_confidence = 60
    else:
        base_confidence = 50
    
    # Factor in risk assessment
    risk_level = risk_assessment.get("risk_level", "medium")
    if risk_level == "high":
        base_confidence = base_confidence * 0.7
    elif risk_level == "low":
        base_confidence = base_confidence * 1.1
    
    return {
        "signal": consensus_signal,
        "confidence": min(max(base_confidence, 30), 95),
        "bullish_pct": bullish_pct,
        "bearish_pct": bearish_pct,
        "neutral_pct": neutral_pct,
        "strength": strength,
        "weighted_score": analyst_scores["weighted_score"],
        "total_analysts": total,
    }


def generate_recommendation(
    consensus: dict,
    risk_assessment: dict,
    levels: dict,
    data: dict
) -> PortfolioRecommendation:
    """Generate trading recommendation."""
    signal = consensus["signal"]
    confidence = consensus["confidence"]
    current_price = levels.get("current_price", data.get("current_price", 1900))
    
    # Get support/resistance
    support = levels.get("nearest_support", current_price * 0.98)
    resistance = levels.get("nearest_resistance", current_price * 1.02)
    atr = levels.get("atr_stop_loss", current_price * 0.015)
    
    # Determine action
    if confidence >= 75 and signal == "bullish":
        action = "strong_buy"
    elif confidence >= 65 and signal == "bullish":
        action = "buy"
    elif confidence >= 75 and signal == "bearish":
        action = "strong_sell"
    elif confidence >= 65 and signal == "bearish":
        action = "sell"
    elif confidence >= 55:
        action = "hold"  # Slight bias
    else:
        action = "hold"
    
    # Calculate stop-loss
    if signal == "bullish":
        stop_loss = current_price - (atr * 1.5)
    elif signal == "bearish":
        stop_loss = current_price + (atr * 1.5)
    else:
        stop_loss = current_price - (atr * 1.0)
    
    # Calculate take-profit
    if signal == "bullish":
        take_profit = current_price + (atr * 3)
    elif signal == "bearish":
        take_profit = current_price - (atr * 3)
    else:
        take_profit = resistance if signal == "bullish" else support
    
    # Risk/reward ratio
    risk_amount = abs(current_price - stop_loss)
    reward_amount = abs(take_profit - current_price)
    rr_ratio = reward_amount / risk_amount if risk_amount > 0 else 0
    
    # Position sizing based on risk
    portfolio = data.get("portfolio", {})
    cash = portfolio.get("cash", 100000)
    risk_pct = 0.01 if risk_assessment.get("risk_level") == "medium" else 0.005 if risk_assessment.get("risk_level") == "low" else 0.005
    
    risk_amount_dollar = cash * risk_pct
    position_size = risk_amount_dollar / risk_amount if risk_amount > 0 else 0
    
    return PortfolioRecommendation(
        action=action,
        quantity=position_size,
        entry_price=current_price,
        stop_loss=stop_loss,
        take_profit=take_profit,
        risk_reward_ratio=rr_ratio,
        confidence=confidence,
        reasoning={
            "consensus": consensus,
            "entry_rationale": f"Based on {consensus['strength']} {signal} consensus from {consensus['total_analysts']} analysts",
            "stop_loss_rationale": f"ATR-based stop at {1.5}x ATR",
            "take_profit_rationale": f"3x ATR target from entry",
        },
        risk_assessment={
            "overall_risk": risk_assessment.get("risk_level", "unknown"),
            "risk_score": risk_assessment.get("overall_risk_score", 0.5),
            "warnings": risk_assessment.get("warnings", []),
        }
    )


def _signal_to_score(signal: str) -> float:
    """Convert signal to numeric score."""
    scores = {
        "strong_buy": 1.0,
        "buy": 0.8,
        "bullish": 0.6,
        "neutral": 0,
        "bearish": -0.6,
        "sell": -0.8,
        "strong_sell": -1.0,
    }
    return scores.get(signal, 0)


def _extract_decision_factors(analyst_scores: dict, consensus: dict) -> list:
    """Extract key decision factors."""
    factors = []
    
    # Analyst consensus
    if consensus["strength"] == "strong":
        factors.append(f"Strong {consensus['signal']} consensus ({consensus['bullish_pct']:.0f}% bullish)")
    elif consensus["strength"] == "moderate":
        factors.append(f"Moderate {consensus['signal']} bias ({consensus['bullish_pct']:.0f}% vs {consensus['bearish_pct']:.0f}% bearish)")
    
    # Weighted score
    if analyst_scores.get("weighted_score", 0) > 0.3:
        factors.append("Strong weighted buy signal")
    elif analyst_scores.get("weighted_score", 0) < -0.3:
        factors.append("Strong weighted sell signal")
    
    return factors


def _extract_decision_warnings(consensus: dict, risk_assessment: dict) -> list:
    """Extract decision warnings."""
    warnings = []
    
    if consensus["strength"] == "mixed":
        warnings.append("Mixed signals from analysts - consider waiting for clarity")
    
    if consensus["confidence"] < 60:
        warnings.append("Low confidence - trade with reduced size")
    
    if risk_assessment.get("risk_level") == "high":
        warnings.append("High risk environment - consider avoiding new positions")
    
    return warnings
