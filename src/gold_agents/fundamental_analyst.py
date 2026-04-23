"""
Gold Fundamental Analyst Agent

Analyzes fundamental factors affecting XAUUSD.
Focuses on: supply/demand dynamics, central bank policies, cost of production, market structure.
"""

from langchain_core.messages import HumanMessage
import json
from datetime import datetime

from src.graph.state import AgentState, show_agent_reasoning
from src.gold_agents.models import GoldSignal, SupplyDemandData
from src.utils.progress import progress


def gold_fundamental_analyst_agent(
    state: AgentState,
    agent_id: str = "gold_fundamental_analyst"
) -> dict:
    """
    Gold Fundamental Analyst Agent.
    
    Analyzes fundamental factors affecting gold:
    - Supply and demand dynamics
    - Central bank gold reserves and policies
    - Mining production and costs
    - Jewelry and technology demand
    - Investment flows (ETF, futures)
    - Market structure (COMEX, LBMA)
    """
    data = state["data"]
    symbol = data.get("symbol", "XAUUSD")
    
    progress.update_status(agent_id, symbol, "Collecting fundamental data")
    
    # Get fundamental data from state or use provided
    fundamental_data = data.get("fundamental_data", {})
    
    if not fundamental_data:
        fundamental_data = _generate_mock_fundamental_data()
    
    # Analyze different fundamental dimensions
    supply_analysis = analyze_supply(fundamental_data)
    demand_analysis = analyze_demand(fundamental_data)
    cb_analysis = analyze_central_bank_policy(fundamental_data)
    market_structure = analyze_market_structure(fundamental_data)
    production_analysis = analyze_production_costs(fundamental_data)
    
    # Weighted combination
    weights = {
        "supply": 0.20,
        "demand": 0.20,
        "central_bank": 0.30,
        "market_structure": 0.15,
        "production": 0.15,
    }
    
    combined = combine_fundamental_signals(
        [supply_analysis, demand_analysis, cb_analysis, market_structure, production_analysis],
        weights
    )
    
    reasoning = {
        "supply_analysis": supply_analysis,
        "demand_analysis": demand_analysis,
        "central_bank_analysis": cb_analysis,
        "market_structure": market_structure,
        "production_analysis": production_analysis,
        "combined": combined,
        "supply_demand_balance": _calculate_supply_demand_balance(fundamental_data),
    }
    
    signal = GoldSignal(
        signal=combined["signal"],
        confidence=combined["confidence"],
        reasoning=reasoning,
        key_factors=_extract_fundamental_factors(reasoning),
        warnings=_extract_fundamental_warnings(reasoning),
    )
    
    progress.update_status(agent_id, symbol, "Done",
                         analysis=json.dumps(reasoning, indent=2, default=str))
    
    if state["metadata"]["show_reasoning"]:
        show_agent_reasoning(reasoning, "Gold Fundamental Analyst")
    
    state["data"]["analyst_signals"][agent_id] = signal.model_dump()
    
    return {
        "messages": state["messages"] + [HumanMessage(content=json.dumps(signal.model_dump()), name=agent_id)],
        "data": state["data"],
    }


def analyze_supply(fundamental_data: dict) -> dict:
    """Analyze gold supply factors."""
    supply = fundamental_data.get("supply", {})
    
    mining_production = supply.get("mining_production_y", 3600)  # tonnes/year
    scrap_supply = supply.get("scrap_supply_y", 1100)
    
    # Supply trend
    mining_trend = supply.get("mining_trend", "stable")  # "increasing", "stable", "decreasing"
    scrap_trend = supply.get("scrap_trend", "stable")
    
    # Total supply
    total_supply = mining_production + scrap_supply
    supply_disruption = supply.get("supply_disruption_risk", "low")  # "low", "medium", "high"
    
    # Impact assessment
    if mining_trend == "decreasing" or supply_disruption == "high":
        signal = "bullish"
        confidence = 70
        impact = "Supply constraints supporting prices"
    elif mining_trend == "increasing":
        signal = "bearish"
        confidence = 60
        impact = "Rising supply pressuring prices"
    else:
        signal = "neutral"
        confidence = 50
        impact = "Stable supply conditions"
    
    return {
        "signal": signal,
        "confidence": confidence,
        "metrics": {
            "mining_production_y": mining_production,
            "scrap_supply_y": scrap_supply,
            "total_supply_y": total_supply,
            "mining_trend": mining_trend,
            "scrap_trend": scrap_trend,
            "supply_disruption_risk": supply_disruption,
        },
        "summary": f"Annual supply: {total_supply} tonnes, Trend: {mining_trend}"
    }


