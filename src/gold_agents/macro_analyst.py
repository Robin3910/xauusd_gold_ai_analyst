"""
Gold Macro Analyst Agent

Analyzes macroeconomic factors affecting XAUUSD.
Focuses on: interest rates, USD strength, inflation, risk sentiment, and correlations.
"""

from langchain_core.messages import HumanMessage
import json
from datetime import datetime

from src.graph.state import AgentState, show_agent_reasoning
from src.gold_agents.models import GoldSignal, MacroIndicators
from src.utils.progress import progress


def gold_macro_analyst_agent(
    state: AgentState,
    agent_id: str = "gold_macro_analyst"
) -> dict:
    """
    Gold Macro Analyst Agent.
    
    Analyzes macroeconomic factors affecting gold:
    - Interest rates and real yields
    - US Dollar strength (DXY)
    - Inflation expectations
    - Risk sentiment (VIX, credit spreads)
    - Cross-asset correlations
    - Global growth indicators
    """
    data = state["data"]
    symbol = data.get("symbol", "XAUUSD")
    
    progress.update_status(agent_id, symbol, "Collecting macro data")
    
    # Get macro data from state or use provided
    macro_data = data.get("macro_data", {})
    
    if not macro_data:
        macro_data = _generate_mock_macro_data()
    
    # Analyze different macro dimensions
    rates_analysis = analyze_interest_rates(macro_data)
    dollar_analysis = analyze_dollar_strength(macro_data)
    inflation_analysis = analyze_inflation_expectations(macro_data)
    risk_analysis = analyze_macro_risk(macro_data)
    correlation_analysis = analyze_correlations(macro_data)
    
    # Weighted combination
    weights = {
        "rates": 0.30,
        "dollar": 0.25,
        "inflation": 0.20,
        "risk": 0.15,
        "correlations": 0.10,
    }
    
    combined = combine_macro_signals(
        [rates_analysis, dollar_analysis, inflation_analysis, risk_analysis, correlation_analysis],
        weights
    )
    
    reasoning = {
        "rates_analysis": rates_analysis,
        "dollar_analysis": dollar_analysis,
        "inflation_analysis": inflation_analysis,
        "risk_analysis": risk_analysis,
        "correlation_analysis": correlation_analysis,
        "combined": combined,
        "gold_drive_model": _identify_gold_driver(macro_data, combined),
    }
    
    signal = GoldSignal(
        signal=combined["signal"],
        confidence=combined["confidence"],
        reasoning=reasoning,
        key_factors=_extract_macro_factors(reasoning),
        warnings=_extract_macro_warnings(reasoning),
    )
    
    progress.update_status(agent_id, symbol, "Done",
                         analysis=json.dumps(reasoning, indent=2, default=str))
    
    if state["metadata"]["show_reasoning"]:
        show_agent_reasoning(reasoning, "Gold Macro Analyst")
    
    state["data"]["analyst_signals"][agent_id] = signal.model_dump()
    
    return {
        "messages": state["messages"] + [HumanMessage(content=json.dumps(signal.model_dump()), name=agent_id)],
        "data": state["data"],
    }


def analyze_interest_rates(macro_data: dict) -> dict:
    """Analyze interest rate impact on gold."""
    rates = macro_data.get("interest_rates", {})
    
    fed_funds = rates.get("fed_funds_rate", 5.25)
    real_yield_10y = rates.get("real_yield_10y", 1.5)
    nominal_yield_10y = rates.get("nominal_yield_10y", 4.5)
    yield_curve = rates.get("yield_curve", "normal")  # "inverted", "normal", "flat"
    
    # Gold-opposite relationship with real yields
    # Negative real yields = bullish for gold
    # Positive real yields = bearish for gold (opportunity cost)
    
    if real_yield_10y < 0:
        signal = "bullish"
        confidence = min(80 - real_yield_10y * 30, 95)  # More negative = higher confidence
        impact = f"Negative real yields ({real_yield_10y:.2f}%) highly supportive"
    elif real_yield_10y < 1:
        signal = "bullish"
        confidence = min(60 + (1 - real_yield_10y) * 20, 75)
        impact = f"Low real yields supportive"
    elif real_yield_10y > 2:
        signal = "bearish"
        confidence = min(70 + (real_yield_10y - 2) * 15, 90)
        impact = f"High real yields ({real_yield_10y:.2f}%) headwind for gold"
    else:
        signal = "neutral"
        confidence = 50
        impact = "Real yields at neutral levels"
    
    # Yield curve impact
    if yield_curve == "inverted":
        confidence = min(confidence + 10, 95)
        impact += " - Inverted curve suggests recession risk"
    elif yield_curve == "flat":
        impact += " - Flat yield curve uncertainty"
    
    return {
        "signal": signal,
        "confidence": confidence,
        "metrics": {
            "fed_funds_rate": fed_funds,
            "real_yield_10y": real_yield_10y,
            "nominal_yield_10y": nominal_yield_10y,
            "yield_curve": yield_curve,
            "gold_yield_correlation": "strong_negative" if real_yield_10y < 0 else "moderate_negative"
        },
        "summary": f"Fed: {fed_funds:.2f}%, Real 10Y: {real_yield_10y:.2f}%, Curve: {yield_curve}"
    }


