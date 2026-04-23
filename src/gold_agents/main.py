"""
Gold Analyst CLI

Command-line interface for the XAUUSD Gold AI Analyst.
"""

import argparse
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pandas as pd

from src.gold_agents.workflow import run_gold_analysis
from src.utils.display import print_trading_output


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="XAUUSD Gold AI Analyst - Multi-agent trading analysis system"
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


def generate_sample_prices(symbol: str, days: int = 180) -> pd.DataFrame:
    """Generate sample price data for testing."""
    import numpy as np
    
    end_date = datetime.now()
    dates = pd.date_range(end=end_date, periods=days, freq="D")
    
    # Simulate gold-like price movement
    np.random.seed(42)
    
    # Start around $1900
    base_price = 1900
    returns = np.random.normal(0.0003, 0.008, days)  # Slight upward drift
    
    prices = base_price * (1 + returns).cumprod()
    
    # Add some trends
    for i in range(days):
        if i > 100:
            prices[i] *= 1 + (i - 100) * 0.0002  # Uptrend
        if i > 150:
            prices[i] *= 0.98  # Correction
    
    # Generate OHLC
    data = []
    for i, (date, close) in enumerate(zip(dates, prices)):
        daily_range = close * 0.005
        open_price = close + np.random.uniform(-daily_range, daily_range)
        high = max(open_price, close) + abs(np.random.normal(0, daily_range))
        low = min(open_price, close) - abs(np.random.normal(0, daily_range))
        volume = int(np.random.uniform(200000, 500000))
        
        data.append({
            "timestamp": date,
            "open": open_price,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        })
    
    return pd.DataFrame(data)


def main():
    """Main entry point."""
    load_dotenv()
    
    args = parse_args()
    
    # Calculate default dates
    end_date = args.end_date or datetime.now().strftime("%Y-%m-%d")
    start_date = args.start_date or (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
    
    print(f"\n{'='*60}")
    print(f"XAUUSD GOLD AI ANALYST")
    print(f"{'='*60}")
    print(f"Symbol: {args.symbol}")
    print(f"Period: {start_date} to {end_date}")
    print(f"Analysts: {args.analysts or 'All'}")
    print(f"{'='*60}\n")
    
    # Generate sample data (replace with real data source)
    print("Generating price data...")
    prices_df = generate_sample_prices(args.symbol, days=200)
    
    # Run analysis
    print("Running analysis...\n")
    
    result = run_gold_analysis(
        symbol=args.symbol,
        start_date=start_date,
        end_date=end_date,
        prices_df=prices_df,
        portfolio={"cash": args.cash, "positions": {}},
        show_reasoning=args.show_reasoning,
        selected_analysts=args.analysts,
        model_name=args.model,
        model_provider=args.provider,
    )
    
    # Display results
    print("\n" + "="*60)
    print("ANALYSIS RESULTS")
    print("="*60)
    
    recommendation = result.get("recommendation", {})
    risk = result.get("risk_assessment", {})
    
    print(f"\nSignal: {recommendation.get('action', 'hold').upper()}")
    print(f"Confidence: {recommendation.get('confidence', 0):.0f}%")
    
    if recommendation.get("entry_price"):
        print(f"\nEntry Price: ${recommendation.get('entry_price', 0):.2f}")
    
    if recommendation.get("stop_loss"):
        print(f"Stop Loss: ${recommendation.get('stop_loss', 0):.2f}")
    
    if recommendation.get("take_profit"):
        print(f"Take Profit: ${recommendation.get('take_profit', 0):.2f}")
    
    if recommendation.get("risk_reward_ratio"):
        print(f"Risk/Reward: 1:{recommendation.get('risk_reward_ratio', 0):.1f}")
    
    if recommendation.get("quantity"):
        print(f"Position Size: {recommendation.get('quantity', 0):.2f} oz")
    
    print(f"\nRisk Level: {risk.get('risk_level', 'unknown').upper()}")
    
    # Show analyst signals summary
    signals = result.get("analyst_signals", {})
    print("\n" + "-"*40)
    print("ANALYST SIGNALS SUMMARY")
    print("-"*40)
    
    for analyst, data in signals.items():
        if isinstance(data, dict) and "signal" in data:
            signal = data.get("signal", "neutral")
            confidence = data.get("confidence", 50)
            signal_icon = "🟢" if signal == "bullish" else "🔴" if signal == "bearish" else "⚪"
            print(f"{signal_icon} {analyst.replace('_', ' ').title()}: {signal} ({confidence:.0f}%)")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