def analyze_demand(fundamental_data: dict) -> dict:
    """Analyze gold demand factors."""
    demand = fundamental_data.get("demand", {})
    
    jewelry_demand = demand.get("jewelry_y", 2100)  # tonnes/year
    investment_demand = demand.get("investment_y", 1000)
    cb_purchase = demand.get("cb_purchase_y", 1000)  # Net central bank purchase
    tech_demand = demand.get("tech_y", 400)
    
    # Demand trends
    jewelry_trend = demand.get("jewelry_trend", "stable")
    investment_trend = demand.get("investment_trend", "stable")
    
    # Total demand
    total_demand = jewelry_demand + investment_demand + tech_demand
    
    # Investment demand is most price-sensitive
    if investment_trend == "increasing" or cb_purchase > 1000:
        signal = "bullish"
        confidence = 75
        impact = "Strong investment and CB demand"
    elif investment_trend == "decreasing" and jewelry_trend == "decreasing":
        signal = "bearish"
        confidence = 65
        impact = "Weak demand across sectors"
    elif jewelry_demand < 1800:  # Weak jewelry demand
        signal = "neutral"
        confidence = 55
        impact = "Below-average jewelry demand"
    else:
        signal = "neutral"
        confidence = 50
        impact = "Normal demand conditions"
    
    return {
        "signal": signal,
        "confidence": confidence,
        "metrics": {
            "jewelry_demand_y": jewelry_demand,
            "investment_demand_y": investment_demand,
            "cb_purchase_y": cb_purchase,
            "tech_demand_y": tech_demand,
            "total_demand_y": total_demand,
            "jewelry_trend": jewelry_trend,
            "investment_trend": investment_trend,
        },
        "summary": f"Annual demand: {total_demand} tonnes, CB: {cb_purchase} tonnes net"
    }


def analyze_central_bank_policy(fundamental_data: dict) -> dict:
    """Analyze central bank gold policies."""
    cb = fundamental_data.get("central_bank", {})
    
    cb_purchase_q = cb.get("purchase_q", 0)  # Quarterly tonnes
    cb_reserves_pct = cb.get("reserves_pct", 10)  # % of total reserves
    cb_diversification = cb.get("diversification_trend", "neutral")  # "buying", "selling", "neutral"
    
    # Major CB policies
    fed_policy = cb.get("fed_policy", "neutral")  # "hawkish", "dovish", "neutral"
    ecb_policy = cb.get("ecb_policy", "neutral")
    
    # Signal based on CB activity
    if cb_purchase_q > 100 or cb_diversification == "buying":
        signal = "bullish"
        confidence = 80
        impact = "Central banks actively buying gold"
    elif cb_purchase_q < -100 or cb_diversification == "selling":
        signal = "bearish"
        confidence = 70
        impact = "Central banks reducing gold exposure"
    else:
        signal = "neutral"
        confidence = 50
        impact = "No major CB activity"
    
    # Add Fed policy impact
    if fed_policy == "dovish":
        signal = "bullish"
        confidence = min(confidence + 10, 90)
        impact += " - Dovish Fed supporting"
    elif fed_policy == "hawkish":
        impact += " - Hawkish Fed pressuring"
    
    return {
        "signal": signal,
        "confidence": confidence,
        "metrics": {
            "cb_purchase_q": cb_purchase_q,
            "cb_reserves_pct": cb_reserves_pct,
            "cb_diversification": cb_diversification,
            "fed_policy": fed_policy,
            "ecb_policy": ecb_policy,
        },
        "summary": f"CB quarterly net: {cb_purchase_q} tonnes, Reserves %: {cb_reserves_pct}%"
    }


def analyze_market_structure(fundamental_data: dict) -> dict:
    """Analyze gold market structure and futures markets."""
    structure = fundamental_data.get("market_structure", {})
    
    comex_inventory = structure.get("comex_inventory", 0)  # tonnes
    etf_holdings = structure.get("etf_holdings", 0)  # tonnes
    open_interest = structure.get("open_interest", 0)  # contracts
    
    # Premium/discount
    spot_futures_premium = structure.get("spot_futures_premium", 0)  # $/oz
    
    # Inventory trend
    inventory_trend = structure.get("inventory_trend", "stable")
    
    # Market structure signal
    if comex_inventory < 500 or inventory_trend == "decreasing":
        signal = "bullish"
        confidence = 65
        impact = "Low warehouse stocks - potential squeeze"
    elif comex_inventory > 1000 and inventory_trend == "increasing":
        signal = "bearish"
        confidence = 60
        impact = "High warehouse stocks - ample supply"
    elif abs(spot_futures_premium) > 20:
        signal = "bullish" if spot_futures_premium < 0 else "bearish"
        confidence = 70
        impact = f"Backwardation: ${spot_futures_premium:.2f}/oz"
    else:
        signal = "neutral"
        confidence = 50
        impact = "Normal market structure"
    
    return {
        "signal": signal,
        "confidence": confidence,
        "metrics": {
            "comex_inventory": comex_inventory,
            "etf_holdings": etf_holdings,
            "open_interest": open_interest,
            "spot_futures_premium": spot_futures_premium,
            "inventory_trend": inventory_trend,
        },
        "summary": f"COMEX: {comex_inventory}t, ETF: {etf_holdings}t, Premium: ${spot_futures_premium:.2f}"
    }


