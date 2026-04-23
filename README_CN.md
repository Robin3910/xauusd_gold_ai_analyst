# XAUUSD 黄金AI分析师

一个用于分析和交易XAUUSD（黄金/美元）的多智能体AI系统。该系统采用专业化AI智能体协同工作，分析黄金市场并生成交易信号。

**注意**：本系统仅用于**教育目的**，不进行实际交易。

## 概述

黄金AI分析师采用复杂的多智能体架构，每个智能体专注于黄金市场分析的特定方面：

### 分析型智能体

| 智能体 | 专注领域 | 关键指标 |
|--------|----------|----------|
| **技术分析师** | 价格走势和图表 | EMA、RSI、MACD、布林带、ADX |
| **新闻分析师** | 市场新闻和事件 | 美联储政策、通胀、地缘政治 |
| **情绪分析师** | 市场定位 | CFTC数据、ETF流向、调查数据 |
| **基本面分析师** | 供需关系 | 矿产产量、珠宝需求、央行储备 |
| **宏观分析师** | 经济因素 | 利率、美元、通胀、风险 |

### 决策型智能体

| 智能体 | 职责 |
|--------|------|
| **风险管理器** | 计算仓位规模、止损水平、风险指标 |
| **投资组合管理器** | 综合所有信号生成最终交易建议 |

## 架构图

```
┌─────────────────────────────────────────────────────────┐
│                     启动节点                             │
└─────────────────────────┬───────────────────────────────┘
                          │
         ┌────────────────┼────────────────┐
         │                │                │
         ▼                ▼                ▼
  ┌────────────┐  ┌────────────┐  ┌────────────┐
  │   技术     │  │   新闻     │  │   情绪     │
  │  分析师    │  │  分析师    │  │  分析师    │
  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘
        │                │                │
        └────────────────┼────────────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │      风险管理器      │
              └──────────┬──────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │   投资组合管理器     │──▶ 结束
              └─────────────────────┘
```

## 功能特点

- **多智能体分析**：5个专业分析师 + 风险 + 投资组合管理
- **实时数据**：集成Yahoo Finance、FRED、NewsAPI
- **技术分析**：趋势、动量、均值回归、波动率指标
- **宏观分析**：利率、美元指数、通胀、风险情绪
- **情绪分析**：CFTC持仓、ETF流向、市场调查
- **风险管理**：波动率调整仓位、止损计算
- **无需API密钥**：使用模拟数据进行测试

## 安装

### 前置要求

- Python 3.11+
- Poetry（推荐）或 pip

### 1. 克隆并安装

```bash
git clone https://github.com/your-repo/xauusd-gold-ai-analyst.git
cd xauusd-gold-ai-analyst
poetry install
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env
```

添加可选的API密钥以获取真实数据（系统无需密钥即可使用模拟数据）：

```bash
# .env 文件
OPENAI_API_KEY=your-openai-key           # 用于AI分析
FRED_API_KEY=your-fred-key               # 免费注册: https://fred.stlouisfed.org/docs/api/api_key.html
NEWS_API_KEY=your-newsapi-key           # 免费版: https://newsapi.org/register
```

## 使用方法

### 命令行界面

```bash
# 使用模拟数据运行分析（无需API密钥）
poetry run python -m src.gold_agents.main

# 显示数据源状态
poetry run python -m src.gold_agents.main --status

# 配置API密钥
poetry run python -m src.gold_agents.main --setup-keys

# 指定分析师运行
poetry run python -m src.gold_agents.main --analysts gold_technical_analyst gold_macro_analyst

# 显示详细分析逻辑
poetry run python -m src.gold_agents.main --show-reasoning

# 使用指定数据源
poetry run python -m src.gold_agents.main --price-source yahoo
```

### Python API

```python
from src.gold_agents.workflow import run_gold_analysis
from src.data_sources.client import GoldDataClient

# 方式1：自动获取数据并运行分析
result = run_gold_analysis(
    symbol="XAUUSD",
    show_reasoning=True,
    auto_fetch_data=True
)

# 方式2：手动提供数据
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

### 输出示例

```
============================================================
XAUUSD 黄金AI分析师 - 分析结果
============================================================

🟢 信号：买入
   置信度：72%

------------------------------------------------------------
交易点位
------------------------------------------------------------
  入场价格：  $1950.00
  止损价格：  $1920.00 (1.5%)
  止盈价格：  $2010.00 (3.1%)
  风险回报比：1:2.1
  仓位规模：  5.20 盎司
  仓位价值：  $10,140.00

------------------------------------------------------------
风险评估
------------------------------------------------------------
  风险等级：  中等
  警告：
    - VIX处于较高水平 - 波动性存在

