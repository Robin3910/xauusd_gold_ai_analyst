"""
Gold Data Sources Module

Unified data source for XAUUSD analysis.
Provides access to price, news, macro, CFTC, and fundamental data.
"""

from src.data_sources.price import (
    get_gold_prices,
    get_market_data,
    GoldPriceData,
)
from src.data_sources.macro import (
    get_macro_data,
    get_fred_data,
    MacroData,
)
from src.data_sources.news import (
    get_gold_news,
    NewsData,
)
from src.data_sources.cftc import (
    get_cftc_data,
    CftcData,
)
from src.data_sources.fundamentals import (
    get_gold_fundamentals,
    GoldFundamentals,
)
from src.data_sources.client import GoldDataClient
from src.data_sources.free_sources import (
    MultiSourceFetcher,
    fetch_gold_from_stooq,
    fetch_gold_from_yahoo_finance,
    import_csv,
    import_excel,
    PUBLIC_FRED_SERIES,
    test_data_sources,
)

__all__ = [
    # Core classes
    "GoldPriceData",
    "MacroData",
    "NewsData",
    "CftcData",
    "GoldFundamentals",
    "GoldDataClient",
    # Fetch functions
    "get_gold_prices",
    "get_market_data",
    "get_macro_data",
    "get_fred_data",
    "get_gold_news",
    "get_cftc_data",
    "get_gold_fundamentals",
    # Free source helpers
    "MultiSourceFetcher",
    "fetch_gold_from_stooq",
    "fetch_gold_from_yahoo_finance",
    "import_csv",
    "import_excel",
    "PUBLIC_FRED_SERIES",
    "test_data_sources",
]