def analyze_production_costs(fundamental_data: dict) -> dict:
    """Analyze gold production costs."""
    costs = fundamental_data.get("production_costs", {})
    
    all_in_sustaining_cost = costs.get("aisc", 1200)  # $/oz
    current_price = costs.get("current_price", 1900)
    
    # Cost curves
    marginal_producer_cost = costs.get("marginal_cost", 1400)  # $/oz
    high_cost_producers = costs.get("high_cost_producers_pct", 20)  # % operating at loss
    
    # Margin analysis
    margin = current_price - aisc
    margin_pct = (margin / aisc) * 100
    
    # Price floor signal
    if margin < 200:  # Tight margins
        signal = "bullish"
        confidence = 70
        impact = f"Thin margins (${margin:.0f}/oz) - production may cut"
    elif margin > 600:  # Healthy margins
        signal = "neutral"
        confidence = 55
        impact = f"Healthy margins (${margin:.0f}/oz)"
    else:
        signal = "neutral"
        confidence = 50
        impact = f"Average margins (${margin:.0f}/oz)"
    
    return {
        "signal": signal,
        "confidence": confidence,
        "metrics": {
            "aisc": aisc_in_sustaining_cost if (aisc_in_sustaining_cost := aisc) else aisc,
            "current_price": current_price,
            "margin": margin,
            "margin_pct": margin_pct,
            "marginal_cost": marginal_producer_cost,
            "high_cost_producers_pct": high_cost_producers,
        },
        "summary": f"AISC: ${aisc}/oz, Price: ${current_price}/oz, Margin: ${margin:.0f}/oz"
    }


def combine_fundamental_signals(signals: list, weights: dict) -> dict:
    """Combine fundamental signals with weighted averaging."""
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


def _calculate_supply_demand_balance(fundamental_data: dict) -> dict:
    """Calculate supply-demand balance."""
    supply = fundamental_data.get("supply", {})
    demand = fundamental_data.get("demand", {})
    
    total_supply = supply.get("mining_production_y", 3600) + supply.get("scrap_supply_y", 1100)
    total_demand = (demand.get("jewelry_y", 2100) + 
                   demand.get("investment_y", 1000) + 
                   demand.get("tech_y", 400))
    
    balance = total_demand - total_supply
    balance_pct = (balance / total_supply) * 100 if total_supply > 0 else 0
    
    return {
        "total_supply": total_supply,
        "total_demand": total_demand,
        "balance": balance,
        "balance_pct": balance_pct,
        "deficit": balance > 0,
        "surplus": balance < 0,
    }


def _extract_fundamental_factors(reasoning: dict) -> list:
    """Extract key factors from fundamental analysis."""
    factors = []
    
    cb = reasoning.get("central_bank_analysis", {})
    if cb.get("signal") == "bullish":
        factors.append("Strong central bank buying")
    
    sd_balance = reasoning.get("supply_demand_balance", {})
    if sd_balance.get("deficit"):
        factors.append(f"Supply deficit: {sd_balance.get('balance_pct', 0):.1f}%")
    elif sd_balance.get("surplus"):
        factors.append(f"Supply surplus: {abs(sd_balance.get('balance_pct', 0)):.1f}%")
    
    market = reasoning.get("market_structure", {})
    if "squeeze" in market.get("summary", "").lower():
        factors.append("Potential market squeeze")
    
    return factors


def _extract_fundamental_warnings(reasoning: dict) -> list:
    """Extract warnings from fundamental analysis."""
    warnings = []
    
    prod = reasoning.get("production_analysis", {})
    if prod.get("metrics", {}).get("high_cost_producers_pct", 0) > 30:
        warnings.append("High cost producers under pressure - production cuts possible")
    
    cb = reasoning.get("central_bank_analysis", {})
    if cb.get("metrics", {}).get("fed_policy") == "hawkish":
        warnings.append("Hawkish Fed policy could pressure gold")
    
    return warnings


def _generate_mock_fundamental_data() -> dict:
    """Generate mock fundamental data for testing."""
    return {
        "supply": {
            "mining_production_y": 3650,  # tonnes
            "scrap_supply_y": 1100,
            "mining_trend": "stable",
            "scrap_trend": "increasing",
            "supply_disruption_risk": "low",
        },
        "demand": {
            "jewelry_y": 2200,
            "investment_y": 1200,
            "cb_purchase_y": 1100,
            "tech_y": 400,
            "jewelry_trend": "stable",
            "investment_trend": "increasing",
        },
        "central_bank": {
            "purchase_q": 150,  # tonnes
            "reserves_pct": 12,
            "diversification_trend": "buying",
            "fed_policy": "dovish",
            "ecb_policy": "neutral",
        },
        "market_structure": {
            "comex_inventory": 700,
            "etf_holdings": 3000,
            "open_interest": 450000,
            "spot_futures_premium": -5,
            "inventory_trend": "stable",
        },
        "production_costs": {
            "aisc": 1250,  # $/oz
            "current_price": 1950,
            "marginal_cost": 1400,
            "high_cost_producers_pct": 15,
        }
    }
