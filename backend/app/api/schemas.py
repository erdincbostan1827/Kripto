from pydantic import BaseModel, Field
from decimal import Decimal
from typing import Any


class AnalyzeRequest(BaseModel):
    symbol: str = 'BTCUSDT'
    timeframe: str = '1h'
    candles: list[dict]


class MultiTimeframeAnalyzeRequest(BaseModel):
    symbol: str = 'BTCUSDT'
    candles_by_timeframe: dict[str, list[dict]]
    weights: dict[str, float] | None = None


class BacktestRequest(BaseModel):
    candles: list[dict]
    initial_equity: Decimal = Decimal('10000')
    risk_fraction: Decimal = Decimal('0.0025')


class TradingAction(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=1, max_length=512)
    mfa_code: str | None = Field(default=None, min_length=6, max_length=12)
    recovery_code: str | None = Field(default=None, min_length=6, max_length=128)


class BootstrapAdminRequest(BaseModel):
    username: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=12, max_length=512)
    bootstrap_token: str = Field(min_length=16, max_length=512)


class HighRiskConfirmationRequest(BaseModel):
    password: str = Field(min_length=12, max_length=512)
    action: str = Field(min_length=3, max_length=80)


class LiveModeRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=500)
    confirmation_nonce: str = Field(min_length=16, max_length=512)


class MfaEnrollmentRequest(BaseModel):
    password: str = Field(min_length=12, max_length=512)


class MfaEnrollmentConfirmRequest(BaseModel):
    code: str = Field(min_length=6, max_length=12, pattern=r'^\d{6,12}$')


class MfaResetRequest(BaseModel):
    target_user_id: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=12, max_length=512)
    confirmation_nonce: str = Field(min_length=16, max_length=512)


class SetupStepRequest(BaseModel):
    setup_id: str = Field(default='default', min_length=1, max_length=128)
    step: int = Field(ge=1, le=8)
    data: dict[str, Any] = Field(default_factory=dict)
