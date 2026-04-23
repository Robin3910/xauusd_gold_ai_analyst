"""
Gold Analysis Workflow

LangGraph workflow for XAUUSD multi-agent analysis system.
"""

from typing import Optional
from langchain_core.messages import HumanMessage
from langgraph.graph import END, StateGraph
from datetime import datetime, timedelta

from src.graph.state import AgentState as BaseAgentState
from src.gold_agents.config import get_gold_analyst_nodes
from src.gold_agents.risk_manager import gold_risk_manager_agent
from src.gold_agents.portfolio_manager import gold_portfolio_manager_agent
from src.data_sources.client import GoldDataClient


def start_node(state: BaseAgentState) -> BaseAgentState:
    """Initialize the workflow."""
    return state


def create_gold_workflow(selected_analysts: list[str] = None) -> StateGraph:
    """
    Create the Gold Analysis workflow.
    
    Args:
        selected_analysts: List of analyst keys to include. 
                          If None, includes all analysts.
    
    Returns:
        Compiled LangGraph workflow
    """
    workflow = StateGraph(BaseAgentState)
    
    # Add start node
    workflow.add_node("start", start_node)
    
    # Get analyst nodes
    analyst_nodes = get_gold_analyst_nodes()
    
    # Default to all analysts
    if selected_analysts is None:
        selected_analysts = list(analyst_nodes.keys())
    
    # Add selected analyst nodes
    for analyst_key in selected_analysts:
        if analyst_key in analyst_nodes:
            node_name, node_func = analyst_nodes[analyst_key]
            workflow.add_node(node_name, node_func)
            workflow.add_edge("start", node_name)
    
    # Add risk management (after all analysts)
    workflow.add_node("risk_management", gold_risk_manager_agent)
    for analyst_key in selected_analysts:
        if analyst_key in analyst_nodes:
            node_name = analyst_nodes[analyst_key][0]
            workflow.add_edge(node_name, "risk_management")
    
    # Add portfolio manager (final decision)
    workflow.add_node("portfolio_manager", gold_portfolio_manager_agent)
    workflow.add_edge("risk_management", "portfolio_manager")
    workflow.add_edge("portfolio_manager", END)
    
    # Set entry point
    workflow.set_entry_point("start")
    
    return workflow


def run_gold_analysis(
    symbol: str = "XAUUSD",
    start_date: str = None,
    end_date: str = None,
    prices_df = None,
    portfolio: dict = None,
    show_reasoning: bool = False,
    selected_analysts: list[str] = None,
    model_name: str = "gpt-4o",
    model_provider: str = "OpenAI",
    news_data: list = None,
    macro_data: dict = None,
    fundamental_data: dict = None,
    sentiment_data: dict = None,
    auto_fetch_data: bool = True,
) -> dict:
    """
    Run the gold analysis workflow.
    
    Args:
        symbol: Trading symbol (default: XAUUSD)
        start_date: Analysis start date
        end_date: Analysis end date
        prices_df: DataFrame with OHLC price data
        portfolio: Portfolio dictionary with cash and positions
        show_reasoning: Whether to display detailed reasoning
        selected_analysts: List of analysts to run
        model_name: LLM model to use
        model_provider: LLM provider
        news_data: List of news items
        macro_data: Macroeconomic indicators
        fundamental_data: Gold fundamental data
        sentiment_data: Market sentiment data
        auto_fetch_data: If True, automatically fetch missing data
    
    Returns:
        Analysis results including recommendation
    """
    from src.utils.progress import progress
    
    # Default dates
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
    
    # Auto-fetch missing data
    if auto_fetch_data and (prices_df is None or macro_data is None):
        client = GoldDataClient(
            start_date=start_date,
            end_date=end_date,
        )
        client.fetch_all()
        analysis_data = client.get_analysis_data()
        
        prices_df = prices_df or analysis_data["prices_df"]
        macro_data = macro_data or analysis_data["macro_data"]
        news_data = news_data or analysis_data["news_data"]
        fundamental_data = fundamental_data or analysis_data["fundamental_data"]
        sentiment_data = sentiment_data or analysis_data["sentiment_data"]
    
    # Default portfolio
    if portfolio is None:
        portfolio = {
            "cash": 100000,
            "positions": {},
            "margin_requirement": 0.0,
            "margin_used": 0.0,
        }
    
    # Initialize state
    initial_state = {
        "messages": [HumanMessage(content="Analyze XAUUSD market conditions.")],
        "data": {
            "symbol": symbol,
            "tickers": [symbol],
            "start_date": start_date,
            "end_date": end_date,
            "prices_df": prices_df,
            "portfolio": portfolio,
            "analyst_signals": {},
            # Gold-specific data
            "news_data": news_data or [],
            "macro_data": macro_data or {},
            "fundamental_data": fundamental_data or {},
            "sentiment_data": sentiment_data or {},
        },
        "metadata": {
            "show_reasoning": show_reasoning,
            "model_name": model_name,
            "model_provider": model_provider,
        },
    }
    
    # Start progress
    progress.start()
    
    try:
        # Create and run workflow
        workflow = create_gold_workflow(selected_analysts)
        agent = workflow.compile()
        
        final_state = agent.invoke(initial_state)
        
        # Extract results
        return {
            "symbol": symbol,
            "recommendation": final_state["data"].get("recommendation", {}),
            "analyst_signals": final_state["data"].get("analyst_signals", {}),
            "risk_assessment": final_state["data"].get("risk_assessment", {}),
            "metadata": {
                "analysis_date": end_date,
                "analysts_run": selected_analysts or list(get_gold_analyst_nodes().keys()),
            }
        }
        
    finally:
        progress.stop()


def quick_gold_analysis(
    symbol: str = "XAUUSD",
    days_back: int = 180,
    show_reasoning: bool = False,
) -> dict:
    """
    Quick analysis with automatic data fetching.
    
    Args:
        symbol: Trading symbol
        days_back: Days of historical data
        show_reasoning: Show detailed reasoning
    
    Returns:
        Analysis results
    """
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    
    return run_gold_analysis(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        auto_fetch_data=True,
        show_reasoning=show_reasoning,
    )
