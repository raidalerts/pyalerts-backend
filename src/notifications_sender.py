from dataclasses import dataclass
from typing import List
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials
from firebase_admin import messaging
from firebase_admin import firestore
from message_bus import message_bus
from ai_worker import AiAlert
from config import Settings
import app_logger

logger = app_logger.get(__name__)


@dataclass
class FcmTokenRecord:
    timestamp: datetime
    token: str
    uid: str

    @staticmethod
    def from_dict(data: dict):
        return FcmTokenRecord(
            timestamp=datetime.utcfromtimestamp(data.get('timestamp') / 1000),
            token=data.get('token'),
            uid=data.get('uid')
        )


class NotificationsSender:
    def __init__(self, settings: Settings):
        cred = credentials.Certificate(settings.firebase_credentials_path)
        firebase_admin.initialize_app(cred)
        self.db = firestore.client()
        self.token_deadline = timedelta(weeks=8)

    def start(self):
        message_bus.subscribe('ai_alert', self.handle_ai_alert)
        logger.info("NotificationsSender started")

    def handle_ai_alert(self, alert: AiAlert):
        try:
            tokens = self.fetch_notification_tokens()
            self.send_push_notifications(tokens, alert)
            logger.info(f"Push notifications sent to {len(tokens)} devices")
        except Exception as e:
            logger.error(f"Error sending push notifications: {e}")

    def fetch_notification_tokens(self):
        collection_ref = self.db.collection('fcm_tokens')
        docs = collection_ref.get()
        tokens = []
        for doc in docs:
            token_record = FcmTokenRecord.from_dict(doc.to_dict())
            if datetime.utcnow() - token_record.timestamp > self.token_deadline:
                logger.info(f"Token {token_record.token} is expired, deleting")
                doc.reference.delete()
            else:
                tokens.append(token_record.token)

        return tokens

    def send_push_notifications(self, tokens: List[str], alert: AiAlert):
        batch_size = 500
        total_tokens = len(tokens)
        num_batches = (total_tokens + batch_size - 1) // batch_size

        for i in range(num_batches):
            start_index = i * batch_size
            end_index = min((i + 1) * batch_size, total_tokens)
            batch_tokens = tokens[start_index:end_index]
            message = messaging.MulticastMessage(
                data={
                    "alert": str(alert.alert),
                    "attacker": alert.attacker,
                    "text": alert.text,
                    "confidence": "{:.2f}".format(alert.confidence),
                    "original_text": alert.original_text,
                },
                notification=messaging.Notification(
                    title="Alert: {}".format(alert.attacker),
                    body=alert.text,
                ),
                android=messaging.AndroidConfig(
                    priority="high",
                ),
                tokens=batch_tokens,
            )

            response = messaging.send_multicast(message)
            if response.failure_count > 0:
                logger.warning("Failed to send push notifications to some devices")
                for idx, error in enumerate(response.responses):
                    if 'error' in error:
                        logger.warning(f"Error sending push notification to {batch_tokens[idx]}: {error['error']}")
