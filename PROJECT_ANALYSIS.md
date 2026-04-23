# AI Hedge Fund 项目分析报告

> 项目路径: `D:/work_space/ai-hedge-fund`
> 分析日期: 2026-04-23

---

## 1. 项目概述

**AI Hedge Fund** 是一个概念验证项目，探索使用 AI 多智能体系统来做出交易决策。该项目用于**教育和研究目的**，不进行实际交易。

### 核心特性

- 多 Agent 协作分析系统（基于 LangGraph）
- 14+ 种 LLM 模型支持
- 完整的回测框架
- Web 可视化界面
- v2 量化交易模块（开发中）

---

## 2. 技术栈

### 后端技术


| 类别         | 技术                                                                                    |
| ---------- | ------------------------------------------------------------------------------------- |
| **框架**     | FastAPI, LangGraph, LangChain                                                         |
| **LLM 集成** | OpenAI, Anthropic, DeepSeek, Google Gemini, Groq, xAI, Ollama, GigaChat, Azure OpenAI |
| **数据处理**   | Pandas, NumPy, SciPy                                                                  |
| **数据库**    | SQLAlchemy, Alembic (SQLite)                                                          |
| **缓存**     | 内存缓存 (Cache 类)                                                                        |


### 前端技术


| 类别       | 技术                         |
| -------- | -------------------------- |
| **框架**   | React 18, TypeScript       |
| **UI 库** | Tailwind CSS, Radix UI     |
| **流程图**  | @xyflow/react (React Flow) |
| **构建工具** | Vite                       |


---

## 3. 项目目录结构

```
ai-hedge-fund/
├── src/                          # 主应用代码 (v1 基于Agent的系统)
│   ├── agents/                   # 投资代理人智能体 (以著名投资者命名)
│   ├── backtesting/             # 回测引擎
│   ├── cli/                      # 命令行接口
│   ├── data/                     # 数据缓存模块
│   ├── graph/                    # LangGraph 状态管理
│   ├── llm/                      # LLM 模型配置
│   ├── tools/                    # API 工具
│   └── utils/                    # 工具函数
├── v2/                           # 量化交易模块 (正在开发)
│   ├── backtesting/              # 量化回测引擎
│   ├── data/                     # 数据客户端
│   ├── event_study/              # 事件研究框架
│   ├── features/                 # 特征工程
│   ├── pipeline/                  # 执行模拟
│   ├── portfolio/                # 投资组合优化
│   ├── risk/                     # 风险管理
│   ├── signals/                  # 量化信号生成
│   └── validation/               # 验证框架
├── app/                          # Web 应用 (FastAPI + React)
│   ├── backend/                  # FastAPI 后端
│   │   ├── routes/               # API 路由
│   │   ├── services/             # 业务服务
│   │   ├── repositories/         # 数据访问层
│   │   ├── models/               # Pydantic 模型
│   │   ├── database/             # SQLAlchemy 数据库
│   │   └── alembic/              # 数据库迁移
│   └── frontend/                 # React + TypeScript 前端
│       └── src/
│           ├── components/        # React 组件
│           ├── nodes/             # 流程节点组件
│           ├── services/          # API 服务
│           ├── contexts/          # React Context
│           └── hooks/             # 自定义 Hooks
├── docker/                       # Docker 部署配置
├── tests/                        # 测试文件
├── pyproject.toml               # Python 依赖管理
└── README.md                    # 项目文档
```

---

## 4. 核心功能模块

### 4.1 基于投资风格的 Agent 系统

项目包含 14 个以著名投资者命名的分析 Agent：


