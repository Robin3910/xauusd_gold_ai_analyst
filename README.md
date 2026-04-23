# XAUUSD Gold AI Analyst

A multi-agent AI system for analyzing and trading XAUUSD (Gold/USD). This system employs specialized AI agents that work together to analyze gold markets and generate trading signals.

**Note**: This system is for **educational purposes only** and does not make actual trades.

## Overview

The Gold AI Analyst uses a sophisticated multi-agent architecture where each agent specializes in a specific aspect of gold market analysis:

### Analysis Agents

| Agent | Focus Area | Key Metrics |
|-------|------------|--------------|
| **Technical Analyst** | Price action & charts | EMA, RSI, MACD, Bollinger Bands, ADX |
| **News Analyst** | Market news & events | Fed policy, inflation, geopolitics |
| **Sentiment Analyst** | Market positioning | CFTC data, ETF flows, surveys |
| **Fundamental Analyst** | Supply & demand | Mining output, jewelry demand, CB reserves |
| **Macro Analyst** | Economic factors | Interest rates, USD, inflation, risk |

### Decision Agents

| Agent | Role |
|-------|------|
| **Risk Manager** | Calculates position sizes, stop-loss levels, risk metrics |
| **Portfolio Manager** | Synthesizes all signals into final trading recommendations |

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     START NODE                          │
└─────────────────────────┬───────────────────────────────┘
                          │
         ┌────────────────┼────────────────┐
         │                │                │
         ▼                ▼                ▼
  ┌────────────┐  ┌────────────┐  ┌────────────┐
  │ Technical  │  │   News     │  │ Sentiment  │
  │ Analyst    │  │ Analyst    │  │ Analyst    │
  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘
        │                │                │
        └────────────────┼────────────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │    Risk Manager     │
              └──────────┬──────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │  Portfolio Manager   │──▶ END
              └─────────────────────┘
```

## Features

- **Multi-Agent Analysis**: 5 specialized analysts + risk + portfolio management
- **Real-Time Data**: Integration with Yahoo Finance, FRED, NewsAPI
- **Technical Analysis**: Trend, momentum, mean reversion, volatility indicators
- **Macro Analysis**: Interest rates, USD Index, inflation, risk sentiment
- **Sentiment Analysis**: CFTC positioning, ETF flows, market surveys
- **Risk Management**: Volatility-adjusted position sizing, stop-loss calculation
- **No API Keys Required**: Works with mock data for testing

## Installation

### Prerequisites

- Python 3.11+
- Poetry (recommended) or pip

### 1. Clone and Install

```bash
git clone https://github.com/your-repo/xauusd-gold-ai-analyst.git
cd xauusd-gold-ai-analyst
poetry install
```

### 2. Configure Environment

```bash
# Copy example env file
cp .env.example .env
```

Add optional API keys for real data (system works without them using mock data):

```bash
# .env file
OPENAI_API_KEY=your-openai-key           # For AI analysis
FRED_API_KEY=your-fred-key               # Free: https://fred.stlouisfed.org/docs/api/api_key.html
NEWS_API_KEY=your-newsapi-key           # Free tier: https://newsapi.org/register
```

## Usage

### Command Line Interface

```bash
# Run analysis with mock data (no API keys needed)
poetry run python -m src.gold_agents.main

# Show data source status
poetry run python -m src.gold_agents.main --status

# Configure API keys
poetry run python -m src.gold_agents.main --setup-keys

# Run with specific analysts
poetry run python -m src.gold_agents.main --analysts gold_technical_analyst gold_macro_analyst

# Show detailed reasoning
poetry run python -m src.gold_agents.main --show-reasoning

# Use specific data source
poetry run python -m src.gold_agents.main --price-source yahoo
```

### Python API

```python
from src.gold_agents.workflow import run_gold_analysis
from src.data_sources.client import GoldDataClient

# Option 1: Auto-fetch data and run analysis
result = run_gold_analysis(
    symbol="XAUUSD",
    show_reasoning=True,
    auto_fetch_data=True
)

# Option 2: Manual data feeding
client = GoldDataClient()
client.fetch_all()

result = run_gold_analysis(
    symbol="XAUUSD",
    prices_df=client.prices.prices_df,
    macro_data=client.macro.to_dict(),
    news_data=client.news.to_list(),
    fundamental_data=client.fundamentals.to_dict(),
    sentiment_data=client.sentiment_data,
)
```

### Output Example

```
============================================================
XAUUSD GOLD AI ANALYST - ANALYSIS RESULTS
============================================================

🟢 SIGNAL: BUY
   Confidence: 72%

------------------------------------------------------------
TRADING LEVELS
------------------------------------------------------------
  Entry Price:  $1950.00
  Stop Loss:    $1920.00 (1.5%)
  Take Profit:  $2010.00 (3.1%)
  Risk/Reward:  1:2.1
  Position:     5.20 oz
  Value:        $10,140.00

