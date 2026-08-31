from __future__ import annotations
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator, model_validator
from .enums import Environment, TradingMode, MarketType

class Settings(BaseModel):
    environment: Environment = Environment.DEV
    mode: TradingMode = TradingMode.PAPER
    market_type: MarketType = MarketType.SPOT
    default_display_symbol: str = "BTCUSDT"
    quote_assets: tuple[str,...] = ("USDT","USDC")
    analysis_timeframes: tuple[str,...] = ("1d","4h","1h","15m","5m")
    max_data_latency_seconds: int = Field(default=10, ge=1, le=300)
    risk_per_trade: Decimal = Field(default=Decimal("0.0025"), gt=0, le=Decimal("0.02"))
    max_daily_loss: Decimal = Field(default=Decimal("0.02"), gt=0, le=Decimal("0.20"))
    max_weekly_loss: Decimal = Field(default=Decimal("0.05"), gt=0, le=Decimal("0.30"))
    max_drawdown: Decimal = Field(default=Decimal("0.10"), gt=0, le=Decimal("0.50"))
    max_portfolio_exposure: Decimal = Field(default=Decimal("0.50"), gt=0, le=1)
    max_single_asset_exposure: Decimal = Field(default=Decimal("0.15"), gt=0, le=1)
    max_correlated_cluster_exposure: Decimal = Field(default=Decimal("0.25"), gt=0, le=1)
    max_quote_asset_exposure: Decimal = Field(default=Decimal("0.85"), gt=0, le=1)
    max_open_positions: int = Field(default=6, ge=1, le=100)
    min_risk_reward: Decimal = Field(default=Decimal("2"), ge=1)
    max_spread_bps: Decimal = Field(default=Decimal("20"), gt=0)
    max_price_deviation_bps: Decimal = Field(default=Decimal("100"), gt=0)
    min_listing_age_days: int = Field(default=30, ge=0)
    min_24h_quote_volume: Decimal = Field(default=Decimal("5000000"), ge=0)
    min_orderbook_depth_notional: Decimal = Field(default=Decimal("100000"), ge=0)
    min_history_bars: int = Field(default=250, ge=50)
    max_universe_size: int = Field(default=50, ge=1, le=1000)
    live_trading_enabled: bool = False
    auto_execution: bool = False
    live_confirmation_token_hash: str | None = None

    @field_validator('analysis_timeframes')
    @classmethod
    def non_empty_tf(cls,v):
        if not v: raise ValueError('analysis_timeframes cannot be empty')
        allowed={'1m','3m','5m','15m','30m','1h','4h','1d'}
        if any(x not in allowed for x in v): raise ValueError('unsupported timeframe')
        return v

    @model_validator(mode='after')
    def safe_defaults(self):
        if self.environment in {Environment.DEV,Environment.TEST,Environment.STAGING} and self.mode==TradingMode.LIVE:
            raise ValueError('LIVE is only permitted in PROD')
        if self.mode==TradingMode.LIVE and not self.live_trading_enabled:
            raise ValueError('LIVE_TRADING_ENABLED gate is false')
        return self
