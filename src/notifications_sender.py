import os
from dataclasses import dataclass
from typing import List
import logging
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials
from firebase_admin import messaging
from message_bus import message_bus
from ai_worker import AiAlert

logger = logging.getLogger(__name__)


@dataclass
class FcmTokenRecord:
    timestamp: datetime
    token: str
    uid: str

    @staticmethod
    def from_dict(data: dict):
        return FcmTokenRecord(
            timestamp=datetime().utcfromtimestamp(data.get('timestamp')),
            token=data.get('token'),
            uid=data.get('uid')
        )


class NotificationsSender:
    def __init__(self):
        cred = credentials.Certificate(os.getcwd() + '/account.json')
        firebase_admin.initialize_app(cred)
        self.db = firebase_admin.firestore.client()
        self.token_deadline = timedelta(weeks=8)

    def start(self):
        message_bus.subscribe('ai_alert', self.handle_ai_alert)
        logger.info("NotificationsSender started")

    def handle_ai_alert(self, alert: AiAlert):
        tokens = self.fetch_notification_tokens()
        self.send_push_notifications(tokens, alert)
        logger.info(f"Push notifications sent to {len(tokens)} devices")

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
            if response.success_count > 0:
                logger.info("Push notifications sent successfully")
            else:
                logger.error("Failed to send push notifications")
                for error in response.errors:
                    logger.error("Error sending push notification: {}".format(error))