------------------------------------------------------------
RISK ASSESSMENT
------------------------------------------------------------
  Risk Level:   MEDIUM
  Warnings:
    - VIX at elevated levels - volatility present

------------------------------------------------------------
ANALYST SIGNALS
------------------------------------------------------------
  🟢 Gold Technical Analyst: bullish (75%)
  🟢 Gold News Analyst: bullish (68%)
  ⚪ Gold Sentiment Analyst: neutral (55%)
  🟢 Gold Fundamental Analyst: bullish (70%)
  🟢 Gold Macro Analyst: bullish (72%)
```

## Data Sources

### Integrated Data Sources

| Source | Type | API Key | Description |
|--------|------|---------|-------------|
| **Yahoo Finance** | Prices | Not required | Real-time gold prices via yfinance |
| **FRED** | Macro | Free | Fed rates, CPI, USD Index, VIX |
| **NewsAPI** | News | Free tier | Gold-related news articles |
| **CFTC** | Sentiment | Not required | Commitment of Traders data |
| **Mock Data** | All | Not required | For testing without API keys |

### Free API Registration

1. **FRED API** (completely free)
   - https://fred.stlouisfed.org/docs/api/api_key.html

2. **NewsAPI** (100 requests/day free)
   - https://newsapi.org/register

## Project Structure

```
xauusd-gold-ai-analyst/
├── src/
│   ├── gold_agents/           # Multi-agent analysis system
│   │   ├── __init__.py
│   │   ├── models.py          # Data models
│   │   ├── config.py          # Agent configuration
│   │   ├── workflow.py        # LangGraph workflow
│   │   ├── main.py           # CLI entry point
│   │   └── agents/
│   │       ├── technical_analyst.py
│   │       ├── news_analyst.py
│   │       ├── sentiment_analyst.py
│   │       ├── fundamental_analyst.py
│   │       ├── macro_analyst.py
│   │       ├── risk_manager.py
│   │       └── portfolio_manager.py
│   │
│   └── data_sources/          # Data fetching modules
│       ├── __init__.py
│       ├── client.py         # Unified data client
│       ├── price.py           # Price data (Yahoo, FRED)
│       ├── macro.py           # Macroeconomic data
│       ├── news.py            # News data
│       ├── cftc.py           # CFTC positioning
│       ├── fundamentals.py    # Gold supply/demand
│       ├── free_sources.py    # Free data utilities
│       └── setup_api_keys.py # API configuration wizard
│
├── .env.example              # Environment template
├── pyproject.toml           # Dependencies
└── README.md
```

## Analysis Components

### Technical Analyst

- **Trend Analysis**: EMA (8/21/55/200), ADX
- **Momentum**: RSI (14/28), MACD, Price momentum
- **Mean Reversion**: Bollinger Bands, Z-score
- **Volatility**: ATR, Volatility regime detection

### News Analyst

- **Fed Policy**: Interest rate decisions, FOMC statements
- **Inflation**: CPI, PPI, PCE data
- **Geopolitics**: Conflicts, sanctions, economic crises
- **Central Banks**: Gold purchases/sales, reserve changes

### Sentiment Analyst

- **CFTC Data**: Net positioning, long/short ratios
- **Surveys**: Bullish/bearish sentiment %
- **ETF Flows**: Holdings changes, inflows
- **Risk Sentiment**: VIX, Fear & Greed index

### Fundamental Analyst

- **Supply**: Mining production, scrap supply
- **Demand**: Jewelry, investment, technology
- **Central Banks**: Reserve changes, buying trends
- **Market Structure**: COMEX inventory, ETF holdings

### Macro Analyst

- **Interest Rates**: Fed Funds, real yields
- **USD**: DXY Index, dollar momentum
- **Inflation**: CPI, breakeven rates
- **Risk**: VIX, credit spreads, recession odds

## Configuration

### Agent Weights

Weights can be adjusted in `src/gold_agents/config.py`:

```python
AGENT_WEIGHTS = {
    "gold_technical_analyst": 0.20,
    "gold_news_analyst": 0.15,
    "gold_sentiment_analyst": 0.15,
    "gold_fundamental_analyst": 0.20,
    "gold_macro_analyst": 0.20,
    "gold_risk_manager": 0.10,
}
```

### Risk Parameters

Adjustable in `src/gold_agents/risk_manager.py`:

```python
RISK_PARAMS = {
    "max_position_pct": 0.25,      # Max 25% of portfolio
    "base_risk_per_trade": 0.01,   # 1% base risk
    "stop_loss_atr_multiplier": 1.5,
    "take_profit_atr_multiplier": 3.0,
}
```

## Disclaimer

This project is for **educational and research purposes only**.

- Not intended for real trading or investment
- No investment advice or guarantees provided
- Creator assumes no liability for financial losses
- Past performance does not indicate future results
- Consult a financial advisor for investment decisions

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License - see LICENSE file for details.

---

**Built with LangGraph, LangChain, and Python**