def analyze_dollar_strength(macro_data: dict) -> dict:
    """Analyze USD strength impact on gold."""
    dollar = macro_data.get("dollar", {})
    
    dxy = dollar.get("dxy", 104)
    dxy_change_1m = dollar.get("dxy_change_1m", 0)
    dxy_change_3m = dollar.get("dxy_change_3m", 0)
    
    # Gold has strong negative correlation with USD
    # Strong USD = bearish for gold (and vice versa)
    
    if dxy > 107:  # Very strong dollar
        signal = "bearish"
        confidence = min(75 + (dxy - 107) * 5, 90)
        impact = "Strong USD headwind"
    elif dxy > 104:  # Above average strength
        signal = "bearish"
        confidence = 65
        impact = "Above-average USD strength"
    elif dxy < 100:  # Weak dollar
        signal = "bullish"
        confidence = min(75 + (100 - dxy) * 3, 90)
        impact = "Weak USD tailwind"
    elif dxy < 95:  # Very weak dollar
        signal = "bullish"
        confidence = 85
        impact = "Very weak USD highly supportive"
    else:
        signal = "neutral"
        confidence = 50
        impact = "Neutral USD levels"
    
    # Momentum
    if dxy_change_1m > 2:
        confidence = min(confidence + 10, 95)
        impact += " - USD gaining rapidly"
    elif dxy_change_1m < -2:
        confidence = min(confidence + 10, 95)
        impact += " - USD weakening rapidly"
    
    return {
        "signal": signal,
        "confidence": confidence,
        "metrics": {
            "dxy": dxy,
            "dxy_change_1m": dxy_change_1m,
            "dxy_change_3m": dxy_change_3m,
            "strength": "strong" if dxy > 107 else "weak" if dxy < 100 else "neutral"
        },
        "summary": f"DXY: {dxy:.2f} ({dxy_change_1m:+.2f}% 1M), Strength: {impact}"
    }


def analyze_inflation_expectations(macro_data: dict) -> dict:
    """Analyze inflation impact on gold."""
    inflation = macro_data.get("inflation", {})
    
    cpi_yoy = inflation.get("cpi_yoy", 3.2)
    core_cpi = inflation.get("core_cpi", 3.8)
    ppi_yoy = inflation.get("ppi_yoy", 2.5)
    breakeven_10y = inflation.get("breakeven_10y", 2.3)  # Market inflation expectations
    
    # Gold is an inflation hedge
    # High/rising inflation = bullish
    # Low/falling inflation = bearish
    
    if cpi_yoy > 5 or core_cpi > 5:
        signal = "bullish"
        confidence = min(70 + (cpi_yoy - 5) * 10, 90)
        impact = "High inflation strongly supportive"
    elif cpi_yoy > 3:
        signal = "bullish"
        confidence = 65
        impact = "Above-target inflation supportive"
    elif cpi_yoy > 2:
        signal = "neutral"
        confidence = 55
        impact = "At-target inflation neutral"
    elif cpi_yoy < 2:
        signal = "bearish"
        confidence = min(70 + (2 - cpi_yoy) * 15, 85)
        impact = "Below-target inflation headwind"
    else:
        signal = "neutral"
        confidence = 50
        impact = "Stable inflation expectations"
    
    # Breakeven inflation expectations
    if breakeven_10y > 2.5:
        impact += f" - Market expects {breakeven_10y:.1f}% inflation"
    elif breakeven_10y < 2.0:
        impact += " - Market expects low inflation"
    
    # Trend
    inflation_trend = inflation.get("trend", "stable")  # "rising", "falling", "stable"
    if inflation_trend == "falling":
        signal = "bearish"
        confidence = min(confidence + 10, 90)
        impact += " - Inflation falling"
    elif inflation_trend == "rising":
        impact += " - Inflation rising"
    
    return {
        "signal": signal,
        "confidence": confidence,
        "metrics": {
            "cpi_yoy": cpi_yoy,
            "core_cpi": core_cpi,
            "ppi_yoy": ppi_yoy,
            "breakeven_10y": breakeven_10y,
            "inflation_trend": inflation_trend,
        },
        "summary": f"CPI: {cpi_yoy:.1f}%, Core: {core_cpi:.1f}%, Breakeven: {breakeven_10y:.1f}%, Trend: {inflation_trend}"
    }


