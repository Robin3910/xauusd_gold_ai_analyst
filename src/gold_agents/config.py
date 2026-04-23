"""
Gold Analyst Configuration

Configuration for XAUUSD gold analysis agents.
"""

from src.gold_agents.technical_analyst import gold_technical_analyst_agent
from src.gold_agents.news_analyst import gold_news_analyst_agent
from src.gold_agents.sentiment_analyst import gold_sentiment_analyst_agent
from src.gold_agents.fundamental_analyst import gold_fundamental_analyst_agent
from src.gold_agents.macro_analyst import gold_macro_analyst_agent
from src.gold_agents.risk_manager import gold_risk_manager_agent
from src.gold_agents.portfolio_manager import gold_portfolio_manager_agent


# Gold Analyst Configuration
GOLD_ANALYST_CONFIG = {
    "gold_technical_analyst": {
        "display_name": "Gold Technical Analyst",
        "description": "Charts & Technicals",
        "focus": "Price action, trend analysis, technical indicators",
        "agent_func": gold_technical_analyst_agent,
        "type": "analyst",
        "order": 1,
    },
    "gold_news_analyst": {
        "display_name": "Gold News Analyst",
        "description": "News & Events",
        "focus": "Fed policy, inflation, geopolitical events, central banks",
        "agent_func": gold_news_analyst_agent,
        "type": "analyst",
        "order": 2,
    },
    "gold_sentiment_analyst": {
        "display_name": "Gold Sentiment Analyst",
        "description": "Market Sentiment",
        "focus": "CFTC data, surveys, ETF flows, positioning",
        "agent_func": gold_sentiment_analyst_agent,
        "type": "analyst",
        "order": 3,
    },
    "gold_fundamental_analyst": {
        "display_name": "Gold Fundamental Analyst",
        "description": "Supply & Demand",
        "focus": "Mining, jewelry demand, central bank reserves, market structure",
        "agent_func": gold_fundamental_analyst_agent,
        "type": "analyst",
        "order": 4,
    },
    "gold_macro_analyst": {
        "display_name": "Gold Macro Analyst",
        "description": "Macroeconomics",
        "focus": "Interest rates, USD, inflation, risk sentiment",
        "agent_func": gold_macro_analyst_agent,
        "type": "analyst",
        "order": 5,
    },
}


def get_gold_analyst_nodes():
    """Get the mapping of analyst keys to their (node_name, agent_func) tuples."""
    return {
        key: (f"{key}_node", config["agent_func"])
        for key, config in GOLD_ANALYST_CONFIG.items()
    }


def get_gold_analysts_list():
    """Get the list of gold analysts for API responses."""
    return [
        {
            "key": key,
            "display_name": config["display_name"],
            "description": config["description"],
            "focus": config["focus"],
            "order": config["order"]
        }
        for key, config in sorted(GOLD_ANALYST_CONFIG.items(), key=lambda x: x[1]["order"])
    ]
