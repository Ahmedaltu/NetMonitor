# app/notifications/webhook.py

import requests
from datetime import datetime
from app.utils.logger import logger


class WebhookNotifier:
    """Send alert notifications via HTTP webhook (Slack, Teams, generic)."""

    def __init__(self, config):
        self.url = config.url
        self.timeout = config.timeout
        self._sent_alerts: dict[str, str] = {}  # alert_key -> last severity sent

    def notify(self, alert_key: str, alert: dict):
        """Send webhook if alert state changed (new alert or severity escalation)."""
        severity = alert.get("severity", "unknown")

        # Only send on state transitions (new alert or severity change)
        if self._sent_alerts.get(alert_key) == severity:
            return

        payload = {
            "text": self._format_message(alert),
            "alert": alert,
            "timestamp": datetime.utcnow().isoformat(),
        }

        try:
            resp = requests.post(
                self.url,
                json=payload,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            self._sent_alerts[alert_key] = severity
            logger.info("Webhook sent for %s (%s)", alert_key, severity)
        except requests.RequestException as e:
            logger.error("Webhook failed for %s: %s", alert_key, e)

    def clear(self, alert_key: str):
        """Mark an alert as resolved so re-trigger will send again."""
        if alert_key in self._sent_alerts:
            # Send recovery notification
            payload = {
                "text": f"\u2705 *RESOLVED* — {alert_key} returned to normal",
                "alert": {"metric": alert_key, "severity": "resolved"},
                "timestamp": datetime.utcnow().isoformat(),
            }
            try:
                requests.post(self.url, json=payload, timeout=self.timeout)
            except requests.RequestException:
                pass
            del self._sent_alerts[alert_key]

    @staticmethod
    def _format_message(alert: dict) -> str:
        severity = alert.get("severity", "unknown").upper()
        message = alert.get("message", "")

        icon = "\U0001f534" if severity == "CRITICAL" else "\U0001f7e1"  # red / yellow circle
        return f"{icon} *{severity}* — {message}"