def analyze_macro_risk(macro_data: dict) -> dict:
    """Analyze macro risk sentiment impact on gold."""
    risk = macro_data.get("risk", {})
    
    vix = risk.get("vix", 18)
    credit_spread_hy = risk.get("hy_spread", 400)  # High yield credit spread
    fear_greed = risk.get("fear_greed_index", 50)  # 0-100
    recession_prob = risk.get("recession_prob", 15)  # %
    
    # Gold as safe haven
    # High risk/recession fear = bullish
    # Low risk/risk-on = bearish
    
    if vix > 30 or recession_prob > 40:
        signal = "bullish"
        confidence = 85
        impact = "High risk/recession fear - safe haven demand"
    elif vix > 25 or recession_prob > 25:
        signal = "bullish"
        confidence = 75
        impact = "Elevated risk environment"
    elif fear_greed < 25:  # Extreme fear
        signal = "bullish"
        confidence = 80
        impact = "Extreme fear - safe haven flows"
    elif vix < 15 or fear_greed > 75:  # Complacent/greed
        signal = "bearish"
        confidence = 65
        impact = "Risk-on environment - reduced safe haven demand"
    elif credit_spread_hy > 600:
        signal = "bullish"
        confidence = 70
        impact = "Credit stress - potential safe haven"
    else:
        signal = "neutral"
        confidence = 50
        impact = "Normal risk conditions"
    
    return {
        "signal": signal,
        "confidence": confidence,
        "metrics": {
            "vix": vix,
            "hy_spread": credit_spread_hy,
            "fear_greed_index": fear_greed,
            "recession_prob": recession_prob,
            "risk_regime": "high" if vix > 25 else "low" if vix < 15 else "normal"
        },
        "summary": f"VIX: {vix:.0f}, Fear/Greed: {fear_greed:.0f}, Recession Prob: {recession_prob:.0f}%"
    }


def analyze_correlations(macro_data: dict) -> dict:
    """Analyze cross-asset correlations for gold."""
    corr = macro_data.get("correlations", {})
    
    gold_dxy_corr = corr.get("gold_dxy_corr", -0.7)
    gold_bonds_corr = corr.get("gold_bonds_corr", 0.3)
    gold_stocks_corr = corr.get("gold_stocks_corr", 0.1)
    
    # Correlations and their implications
    analysis = []
    
    if gold_dxy_corr < -0.8:
        analysis.append("Strong inverse DXY correlation - watch USD")
        inv_dxy = "strong"
    elif gold_dxy_corr < -0.5:
        analysis.append("Moderate inverse DXY correlation")
        inv_dxy = "moderate"
    else:
        inv_dxy = "weak"
    
    # Regime detection based on correlation shifts
    corr_regime = corr.get("regime", "normal")  # "risk_on", "risk_off", "inflation", "normal"
    
    if corr_regime == "risk_off":
        signal = "bullish"
        confidence = 75
        impact = "Risk-off correlation regime"
    elif corr_regime == "inflation":
        signal = "bullish"
        confidence = 70
        impact = "Inflation hedge correlation regime"
    elif corr_regime == "risk_on":
        signal = "bearish"
        confidence = 65
        impact = "Risk-on correlation regime"
    else:
        signal = "neutral"
        confidence = 50
        impact = "Normal correlation regime"
    
    return {
        "signal": signal,
        "confidence": confidence,
        "metrics": {
            "gold_dxy_corr": gold_dxy_corr,
            "gold_bonds_corr": gold_bonds_corr,
            "gold_stocks_corr": gold_stocks_corr,
            "correlation_regime": corr_regime,
            "inverse_dxy": inv_dxy,
        },
        "analysis": analysis,
        "summary": f"Regime: {corr_regime}, DXY Corr: {gold_dxy_corr:.2f}"
    }