| Agent                     | 投资风格           | 文件                                    |
| ------------------------- | -------------- | ------------------------------------- |
| **Warren Buffett**        | 价值投资，寻找优秀公司    | `src/agents/warren_buffett.py`        |
| **Ben Graham**            | 格雷厄姆式价值投资，安全边际 | `src/agents/ben_graham.py`            |
| **Charlie Munger**        | 合理价格买入优质企业     | `src/agents/charlie_munger.py`        |
| **Peter Lynch**           | 寻找十倍股，成长投资     | `src/agents/peter_lynch.py`           |
| **Phil Fisher**           | 成长投资，深度调研      | `src/agents/phil_fisher.py`           |
| **Cathie Wood**           | 创新和颠覆性技术投资     | `src/agents/cathie_wood.py`           |
| **Michael Burry**         | 逆向投资，深度价值      | `src/agents/michael_burry.py`         |
| **Bill Ackman**           | 积极型投资，推动变革     | `src/agents/bill_ackman.py`           |
| **Aswath Damodaran**      | 估值专家           | `src/agents/aswath_damodaran.py`      |
| **Stanley Druckenmiller** | 宏观对冲，不对称机会     | `src/agents/stanley_druckenmiller.py` |
| **Mohnish Pabrai**        | Dhandho 投资法    | `src/agents/mohnish_pabrai.py`        |
| **Nassim Taleb**          | 黑天鹅风险管理        | `src/agents/nassim_taleb.py`          |
| **Rakesh Jhunjhunwala**   | 印度市场投资         | `src/agents/rakesh_jhunjhunwala.py`   |
| **Growth Agent**          | 成长型投资分析        | `src/agents/growth_agent.py`          |


### 4.2 核心分析 Agent


| Agent                  | 功能                         | 文件                           |
| ---------------------- | -------------------------- | ---------------------------- |
| **Fundamentals Agent** | 分析基本面数据（盈利能力、成长性、财务健康）     | `src/agents/fundamentals.py` |
| **Sentiment Agent**    | 分析市场情绪                     | `src/agents/sentiment.py`    |
| **Technical Agent**    | 技术指标分析                     | `src/agents/technicals.py`   |
| **Valuation Agent**    | 估值计算（DCF、所有者收益、EV/EBITDA等） | `src/agents/valuation.py`    |


### 4.3 风险管理 (`src/agents/risk_manager.py`)

- 基于波动率调整的风险敞口计算
- 头寸限制计算
- 相关性分析和调整
- 保证金管理

### 4.4 投资组合管理 (`src/agents/portfolio_manager.py`)

- 整合所有分析师信号
- 生成交易决策 (买入/卖出/做空/平仓/持有)
- 头寸规模确定

---

## 5. v2 量化交易模块

项目正在开发 v2 版本，采用纯量化方法而非基于人格的 Agent。

### 架构流程

```
Data (FD API) → Signals → Features → Portfolio Construction → Risk Management → Execution
```

### 核心模块


| 模块              | 功能                                    | 关键文件                 |
| --------------- | ------------------------------------- | -------------------- |
| **Signals**     | 量化信号生成 (`BaseSignal` ABC，输出 [-1, +1]) | `v2/signals/base.py` |
| **Features**    | 特征工程（盈利惊喜、KPI动量、跨行业领先滞后）              | `v2/features/`       |
| **Validation**  | CPCV 和 PBO 验证                         | `v2/validation/`     |
| **Backtesting** | 向量化回测，支持时间点约束和交易成本                    | `v2/backtesting/`    |
| **Portfolio**   | 投资组合优化（均值方差、Black-Litterman、风险平价）     | `v2/portfolio/`      |
| **Risk**        | 风险管理（回撤控制、头寸调整、压力测试）                  | `v2/risk/`           |
| **Pipeline**    | 执行模拟（Almgren-Chriss、流动性分析）            | `v2/pipeline/`       |


---

## 6. 回测引擎

### v1 回测 (`src/backtesting/`)


| 文件              | 功能                          |
| --------------- | --------------------------- |
| `engine.py`     | 回测主引擎                       |
| `controller.py` | Agent 控制器                   |
| `trader.py`     | 交易执行器                       |
| `portfolio.py`  | 投资组合状态管理                    |
| `metrics.py`    | 性能指标计算（Sharpe、Sortino、最大回撤） |
| `valuation.py`  | 投资组合估值                      |
| `benchmarks.py` | 基准计算                        |


### v2 回测 (`v2/backtesting/`)

采用向量化回测，集成交易成本模型和点对点约束验证。

---

## 7. Web 应用架构

### 后端 (`app/backend/`)

```
routes/
├── hedge_fund.py      # 对冲基金运行 API
├── flows.py           # 流程管理
├── flow_runs.py       # 流程执行记录
├── language_models.py # LLM 模型列表
├── api_keys.py        # API 密钥管理
├── storage.py         # 文件存储
└── health.py         # 健康检查

services/
├── portfolio.py       # 投资组合服务
├── backtest_service.py # 回测服务
├── agent_service.py   # Agent 服务
├── graph.py           # 流程图服务
└── ollama_service.py  # Ollama 集成
```

### 前端 (`app/frontend/`)

