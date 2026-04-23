"""
Gold Analyst CLI

Command-line interface for the XAUUSD Gold AI Analyst.
"""

import argparse
from datetime import datetime, timedelta
from dotenv import load_dotenv
import sys

from src.gold_agents.workflow import run_gold_analysis, quick_gold_analysis
from src.data_sources.client import GoldDataClient
from src.data_sources.setup_api_keys import main as setup_keys_main


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="XAUUSD Gold AI Analyst - Multi-agent AI system for gold trading analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with auto-detected data sources (no API keys needed):
  python -m src.gold_agents.main

  # Configure API keys:
  python -m src.gold_agents.main --setup-keys

  # Show data sources status:
  python -m src.gold_agents.main --status

  # Run with specific analysts:
  python -m src.gold_agents.main --analysts gold_technical_analyst gold_macro_analyst

  # Show detailed analysis reasoning:
  python -m src.gold_agents.main --show-reasoning

  # Use specific price source:
  python -m src.gold_agents.main --price-source yahoo
        """
    )
    
    parser.add_argument(
        "--setup-keys",
        action="store_true",
        help="Run API key configuration wizard"
    )
    
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show data source configuration status"
    )
    
    parser.add_argument(
        "--symbol", "-s",
        type=str,
        default="XAUUSD",
        help="Trading symbol (default: XAUUSD)"
    )
    
    parser.add_argument(
        "--start-date",
        type=str,
        default=None,
        help="Analysis start date (YYYY-MM-DD). Default: 180 days ago"
    )
    
    parser.add_argument(
        "--end-date", "-e",
        type=str,
        default=None,
        help="Analysis end date (YYYY-MM-DD). Default: today"
    )
    
    parser.add_argument(
        "--days", "-d",
        type=int,
        default=180,
        help="Number of days of historical data (default: 180)"
    )
    
    parser.add_argument(
        "--analysts",
        nargs="+",
        default=None,
        choices=[
            "gold_technical_analyst",
            "gold_news_analyst",
            "gold_sentiment_analyst",
            "gold_fundamental_analyst",
            "gold_macro_analyst",
        ],
        help="Analysts to run. Default: all"
    )
    
    parser.add_argument(
        "--cash",
        type=float,
        default=100000,
        help="Initial cash for position sizing (default: 100000)"
    )
    
    parser.add_argument(
        "--show-reasoning",
        action="store_true",
        help="Show detailed reasoning from each analyst"
    )
    
    parser.add_argument(
        "--fetch-data",
        action="store_true",
        default=True,
        help="Automatically fetch data from sources (default: True)"
    )
    
    parser.add_argument(
        "--price-source",
        choices=["auto", "yahoo", "stooq", "fred", "mock"],
        default="auto",
        help="Price data source (default: auto)"
    )
    
    parser.add_argument(
        "--show-data",
        action="store_true",
        help="Show fetched data summary"
    )
    
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-4o",
        help="LLM model to use"
    )
    
    parser.add_argument(
        "--provider",
        type=str,
        default="OpenAI",
        choices=["OpenAI", "Anthropic", "DeepSeek", "Google", "Groq"],
        help="LLM provider"
    )
    
    return parser.parse_args()


def fetch_data(args):
    """Fetch all required data."""
    print("Fetching data...")
    
    end_date = args.end_date or datetime.now().strftime("%Y-%m-%d")
    
    client = GoldDataClient(
        start_date=args.start_date or (datetime.now() - timedelta(days=args.days)).strftime("%Y-%m-%d"),
        end_date=end_date,
        price_source=args.price_source,
    )
    
    client.fetch_all()
    
    if args.show_data:
        print(client.get_summary())
    
    return client.get_analysis_data()


def run_analysis(args, data):
    """Run the analysis."""
    print("\nRunning analysis...\n")
    
    result = run_gold_analysis(
        symbol=args.symbol,
        start_date=args.start_date or (datetime.now() - timedelta(days=args.days)).strftime("%Y-%m-%d"),
        end_date=args.end_date or datetime.now().strftime("%Y-%m-%d"),
        prices_df=data.get("prices_df"),
        portfolio={"cash": args.cash, "positions": {}},
        show_reasoning=args.show_reasoning,
        selected_analysts=args.analysts,
        news_data=data.get("news_data"),
        macro_data=data.get("macro_data"),
        fundamental_data=data.get("fundamental_data"),
        sentiment_data=data.get("sentiment_data"),
        auto_fetch_data=False,
    )
    
    return result


def display_results(result):
    """Display analysis results."""
    print("\n" + "=" * 60)
    print("XAUUSD GOLD AI ANALYST - ANALYSIS RESULTS")
    print("=" * 60)
    
    recommendation = result.get("recommendation", {})
    risk = result.get("risk_assessment", {})
    
    # Signal
    action = recommendation.get("action", "hold").upper()
    confidence = recommendation.get("confidence", 0)
    
    action_emoji = {
        "STRONG_BUY": "🟢🟢",
        "BUY": "🟢",
        "HOLD": "⚪",
        "SELL": "🔴",
        "STRONG_SELL": "🔴🔴",
    }.get(action, "⚪")
    
    print(f"\n{action_emoji} SIGNAL: {action}")
    print(f"   Confidence: {confidence:.0f}%")
    
    # Trading levels
    print("\n" + "-" * 40)
    print("TRADING LEVELS")
    print("-" * 40)
    
    if recommendation.get("entry_price"):
        print(f"  Entry Price:  ${recommendation.get('entry_price', 0):.2f}")
    
    if recommendation.get("stop_loss"):
        sl = recommendation.get("stop_loss", 0)
        ep = recommendation.get("entry_price", sl)
        risk_pct = abs(sl - ep) / ep * 100
        print(f"  Stop Loss:    ${sl:.2f} ({risk_pct:.1f}%)")
    
    if recommendation.get("take_profit"):
        tp = recommendation.get("take_profit", 0)
        ep = recommendation.get("entry_price", tp)
        reward_pct = abs(tp - ep) / ep * 100
        print(f"  Take Profit:  ${tp:.2f} ({reward_pct:.1f}%)")
    
    if recommendation.get("risk_reward_ratio"):
        rr = recommendation.get("risk_reward_ratio", 0)
        print(f"  Risk/Reward:  1:{rr:.1f}")
    
    if recommendation.get("quantity"):
        print(f"  Position:     {recommendation.get('quantity', 0):.2f} oz")
        value = recommendation.get("quantity", 0) * recommendation.get("entry_price", 0)
        print(f"  Value:        ${value:,.2f}")
    
    # Risk assessment
    print("\n" + "-" * 40)
    print("RISK ASSESSMENT")
    print("-" * 40)
    print(f"  Risk Level:   {risk.get('risk_level', 'unknown').upper()}")
    
    if risk.get("warnings"):
        print("  Warnings:")
        for warning in risk.get("warnings", [])[:3]:
            print(f"    - {warning}")
    
    # Analyst signals
    signals = result.get("analyst_signals", {})
    print("\n" + "-" * 40)
    print("ANALYST SIGNALS")
    print("-" * 40)
    
    signal_counts = {"bullish": 0, "neutral": 0, "bearish": 0}
    
    for analyst, data in signals.items():
        if isinstance(data, dict) and "signal" in data:
            signal = data.get("signal", "neutral")
            conf = data.get("confidence", 50)
            signal_counts[signal] = signal_counts.get(signal, 0) + 1
            
            icons = {"bullish": "🟢", "bearish": "🔴", "neutral": "⚪"}
            icon = icons.get(signal, "⚪")
            name = analyst.replace("_", " ").replace("gold", "").title()
            print(f"  {icon} {name}: {signal} ({conf:.0f}%)")
    
    # Summary
    print("\n" + "-" * 40)
    print("CONSENSUS")
    print("-" * 40)
    total = sum(signal_counts.values())
    if total > 0:
        for signal, count in signal_counts.items():
            pct = count / total * 100
            bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
            print(f"  {signal.capitalize():8}: {bar} {pct:.0f}%")
    
    print("\n" + "=" * 60)


def main():
    """Main entry point."""
    load_dotenv()
    
    args = parse_args()
    
    # Handle special commands
    if args.setup_keys:
        setup_keys_main()
        return
    
    if args.status:
        from src.data_sources.setup_api_keys import load_current_keys, print_status_table
        keys_needed = {
            "FRED_API_KEY": {
                "name": "FRED API Key",
                "description": "Federal Reserve Economic Data - completely free",
                "url": "https://fred.stlouisfed.org/docs/api/api_key.html",
                "required": False,
            },
            "NEWS_API_KEY": {
                "name": "NewsAPI Key",
                "description": "News data (free tier: 100 requests/day)",
                "url": "https://newsapi.org/register",
                "required": False,
            },
        }
        keys_current = load_current_keys()
        print_status_table(keys_needed, keys_current)
        return
    
    # Display config
    end_date = args.end_date or datetime.now().strftime("%Y-%m-%d")
    start_date = args.start_date or (datetime.now() - timedelta(days=args.days)).strftime("%Y-%m-%d")
    
    print(f"\n{'=' * 60}")
    print(f"XAUUSD GOLD AI ANALYST")
    print(f"{'=' * 60}")
    print(f"  Symbol:      {args.symbol}")
    print(f"  Period:      {start_date} to {end_date}")
    print(f"  Analysts:    {args.analysts or 'All'}")
    print(f"  Data Source: {args.price_source}")
    print(f"  LLM Model:   {args.model} ({args.provider})")
    print(f"{'=' * 60}\n")
    
    try:
        # Fetch data
        data = fetch_data(args)
        
        # Run analysis
        result = run_analysis(args, data)
        
        # Display results
        display_results(result)
        
    except KeyboardInterrupt:
        print("\n\nAnalysis cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError: {e}")
        if args.show_reasoning:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