------------------------------------------------------------
分析师信号
------------------------------------------------------------
  🟢 黄金技术分析师：看涨 (75%)
  🟢 黄金新闻分析师：看涨 (68%)
  ⚪ 黄金情绪分析师：中性 (55%)
  🟢 黄金基本面分析师：看涨 (70%)
  🟢 黄金宏观分析师：看涨 (72%)

------------------------------------------------------------
共识
------------------------------------------------------------
  看涨       : ████████████░░░░░░░░░░ 60%
  中性       : ██████░░░░░░░░░░░░░░░░ 25%
  看跌       : ████░░░░░░░░░░░░░░░░░░ 15%
```

## 数据源

### 集成的数据源

| 数据源 | 类型 | API密钥 | 说明 |
|--------|------|---------|------|
| **Yahoo Finance** | 价格 | 不需要 | 通过yfinance获取实时黄金价格 |
| **FRED** | 宏观 | 免费 | 联邦基金利率、CPI、美元指数、VIX |
| **NewsAPI** | 新闻 | 免费版 | 黄金相关新闻文章 |
| **CFTC** | 情绪 | 不需要 | 交易商持仓报告数据 |
| **模拟数据** | 全部 | 不需要 | 无API密钥时用于测试 |

### 免费API注册

1. **FRED API**（完全免费）
   - https://fred.stlouisfed.org/docs/api/api_key.html

2. **NewsAPI**（每天100次请求免费）
   - https://newsapi.org/register

## 项目结构

```
xauusd-gold-ai-analyst/
├── src/
│   ├── gold_agents/           # 多智能体分析系统
│   │   ├── __init__.py
│   │   ├── models.py         # 数据模型
│   │   ├── config.py         # 智能体配置
│   │   ├── workflow.py       # LangGraph工作流
│   │   ├── main.py           # CLI入口
│   │   └── agents/
│   │       ├── technical_analyst.py    # 技术分析
│   │       ├── news_analyst.py         # 新闻分析
│   │       ├── sentiment_analyst.py    # 情绪分析
│   │       ├── fundamental_analyst.py  # 基本面分析
│   │       ├── macro_analyst.py        # 宏观分析
│   │       ├── risk_manager.py         # 风险管理
│   │       └── portfolio_manager.py    # 投资组合管理
│   │
│   └── data_sources/          # 数据获取模块
│       ├── __init__.py
│       ├── client.py         # 统一数据客户端
│       ├── price.py           # 价格数据 (Yahoo, FRED)
│       ├── macro.py           # 宏观经济数据
│       ├── news.py            # 新闻数据
│       ├── cftc.py           # CFTC持仓数据
│       ├── fundamentals.py     # 黄金供需数据
│       ├── free_sources.py    # 免费数据工具
│       └── setup_api_keys.py # API配置向导
│
├── .env.example              # 环境变量模板
├── pyproject.toml           # 依赖管理
└── README.md
```

## 分析组件详解

### 技术分析师

- **趋势分析**：EMA (8/21/55/200)、ADX
- **动量指标**：RSI (14/28)、MACD、价格动量
- **均值回归**：布林带、Z-score
- **波动率**：ATR、波动率区间检测

### 新闻分析师

- **美联储政策**：利率决议、FOMC声明
- **通胀数据**：CPI、PPI、PCE
- **地缘政治**：冲突、制裁、经济危机
- **央行动态**：黄金购买/出售、储备变化

### 情绪分析师

- **CFTC数据**：净持仓、多空比率
- **调查数据**：看涨/看跌百分比
- **ETF流向**：持仓变化、净流入
- **风险情绪**：VIX、恐惧贪婪指数

### 基本面分析师

- **供应端**：矿产产量、废金供应
- **需求端**：珠宝、投资、科技
- **央行数据**：储备变化、购买趋势
- **市场结构**：COMEX库存、ETF持仓

### 宏观分析师

- **利率**：联邦基金利率、实际收益率
- **美元**：DXY指数、美元动能
- **通胀**：CPI、盈亏平衡通胀率
- **风险**：VIX、信用利差、衰退概率

## 配置说明

### 智能体权重

在 `src/gold_agents/config.py` 中调整：

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

### 风险参数

在 `src/gold_agents/risk_manager.py` 中调整：

```python
RISK_PARAMS = {
    "max_position_pct": 0.25,      # 最大仓位25%
    "base_risk_per_trade": 0.01,   # 基础风险1%
    "stop_loss_atr_multiplier": 1.5,
    "take_profit_atr_multiplier": 3.0,
}
```

## 免责声明

本项目仅供**教育和研究目的**。

- 不适用于实际交易或投资
- 不提供投资建议或任何保证
- 作者对任何经济损失不承担责任
- 过往业绩不代表未来表现
- 投资决策请咨询专业财务顾问

## 贡献

1. Fork 本仓库
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

MIT 许可证 - 详见 LICENSE 文件。

---

**基于 LangGraph、LangChain 和 Python 构建**