使用 React Flow 构建可视化流程图界面：


| 节点类型                     | 功能         |
| ------------------------ | ---------- |
| `Stock Analyzer Node`    | 股票分析入口     |
| `Agent Node`             | Agent 执行节点 |
| `Portfolio Manager Node` | 投资组合管理节点   |
| `Investment Report Node` | 投资报告节点     |
| `JSON Output Node`       | JSON 输出节点  |


---

## 8. 数据流架构

```
用户输入 (股票代码、日期范围、选择分析师)
        ↓
LangGraph 工作流创建
        ↓
    ┌───┴───┐
    ↓       ↓
分析师 Agent  执行分析
(基本面、技术面、情绪、估值)
    ↓
风险管理 Agent
(波动率调整、相关性分析、头寸限制)
    ↓
投资组合管理 Agent
(整合信号、生成交易决策)
    ↓
输出交易决策
```

---

## 9. 模块依赖关系

```
src/
├── main.py (入口点)
├── agents/
│   ├── portfolio_manager.py → risk_manager.py, analyst agents
│   ├── risk_manager.py → tools/api.py (价格数据)
│   ├── fundamentals.py → tools/api.py
│   └── valuation.py → tools/api.py
├── backtesting/
│   ├── engine.py → controller.py, trader.py, portfolio.py, metrics.py
│   └── portfolio.py
├── graph/
│   └── state.py (AgentState 定义)
├── tools/
│   └── api.py → data/cache.py, data/models.py
└── utils/
    ├── llm.py → llm/models.py
    └── progress.py

v2/
├── signals/base.py (BaseSignal ABC)
├── data/client.py → data/models.py
└── portfolio/optimizer.py → scipy
```

---

## 10. API 集成

### Financial Datasets API


| 端点                              | 用途   |
| ------------------------------- | ---- |
| `/prices/`                      | 价格数据 |
| `/financial-metrics/`           | 财务指标 |
| `/insider-trades/`              | 内部交易 |
| `/news/`                        | 公司新闻 |
| `/company/facts/`               | 公司事实 |
| `/financials/search/line-items` | 财务报表 |


---

## 11. 关键配置文件


| 文件                                | 用途                |
| --------------------------------- | ----------------- |
| `pyproject.toml`                  | Python 依赖管理       |
| `.env.example`                    | API 密钥模板          |
| `docker/Dockerfile`               | Docker 镜像定义       |
| `docker/docker-compose.yml`       | Docker Compose 配置 |
| `app/frontend/vite.config.ts`     | Vite 构建配置         |
| `app/frontend/tailwind.config.ts` | Tailwind CSS 配置   |


---

## 12. 运行环境

- **Python**: 3.11+
- **Node.js**: 前端开发
- **Docker**: 容器化部署
- **Poetry**: Python 包管理

---

## 13. 使用方式

### CLI 模式

```bash
# 基本使用
poetry run python src/main.py --ticker AAPL,MSFT,NVDA

# 使用本地 Ollama
poetry run python src/main.py --ticker AAPL,MSFT,NVDA --ollama
```

### 回测模式

```bash
poetry run python src/backtester.py --ticker AAPL,MSFT,NVDA
```

### Web 应用

```bash
cd app && docker compose up
```

---

## 14. LLM 模型支持

项目支持以下 LLM 提供商：


| 提供商           | 状态  |
| ------------- | --- |
| OpenAI        | 支持  |
| Anthropic     | 支持  |
| DeepSeek      | 支持  |
| Google Gemini | 支持  |
| Groq          | 支持  |
| xAI           | 支持  |
| Ollama        | 支持  |
| GigaChat      | 支持  |
| Azure OpenAI  | 支持  |


---

## 15. 总结

AI Hedge Fund 是一个功能完整的 AI 量化交易研究项目，具有以下特点：

1. **多 Agent 协作系统**: 基于 LangGraph 实现的投资分析工作流
2. **多种 LLM 支持**: 支持 9+ 种 LLM 提供商
3. **完整的回测框架**: 支持历史数据回测和性能评估
4. **Web 界面**: 现代化的 React 前端，带有可视化流程图
5. **v2 量化模块**: 正在开发中的纯量化交易系统
6. **容器化部署**: Docker 支持便于部署

> **重要提示**: 项目设计用于教育研究，强调不承担实际交易责任。

---

*本报告由 AI 自动生成*