def combine_macro_signals(signals: list, weights: dict) -> dict:
    """Combine macro signals with weighted averaging."""
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


def _identify_gold_driver(macro_data: dict, combined: dict) -> dict:
    """Identify the primary driver for gold."""
    drivers = {}
    
    rates = macro_data.get("interest_rates", {})
    if rates.get("real_yield_10y", 0) < 0:
        drivers["negative_real_yields"] = 0.9
    elif rates.get("real_yield_10y", 0) > 1.5:
        drivers["positive_real_yields"] = 0.8
    
    dollar = macro_data.get("dollar", {})
    if dollar.get("dxy", 104) > 107:
        drivers["strong_usd"] = 0.7
    
    risk = macro_data.get("risk", {})
    if risk.get("vix", 18) > 25:
        drivers["risk_off"] = 0.8
    elif risk.get("vix", 18) < 15:
        drivers["risk_on"] = 0.6
    
    inflation = macro_data.get("inflation", {})
    if inflation.get("cpi_yoy", 3) > 4:
        drivers["inflation_hedge"] = 0.7
    
    return {
        "primary_driver": max(drivers, key=drivers.get) if drivers else "mixed",
        "confidence": drivers.get(max(drivers, key=drivers.get), 0.5) if drivers else 0.5,
        "all_drivers": drivers
    }


def _extract_macro_factors(reasoning: dict) -> list:
    """Extract key factors from macro analysis."""
    factors = []
    
    rates = reasoning.get("rates_analysis", {})
    if rates.get("signal") == "bullish":
        factors.append(f"Negative/low real yields")
    
    dollar = reasoning.get("dollar_analysis", {})
    if dollar.get("signal") == "bullish":
        factors.append("Weak USD tailwind")
    elif dollar.get("signal") == "bearish":
        factors.append("Strong USD headwind")
    
    driver = reasoning.get("gold_drive_model", {})
    primary = driver.get("primary_driver", "mixed")
    if primary != "mixed":
        factors.append(f"Primary driver: {primary.replace('_', ' ')}")
    
    return factors


def _extract_macro_warnings(reasoning: dict) -> list:
    """Extract warnings from macro analysis."""
    warnings = []
    
    rates = reasoning.get("rates_analysis", {})
    if rates.get("metrics", {}).get("fed_funds_rate", 5) > 5.5:
        warnings.append("Very high interest rates - headwind for gold")
    
    dollar = reasoning.get("dollar_analysis", {})
    if dollar.get("metrics", {}).get("dxy", 104) > 110:
        warnings.append("Extremely strong USD - significant headwind")
    
    return warnings


def _generate_mock_macro_data() -> dict:
    """Generate mock macro data for testing."""
    return {
        "interest_rates": {
            "fed_funds_rate": 5.25,
            "real_yield_10y": 1.8,
            "nominal_yield_10y": 4.5,
            "yield_curve": "inverted",
        },
        "dollar": {
            "dxy": 104.5,
            "dxy_change_1m": 0.5,
            "dxy_change_3m": 1.2,
        },
        "inflation": {
            "cpi_yoy": 3.2,
            "core_cpi": 3.8,
            "ppi_yoy": 2.1,
            "breakeven_10y": 2.3,
            "trend": "falling",
        },
        "risk": {
            "vix": 18,
            "hy_spread": 380,
            "fear_greed_index": 55,
            "recession_prob": 20,
        },
        "correlations": {
            "gold_dxy_corr": -0.75,
            "gold_bonds_corr": 0.25,
            "gold_stocks_corr": 0.05,
            "regime": "normal",
        }
    }
