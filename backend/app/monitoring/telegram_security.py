from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import hmac
import secrets
from typing import Callable


class TelegramSecurityError(RuntimeError):
    """Raised when an inbound Telegram command violates the security policy."""


@dataclass(frozen=True)
class TelegramCommandContext:
    chat_id: str
    user_id: str
    command: str
    now_epoch: int


@dataclass(frozen=True)
class LiveConfirmation:
    nonce: str
    chat_id: str
    user_id: str
    symbol: str
    side: str
    max_notional: str
    mode: str
    expires_at_epoch: int
    digest: str

    @property
    def summary(self) -> str:
        return f"{self.symbol} {self.side} max_notional={self.max_notional} mode={self.mode}"


class TelegramCommandSecurity:
    """Fail-closed inbound Telegram policy with allowlists and one-time LIVE nonce confirmation."""

    def __init__(
        self,
        *,
        allowed_chat_ids: set[str],
        allowed_user_ids: set[str],
        signing_key: bytes,
        state_changing_commands_enabled: bool = False,
        live_nonce_ttl_seconds: int = 90,
        nonce_factory: Callable[[], str] | None = None,
    ) -> None:
        if len(signing_key) < 16:
            raise ValueError("telegram signing key must be at least 16 bytes")
        if live_nonce_ttl_seconds <= 0 or live_nonce_ttl_seconds > 600:
            raise ValueError("live nonce ttl must be within 1..600 seconds")
        self._allowed_chats = {str(x) for x in allowed_chat_ids}
        self._allowed_users = {str(x) for x in allowed_user_ids}
        self._key = bytes(signing_key)
        self._state_enabled = bool(state_changing_commands_enabled)
        self._ttl = int(live_nonce_ttl_seconds)
        self._nonce_factory = nonce_factory or (lambda: secrets.token_urlsafe(18))
        self._issued: dict[str, LiveConfirmation] = {}
        self._consumed: set[str] = set()

    def authorize(self, context: TelegramCommandContext, *, state_changing: bool = False) -> None:
        if str(context.chat_id) not in self._allowed_chats:
            raise TelegramSecurityError("TELEGRAM_CHAT_NOT_ALLOWED")
        if str(context.user_id) not in self._allowed_users:
            raise TelegramSecurityError("TELEGRAM_USER_NOT_ALLOWED")
        if state_changing and not self._state_enabled:
            raise TelegramSecurityError("TELEGRAM_STATE_CHANGING_COMMANDS_DISABLED")

    def issue_live_confirmation(
        self,
        context: TelegramCommandContext,
        *,
        symbol: str,
        side: str,
        max_notional: str,
        mode: str,
    ) -> LiveConfirmation:
        self.authorize(context, state_changing=True)
        if mode.upper() != "LIVE":
            raise TelegramSecurityError("LIVE_CONFIRMATION_REQUIRES_LIVE_MODE")
        normalized_side = side.upper()
        if normalized_side not in {"BUY", "SELL"}:
            raise TelegramSecurityError("INVALID_SIDE")
        nonce = self._nonce_factory()
        if not nonce or nonce in self._issued or nonce in self._consumed:
            raise TelegramSecurityError("NONCE_COLLISION")
        expires = int(context.now_epoch) + self._ttl
        material = "|".join((nonce, str(context.chat_id), str(context.user_id), symbol.upper(), normalized_side, str(max_notional), "LIVE", str(expires)))
        digest = hmac.new(self._key, material.encode("utf-8"), hashlib.sha256).hexdigest()
        confirmation = LiveConfirmation(nonce, str(context.chat_id), str(context.user_id), symbol.upper(), normalized_side, str(max_notional), "LIVE", expires, digest)
        self._issued[nonce] = confirmation
        return confirmation

    def consume_live_confirmation(self, context: TelegramCommandContext, *, nonce: str, digest: str) -> LiveConfirmation:
        self.authorize(context, state_changing=True)
        if nonce in self._consumed:
            raise TelegramSecurityError("LIVE_CONFIRMATION_REPLAY")
        confirmation = self._issued.get(nonce)
        if confirmation is None:
            raise TelegramSecurityError("LIVE_CONFIRMATION_UNKNOWN")
        if confirmation.chat_id != str(context.chat_id) or confirmation.user_id != str(context.user_id):
            raise TelegramSecurityError("LIVE_CONFIRMATION_PRINCIPAL_MISMATCH")
        if int(context.now_epoch) > confirmation.expires_at_epoch:
            self._issued.pop(nonce, None)
            raise TelegramSecurityError("LIVE_CONFIRMATION_EXPIRED")
        if not hmac.compare_digest(confirmation.digest, str(digest)):
            raise TelegramSecurityError("LIVE_CONFIRMATION_DIGEST_INVALID")
        self._issued.pop(nonce, None)
        self._consumed.add(nonce)
        return confirmation

    @staticmethod
    def now_epoch() -> int:
        return int(datetime.now(timezone.utc).timestamp())
