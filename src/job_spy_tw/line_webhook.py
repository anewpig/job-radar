"""LINE webhook handlers for notification binding and delivery flows."""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .config import Settings, load_settings
from .notification_service import NotificationService
from .product_store import ProductStore

LINE_WEBHOOK_PATH = "/line/webhook"
LINE_HEALTH_PATH = "/line/health"


def verify_line_signature(channel_secret: str, body: bytes, signature: str) -> bool:
    expected = base64.b64encode(
        hmac.new(
            channel_secret.encode("utf-8"),
            body,
            hashlib.sha256,
        ).digest()
    ).decode("utf-8")
    return hmac.compare_digest(expected, signature.strip())


def extract_line_bind_code(text: str) -> str:
    cleaned = " ".join(str(text).strip().upper().split())
    if not cleaned:
        return ""
    for token in cleaned.replace("：", " ").replace(":", " ").split():
        if token.startswith("LINE-"):
            return token
    return ""


def handle_line_event(
    event: dict[str, Any],
    *,
    store: ProductStore,
    notification_service: NotificationService,
) -> dict[str, Any]:
    event_type = str(event.get("type", "")).strip()
    reply_token = str(event.get("replyToken", "")).strip()
    source = event.get("source") or {}
    source_type = str(source.get("type", "")).strip()
    user_id = str(source.get("userId", "")).strip()

    if event_type == "follow":
        if reply_token:
            notification_service.reply_line_text(
                reply_token,
                "歡迎使用職缺雷達。請先回到網站通知設定頁產生綁定碼，再傳送「綁定 LINE-XXXXXX」給我。",
            )
        return {"event": "follow", "status": "instruction_sent"}

    if event_type != "message":
        return {"event": event_type or "unknown", "status": "ignored"}

    message = event.get("message") or {}
    if str(message.get("type", "")).strip() != "text":
        return {"event": "message", "status": "ignored"}

    bind_code = extract_line_bind_code(str(message.get("text", "")))
    if not bind_code:
        return {"event": "message", "status": "ignored"}

    if source_type != "user" or not user_id:
        if reply_token:
            notification_service.reply_line_text(
                reply_token,
                "請直接私訊官方帳號完成 LINE 綁定，不要在群組或聊天室內操作。",
            )
        return {"event": "message", "status": "invalid_source"}

    result = store.consume_line_bind_code(bind_code, user_id)
    if reply_token:
        notification_service.reply_line_text(
            reply_token,
            (
                "LINE 綁定成功，回到網站重新整理就能看到已綁定狀態。"
                if result["ok"]
                else str(result["message"])
            ),
        )
    return {
        "event": "message",
        "status": "bound" if result["ok"] else "rejected",
        "message": str(result["message"]),
    }


def build_handler(
    *,
    settings: Settings,
    store: ProductStore,
    notification_service: NotificationService,
):
    class LineWebhookHandler(BaseHTTPRequestHandler):
        server_version = "JobRadarLineWebhook/1.0"

        def log_message(self, _format: str, *args: Any) -> None:  # noqa: ANN401
            return

        def _send_json(self, status: int, payload: dict[str, Any]) -> None:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self) -> None:  # noqa: N802
            path = self.path.split("?", 1)[0]
            if path == LINE_HEALTH_PATH:
                self._send_json(200, {"ok": True, "path": LINE_HEALTH_PATH})
                return
            self._send_json(404, {"ok": False, "message": "Not found"})

        def do_POST(self) -> None:  # noqa: N802
            path = self.path.split("?", 1)[0]
            if path != LINE_WEBHOOK_PATH:
                self._send_json(404, {"ok": False, "message": "Not found"})
                return
            if not settings.line_channel_secret:
                self._send_json(500, {"ok": False, "message": "Missing LINE channel secret"})
                return

            content_length = int(self.headers.get("Content-Length", "0") or 0)
            body = self.rfile.read(content_length)
            signature = self.headers.get("X-Line-Signature", "")
            if not verify_line_signature(settings.line_channel_secret, body, signature):
                self._send_json(401, {"ok": False, "message": "Invalid LINE signature"})
                return

            try:
                payload = json.loads(body.decode("utf-8"))
            except json.JSONDecodeError:
                self._send_json(400, {"ok": False, "message": "Invalid JSON payload"})
                return

            results: list[dict[str, Any]] = []
            for event in payload.get("events", []):
                try:
                    results.append(
                        handle_line_event(
                            event,
                            store=store,
                            notification_service=notification_service,
                        )
                    )
                except Exception as exc:  # noqa: BLE001
                    results.append({"event": "unknown", "status": "error", "message": str(exc)})
            self._send_json(200, {"ok": True, "results": results})

    return LineWebhookHandler


def serve_line_webhook(settings: Settings) -> None:
    store = ProductStore(settings.product_state_db_path)
    notification_service = NotificationService(settings)
    handler = build_handler(
        settings=settings,
        store=store,
        notification_service=notification_service,
    )
    with ThreadingHTTPServer(
        (settings.line_webhook_host, settings.line_webhook_port),
        handler,
    ) as server:
        webhook_url = (
            f"{settings.public_base_url}{LINE_WEBHOOK_PATH}"
            if settings.public_base_url
            else f"http://{settings.line_webhook_host}:{settings.line_webhook_port}{LINE_WEBHOOK_PATH}"
        )
        print(f"LINE webhook server listening on {settings.line_webhook_host}:{settings.line_webhook_port}")
        print(f"Webhook URL: {webhook_url}")
        server.serve_forever()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run LINE webhook server for auto binding.")
    parser.add_argument("--host", default=None, help="Webhook host, default from .env")
    parser.add_argument("--port", type=int, default=None, help="Webhook port, default from .env")
    parser.add_argument(
        "--base-dir",
        default=".",
        help="Project base directory for loading .env and SQLite state.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    settings = load_settings(args.base_dir)
    if args.host:
        settings.line_webhook_host = args.host
    if args.port:
        settings.line_webhook_port = args.port
    if not settings.line_channel_secret:
        raise SystemExit("請先在 .env 設定 JOB_RADAR_LINE_CHANNEL_SECRET")
    if not settings.line_channel_access_token:
        raise SystemExit("請先在 .env 設定 JOB_RADAR_LINE_CHANNEL_ACCESS_TOKEN")
    serve_line_webhook(settings)


if __name__ == "__main__":
    main()
