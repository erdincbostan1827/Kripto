from __future__ import annotations

from dataclasses import dataclass
import httpx


@dataclass(frozen=True)
class TelegramDelivery:
    delivered: bool
    message_id: int | None = None


class TelegramBotClient:
    """Minimal Telegram Bot API sender with injectable HTTP client for tests."""

    def __init__(self, bot_token: str, chat_id: str, *, client=None, timeout_seconds: float = 5.0):
        if not bot_token or not chat_id:
            raise ValueError("telegram bot token and chat id are required")
        self._token = bot_token
        self._chat_id = str(chat_id)
        self._client = client
        self._timeout = float(timeout_seconds)

    def send(self, message: str) -> TelegramDelivery:
        if not message or not message.strip():
            raise ValueError("telegram message must not be empty")
        endpoint = f"https://api.telegram.org/bot{self._token}/sendMessage"
        payload = {"chat_id": self._chat_id, "text": message, "disable_web_page_preview": True}
        try:
            if self._client is None:
                response = httpx.post(endpoint, json=payload, timeout=self._timeout)
            else:
                response = self._client.post(endpoint, json=payload, timeout=self._timeout)
            response.raise_for_status()
            body = response.json()
            if not body.get("ok"):
                raise RuntimeError("telegram delivery rejected")
            msg_id = (body.get("result") or {}).get("message_id")
            return TelegramDelivery(True, int(msg_id) if msg_id is not None else None)
        except Exception as exc:
            # Never include URL/token or remote body in the public error.
            raise RuntimeError("telegram delivery failed") from exc
